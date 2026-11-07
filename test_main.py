from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_get_recipe():
    r = client.post(
        "/recipes",
        json={"title": "Pancakes", "ingredients": ["flour", "milk"], "tags": ["breakfast"]},
    )
    assert r.status_code == 200
    rid = r.json()["id"]
    r2 = client.get(f"/recipes/{rid}")
    assert r2.status_code == 200
    assert r2.json()["title"] == "Pancakes"
    assert r2.json()["tags"] == ["breakfast"]


def test_list_recipes():
    client.post("/recipes", json={"title": "Toast"})
    r = client.get("/recipes")
    assert r.status_code == 200
    assert any(rec["title"] == "Toast" for rec in r.json())


def test_unknown_recipe_404():
    r = client.get("/recipes/99999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Task 1: Shopping list
# ---------------------------------------------------------------------------

def test_shopping_list_basic():
    """Single recipe: ingredients returned as-is."""
    r = client.post(
        "/recipes",
        json={"title": "Omelette", "ingredients": ["eggs", "salt", "butter"], "tags": []},
    )
    assert r.status_code == 200
    rid = r.json()["id"]

    r2 = client.get(f"/shopping-list?ids={rid}")
    assert r2.status_code == 200
    assert r2.json()["ingredients"] == ["eggs", "salt", "butter"]


def test_shopping_list_deduplication():
    """Duplicate ingredients across recipes appear only once."""
    r1 = client.post(
        "/recipes",
        json={"title": "Recipe A", "ingredients": ["flour", "sugar"], "tags": []},
    )
    r2 = client.post(
        "/recipes",
        json={"title": "Recipe B", "ingredients": ["sugar", "milk"], "tags": []},
    )
    ids = f"{r1.json()['id']},{r2.json()['id']}"

    r3 = client.get(f"/shopping-list?ids={ids}")
    assert r3.status_code == 200
    items = r3.json()["ingredients"]
    # sugar appears in both recipes but should only be in the list once
    assert items.count("sugar") == 1
    assert set(items) == {"flour", "sugar", "milk"}


def test_shopping_list_order_preserved():
    """First-seen order is preserved after de-duplication."""
    r1 = client.post(
        "/recipes",
        json={"title": "Recipe X", "ingredients": ["a", "b", "c"], "tags": []},
    )
    r2 = client.post(
        "/recipes",
        json={"title": "Recipe Y", "ingredients": ["b", "d"], "tags": []},
    )
    ids = f"{r1.json()['id']},{r2.json()['id']}"

    r3 = client.get(f"/shopping-list?ids={ids}")
    assert r3.status_code == 200
    assert r3.json()["ingredients"] == ["a", "b", "c", "d"]


def test_shopping_list_unknown_id_404():
    """Returns 404 when any id is unknown."""
    r = client.get("/shopping-list?ids=99998,99999")
    assert r.status_code == 404


def test_shopping_list_malformed_ids_400():
    """Returns 400 for non-integer ids."""
    r = client.get("/shopping-list?ids=abc")
    assert r.status_code == 400


def test_shopping_list_empty_ids_400():
    """Returns 400 when ids resolves to an empty list (commas only)."""
    r = client.get("/shopping-list?ids=,,,")
    assert r.status_code == 400
def test_tag_filter_returns_matching_recipes():
    """GET /recipes?tag=<tag> returns only recipes that have that tag."""
    client.post("/recipes", json={"title": "Omelette", "ingredients": ["eggs"], "tags": ["breakfast"]})
    client.post("/recipes", json={"title": "Pasta", "ingredients": ["pasta"], "tags": ["dinner"]})

    r = client.get("/recipes?tag=breakfast")
    assert r.status_code == 200
    results = r.json()
    assert len(results) > 0
    assert all("breakfast" in rec["tags"] for rec in results)
    assert all(rec["title"] != "Pasta" for rec in results)


def test_tag_filter_no_match_returns_empty():
    """GET /recipes?tag=<nonexistent> returns an empty list."""
    r = client.get("/recipes?tag=nonexistenttag_xyz")
    assert r.status_code == 200
    assert r.json() == []


def test_no_tag_param_returns_all_recipes():
    """GET /recipes without a tag parameter returns all recipes."""
    client.post("/recipes", json={"title": "Soup", "ingredients": ["water"], "tags": ["lunch"]})
    r_all = client.get("/recipes")
    assert r_all.status_code == 200
    titles = [rec["title"] for rec in r_all.json()]
    assert "Soup" in titles


# ---------------------------------------------------------------------------
# Task 3: Ingredient scaling
# ---------------------------------------------------------------------------

def test_scaled_basic_factor_2():
    """Factor 2 doubles the leading quantity of each ingredient."""
    r = client.post(
        "/recipes",
        json={
            "title": "Simple Cake",
            "ingredients": ["200 g flour", "100 g sugar", "2 eggs"],
            "tags": [],
        },
    )
    assert r.status_code == 200
    rid = r.json()["id"]

    r2 = client.get(f"/recipes/{rid}/scaled?factor=2")
    assert r2.status_code == 200
    body = r2.json()
    assert body["title"] == "Simple Cake"
    assert "400 g flour" in body["ingredients"]
    assert "200 g sugar" in body["ingredients"]
    assert "4 eggs" in body["ingredients"]


def test_scaled_factor_half():
    """Factor 0.5 halves the leading quantity."""
    r = client.post(
        "/recipes",
        json={
            "title": "Halved Soup",
            "ingredients": ["400 ml water", "50 g salt"],
            "tags": [],
        },
    )
    rid = r.json()["id"]

    r2 = client.get(f"/recipes/{rid}/scaled?factor=0.5")
    assert r2.status_code == 200
    ings = r2.json()["ingredients"]
    assert "200 ml water" in ings
    assert "25 g salt" in ings


def test_scaled_ingredient_without_quantity():
    """Ingredients with no leading number are returned unchanged."""
    r = client.post(
        "/recipes",
        json={
            "title": "Free-form",
            "ingredients": ["a pinch of pepper", "100 g butter"],
            "tags": [],
        },
    )
    rid = r.json()["id"]

    r2 = client.get(f"/recipes/{rid}/scaled?factor=3")
    assert r2.status_code == 200
    ings = r2.json()["ingredients"]
    assert "a pinch of pepper" in ings   # unchanged – no leading number
    assert "300 g butter" in ings


def test_scaled_unknown_recipe_404():
    """Returns 404 for a recipe that does not exist."""
    r = client.get("/recipes/99999/scaled?factor=2")
    assert r.status_code == 404


def test_scaled_missing_factor_422():
    """Returns 422 when the required factor query param is omitted."""
    r = client.post(
        "/recipes",
        json={"title": "Test", "ingredients": ["100 g oats"], "tags": []},
    )
    rid = r.json()["id"]
    r2 = client.get(f"/recipes/{rid}/scaled")
    assert r2.status_code == 422


def test_scaled_factor_zero_422():
    """Returns 422 when factor=0 (must be > 0)."""
    r = client.post(
        "/recipes",
        json={"title": "Test Zero", "ingredients": ["100 g oats"], "tags": []},
    )
    rid = r.json()["id"]
    r2 = client.get(f"/recipes/{rid}/scaled?factor=0")
    assert r2.status_code == 422


def test_scaled_decimal_result_formatted_cleanly():
    """Non-integer scaled quantities are formatted without trailing zeros."""
    r = client.post(
        "/recipes",
        json={
            "title": "Precise",
            "ingredients": ["1.5 tsp vanilla"],
            "tags": [],
        },
    )
    rid = r.json()["id"]

    r2 = client.get(f"/recipes/{rid}/scaled?factor=2")
    assert r2.status_code == 200
    ings = r2.json()["ingredients"]
    assert "3 tsp vanilla" in ings


def test_scaled_fraction_quantity():
    """Fraction quantities like '1/2 tsp salt' are scaled correctly."""
    r = client.post(
        "/recipes",
        json={
            "title": "Fraction Recipe",
            "ingredients": ["1/2 tsp salt", "1/4 cup oil"],
            "tags": [],
        },
    )
    assert r.status_code == 200
    rid = r.json()["id"]

    r2 = client.get(f"/recipes/{rid}/scaled?factor=2")
    assert r2.status_code == 200
    ings = r2.json()["ingredients"]
    assert "1 tsp salt" in ings   # 1/2 * 2 = 1
    assert "0.5 cup oil" in ings  # 1/4 * 2 = 0.5


def test_scaled_number_without_unit():
    """Quantities with no unit (e.g. '3 eggs') are scaled correctly."""
    r = client.post(
        "/recipes",
        json={
            "title": "Eggs Only",
            "ingredients": ["3 eggs"],
            "tags": [],
        },
    )
    assert r.status_code == 200
    rid = r.json()["id"]

    r2 = client.get(f"/recipes/{rid}/scaled?factor=2")
    assert r2.status_code == 200
    ings = r2.json()["ingredients"]
    assert "6 eggs" in ings


def test_scaled_factor_negative_422():
    """Returns 422 when factor is negative (must be > 0)."""
    r = client.post(
        "/recipes",
        json={"title": "Test Negative", "ingredients": ["100 g oats"], "tags": []},
    )
    rid = r.json()["id"]
    r2 = client.get(f"/recipes/{rid}/scaled?factor=-1")
    assert r2.status_code == 422
