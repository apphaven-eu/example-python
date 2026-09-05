import os
from contextlib import asynccontextmanager
from html import escape

import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from psycopg_pool import ConnectionPool

SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
  id         BIGSERIAL PRIMARY KEY,
  title      TEXT        NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

STYLE = """
  * { box-sizing: border-box; }
  input[type=text] { min-width: 0; }
  li span { min-width: 0; overflow-wrap: anywhere; }
  li form { flex-shrink: 0; }
  footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #8884; font-size: .875rem; }
  a { color: #2457bd; }
  :focus-visible { outline: 2px solid #2457bd; outline-offset: 3px; }

:root { color-scheme: light; }
body {
  margin: 0;
  padding: 48px 16px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  background: #f7f7f8;
  color: #16181d;
}
main { max-width: 640px; margin: 0 auto; }
h1 { font-size: 22px; margin: 0 0 24px; letter-spacing: -0.01em; }
form.add { display: flex; gap: 8px; margin-bottom: 24px; }
input[type=text] {
  flex: 1; padding: 10px 12px; font: inherit;
  border: 1px solid #ccced4; border-radius: 6px; background: #fff;
}
input[type=text]:focus { outline: 2px solid #4b6bfb; outline-offset: -1px; border-color: #4b6bfb; }
button {
  font: inherit; padding: 10px 16px; border-radius: 6px;
  border: 1px solid #2a2d34; background: #2a2d34; color: #fff; cursor: pointer;
}
button.link {
  padding: 4px 8px; background: none; color: #6a6f7a;
  border: 1px solid transparent; font-size: 13px;
}
button.link:hover { color: #b3261e; border-color: #e0d0cf; }
ul { list-style: none; margin: 0; padding: 0; border-top: 1px solid #e4e5e9; }
li {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 10px 4px; border-bottom: 1px solid #e4e5e9; background: #fff;
}
li span { overflow-wrap: anywhere; }
p.empty { color: #6a6f7a; padding: 16px 4px; margin: 0; border-bottom: 1px solid #e4e5e9; }
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    dsn = os.environ["DATABASE_URL"]
    with ConnectionPool(dsn, min_size=1, max_size=5, kwargs={"autocommit": True}) as pool:
        with pool.connection() as conn:
            conn.execute(SCHEMA)
        app.state.pool = pool
        yield


app = FastAPI(lifespan=lifespan)


def render(rows) -> str:
    if rows:
        items = "".join(
            "<li><span>{title}</span>"
            '<form method="post" action="/delete">'
            '<input type="hidden" name="id" value="{id}">'
            '<button class="link" type="submit">Delete</button>'
            "</form></li>".format(title=escape(title), id=todo_id)
            for todo_id, title in rows
        )
        body = f"<ul>{items}</ul>"
    else:
        body = '<p class="empty">No items yet.</p>'
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>FastAPI Todo | AppHaven</title><style>{STYLE}</style></head><body><main>"
        "<h1>FastAPI Todo</h1><p>A shared task list, built with FastAPI and PostgreSQL.</p>"
        '<form class="add" method="post" action="/add">'
        '<input type="text" name="title" aria-label="New task" placeholder="Add an item" autocomplete="off" maxlength="200" required>'
        '<button type="submit">Add</button></form>'
        f"{body}<footer><p>Deploy your own on "
        '<a href="https://apphaven.eu">AppHaven</a> · '
        '<a href="https://github.com/apphaven-eu/example-python">Source code</a> · '
        '<a href="https://docs.apphaven.eu/getting-started">Deployment guide</a>'
        "</p></footer></main></body></html>"
    )


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    with app.state.pool.connection() as conn:
        rows = conn.execute("SELECT id, title FROM todos ORDER BY id DESC").fetchall()
    return HTMLResponse(render(rows))


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
