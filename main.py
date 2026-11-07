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
