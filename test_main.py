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
