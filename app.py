import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

BASE_DIR = Path(__file__).parent

# Jinja2Templates escapes values by default, so a title containing markup is shown as text.
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    dsn = os.environ["DATABASE_URL"]
    with ConnectionPool(
        dsn, min_size=1, max_size=5, kwargs={"autocommit": True, "row_factory": dict_row}
    ) as pool:
        with pool.connection() as conn:
            conn.execute((BASE_DIR / "schema.sql").read_text())
        app.state.pool = pool
        yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index(request: Request):
    with app.state.pool.connection() as conn:
        todos = conn.execute("SELECT id, title FROM todos ORDER BY id DESC").fetchall()
    return templates.TemplateResponse(request, "index.html", {"todos": todos})


@app.post("/add")
def add(title: str = Form("")) -> RedirectResponse:
    title = title.strip()[:200]
    if title:
        with app.state.pool.connection() as conn:
            conn.execute("INSERT INTO todos (title) VALUES (%s)", (title,))
    return RedirectResponse("/", status_code=303)


@app.post("/delete")
def delete(id: int = Form(...)) -> RedirectResponse:
    with app.state.pool.connection() as conn:
        conn.execute("DELETE FROM todos WHERE id = %s", (id,))
    return RedirectResponse("/", status_code=303)


@app.get("/healthz", response_class=PlainTextResponse)
def healthz() -> PlainTextResponse:
    return PlainTextResponse("ok")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
