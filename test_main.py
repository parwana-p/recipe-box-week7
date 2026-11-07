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
