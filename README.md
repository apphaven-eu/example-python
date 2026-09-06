# Python FastAPI with PostgreSQL on AppHaven

Deploy a Python FastAPI application with managed PostgreSQL on [AppHaven](https://apphaven.eu). This example serves HTML forms with FastAPI and uses psycopg 3 connection pooling for a PostgreSQL-backed todo list.

Add, list, and delete tasks. Data persists across app restarts in PostgreSQL.
The repository includes the application, a `Dockerfile`, and an `apphaven.yaml` manifest.

## Stack

- FastAPI 0.141 on uvicorn, server-rendered HTML, no front-end build step
- Jinja2 template at `templates/index.html`, which escapes values by default; stylesheet
  served from `static/` and schema read from `schema.sql` at startup
- psycopg 3 with `psycopg_pool.ConnectionPool`, plain SQL, no ORM
- PostgreSQL 17 (managed by AppHaven in production)
- Container base image `python:3.13-slim`, runs as a non-root user

## Run it locally

You need Docker for PostgreSQL and Python 3.13. Clone this repository first:

```sh
git clone https://github.com/apphaven-eu/example-python.git
cd example-python
```

1. Start PostgreSQL for development:

   ```
   docker run -d --name todo-pg -p 127.0.0.1:5432:5432 -e POSTGRES_PASSWORD=devpassword postgres:17
   ```

2. Install the dependencies:

   ```
   python3.13 -m venv .venv && . .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Point the app at that database and run it:

   ```
   export DATABASE_URL="postgresql://postgres:devpassword@127.0.0.1:5432/postgres"
   python app.py
   ```

The app listens on http://localhost:8080/. The `todos` table is created at startup if it does not
exist. Set `PORT` to use a different port.

## Deploy FastAPI on AppHaven

1. Fork this repository, or push a copy to a Git host reachable over HTTPS.
2. Open the [AppHaven console](https://console.apphaven.eu/), select a project, and create an app.
3. In **Source**, connect your repository and select the production branch (usually `main`).
4. Click **Deploy** and select that branch. Follow the build logs, then open the deployment URL.

You need an AppHaven account with console access. See the
[getting started guide](https://docs.apphaven.eu/getting-started) for account and repository setup.

`apphaven.yaml` declares the `web` service (built from the `Dockerfile`) and the managed `db`
service running PostgreSQL 17. `DATABASE_URL` is injected at deploy time from `${service.db.url}`,
so production database credentials stay out of source control.

### Access and shared data

Apps are **private by default**: only members of the AppHaven project can open them.
This example has one shared todo list; it does not separate tasks by user.
For a public demo, a project administrator can select **Public** in the app's **Security**
section and redeploy. Anyone who can reach the app can add and delete tasks, so use demo data.
Production can be public while previews remain private. See [access control](https://docs.apphaven.eu/access).

### Preview a change

Push a new branch and deploy it from the console. AppHaven creates a preview with its own URL,
storage, and database, separate from production. Add a task in the preview, redeploy that branch,
and check that the task is still there before merging the change.

### Verify the deployment

Open the app, add a task, refresh, and delete it. The manifest waits for PostgreSQL to be healthy
before starting the web container. `/healthz` is a process liveness endpoint; it does not query
the database. The container's healthcheck runs internally, so it needs no public-path exemption.

The schema lives in `schema.sql` and is applied at startup. It uses `CREATE TABLE IF NOT
EXISTS` for the initial table, so repeated starts are safe. When extending the app, use
versioned migrations for changes to existing columns and tables.

## AppHaven

On AppHaven, both the runtime and the database are managed by the platform. PostgreSQL is a
`type: postgres` service in `apphaven.yaml`. AppHaven provisions and operates it, and takes care of
its backups.

- Platform: https://apphaven.eu
- Managed PostgreSQL: https://docs.apphaven.eu/services/postgres
- Manifest reference: https://docs.apphaven.eu/reference/manifest

## Related examples

[Go](https://github.com/apphaven-eu/example-go), [Spring Boot](https://github.com/apphaven-eu/example-java), [Next.js](https://github.com/apphaven-eu/example-nextjs), [Express](https://github.com/apphaven-eu/example-node), [PHP](https://github.com/apphaven-eu/example-php).

## License

[MIT](LICENSE).
