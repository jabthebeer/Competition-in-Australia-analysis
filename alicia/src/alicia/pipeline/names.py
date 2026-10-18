"""Infer an ANZSIC 2006 industry from business names with keyword rules.

Registers such as the ABN Bulk Extract and the ASIC business-names dataset carry no industry. Many
business names say what the business does ("Smith Plumbing", "Harbour Pharmacy"). These rules map
such words to an ANZSIC class (or a division where the word is broad). They favour precision over
coverage: most names match no rule, and a name is classified by its leftmost matching word.

Results are labelled ``ANZSIC06-inferred`` in the panels. Their precision is measured against names
with known ANZSIC codes (``validate``; see docs/data_pipeline_feasibility.md).

OVERRIDES are checked first and win wherever they appear in a name: words that mark a name as a
supplier, an association or a holding company (left unclassified or sent to wholesale), and phrases
that would otherwise trip a trade word ("landscape architects", "dry cleaners"). Version 2 of the
rules (18 Oct 2026) was revised after reading misclassified names in one half of the City of
Melbourne CLUE names; precision is reported on the other half.
"""

from __future__ import annotations

import re
from functools import cache

VERSION = 2

# (code, regex alternatives); "" leaves the name unclassified. Checked before RULES.
OVERRIDES: tuple[tuple[str, str], ...] = (
    ("", r"ASSOCIATION|ASSOC|UNION|INSTITUTE|INSTITUTION|FEDERATION|SOCIETY|COUNCIL|CHAMBER OF|HOLDINGS"),
    ("6923", r"CONSULTING ENGINEERS?|ENGINEERING (?:CONSULTANTS?|DESIGN)"),
    ("", r"CONSULT(?:ING|ANTS?|ANCY)"),
    ("F", r"WHOLESALE(?:RS)?|SUPPLIES|MERCHANTS|DISTRIBUTORS?|IMPORTERS?"),
    ("6921", r"LANDSCAPE ARCHITECT(?:S|URE|URAL)?"),
    ("9531", r"DRY CLEAN(?:ING|ERS?)|LAUNDR(?:Y|IES|OMAT)"),
    ("2619", r"(?:WIND|SOLAR) FARMS?"),
    ("5292", r"FREIGHT FORWARD(?:ING|ERS?)|CUSTOMS BROK(?:ER|ERS|ING)"),
    ("4610", r"TAXI TRUCKS?"),
    ("4511", r"BAKERY CAFE"),
)

# (ANZSIC code, regex alternatives). Codes are checked against the bundled ABS codelist by the tests.
RULES: tuple[tuple[str, str], ...] = (
    ("4623", r"TAXIS?|CABS|RIDE ?SHARE|UBER|LIMOUSINES?|CHAUFFEURS?"),
    ("4271", r"PHARMAC(?:Y|IES|IST|ISTS)|CHEMISTS?"),
    ("4123", r"BOTTLE ?SHOPS?|LIQUOR(?:LAND| STORE| MART)?"),
    ("4520", r"TAVERN|PUB|WINE BAR|COCKTAIL BAR"),
    ("4511", r"CAFE|CAFFE|COFFEE|ESPRESSO|RESTAURANTS?|BISTRO|TRATTORIA|EATERY|BRASSERIE"),
    ("4512", r"TAKE ?AWAY|FISH (?:AND|&|N) CHIPS"),
    ("451", r"PIZZ(?:A|ERIA)|KEBABS?|BURGERS?|SUSHI|NOODLES?"),  # restaurant or takeaway
    ("4513", r"CATERING|CATERERS?"),
    ("1174", r"BAKERY|BAKEHOUSE|PATISSERIE|BAKERS"),
    ("4121", r"BUTCHERS?|BUTCHERY"),
    ("4122", r"FRUIT (?:AND|&) VEG(?:ETABLES?)?|GREENGROCERS?"),
    ("4110", r"SUPERMARKETS?|GROCER(?:Y|IES)|CONVENIENCE STORE|MINI ?MART"),
    ("4274", r"FLORISTS?|FLOWERS"),
    ("4251", r"BOUTIQUE|FASHIONS?|APPAREL|CLOTHING"),
    ("4231", r"HARDWARE(?! LANE)"),
    ("4000", r"SERVICE STATIONS?|PETROL STATIONS?|ROADHOUSE"),
    ("3911", r"CAR SALES|CAR DEALERS?|MOTOR DEALERS?"),
    ("9511", r"HAIR|HAIRDRESS(?:ER|ERS|ING)|BARBERS?|BARBERSHOP|SALON|BEAUTY|NAILS|LASH(?:ES)?|BROWS"),
    ("9111", r"FITNESS|GYM|GYMNASIUM|PERSONAL TRAIN(?:ER|ING)"),
    ("3231", r"PLUMB(?:ING|ER|ERS)|GAS ?FITT(?:ER|ERS|ING)"),
    ("3232", r"ELECTRICAL|ELECTRICIANS?|SPARKY"),
    ("3242", r"CARPENTRY|CARPENTERS?|JOINERY"),
    ("3244", r"PAINTING|PAINTERS?|DECORATORS?"),
    ("3243", r"TILING|TILERS?"),
    ("3223", r"ROOFING|ROOFERS?"),
    ("3221", r"CONCRETING|CONCRETERS?"),
    ("3222", r"BRICKLAY(?:ING|ER|ERS)"),
    ("3241", r"PLASTERING|PLASTERERS?"),
    ("3245", r"GLAZING|GLAZIERS?"),
    ("3291", r"LANDSCAP(?:E|ES|ING|ERS?)"),
    ("7313", r"GARDENING|GARDENERS?|LAWN|LAWNS|MOWING"),
    ("7312", r"PEST CONTROL|PEST MANAGEMENT"),
    ("7311", r"CLEANING|CLEANERS?"),
    ("3011", r"BUILDERS?"),
    ("E", r"CONSTRUCTIONS?"),
    ("6720", r"REAL ESTATE|REALTY|PROPERTY MANAGEMENT"),
    ("6932", r"ACCOUNTING|ACCOUNTANTS?|BOOKKEEPING|TAX AGENTS?"),
    ("6931", r"LAWYERS?|SOLICITORS?|LEGAL|BARRISTERS?|LAW (?:FIRM|PRACTICE|GROUP|OFFICE)"),
    ("8710", r"CHILD ?CARE|EARLY LEARNING|DAY ?CARE|OSHC"),
    ("8010", r"KINDERGARTEN|KINDY|PRE-?SCHOOL"),
    ("5102", r"COURIERS?"),
    ("4610", r"HAULAGE|TRUCKING|REMOVALS?|REMOVALISTS?"),
    ("9412", r"SMASH REPAIRS?|PANEL BEAT(?:ING|ERS?)|COLLISION REPAIRS?"),
    ("9419", r"MECHANICS?|AUTO REPAIRS?|CAR REPAIRS?"),
    ("8531", r"DENTAL|DENTISTS?"),
    ("8533", r"PHYSIO(?:THERAPY)?"),
    ("8534", r"CHIROPRACT(?:IC|OR|ORS)|OSTEOPATH(?:Y|S)?"),
    ("8532", r"OPTOMETR(?:Y|ISTS?)|OPTICAL|OPTICIANS?"),
    ("8511", r"MEDICAL (?:CENTRE|CLINIC|PRACTICE)|GENERAL PRACTICE"),
    ("6970", r"VETERINARY|VETS|ANIMAL HOSPITAL"),
    ("6921", r"ARCHITECTS?|ARCHITECTURE|ARCHITECTURAL"),
    ("6991", r"PHOTOGRAPHY|PHOTOGRAPHERS?|PHOTOGRAPHIC"),
    ("7000", r"SOFTWARE|IT SOLUTIONS|IT SERVICES|WEB DESIGN"),
    ("6940", r"ADVERTISING"),
    ("7211", r"RECRUITMENT|STAFFING"),
    ("1611", r"PRINTING|PRINTERS"),
    ("7712", r"SECURITY (?:SERVICES|GUARDS?|PATROLS?)|PATROLS"),
    ("7220", r"TRAVEL"),
    ("4400", r"MOTEL|ACCOMMODATION|BED (?:AND|&) BREAKFAST|GUEST ?HOUSE"),
    ("9520", r"FUNERALS?"),
    ("A", r"FARMS?|FARMING|PASTORAL|ORCHARDS?|VINEYARDS?|GRAZING"),
)


@cache
def _pattern(rules: tuple[tuple[str, str], ...]) -> re.Pattern:
    alts = [f"(?P<r{i}>{pat})" for i, (_, pat) in enumerate(rules)]
    return re.compile(r"(?<![A-Z0-9])(?:" + "|".join(alts) + r")(?![A-Z0-9])")


def classify(*names: str | None) -> str:
    """ANZSIC code for the leftmost override found, else the leftmost matching rule, or ""."""
    text = " | ".join(n for n in names if n).upper().replace("&AMP;", "&")
    if not text:
        return ""
    for rules in (OVERRIDES, RULES):
        if m := _pattern(rules).search(text):
            return rules[int(m.lastgroup[1:])][0]
    return ""


def level(code: str) -> str:
    """Level of an inferred code ("" for no code, e.g. an unused category)."""
    return "division" if code.isalpha() else {3: "group", 4: "class"}.get(len(code), "")


def matches(code: str, true: str) -> bool:
    """Whether an inferred code agrees with a true ANZSIC class (at the inferred code's level)."""
    from .. import anzsic

    return anzsic.division(true) == code if code.isalpha() else true.startswith(code)


def validate(names: list[str], truth: list[str]) -> dict:
    """Precision by inferred code (share of classified names whose true class matches, at the level
    of the inferred code) and overall coverage, given names with known ANZSIC classes."""
    hits: dict[str, list[int]] = {}
    classified = 0
    for name, true in zip(names, truth, strict=True):
        code = classify(name)
        if not code:
            continue
        classified += 1
        hits.setdefault(code, []).append(int(matches(code, true)))
    per_code = {c: {"n": len(v), "precision": round(sum(v) / len(v), 3)} for c, v in sorted(hits.items())}
    correct = sum(sum(v) for v in hits.values())
    return {
        "names": len(names),
        "classified": classified,
        "coverage": round(classified / len(names), 3) if names else 0.0,
        "precision": round(correct / classified, 3) if classified else 0.0,
        "by_code": per_code,
    }
