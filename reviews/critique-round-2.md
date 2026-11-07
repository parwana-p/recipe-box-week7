# Critique — Round 2: Task 3 Ingredient Scaling

Reviewed files:
- [`main.py`](file:///c:/Users/parwa/Documents/recipe-task-c/main.py) (lines 148–210)
- [`test_main.py`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py) (lines 133–279)

---

## Verification of Problems from Round 1

| Round 1 Issue | Status | Details |
|---|---|---|
| **Problem 1: Fraction quantities silently dropped** (Correctness) | **FIXED** | `_QTY_RE` was updated to `r"^(\d+(?:[./]\d+)?)\s+(.*)"` and helper `_parse_quantity` was added. Fractions such as `"1/2 tsp salt"` and `"1/4 cup oil"` now parse and scale correctly. |
| **Problem 2: No test for fraction input** (Tests) | **FIXED** | Added `test_scaled_fraction_quantity`, verifying both `"1/2 tsp salt"` scaling to `"1 tsp salt"` and `"1/4 cup oil"` scaling to `"0.5 cup oil"`. |
| **Problem 3: `factor=0` returns 422** (Correctness) | **ACCEPTABLE** | FastAPI's `Query(gt=0)` returns 422, which is explicitly permitted by the rubric ("returns 400/422"). |
| **Problem 4: `"3 eggs"` case not explicitly tested** (Tests) | **FIXED** | Added dedicated test `test_scaled_number_without_unit` verifying `["3 eggs"]` scaled by 2 returns `["6 eggs"]`. |

---

## New Problems Found

### Problem 1 — Missing behavioral test for negative factor (Rubric: **Tests**)

Rubric Item 1 states:
> *"invalid factor (0, negative, missing) returns 400/422"*

Rubric Item 2 requires:
> *"each case above is covered by a behavioral test."*

In `test_main.py`:
- Missing factor is tested by `test_scaled_missing_factor_422`.
- Factor of 0 is tested by `test_scaled_factor_zero_422`.
- **Negative factor** (e.g. `factor=-1` or `factor=-0.5`) is **not tested** anywhere in `test_main.py`.

Although `main.py` correctly rejects negative numbers with HTTP 422 thanks to `Query(gt=0)`, Rubric Item 2 requires a dedicated behavioral test covering the negative factor case.

---

## Rubric Evaluation Summary

| Rubric Item | Status | Notes |
|---|---|---|
| **1. Correctness** | **PASS** | Supports decimals (`"1.5 cups"`), fractions (`"1/2 tsp"`), ingredients with no number (`"salt"`), numbers without unit (`"3 eggs"`), invalid factors (0, negative, missing → 422), and unknown id → 404. |
| **2. Tests** | **FAIL** | All cases are covered by behavioral tests except for the negative factor case (`factor < 0`). |
| **3. Clarity** | **PASS** | Code is well-structured, clear helper functions (`_parse_quantity`, `_scale_ingredient`), descriptive variable names, and no logic duplication. |

---

VERDICT: REVISE
