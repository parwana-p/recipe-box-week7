# Critique — Round 3: Task 3 Ingredient Scaling

Reviewed files:
- [`main.py`](file:///c:/Users/parwa/Documents/recipe-task-c/main.py) (lines 148–210)
- [`test_main.py`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py) (lines 133–290)

---

## Verification of Problems from Round 2

| Issue from Round 2 | Status | Details |
|---|---|---|
| **Problem 1: Missing behavioral test for negative factor** (Rubric: **Tests**) | **FIXED** | Added [`test_scaled_factor_negative_422`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L282-L290), verifying that `factor=-1` triggers validation and returns HTTP 422. |

---

## Rubric Compliance Assessment

### 1. Correctness
- **Decimals (`"1.5 cups"`):** Parsed and scaled correctly (`"1.5"` parsed to float, formatted cleanly without trailing `.0` when whole).
- **Fractions (`"1/2 tsp"`):** `_QTY_RE` matches fractional quantities (`[./]`) and `_parse_quantity` evaluates them via division (`0.5`).
- **Ingredients with no number (`"salt"`):** Regex fails match on non-numeric prefixes, returning ingredient unchanged.
- **Number without unit (`"3 eggs"`):** Captures leading digits and preserves the remaining text without requiring a unit.
- **Invalid factor (0, negative, missing):** FastAPI's `Query(gt=0)` enforces positive non-zero factor; missing, zero, or negative query params return HTTP 422.
- **Unknown ID:** Nonexistent recipe ID queries return HTTP 404.

*Result:* **PASS**

### 2. Tests
Each required scenario has a dedicated, passing behavioral test:
- Decimals: [`test_scaled_decimal_result_formatted_cleanly`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L225-L241) (`"1.5 tsp vanilla"`)
- Fractions: [`test_scaled_fraction_quantity`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L243-L261) (`"1/2 tsp salt"`, `"1/4 cup oil"`)
- No number: [`test_scaled_ingredient_without_quantity`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L178-L195) (`"a pinch of pepper"`)
- Number without unit: [`test_scaled_number_without_unit`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L263-L280) (`"3 eggs"`)
- Invalid factor - 0: [`test_scaled_factor_zero_422`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L214-L223)
- Invalid factor - Negative: [`test_scaled_factor_negative_422`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L282-L290)
- Invalid factor - Missing: [`test_scaled_missing_factor_422`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L203-L212)
- Unknown recipe ID: [`test_scaled_unknown_recipe_404`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py#L197-L201)

*Result:* **PASS**

### 3. Clarity
- **Readability:** Functions are compact, well-documented with clear docstrings, and leverage standard library regex and float conversion.
- **Helper naming:** `_parse_quantity` and `_scale_ingredient` are concise, descriptive, and accurately reflect their purpose.
- **No duplicated logic:** Helper functions cleanly isolate regex matching, numeric parsing, formatting, and route handling.

*Result:* **PASS**

---

## Verdict

Every rubric item has been verified and fully passes.

VERDICT: ACCEPT
