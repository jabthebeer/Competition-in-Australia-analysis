"""Concordances from source-specific groupings to ANZSIC 2006.

Retail Trade industry groups and subgroups, from the ABS Retail Trade methodology (July 2020 edition,
https://www.abs.gov.au/methodologies/retail-trade-australia-methodology/jul-2020), which lists the
ANZSIC classes in each subgroup. Groups that are exactly one class are stored at class level in the
panel; the others are "retail-group" codes (RTxx) whose composition is given here, so coverage
matching can see which classes they contain.
"""

from __future__ import annotations

# Subgroups: ABS code -> ANZSIC classes. "4000*" marks a partial class (non-petrol, convenience-store
# sales of fuel retailers are counted with supermarkets).
RETAIL_SUBGROUPS: dict[str, tuple[str, ...]] = {
    "01": ("4110", "4000*"),
    "02": ("4123",),
    "03": ("4121", "4122", "4129"),
    "04": ("4211", "4212", "4213", "4214"),
    "05": ("4221", "4222", "4229"),
    "06": ("4231", "4232"),
    "07": ("4251",),
    "08": ("4252", "4253", "4259"),
    "09": ("4260",),
    "10": ("4244",),
    "11": ("4241", "4242", "4243"),
    "12": ("4271",),
    "13": ("4272", "4273", "4274", "4279", "4310", "4320"),
    "14": ("4511", "4513"),
    "15": ("4512",),
}
RETAIL_GROUPS: dict[str, tuple[str, ...]] = {
    "41": ("01", "02", "03"),
    "42": ("04", "05", "06"),
    "43": ("07", "08"),
    "44": ("09",),
    "45": ("10", "11", "12", "13"),
    "46": ("14", "15"),
}


def retail_classes(code: str) -> tuple[str, ...]:
    """ANZSIC classes in a Retail Trade industry code (group or subgroup); () for the total."""
    if code in RETAIL_SUBGROUPS:
        return RETAIL_SUBGROUPS[code]
    if code in RETAIL_GROUPS:
        return tuple(c for sub in RETAIL_GROUPS[code] for c in RETAIL_SUBGROUPS[sub])
    return ()


def retail_industry(code: str) -> tuple[str, str]:
    """(industry_level, industry_code) for the panel: exact single classes at class level."""
    if code == "20":
        return "total", ""
    classes = retail_classes(code)
    if code in RETAIL_SUBGROUPS and len(classes) == 1 and not classes[0].endswith("*"):
        return "class", classes[0]
    return "retail-group", f"RT{code}"


def composition() -> dict[str, list[str]]:
    """Retail-group code -> ANZSIC classes (partial classes keep their '*')."""
    out = {}
    for code in [*RETAIL_SUBGROUPS, *RETAIL_GROUPS]:
        level, panel_code = retail_industry(code)
        if level == "retail-group":
            out[panel_code] = list(retail_classes(code))
    return out
