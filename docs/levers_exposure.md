# Phase 5: counting the businesses each rule can bind

*17 November 2026. Draft by Claude Code on the legislation branch, for the owner to check. Phase 5 of the [re-evaluation plan](plan_levers_reevaluation.md) (DECISIONS E-178). The counting is in `alicia/src/alicia/menu/exposure.py` (`size_basis`, `form_limited`) and `explorer.py`; tests are in `alicia/tests/test_exposure.py`.*

## What changed

Until now, every rule counted all the businesses in the industries it reaches. A rule that binds only employers, or only businesses above a size threshold, was counted as reaching every business. Payroll tax, for example, was counted at 100% of businesses in each state.

The framework's own note already said that a rule binding only some businesses in an industry (those above a threshold, or doing one activity) is an upper bound and is never classed as wide. The counting applied this to activities, but not to thresholds. It now applies to both. It also uses the size bands the ABS publishes.

| A rule that binds | Counted as | Exact or upper bound |
|---|---|---|
| Every business in its industries | All businesses | Exact |
| Every employer (it starts with the first employee) | Businesses with employees | Exact |
| Employers above a payroll threshold | Businesses with employees | Upper bound. Exception: a threshold under $10,000 a year (Victoria's $7,500 for workers' compensation) is counted as every employer |
| Employers above an employee threshold | Businesses with 20 or more, or 200 or more, employees; with employees, below 20 | Upper bound, unless the threshold is a band's edge |
| Businesses above a turnover, revenue or asset threshold | All businesses | Upper bound. Exception: a turnover threshold no higher than GST's ($75,000), because the counts hold only businesses registered for GST |
| Only some legal forms, none of them sole traders (for example, companies only) | All businesses | Upper bound (the counts are not split by legal form) |
| Businesses doing an activity | All businesses | Upper bound (as before) |

A register item now counts the businesses that the requirements inside it bind: the widest of their bases, and an upper bound if any of them is one.

**Source for the GST rule.** The ABS counts "only actively trading businesses in the Australian market sector", which are "ABNs from the non-profiled population that are actively remitting Goods and Services Tax (GST)" (ABS, *Counts of Australian Businesses, including Entries and Exits*, methodology, July 2020 to June 2024). The size bands are non-employing, 1 to 19, 20 to 199, and 200 or more employees.

## Effect on the impact classes

12 ranked rules move from Major, wide to Minor. Each is now counted as an upper bound, and an upper bound is never wide.

| Rule | Was counted | Now counted |
|---|---|---|
| Payroll tax in each of the 8 states and territories | 100% of businesses | Up to the employing businesses: 33% (SA) to 42% (ACT) |
| Mandatory climate-related financial reporting | 100% | Up to 100%: it binds only entities that meet its size or emissions tests |
| Modern slavery statements | 100% | Up to 100%: revenue of $100 million or more |
| The Australian Privacy Principles | 100% | Up to 100%: turnover above $3 million |
| Workplace gender equality reporting | 100% | Up to the businesses with 20 or more employees: 2.7% (100 or more employees) |

The levers page now ranks 2 Severe, 25 Major wide, 260 Major narrow and 404 Minor rules.

**Still wide, now counted exactly:** the rules that bind every employer: workers' compensation, long service leave, superannuation, PAYG withholding, fringe benefits tax, paid parental leave, Fair Work terms, work rights checks, and Victoria's occupational health and safety duty. Each reaches 33% to 42% of the businesses in its jurisdiction, well above the 25% line.

**Unchanged:** the primary work health and safety duty in the 7 jurisdictions with the model law stays at 100%. It binds every person conducting a business, not only employers.

## The plan's three checks

| Check | Result |
|---|---|
| Rules that name only a division, or no industry (15 items) | 12 reach every industry correctly (payroll tax, climate reporting, foreign investment, non-compete clauses, Victoria's occupational health and safety law), and are now sharpened by size. 3 name divisions that their laws do not narrow further (mandatory product standards; import tariffs; the right to disconnect). The right to disconnect item names finance and professional services, but the law reaches every employee: a question for re-marking (phase 7) |
| Upper bounds state their condition | All 28 register items coded as binding some businesses say which in their coding note. 4 requirements were upper bounds with no stated condition, and now state it from their quoted section (domestic minimum tax, ransomware payment reports, the Skilling Australians Fund levy, foreign investment notification). CATSI reporting, which binds only Aboriginal and Torres Strait Islander corporations, was counted as every business; it now states that condition. ASIC's annual review fee binds only companies, so it is now an upper bound |
| Rules near the 25% line | The closest are the SA and Victorian employer rules, at 32.7% and 33.2%. They are exact counts, so the line is not in doubt |

## On the site

- **Legislative levers:** an item's impact section says which businesses are counted ("Only employing businesses") and why a figure is an upper bound. The section's summary shows "up to" where it applies.
- **Register data:** a new "Businesses counted" column.
- **Methodology:** the reliance row for businesses reached says what is counted.

## Limits

- **Payroll thresholds** are counted at all employers, an upper bound. The 20 or more employees band is not a bound, because a business with fewer employees can pass a payroll threshold on wages.
- **The $10,000 payroll cut-off** is a judgement, made so that Victoria's workers' compensation ($7,500 a year) is counted with the other states' as every employer.
- **Non-compete clauses** (a non-legislative barrier) are still counted at every business, though they concern employees; counted as employers, they would still be Severe.
- **Legal form** cannot be counted, so a rule for companies only is an upper bound rather than a count of companies.
