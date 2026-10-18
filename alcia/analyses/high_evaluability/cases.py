"""Case specifications for the high-evaluability batch (docs/pap_high_evaluability.md, section 3).

One entry per reform. Units are states; times are financial years (named by the year they end)
for business counts and productivity, and quarters (year * 4 + quarter - 1) for prices. Each
cohort lists the states that adopted together, their first exposed period, the last period used
and the clean controls (states not treated at any time up to that last period).

First exposed financial year: the one containing the effective date, unless that date is the
last day of the year (30 June), in which case the next. Quarters follow the same rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from alcia.evaluate.stacked import Cohort


def q(year: int, quarter: int) -> int:
    return year * 4 + quarter - 1


@dataclass(frozen=True)
class PriceSpec:
    codes: tuple[str, ...]  # CPI expenditure classes; the first is the main price outcome
    cohorts: tuple[Cohort, ...]
    expected: str  # "up" or "down"
    role: str  # "secondary" or "descriptive"
    exclude_subgroups: tuple[str, ...]  # related CPI subgroups left out of the placebo classes
    start: int = q(2001, 1)


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    records: tuple[str, ...]
    family: str | None
    hypothesis: str  # register direction tested: enhancing, weakening or mixed
    classes: tuple[str, ...]  # ANZSIC classes directly affected (the treated group)
    cohorts: tuple[Cohort, ...]
    division: str  # ANZSIC division for productivity and pay
    design: str
    start: int = 2008
    price: PriceSpec | None = None
    grade_cap: tuple[str, str] | None = None  # (highest grade, reason), set before unblinding
    extend_to_2019: bool = False  # robustness: add 2018-19 (only where no control is treated by then)
    notes: tuple[str, ...] = field(default_factory=tuple)


ALL_BUT = lambda *xs: tuple(s for s in ("NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT") if s not in xs)  # noqa: E731

CASES: tuple[Case, ...] = (
    Case(
        id="nt-container-deposits-2012",
        title="Northern Territory container deposit scheme (2012)",
        records=("nt-cds-2012",),
        family="container-deposit-scheme",
        hypothesis="mixed",
        classes=("1211", "1212", "2922"),
        cohorts=(Cohort(("NT",), 2012, 2017, ("NSW", "VIC", "QLD", "WA", "TAS", "ACT")),),
        division="C",
        design="One treated territory (NT, from January 2012) against states without a scheme; window ends "
        "2016-17, before NSW's scheme. SA (scheme since 1977) is excluded.",
        price=PriceSpec(
            codes=("115520", "40087"),
            cohorts=(Cohort(("NT",), q(2012, 1), q(2017, 3), ("NSW", "VIC", "QLD", "WA", "TAS", "ACT")),),
            expected="up",
            role="secondary",
            exclude_subgroups=("Non-alcoholic beverages", "Alcoholic beverages"),
        ),
        notes=("NT business counts start in 2009-10, so there are two pre-reform years.",),
    ),
    Case(
        id="childcare-nqf-2012",
        title="National Quality Framework for childcare (2012): the WA stagger",
        records=("cth-nqf-childcare-2012", "wa-nqf-childcare-2012"),
        family="childcare-nqf",
        hypothesis="weakening",
        classes=("8710",),
        cohorts=(Cohort(ALL_BUT("WA"), 2012, 2012, ("WA",)),),
        division="Q",
        design="The framework started in January 2012 everywhere except WA (August 2012). The only clean "
        "comparison is 2011-12, when the other states had it and WA did not: a first-year effect.",
        price=PriceSpec(
            codes=("115498",),
            cohorts=(Cohort(ALL_BUT("WA"), q(2012, 1), q(2012, 2), ("WA",)),),
            expected="up",
            role="descriptive",
            exclude_subgroups=("Domestic and household services",),
        ),
    ),
    Case(
        id="retail-energy-deregulation-2013-2016",
        title="Retail energy price deregulation (SA 2013, NSW 2014, south-east Queensland 2016)",
        records=(
            "sa-energy-price-deregulation-2013",
            "nsw-energy-price-deregulation-2014",
            "qld-seq-energy-price-deregulation-2016",
        ),
        family="retail-energy-price-deregulation",
        hypothesis="enhancing",
        classes=("2640",),
        cohorts=(
            Cohort(("SA",), 2013, 2018, ("TAS", "ACT", "WA", "NT")),
            Cohort(("NSW",), 2015, 2018, ("TAS", "ACT", "WA", "NT")),
            Cohort(("QLD",), 2017, 2018, ("TAS", "ACT", "WA", "NT")),
        ),
        extend_to_2019=True,
        division="D",
        design="Staggered: each deregulating state against the states whose prices stayed regulated "
        "(Tasmania, ACT, WA, NT). Victoria (deregulated 2009) is excluded.",
        price=PriceSpec(
            codes=("40055",),
            cohorts=(
                Cohort(("SA",), q(2013, 1), q(2019, 2), ("TAS", "ACT", "WA", "NT")),
                Cohort(("NSW",), q(2014, 3), q(2019, 2), ("TAS", "ACT", "WA", "NT")),
                Cohort(("QLD",), q(2016, 3), q(2019, 2), ("TAS", "ACT", "WA", "NT")),
            ),
            expected="down",
            role="secondary",
            exclude_subgroups=("Utilities",),
        ),
        grade_cap=(
            "Weak",
            "Business counts place a retailer in its head-office state, not where it sells; and state "
            "network charges moved electricity prices differently over the same years.",
        ),
    ),
    Case(
        id="heavy-vehicle-national-law-2014",
        title="Heavy Vehicle National Law (2014)",
        records=tuple(f"{s}-heavy-vehicle-national-law-2014" for s in ("act", "nsw", "qld", "sa", "tas", "vic")),
        family="heavy-vehicle-national-law",
        hypothesis="enhancing",
        classes=("4610",),
        cohorts=(Cohort(("NSW", "VIC", "QLD", "SA", "TAS", "ACT"), 2014, 2018, ("WA", "NT")),),
        extend_to_2019=True,
        division="I",
        design="Six jurisdictions adopted on 10 February 2014; WA and NT never did.",
    ),
    Case(
        id="vic-taxi-licensing-2014",
        title="As-of-right taxi licences in Victoria (2014)",
        records=("vic-taxi-licensing-2014",),
        family=None,
        hypothesis="enhancing",
        classes=("4623",),
        cohorts=(Cohort(("VIC",), 2015, 2015, ALL_BUT("VIC")),),
        division="I",
        design="Victoria against all other states, using only 2014-15, the one post-reform year before "
        "ride-share legalisation and driver GST registration.",
        price=PriceSpec(
            codes=("40086",),
            cohorts=(Cohort(("VIC",), q(2014, 3), q(2015, 2), ALL_BUT("VIC")),),
            expected="down",
            role="descriptive",
            exclude_subgroups=("Urban transport fares",),
        ),
        grade_cap=(
            "Weak",
            "Unlicensed UberX began in Melbourne in 2014, the same year, and only one post-reform year is usable.",
        ),
    ),
    Case(
        id="legal-profession-uniform-law-2015",
        title="Legal Profession Uniform Law (NSW and Victoria, 2015)",
        records=("nsw-legal-profession-uniform-law-2015", "vic-legal-profession-uniform-law-2015"),
        family="legal-profession-uniform-law",
        hypothesis="enhancing",
        classes=("6931",),
        cohorts=(Cohort(("NSW", "VIC"), 2016, 2018, ("QLD", "SA", "WA", "TAS", "ACT", "NT")),),
        extend_to_2019=True,
        division="M",
        design="NSW and Victoria adopted on 1 July 2015; the other jurisdictions had not by 2017-18.",
    ),
    Case(
        id="rideshare-legalisation-2015-2018",
        title="Ride-share legalisation (2015 to 2018)",
        records=tuple(
            f"{s}-rideshare-{y}"
            for s, y in (
                ("act", 2015),
                ("nsw", 2015),
                ("sa", 2016),
                ("qld", 2016),
                ("tas", 2016),
                ("vic", 2017),
                ("nt", 2017),
            )
        ),
        family="rideshare-legalisation",
        hypothesis="enhancing",
        classes=("4623",),
        cohorts=(
            Cohort(("ACT", "NSW"), 2016, 2017, ("VIC", "NT", "WA")),
            Cohort(("SA", "QLD", "TAS"), 2017, 2017, ("VIC", "NT", "WA")),
            Cohort(("VIC", "NT"), 2018, 2018, ("WA",)),
        ),
        division="I",
        design="Staggered: each group of states that legalised in the same year against states that had "
        "not yet (WA legalised in 2019).",
        price=PriceSpec(
            codes=("40086",),
            cohorts=(
                Cohort(("ACT", "NSW"), q(2015, 4), q(2017, 2), ("VIC", "NT", "WA")),
                Cohort(("SA", "QLD", "TAS"), q(2016, 3), q(2017, 2), ("VIC", "NT", "WA")),
                Cohort(("VIC",), q(2017, 3), q(2018, 4), ("WA",)),
                Cohort(("NT",), q(2018, 1), q(2018, 4), ("WA",)),
            ),
            expected="down",
            role="descriptive",
            exclude_subgroups=("Urban transport fares",),
        ),
        grade_cap=(
            "Weak",
            "Ride-sharing ran before it was legal in most cities, and drivers had to register for GST from "
            "August 2015 wherever it ran, so legal dates are not the economic dates.",
        ),
    ),
)
