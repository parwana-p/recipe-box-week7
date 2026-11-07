"""Recipe Box — starter app for Week 7.

A tiny FastAPI service for recipes and tags, with a static frontend. Use it as the
playground for concurrent multi-agent work and a generator-critic loop.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload
    # open http://localhost:8000/
Test:
    pytest
"""
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE = Path(__file__).parent
DB_PATH = BASE / "recipes.db"

app = FastAPI(title="Recipe Box")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_db()) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS recipes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                ingredients TEXT NOT NULL,  -- JSON list of strings
                tags        TEXT NOT NULL   -- JSON list of strings
            )"""
        )
        conn.commit()


init_db()


class RecipeIn(BaseModel):
    title: str
    ingredients: list[str] = []
    tags: list[str] = []


def _row_to_recipe(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "ingredients": json.loads(row["ingredients"]),
        "tags": json.loads(row["tags"]),
    }


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.post("/recipes")
def create_recipe(recipe: RecipeIn):
    with closing(get_db()) as conn:
        cur = conn.execute(
            "INSERT INTO recipes (title, ingredients, tags) VALUES (?, ?, ?)",
            (recipe.title, json.dumps(recipe.ingredients), json.dumps(recipe.tags)),
        )
        conn.commit()
        rid = cur.lastrowid
    return {"id": rid, **recipe.model_dump()}


@app.get("/recipes")
def list_recipes(tag: str | None = Query(default=None)):
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT * FROM recipes ORDER BY id").fetchall()
    recipes = [_row_to_recipe(r) for r in rows]
    if tag is not None:
        recipes = [r for r in recipes if tag in r["tags"]]
    return recipes


@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    with closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="unknown recipe")
    return _row_to_recipe(row)


@app.get("/shopping-list")
def shopping_list(ids: str):
    """Merge ingredients of the given recipe IDs into a de-duplicated list.

    Query param:
        ids: comma-separated integer recipe IDs, e.g. ``?ids=1,2,3``

    Returns:
        200 {"ingredients": [...]}
        400 if `ids` is malformed (non-integer tokens, empty string)
        404 if any id is not found in the database
    """
    # Validate and parse the ids query parameter
    try:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip()]
        if not id_list:
            raise ValueError("empty list")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="malformed ids: expected comma-separated integers",
        )

    with closing(get_db()) as conn:
        all_ingredients: list[str] = []
        for rid in id_list:
            row = conn.execute(
                "SELECT ingredients FROM recipes WHERE id = ?", (rid,)
            ).fetchone()
            if row is None:
                raise HTTPException(
                    status_code=404, detail=f"unknown recipe id: {rid}"
                )
            all_ingredients.extend(json.loads(row["ingredients"]))

    # De-duplicate while preserving first-seen insertion order
    seen: set[str] = set()
    deduped: list[str] = []
    for item in all_ingredients:
        if item not in seen:
            seen.add(item)
            deduped.append(item)

    return {"ingredients": deduped}


# ---------------------------------------------------------------------------
# Task 3: Ingredient scaling
# ---------------------------------------------------------------------------

# Matches an optional leading number (int or float) followed by the rest of
# the ingredient string, e.g. "200 g flour", "1.5 tsp salt", "eggs".
_QTY_RE = re.compile(r"^(\d+(?:\.\d+)?)\s+(.*)")


def _scale_ingredient(ingredient: str, factor: float) -> str:
    """Return *ingredient* with its leading quantity multiplied by *factor*.

    If the ingredient string does not start with a number the original string
    is returned unchanged.
    """
    m = _QTY_RE.match(ingredient)
    if not m:
        return ingredient
    qty_str, rest = m.group(1), m.group(2)
    original = float(qty_str)
    scaled = original * factor
    # Format: drop the decimal point when the result is a whole number.
    if scaled == int(scaled):
        scaled_str = str(int(scaled))
    else:
        scaled_str = f"{scaled:g}"
    return f"{scaled_str} {rest}"


@app.get("/recipes/{recipe_id}/scaled")
def get_scaled_recipe(recipe_id: int, factor: float = Query(gt=0)):
    """Return the recipe with ingredient quantities multiplied by *factor*.

    Query param:
        factor: positive number to scale ingredient quantities by.

    Returns:
        200 recipe dict with scaled ingredients
        404 if the recipe is not found
        422 if factor is missing or <= 0 (FastAPI validation)
    """
    with closing(get_db()) as conn:
        row = conn.execute(
            "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="unknown recipe")

    recipe = _row_to_recipe(row)
    recipe["ingredients"] = [
        _scale_ingredient(ing, factor) for ing in recipe["ingredients"]
    ]
    return recipe
