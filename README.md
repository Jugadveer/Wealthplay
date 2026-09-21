# WealthPlay

A daily financial workout. Five minutes a day of puzzles and spaced repetition,
on top of a ₹50,000 paper-trading simulator where being wrong costs nothing.

Django 5 + DRF on the back, React 18 + Vite on the front.

---

## Why it is built this way

Three decisions shape everything else.

**A daily loop, not a course library.** Twenty-five courses are a weekend of
content for a committed learner, and a fixed question bank runs dry. The product
is instead a daily *edition* — one puzzle, one market call, one number to
estimate, and five questions scheduled by SM-2 out of what the learner has
already finished. The pool grows with every module completed, and no question
recurs two days running.

**Every quote is cached; no view touches the network.** `market_data.services`
is the only module allowed to call a provider. Views read through it, so a page
never blocks on `yfinance`. The cache is load-bearing rather than an
optimisation: without it, one dashboard load spent ~15 seconds in provider I/O.

**AI degrades honestly.** `ai/client.py` is the single LLM entry point. When no
provider answers it raises, callers receive `None`, and the UI says the feature
is unavailable. Nothing substitutes a template and labels it AI. Computed
analysis (concentration, ESG weighting, exit discipline) is visually distinct
from model-written analysis, because one always works and the other might not.

---

## Running it

Python 3.11+ and Node 18+.

```bash
python -m venv .venv && .venv/Scripts/activate   # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env                              # set SECRET_KEY; keys are optional
python manage.py migrate
python manage.py createcachetable
python manage.py warm_market_cache                # optional, makes the first load instant
python manage.py runserver
```

```bash
cd frontend && npm install && npm run dev
```

The Vite dev server proxies `/api` to Django, so open `http://localhost:3000`.

Without an LLM key everything still works; the AI surfaces report themselves as
unavailable. Groq's free tier is the primary provider and answers in about half
a second — get a key at [console.groq.com](https://console.groq.com/keys).

### Tests

```bash
python manage.py test
```

48 tests covering currency conversion on foreign holdings, the achievement
rules, streak freezes, SM-2 intervals, puzzle determinism, content cleaning, and
the LLM client's failure path. Each one pins a bug that actually shipped.

### Scheduled jobs

Both are management commands so they run under cron, Task Scheduler or Celery
Beat without needing a broker.

```bash
python manage.py warm_market_cache        # every 15 minutes
python manage.py advance_simulated_prices # once a day
```

---

## Architecture

```
wealthplay/          settings, URLs, ASGI
market_data/         the ONLY module that calls a market provider
  services.py          cached quotes, history, news; degrades to stale, then to neutral
ai/                  the ONLY module that calls an LLM
  client.py            provider order, key failover, JSON extraction, response cache
  tutor.py             one function per AI feature; each owns its prompt
courses/
  content.py           parses course_modules/ once; strips generation artifacts
  views.py             catalogue, module, grading, completion
users/
  portfolio/           pricing → valuation → insights → views
  achievement_views.py declarative rule table
  challenge_views.py   prediction game and leaderboards
daily/               the habit loop
  puzzles.py           date-seeded generators, identical for every player
  review.py            SM-2 scheduling over completed modules
simulator/           branching decision scenarios
chat/                the mentor, grounded in courses.content
frontend/src/
  lib/                 api, query cache, formatting, theme
  ui/                  design system: primitives, charts, markdown
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

The interface is modelled on a newspaper's markets-and-puzzle page: warm
newsprint, an editorial serif masthead, hairline rules instead of drop shadows,
and tabular figures everywhere a number appears.

One brand accent (ink blue). Amber is reserved for streaks and XP. Green and red
are reserved for market direction, so a red number always means a loss and never
"danger" or "delete".

Both themes are designed rather than inverted — each has its own token values in
`index.css`, applied before first paint so there is no flash.

Chart colours are validated rather than chosen: the categorical palette clears
the lightness band, chroma floor, CVD separation and normal-vision floor in both
modes against this app's own surfaces. Composition renders as labelled bars
rather than a donut, because labels beside marks do not depend on colour
discrimination.

---

## What changed in the rebuild

Measured before and after, on the same machine.

| | Before | After |
|---|---|---|
| Requests per dashboard load | 44 | 5 |
| Slowest endpoint | 5.62s | 0.03s |
| `portfolio_views.py` | 1,950 lines | a 5-module package |
| Working LLM providers | 0 (both models retired upstream) | Groq, with Gemini failover |
| Tests | 0 | 48 |

Functional fixes, each verified in a browser:

- The mentor resolved course ids against an unrelated JSON file, so every
  question answered *"Course 'investing-basics' not found."*
- A dollar holding was converted to rupees twice, showing a flat AAPL position
  as −98%.
- Achievement XP was granted inline and again in a trailing pass.
- Earned achievements displayed as locked, because the list was cached in
  `localStorage` and never invalidated.
- The news feed parsed a yfinance schema that had moved, rendering an empty
  headline dated 1 January 1970.
- Flashcards showed the answer face-up, duplicating the theory above them.
- `**Inflation**` rendered as literal asterisks; `[Image of inflation chart…]`
  shipped as body copy.
- Lessons ended at the FAQ with no completion, no XP and no next module.
- The floating nav covered page titles on every page with a sticky sub-header.
- The portfolio drew two stacked tab bars.
- Scenario scores were sent by the client and trusted by the server.
- The "AI hint" was a hardcoded string containing the typo *"the volume volume
  surge"*.
- ESG, hindsight replay and copy trading were fetched on every analysis load and
  never rendered.

---

## Not done

- **Real-time prices.** Quotes are cached for 90 seconds. A live feed needs
  WebSockets and a provider that permits streaming.
- **Market Call settlement** resolves on the next request after the close rather
  than on a schedule. A cron job would make it exact.
- **Content depth.** Nineteen of twenty-five courses have a single module.
  Generated drill questions cover the gap for daily use, but authored content
  would be better.
- **Multi-worker deployment** needs `REDIS_URL` set; the default database cache
  is correct but not fast enough under real load.
- **The LightGBM price model was removed, not fixed.** `ml/` trained a direction
  classifier that no view had called in a long time, and it pulled in scikit-learn,
  scipy, lightgbm and pyarrow for a clean install. Dead code with four heavy
  dependencies is worse than no code; wiring a model to a real decision — sizing
  the prediction game's difficulty, say — is the version worth building.
