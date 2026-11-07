# Critique — Round 1: Task 3 Ingredient Scaling

Reviewed files:
- [`main.py`](file:///c:/Users/parwa/Documents/recipe-task-c/main.py) (lines 148–200)
- [`test_main.py`](file:///c:/Users/parwa/Documents/recipe-task-c/test_main.py) (lines 133–240)

---

## Problems Found

### Problem 1 — Fraction quantities silently dropped (Rubric: **Correctness**)

The regex `_QTY_RE` is defined as:

```python
_QTY_RE = re.compile(r"^(\d+(?:\.\d+)?)\s+(.*)")
```

It matches only decimal numbers (`\d+` or `\d+.\d+`). A fraction like `1/2 tsp salt` produces **no match**, so `_scale_ingredient` returns the string **unchanged** — the fraction is **not scaled at all**.

Rubric item *"fractions ('1/2 tsp')"* explicitly requires this case to be handled. The implementation silently treats `"1/2 tsp salt"` the same as `"salt"` (a no-number ingredient), producing a wrong result with no error.

**Verified** by running:
```
'1/2 tsp salt'  ->  regex match: None   (factor=2, result stays "1/2 tsp salt", not "1 tsp salt")
```

---

### Problem 2 — No test for fraction input (Rubric: **Tests**)

There is no test that passes an ingredient with a fractional quantity (e.g., `"1/2 tsp salt"`) to the `/scaled` endpoint and asserts that the fraction is correctly scaled. The existing test `test_scaled_ingredient_without_quantity` covers `"a pinch of pepper"` (truly no number), but `1/2` is a numeric quantity expressed as a fraction — a distinct case called out in the rubric.

Because Problem 1 means the code is silently wrong for fractions, and there is no test to catch it, **both** the Correctness and Tests rubric items fail on this case.

---

### Problem 3 — `factor=0` returns 422 instead of 400 (Rubric: **Correctness**, minor concern)

The rubric says *"invalid factor (0, negative, missing) returns 400/422"*, allowing either status code. The implementation uses FastAPI's `Query(gt=0)` validation, which produces **422 Unprocessable Entity**. This is consistent with FastAPI conventions and the rubric explicitly permits 422 here, so this is not a defect — noted for completeness only.

---

### Problem 4 — `"3 eggs"` case not explicitly tested (Rubric: **Tests**)

The rubric calls out *"number without unit ('3 eggs')"* as a required test case. While `test_scaled_basic_factor_2` incidentally includes `"2 eggs"` among other ingredients and checks `"4 eggs"`, this is embedded inside a multi-ingredient batch test rather than an isolated behavioural test for the "number without unit" case. The rubric requires each case to be covered by its own behavioural test; the `eggs` coverage is a by-product, not an intentional standalone test.

> [!NOTE]
> This is a mild concern. If the team's interpretation of "covered" permits the existing test, this item could be waived. However, the fraction test gap (Problem 2) is unambiguous.

---

## Summary Table

| # | Description | Rubric Item | Severity |
|---|---|---|---|
| 1 | Fraction quantities (`1/2 tsp`) not scaled — regex misses `/` | **Correctness** | ❌ Blocking |
| 2 | No test for fraction quantity input | **Tests** | ❌ Blocking |
| 3 | `factor=0` returns 422 (not 400) — rubric allows both | Correctness (note) | ✅ Acceptable |
| 4 | `"3 eggs"` (number without unit) not covered by a dedicated test | **Tests** | ⚠️ Minor |

---

## What Passes

- ✅ Decimal inputs (`"1.5 cups"`) — regex matches and scales correctly.
- ✅ Ingredients with no number (`"salt"`, `"a pinch of pepper"`) — returned unchanged.
- ✅ Missing factor → 422; zero factor → 422; negative factor → 422.
- ✅ Unknown recipe ID → 404.
- ✅ Whole-number results formatted without `.0`; `{scaled:g}` avoids trailing zeros.
- ✅ Code is concise and readable; `_scale_ingredient` is a well-named, single-purpose helper.
- ✅ No duplicated logic; the helper is called uniformly via a list comprehension.

---

VERDICT: REVISE
