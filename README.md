# WealthPlay

**A daily financial workout.** Five minutes a day of puzzles and spaced
repetition, on top of a ₹50,000 paper-trading simulator where being wrong costs
nothing.

Django 5 + DRF on the back, React 18 + Vite on the front, and a half-billion
parameter language model running on the same machine as the app.

```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py runserver
cd frontend && npm install && npm run dev      # http://localhost:3000
```

---

## What it is

Twenty-five courses, sixty modules, and a simulator are the raw material. The
product is what sits on top of them:

| | |
|---|---|
| **Today** | Six short plays that reset each morning, plus five questions scheduled by SM-2 out of what you have already studied. Everyone gets the same set, so a score is comparable. |
| **Learn** | 60 modules, 210 theory cards, 180 questions. Content lives on disk as JSON; only progress is in the database. |
| **Markets** | A practice terminal with its own chrome. Real quotes for real listings, a seeded simulated market for the rest, and a portfolio review that names what is concentrated. |
| **Goals** | A target and a date become a monthly figure — and an allocation that depends on what the goal is *for*. |
| **Play** | Scenarios, the prediction oracle, and the daily games. |
| **Progress** | Not "how often were you right" but "how often were you right when you said you were sure". |
| **Nex** | An assistant on every page, answering from the course content rather than from a model's memory. |

---

## Why it is built this way

Six decisions shape everything else.

**A daily loop, not a course library.** Twenty-five courses are a weekend of
content for a committed learner, and a fixed question bank runs dry. The product
is instead a daily *set* — six short plays, and five questions scheduled by SM-2
out of what the learner has already finished. The pool grows with every module
completed, and nothing recurs until the whole list has been used: `daily_pick`
shuffles each list once with a fixed seed and then walks it in order, so the
cycle is exactly as long as the list.

**A goal decides how much risk its plan may carry.** Most calculators turn a
target and a date into a monthly figure and stop. `users/goals/planner.py` also
asks what the goal is *for*: school fees in the year they are due cannot slip,
a holiday can. The same fifteen-year horizon therefore produces 45% equity for a
child's education and 75% for travel, and the growth option is never offered for
a goal that cannot be postponed. Linking a goal to the practice account turns
trading into practice for something specific rather than a score.

**Calibration is the thing being taught.** Being right a lot is easy on easy
calls. Being right 70% of the times you said 70% is a different and harder
skill, and it is the one that transfers to actually risking money. Every
prediction carries a stated confidence, and Progress shows the gap between what
you claimed and what happened. Nothing else here is unusual; this is.

**Every quote is cached; no view touches the network.** `market_data.services`
is the only module allowed to call a provider. Views read through it, so a page
never blocks on the provider. The cache is load-bearing rather than an
optimisation: without it, one dashboard load spent ~15 seconds in provider I/O.

**The practice market is a factor model, not noise.** Each simulated stock has a
beta to a shared market factor, a sector factor, and its own drift and
volatility, seeded on `(symbol, date)`. 68% of stocks agree with the market
direction on a given day, which is roughly what a real one does — and the series
is identical however often you look at it, so prices catch up lazily on read
instead of needing a nightly job.

**The AI is small, local, and not trusted.** See below. It is the part of this
codebase with the most engineering in it and the least magic.

---

## The AI layer

Every AI surface runs on `qwen2.5:0.5b-instruct` through [Ollama](https://ollama.com),
on the same machine as the app. No key, no quota, no per-token cost, and nothing
about a user's income leaves the machine. Warm responses take under a second.

A model that small is also confidently wrong. Measured on this app's own prompts,
before any of the work below:

| Asked | Answered |
|---|---|
| What is an index fund? | *"also known as an ETF… represents shares of a single underlying stock"*, citing the S&P 500 to a user in India |
| Grade a portfolio 90% in one stock | **"A"** — the best grade for the worst case |
| Review a portfolio 81% in IT | *"Invest more in IT stocks"*, and reported INFY's −4.2% as a banking figure |
| Future value of ₹5,000/month, 10y at 12% | ₹2,88,000. The answer is about ₹11.6 lakh |
| Assess a ₹25,00,000 goal over 15.8 years | `$25 million` over `15 months` — valid JSON, every figure invented |

So the architecture is one rule: **Python computes every number and every
verdict; the model only writes the sentence, and a guard rejects any figure it
invents.**

```
ai/
  client.py      one entry point. Ollama first, Groq and Gemini as failover.
                 Schema-constrained decoding, so malformed JSON is not a failure mode.
  guard.py       strips markdown, prompt leakage and mid-word truncation; rejects
                 any figure, currency or institution that was not supplied
  retrieve.py    BM25 over the 60 authored modules — what the model is allowed to say
  glossary.py    64 authored definitions, each with a worked rupee example
  coach.py       help that follows the user: explain a term, a number, a page
  tutor.py       one function per feature; each owns its prompt
  management/commands/ai_eval.py   the harness that keeps all of it honest
```

**Three sources, in order of how much they can be trusted.** A question is
answered from the glossary, then from an authored Q&A whose wording matches, then
by the model rewriting retrieved passages. There is no fourth step where it
answers from memory — asked to define "quantum arbitrage swap", a phrase with no
meaning, it produced a confident paragraph, so a term the app cannot source is a
term it says it does not know. The UI prints which of the three you got.

**Some surfaces were taken off the model** because measuring them showed it
subtracted value. The portfolio review, page guidance and metric explanations are
computed. They are right every time, instant, and say the same thing twice for
the same input — which the model did not.

**`ai_eval` is the point.** "We added AI" is not a claim anyone should take on
trust, including us:

```bash
python manage.py ai_eval --fresh
```

It puts all 28 surfaces in front of realistic data and fails on wrong or harmful
output — an index fund described as a single stock, a figure nobody supplied, a
review that tells you to buy more of the sector it just flagged. `--fresh` clears
the completion cache first, because an evaluation that reads its own cache grades
yesterday's model.

Without Ollama everything still works. The glossary, the search, the computed
review and the goal verdicts need no model at all; only the written surfaces
degrade, and they say so rather than substituting a template.

---

## Running it

Python 3.12+ and Node 18+.

```bash
python -m venv .venv && .venv/Scripts/activate   # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env                              # set SECRET_KEY; model keys are optional
python manage.py migrate
python manage.py createcachetable
python manage.py warm_market_cache                # optional, makes the first load instant
python manage.py runserver
```

```bash
cd frontend && npm install && npm run dev
```

The Vite dev server proxies `/api` to Django, so open `http://localhost:3000`.
If Django is not on port 8000, put `API_PROXY=http://127.0.0.1:8001` in
`frontend/.env`.

### The local model

```bash
ollama pull qwen2.5:0.5b-instruct
```

That is the whole setup — `OLLAMA_HOST` and `OLLAMA_MODEL` already default
correctly in `.env.example`. Django warms the model on startup so the first
request does not pay the ~25 second load.

No Ollama and no keys is a supported state: AI surfaces report themselves
unavailable and nothing else changes. To use a hosted provider instead, set
`GROQ_API_KEY` ([free tier](https://console.groq.com/keys)) or `GEMINI_API_KEY`.

### Tests

```bash
python manage.py test        # 209 tests
python manage.py ai_eval     # 28 AI surfaces against realistic data
npm --prefix frontend run lint
```

Covering currency conversion on foreign holdings, the achievement rules, streak
freezes, SM-2 intervals, puzzle determinism, content cleaning, the simulated
market, deposits and SIPs, the grounding guard, retrieval, and the LLM client's
failure path. Each one pins a bug that actually shipped.

### Scheduled jobs

Both are management commands, so they run under cron, Task Scheduler or Celery
Beat without needing a broker — and neither is required for correctness.

```bash
python manage.py warm_market_cache        # every 15 minutes
python manage.py advance_simulated_prices # once a day
```

Simulated prices catch up lazily on read, so the second one only exists to move
that work off a user's request. On a host with no worker, `/api/market/cron/warm/`
does the first one from any scheduler.

---

## Deploying

One Django process serves the API and the page; the React bundle is built to
`static/react/` and served by WhiteNoise from the same origin, so there is no
CORS and nothing to keep in sync across two hosts.

```bash
vercel --prod            # needs DATABASE_URL and SECRET_KEY set
```

`vercel.json` and `scripts/vercel-build.sh` do the rest. Postgres is required —
a serverless filesystem is per-invocation, so a SQLite file there loses every
signup, and `settings.py` refuses to start rather than let the site look like it
works.

A serverless function is capped at 225 MB unzipped and these dependencies come to
about 70 MB. That margin exists because `requirements.txt` is the smaller file:
Daphne, Channels, Twisted and Celery moved to `requirements-asgi.txt`, being
~80 MB that served no route the app actually has. `settings.py` registers them
when they are importable and skips them when they are not, so a long-lived ASGI
host installs both files and changes nothing else.

Railway, Render, Fly and plain VMs are supported through `Procfile` and
`nixpacks.toml`. Full instructions, including what happens to the local model in
production, are in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Architecture

```
wealthplay/          settings, URLs, WSGI/ASGI; serves the built SPA shell
api/index.py         serverless entry point
market_data/         the ONLY module that calls a market provider
  services.py          cached quotes, history, news; degrades to stale, then to neutral
  cron.py              scheduled warming for hosts with no worker
ai/                  the ONLY module that calls an LLM — see above
courses/
  content.py           parses course_modules/ once; strips generation artifacts
  views.py             catalogue, module, grading, completion
users/
  portfolio/           pricing → valuation → insights → views
    simulation.py        the practice market: shared factor, sector factor, seeded per day
    instruments.py       fixed deposits and SIPs, gated on a linked goal
  goals/
    planner.py           horizon x criticality -> allocation, SIP, ladder, EMI, feasibility
    assessment.py        deterministic classification and risk capacity
    realworld.py         an implementable plan, with live index prices
  achievement_views.py declarative rule table
  challenge_views.py   prediction game, calibration and leaderboards
daily/               the habit loop
  puzzles.py           date-seeded generators, identical for every player
  games.py             Ledger and Rank It
  review.py            SM-2 scheduling over completed modules
simulator/           branching decision scenarios
chat/                the mentor, grounded in courses.content
frontend/src/
  lib/                 api, query cache, formatting, theme, notifications
  ui/                  design system: primitives, charts, markdown
  components/          shell, zone curtain, toaster, market strip, wire, mentor
  pages/               one folder per section
```

### The data layer

`frontend/src/lib/query.js` is ~120 lines and does three things: dedupes
in-flight requests by key, serves cached data while revalidating, and refetches
mounted queries when a mutation invalidates their key. That last part is what
makes a trade show up in the portfolio immediately.

### Content

Course content lives on disk at
`course_modules/<course>/<module>/{flash_cards,mcqs,qna}.json` and is parsed
once per process by `courses.content`. Nothing about content is in the database;
only per-user progress is. `clean()` strips the LLM artifacts the source files
still carry — image placeholders, and LaTeX that JSON escaping mangled.

---

## Design

The interface is modelled on an instrument: a cool graphite shell, hairline
structure instead of drop shadows, and monospaced tabular figures everywhere a
number appears. Headings are Space Grotesk, body is Geist, figures are Geist
Mono.

**Primary actions are ink, not the accent** — a filled button is black on light
and white on dark. That one decision keeps the accent free to mean "interactive"
wherever it appears: links, the active tab, focus rings, meters. Green and red
are reserved for market direction, so a red number always means a loss and never
"danger" or "delete".

**Each section owns a hue.** `data-zone` on `<html>` redefines `--accent`, so
every `text-accent` and `bg-accent/10` already in the codebase becomes
section-aware without a single component knowing about it: honey for Today,
violet for Learn, cobalt for Markets, magenta for Play, teal for Progress.
Surfaces stay neutral and the hue only ever touches chrome.

Entering **Markets** or **Play** plays a short curtain in that colour, because
those are the two places the app stops being a reader and becomes an
environment. Today, Learn and Progress get none: they are surfaces you open
constantly, and a curtain in front of one is an interruption rather than an
arrival. Progress celebrates on the page instead, with a single rocket crossing
it on load. All of it is skipped under `prefers-reduced-motion`.

Both themes are designed rather than inverted — each has its own token values in
`index.css`, applied before first paint so there is no flash. A modal scrim gets
its own token, because a scrim built from `--ink` inverts with the theme and
lightens the page it is supposed to dim.

Chart colours are measured rather than chosen. On the chart surfaces every step
clears 3:1 contrast and the set clears CIEDE2000 31 (light) / 29 (dark) for
normal vision. Under deuteranopia and protanopia the first three slots clear 21
and 18, the fourth clears 10 and 12, and the fifth does not separate from the
fourth at all — so colour never carries identity alone. Every chart ships direct
labels, and composition renders as labelled bars rather than a donut.

---

## What changed in the rebuild

Measured before and after, on the same machine.

| | Before | After |
|---|---|---|
| Requests per dashboard load | 44 | 5 |
| Slowest endpoint | 5.62s | 0.03s |
| `portfolio_views.py` | 1,950 lines | a 5-module package |
| Working LLM providers | 0 (both models retired upstream) | local model, hosted failover |
| AI cost per answer | metered | none — it runs here |
| Tests | 0 | 209 |
| Deployment size | 280 MB | 70 MB |

Functional fixes, each verified in a browser:

- The mentor resolved course ids against an unrelated JSON file, so every
  question answered *"Course 'investing-basics' not found."*
- A dollar holding was converted to rupees twice, showing a flat AAPL position
  as −98%.
- **Every deployment served a blank page.** Django rendered a leftover
  `npm create vite` template whose only script tag was `/src/main.jsx`, which
  resolves solely through the dev server. Invisible in development, because there
  the browser talks to Vite and Django's copy is never rendered.
- **The Rank It board had never once saved.** The provider returns `NaN` for days
  it has no price, `round(NaN, 2)` is `NaN` and raises nothing, `json.dumps`
  writes bare `NaN`, and SQLite rejected the row on its `JSON_VALID` constraint.
  The same `NaN` returned intermittent 500s from the prediction oracle, and made
  the board's answer arbitrary even when it did save, because `sorted` against
  `NaN` has no defined order.
- Achievement XP was granted inline and again in a trailing pass.
- Earned achievements displayed as locked, because the list was cached in
  `localStorage` and never invalidated.
- **The deployed function was 17 MB over the serverless size limit.** `yfinance`
  returns DataFrames, so it drags pandas and numpy behind it — 119 MB of wheels
  to read a few hundred numbers out of a JSON response. The provider's JSON
  endpoints are called directly now, which also removes pandas from every cold
  start. `curl_cffi` stays, because it is the part of yfinance that mattered:
  Yahoo rejects a plain HTTP client on its TLS fingerprint.
- The news feed parsed a yfinance schema that had moved, rendering an empty
  headline dated 1 January 1970.
- Flashcards showed the answer face-up, duplicating the theory above them.
- `**Inflation**` rendered as literal asterisks; `[Image of inflation chart…]`
  shipped as body copy.
- Lessons ended at the FAQ with no completion, no XP and no next module.
- The floating nav covered page titles on every page with a sticky sub-header.
- Scenario scores were sent by the client and trusted by the server.
- The "AI hint" was a hardcoded string containing the typo *"the volume volume
  surge"*.
- Course blurbs were a 180-character slice of an arbitrary Q&A answer, so every
  card opened mid-thought, stopped mid-word, and showed `**bold**` as asterisks.
- The portfolio chart padded its axis below zero, drawing a negative floor under
  an account that had never been worth less than nothing.
- The prediction game drew from a seven-question bank with `order_by('?')` and no
  memory of what you had answered, so it repeated within a handful of rounds.
- The AI portfolio review ran on every analysis load because it passed no cache
  key, and its prompt embedded a P&L figure that moved with every tick. Keyed on
  composition instead: 1.19s to 0.01s on a repeat load.
- The practice stocks never moved. Advancing prices was a cron job and no cron
  was running, so every position read exactly +0.00% forever.
- `investing-101/m1` shipped with empty `flash_cards.json` and `mcqs.json`, so
  the module had no title and no theory and rendered as "M1" above nothing.
- Thirty-six tests were never running: they lived in files named `*_tests.py`,
  and Django discovers `test*.py`.
- The CSRF cookie was pinned to `secure=False`, so it travelled in the clear on
  any deployed site.

---

## Not done

- **Real-time prices.** Quotes are cached for 90 seconds. A live feed needs
  WebSockets and a provider that permits streaming.
- **Market Call settlement** resolves on the next request after the close rather
  than on a schedule. A cron job would make it exact.
- **Market Call and the daily set do not push.** A settled call is discovered on
  the next visit rather than announced. The notification bus is in place; a web
  push subscription is the missing half.
- **The glossary is the AI's ceiling.** 64 terms answer the common questions
  exactly; outside them the model rewrites retrieved passages and the quality is
  visibly lower. Widening the glossary is the highest-leverage improvement
  available, and it is authoring rather than engineering.
- **Goal observations are rejected by the guard perhaps half the time**, falling
  back to the computed verdict. Correct, and plainer than it should be. A larger
  local model would close this without changing a line of the architecture.
- **The local model cannot follow to serverless.** On Vercel the AI falls through
  to a hosted provider. Keeping it local in production needs a host that can run
  Ollama.
- **Multi-worker deployment** wants `REDIS_URL` set; the database cache is
  correct but not fast enough under real load.
- **The LightGBM price model was removed, not fixed.** `ml/` trained a direction
  classifier that no view had called in a long time, and it pulled in
  scikit-learn, scipy, lightgbm and pyarrow for a clean install. Dead code with
  four heavy dependencies is worse than no code; wiring a model to a real
  decision — sizing the prediction game's difficulty, say — is the version worth
  building.
