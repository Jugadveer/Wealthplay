# Deploying WealthPlay

One Django process serves the API and the page. The React bundle is built to
`static/react/` and served by WhiteNoise from the same origin, so there is no
CORS between the page and its API and nothing to keep in sync across two hosts.

Two targets are supported and both run the same code.

| | Vercel | Railway / Render / Fly |
|---|---|---|
| Runs as | serverless function | long-lived process |
| Server | platform handler → `api/index.py` | `gunicorn` via `Procfile` |
| Requirements | `requirements.txt` | `requirements.txt` (+ `requirements-asgi.txt` for ASGI) |
| Scheduled jobs | `crons` in `vercel.json` | Celery Beat, or the same endpoints |
| Database | Postgres, required | Postgres, recommended |

---

## Vercel

### 1. Attach a Postgres database

**Required.** A serverless filesystem is per-invocation, so a SQLite file is not
a database there — it appears empty to the next request and loses everything
written in between. `settings.py` refuses to start without `DATABASE_URL` rather
than let the site look like it works.

Vercel Postgres, Neon and Supabase all work. Copy the connection string.

### 2. Set the environment variables

In **Project → Settings → Environment Variables**:

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | yes | Postgres connection string |
| `SECRET_KEY` | yes | 50+ random characters. `settings.py` refuses to start without it when `DEBUG` is off |
| `DEBUG` | yes | `False` |
| `SECURE_SSL_REDIRECT` | recommended | `True` — also switches the session and CSRF cookies to secure-only |
| `CRON_SECRET` | recommended | Protects `/api/market/cron/warm/`. Vercel sends it as `Authorization: Bearer …` |
| `ALLOWED_HOSTS` | no | The deployment hostname is read from `VERCEL_URL` automatically, including for preview builds |
| `GROQ_API_KEY`, `GEMINI_API_KEY` | see below | The AI provider in production |
| `REDIS_URL` | no | Without it the database cache is used, which is the right default here |

### 3. Deploy

`vercel.json` already sets the build command, the function and the routes.

```bash
vercel --prod
```

The build runs `scripts/vercel-build.sh`, which builds the frontend, collects
static files, applies migrations and creates the cache table. If `DATABASE_URL`
is missing it warns instead of failing, so a first deploy comes up and tells you
what is wrong rather than erroring opaquely.

### What the size limit means

A serverless function is capped at 250 MB unzipped. The dependencies come to
about 200 MB, of which pandas and numpy are half — they are not optional,
because `yfinance` needs them for real market history.

That margin is why `requirements.txt` is the smaller file. Daphne, Channels,
Twisted and Celery moved to `requirements-asgi.txt`: they were about 80 MB and
served no route the app actually has, since there are no WebSocket consumers
(see `wealthplay/asgi.py`). Keep an eye on the margin before adding a large
dependency.

---

## Railway, Render, Fly, or a VM

```bash
pip install -r requirements.txt
npm --prefix frontend ci && npm --prefix frontend run build
python manage.py migrate && python manage.py createcachetable
python manage.py collectstatic --noinput
gunicorn wealthplay.wsgi:application --bind 0.0.0.0:$PORT --workers 3
```

`Procfile` and `nixpacks.toml` do all of this. Set the same environment
variables as above, minus the Vercel-specific ones.

To run under ASGI instead — needed only if you add a WebSocket route:

```bash
pip install -r requirements.txt -r requirements-asgi.txt
daphne -b 0.0.0.0 -p $PORT wealthplay.asgi:application
```

No settings change is required. `settings.py` registers Daphne and Channels when
they are importable and skips them when they are not.

---

## The AI layer in production

The primary provider is a local `qwen2.5:0.5b-instruct` served by Ollama. **No
hosted platform has Ollama**, so on Vercel or Railway the client falls through to
Groq and then Gemini. Set `GROQ_API_KEY` or `GEMINI_API_KEY`, or the
model-written surfaces return `available: false` and the UI says so.

Most of the AI keeps working with no model at all, which is deliberate:

| Surface | Needs a model? |
|---|---|
| Glossary definitions (64 terms) | no |
| Course content search | no |
| Portfolio risk review | no — computed from the holdings |
| Page guidance, metric explanations | no — written |
| Goal verdict, stance, monthly figure | no — computed |
| Mentor answers outside the glossary | yes |
| Trade critiques, recaps, goal observations | yes |

`GET /api/ai/status/` reports which provider answered and whether it was local.

To keep the local model in production you need a host that can run Ollama —
a VM or a container platform, not a serverless function — with `OLLAMA_HOST`
pointing at it.

---

## Scheduled work

Two jobs exist. Neither is required for correctness:

- **Warming the market cache** so the first visitor of the day does not wait on
  eight provider round trips. On Vercel this is the cron in `vercel.json`
  calling `/api/market/cron/warm/`; elsewhere it is `users.tasks.warm_market_cache`
  under Celery Beat, or the same endpoint from any scheduler.
- **Advancing simulated prices.** No schedule needed anywhere: each stock catches
  up on read, seeded on `(symbol, date)`, so the series is identical to what a
  nightly job would have written.

---

## Checks before shipping

```bash
python manage.py check --deploy    # security settings
python manage.py test              # 209 tests
python manage.py ai_eval --fresh   # every AI surface against real data
npm --prefix frontend run lint
```
