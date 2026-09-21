# WealthPlay — Rebuild Plan

Working spec for the full audit → redesign → expansion pass.
Written after a live walkthrough of every route with both servers running.

---

## 0. What this app is today

Django 5 + DRF backend (`courses`, `users`, `simulator`, `chat`, `market_data`, `cursor`,
`mentor_engine`, `ml`) with a React 18 + Vite + Tailwind SPA in `frontend/`.
13 routes, ~8,000 lines of JSX, ~15,000 lines of Python.

Feature surface: 25 courses / 32 modules, a ₹50,000 paper-trading simulator over 15
fictional stocks plus live yfinance tickers, 20 branching financial scenarios, a stock
direction-prediction game, 20 achievements, goals, XP/levels/streaks, and an
"AI mentor" (Nex) split across two separate chat widgets.

---

## 1. What is broken (verified live)

### 1.1 Every LLM provider in the app is dead

| Provider | Configured model | Reality |
|---|---|---|
| Gemini | `gemini-2.0-flash-lite` | **404 — model retired.** Server response says to use `gemini-3.5-flash-lite`. |
| Groq | `llama-3.1-8b-instant` | **404 — model retired.** Account now serves `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `groq/compound`. |

Consequence: every "AI" surface silently falls through to a canned template. What users see
labelled as AI is hardcoded string interpolation. Verified examples:

- `StockChallenge.jsx:475` — the "NEX HINT" button returns a literal fallback string
  containing the typo **"The volume volume surge suggests a potential trend reversal."**
- Portfolio "AI Recommendations" returns self-contradicting boilerplate:
  *"showing strong positive momentum. Technical indicators suggest a cooling period."*
- "AI Judge Feedback" on a prediction repeats its own "AI Analysis" paragraph verbatim.

Groq `openai/gpt-oss-20b` answers in **0.5s** on the existing key and is free. That is the
provider to standardise on. Its responses carry a `reasoning` field alongside `content`,
which the current parsing does not account for.

### 1.2 The lesson mentor is wired to the wrong content store

Asking the in-lesson mentor anything returns **"Course 'investing-basics' not found."**

Two disconnected content systems exist:

- `mentor_engine/course_mentor.py` reads `financial_course.json` — 4 courses
  (`psychology-of-the-pixel`, `quant-technical`, `chart-patterns-pro`, `market-survival`).
- The real catalogue loads from `course_modules/<course>/<module>/*.json` — 25 courses with
  ids like `investing-basics`.

The mentor looks up the user's course id in a file that has never contained it.

### 1.3 Content quality defects baked into the source JSON

- Raw markdown renders literally: `**Inflation**` shows as asterisks on screen.
- An unresolved LLM artifact ships as body copy:
  `[Image of inflation chart showing price of an item increasing over 20 years]`
- "Key Flashcards" are not flashcards. Each card shows the answer immediately, labelled
  "EXPERT ANSWER", and its text is a verbatim copy of the Lesson Theory block directly
  above it. No question, no flip, no recall.

### 1.4 Market news parses a schema that no longer exists

`market_data/views.py` reads `article['title']`, `article['publisher']`,
`article['providerPublishTime']`. yfinance moved these under a `content` object. Every field
comes back empty, so the dashboard renders:

> • 1/1/1970 — "Latest market report: . This development, reported by , is currently
> impacting trader sentiment for AAPL."

An empty title, an empty publisher, and the Unix epoch, shipped to the dashboard.

### 1.5 Performance: one dashboard load costs 44 API calls

Measured from the Django access log on a single `/dashboard` mount:

| Endpoint | Calls | Slowest |
|---|---|---|
| `GET /api/users/portfolio/` | 6× | **4.54s** |
| `GET /api/users/portfolio/stocks/AAPL/` | 3× | **5.62s** |
| `POST /api/users/achievements/check/` | 5× | **4.46s** |
| `GET /api/users/achievements/` | 3× | 4.62s |
| `GET /api/users/profile/` | 6× | 0.20s |

Root causes:

1. `PredictedStockData` — the stock cache table — is **empty (0 rows)**, so `get_stock_info`
   falls through to live yfinance on every call: `.info` plus two `.history()` round trips
   per symbol, ~5s each, inside the request/response cycle.
2. No HTTP-layer or in-process cache. The 10-minute DB cache only helps if something
   populates it, and nothing does.
3. `achievements/check/` is a **POST that writes**, fired on mount from several components
   at once — 5 concurrent writes per page view.
4. React StrictMode double-invokes effects and nothing dedupes in-flight requests.

### 1.6 State is cached but never invalidated

`GlobalDataContext` writes to `localStorage` and guards refetch with
`isHydrated.current !== user.id`. After buying 10 AECB shares the DB correctly recorded the
`first_trade` unlock — but `/achievements` still rendered **0/20, all locked**. The user does
the thing, earns the thing, and the UI shows nothing.

`AuthWrapper` also blocks the **entire app**, including the public landing page, behind a
`checkAuth()` round trip before rendering anything.

### 1.7 Layout and visual bugs

- The floating pill nav is `fixed top-6` while `<main>` gets only `pt-28`. On Goals, Stock
  Challenge and every page with its own sticky sub-header, **the nav sits on top of the page
  title.** Reproduced at 1440×900 — not an edge case.
- **The portfolio tab bar renders twice** — "Explore / Dashboard / Analysis" appears as a
  pill group and again as an underline group, on both desktop and mobile.
- Portfolio chart axes start at ₹0 with a ₹0–₹100 scale while the value is ₹50,000; the empty
  state draws a single meaningless dot; the populated state draws a straight diagonal between
  two points both labelled "17 Sept".
- Sector Distribution pie does not render — legend present, chart area blank.
- Number formatting is inconsistent: `₹45,521.5` next to `₹45,521.50`; `+₹0.00` puts the sign
  before the currency symbol.
- AAPL is priced in **₹** on the Stock Challenge.
- Scenario "Impact Projection (1Y)" draws Current and Projected as identical bars.
- The scenario Risk Exposure gauge needle is pinned and never moves.
- Lesson pages dead-end at "Common Questions" — no complete button, no next module.
- Enter does not submit the mentor chat input.
- Naming is inconsistent: the chat header says **"Next"**, the greeting says **"Nex"**.

### 1.8 Features that exist in the backend but are unreachable

Fully implemented endpoints with no route, no link, and no UI:

- **Time Capsule** — `HistoricalCrisis` (3 rows), `TimeCapsuleSession`, 3 API endpoints.
  Zero frontend references.
- **Dynamic course generation** — `generateDynamicCourse` in `api.js`, never called.
- **ESG scoring, Hindsight Replay, Copy Trading** — `PortfolioAnalysis.jsx` *fetches*
  `getPortfolioESG()` and `getCopyTradingHub()`, defines `runHindsightReplay()`, stores the
  results in `esgData` / `copyHub` / `hindsightData`, and **renders none of them.** Two
  network round trips per page load whose responses are discarded.

### 1.9 Dead code

- `HistoricalLab.jsx` (367 lines) — not imported anywhere.
- `ScenarioPlay.jsx` (538) and `ScenarioResult.jsx` (129) — imported in `App.jsx`, no route.
- ~1,000 lines of unreachable JSX in a repo meant to be read by interviewers.

### 1.10 Repo hygiene

- **A comment-stripper was run over the entire codebase** (`tmp/strip_comments_repo.py`).
  Every Python file now reads `from django .db import models` — mangled spacing, zero
  comments, zero docstrings. This is the single worst thing in the repo for an interview.
- `requirements.txt` is **UTF-16 encoded**, so `pip install -r requirements.txt` fails.
- Both committed virtualenvs point at `C:\python`, which does not exist on this machine —
  Python 3.13 wheels with no matching interpreter. The project does not start from a clean
  clone.
- `SECRET_KEY` defaults to `django-insecure-change-me`.
- API keys are committed in `.env`.

### 1.11 Content volume cannot sustain daily use

| Content | Count | Exhausted in |
|---|---|---|
| Course modules | 32 (19 courses have exactly 1) | a weekend |
| MCQs | ~96 | a weekend |
| Scenarios | 20, served 3 per run | ~7 runs |
| Stock prediction questions | **7** | one sitting |
| Custom stocks | 15 | — |

Requirement 8 — "one user can use this daily and still not feel repetitive" — is not
reachable from this content base without a generation strategy.

---

## 2. Design direction

### 2.1 Why the current UI reads as AI-generated

Measured against the anti-slop audit, the landing page hits nearly every marker: centred hero
with an orange gradient CTA, a 4-box stat strip, a 3-equal-column feature row with pastel icon
chips, a "How It Works" 1-2-3, two fake 5-star testimonials, and a dark navy CTA band dropped
into an otherwise light page. Lucide icons throughout. Every card is border + shadow + white.
Every heading is Title Case and centred.

Worse, the app is not one design — it is four. The dashboard, Achievements, Goals and the
scenario simulator each use a different background colour, header treatment and alignment.
Nothing feels authored.

### 2.2 The direction: The Financial Daily

A daily newspaper's puzzle-and-markets page. Chosen because it answers three requirements at
once:

- It is an identity a person recognises as *designed*, not generated — editorial serif
  masthead, rules instead of shadows, a real grid, tabular figures.
- It gives the daily-return mechanic a native home. A newspaper is inherently a daily
  product; "today's edition" is not a gamification bolt-on.
- It carries Wordle's visual grammar (paper, heavy type, green/amber/grey tiles) without
  copying it, and finance's grammar (tickers, rules, dense tables) without becoming a
  Bloomberg clone.

**Tokens**

```
Paper      #F7F5EF   warm newsprint, light base
Ink        #15140F   near-black, never #000
Dark base  #141310   dark mode paper
Dark raise #1D1C17   dark mode surface

Accent     #1E3A5F   ink blue — authority, the single brand accent
Play       #D9A441   amber — streaks, XP, puzzle tiles only
Up         #15803D   market semantics only
Down       #B91C1C   market semantics only
Rule       #DDD8CB / #2A2822   hairline rules replace most shadows
```

One accent. Green and red are reserved for market data and never used decoratively, so a red
number always means a loss.

**Type**

- Display: `Instrument Serif` — masthead, page titles, large editorial numbers.
- UI and body: `Geist` — 400/500/600, sentence case, 65ch measure.
- Numerals: `Geist Mono` with `font-variant-numeric: tabular-nums` on every figure, so columns
  of money align and digits do not jitter when they tick.

**Layout rules**

- Asymmetric editorial grid. No more centred 3-card rows.
- Hairline rules and spacing carry hierarchy; shadows only where something genuinely floats.
- Dense where it earns it (portfolio, markets, leaderboards), airy where it teaches.
- Full dark mode, system-aware, both themes designed rather than inverted.
- Nav becomes a real top bar in normal flow — this alone removes the overlap class of bugs.

### 2.3 Applied skills

Imported from `/d/BOT` into `.claude/skills/` (22 skills) and used as follows:
`redesign-existing-projects` for the audit method above, `design-taste-frontend` and
`high-end-visual-design` for the anti-slop constraints and motion, `minimalist-ui` for the
editorial surface treatment, `ui-ux-pro-max` for palette, pairing and component checks,
`dataviz` for every chart, `vercel-web-design-guidelines` for the accessibility pass,
`senior-backend` and `code-reviewer` for the Python rewrite.

---

## 3. The daily loop

The hook is a single daily edition with four short plays, all resolving in under five minutes.

**1. Ticker Tiles** — the Wordle mechanic, done properly. Guess the mystery listed company in
five tries. Each wrong guess reveals one more clue in a fixed order: sector → market-cap band
→ 1-year chart silhouette → P/E band → first letter. Tile feedback is green / amber / grey.
Everyone gets the same puzzle on the same day. Shareable emoji grid. It teaches company
identification by fundamentals, which is the point.

**2. Market Call** — one binary call on a real index, locked at market open, resolved at
close. Builds a separate calibration streak and a Brier score, so the app can eventually tell
a user *"you are overconfident on down days"* — a real, teachable insight.

**3. Number Sense** — guess one real figure (the current repo rate, gold per 10g, the EMI on
₹30L over 20 years). Scored by proximity band, not exact match. Builds intuition for
magnitudes, which most beginners lack.

**4. Daily Drill** — five questions drawn by an SM-2 spaced-repetition scheduler from modules
the user has already completed. Because scheduling is per-user and interval-based, the same
question does not recur on consecutive days, and the pool grows as the user learns more.

Around these: a streak with one earnable freeze token, a weekly recap, a share card, and a
"today's edition" masthead that changes date and lead story daily.

---

## 4. Work plan

### Stage 1 — Foundations

1. Repo hygiene: UTF-8 `requirements.txt`, working venv bootstrap, `.env.example`,
   `SECRET_KEY` from env with a startup check, `.gitignore` audit.
2. Delete `tmp/strip_comments_repo.py`, reformat all Python, restore real docstrings.
3. Delete dead code: `HistoricalLab.jsx`, `ScenarioPlay.jsx`, `ScenarioResult.jsx`, the unused
   state in `PortfolioAnalysis.jsx`, and the duplicated `transform_topic_to_course` in both
   `courses/course_views.py` and `mentor_engine/course_mentor.py`.
4. Design tokens: rewrite `index.css` and `tailwind.config.js` around the palette above, with
   dark mode. One source of truth, no ad-hoc hex values in components.

### Stage 2 — Make it fast

5. `services/market.py`: one cached accessor for prices, quotes and history. Django cache
   (LocMem in dev, Redis-ready) with staggered TTLs, a warm-on-startup pass, and a management
   command to prime `PredictedStockData`. No yfinance call in a request path, ever.
6. Split `achievements/check/` into a cheap idempotent GET and an explicit POST fired only
   after a real XP event.
7. Replace `GlobalDataContext` with a small query cache: request dedupe, stale-while-
   revalidate, cache keys invalidated by mutations. Target: dashboard from 44 requests to
   under 8, cold load under 800ms.
8. Move `AuthWrapper` off the render-blocking path so the landing page paints immediately.
9. Route-level code splitting via `React.lazy`.

### Stage 3 — Make the AI real

10. `ai/client.py`: one provider-agnostic LLM client. Groq `openai/gpt-oss-20b` primary (free,
    0.5s), `openai/gpt-oss-120b` for heavier reasoning, Gemini `gemini-3.5-flash-lite` as
    failover, deterministic fallback last. Handles the `reasoning` field, retries, timeouts,
    response caching and a per-user rate limit.
11. Delete every hardcoded "AI" string, including the `volume volume` fallback.
12. Rebuild the mentor against the **real** course store, with the current module's theory,
    its MCQs and the user's own progress as context. One mentor component, not two. Streaming
    responses, Enter to send, persisted history.
13. Real AI where it earns its place: trade-rationale critique, portfolio risk review,
    wrong-answer explanations, weekly recap narration.

### Stage 4 — Fix every broken feature

14. Rewrite the yfinance news adapter against the current schema, with a real empty state.
15. Markdown rendering in lesson content; strip the `[Image of ...]` artifacts from source.
16. Rebuild flashcards as genuine two-sided recall cards with a confidence rating that feeds
    the spaced-repetition scheduler.
17. Fix charts: correct domains, real date axes, working pie, dataviz-compliant palette.
18. One `formatMoney` / `formatPercent` / `formatCompact` utility. Correct currency per
    instrument — AAPL in USD, RELIANCE in INR.
19. Lesson completion flow: complete → XP → next module → course progress.
20. Fix the nav overlap, the duplicated portfolio tab bar and the scenario projection.

### Stage 5 — Build the daily loop

21. New `daily` app: `DailyPuzzle`, `PuzzleAttempt`, `Streak`, `ReviewCard` (SM-2), with
    deterministic daily seeding so all users share a puzzle.
22. Ticker Tiles, Market Call, Number Sense, Daily Drill.
23. Streak with freeze token, share cards, weekly recap.

### Stage 6 — Expand what exists

24. Surface Time Capsule as a real route.
25. Render ESG, Hindsight Replay and Copy Trading — the data is already being fetched.
26. Trading: limit orders, short positions and stop-loss (currently padlocked), a real trade
    ledger, and P&L attribution.
27. Course content: fill every 1-module course to 4+ modules, plus LLM-generated practice
    questions seeded from module theory so drills never run dry.
28. Leaderboards by category, with weekly seasons.
29. Onboarding that actually personalises the first week.

### Stage 7 — Interview-grade finish

30. Tests: pytest for the market cache, the AI client fallback chain, scoring and streaks;
    Playwright for the critical paths.
31. `README` rewrite with architecture diagram, decisions and trade-offs.
32. Accessibility pass against `vercel-web-design-guidelines`: focus rings, skip link,
    contrast, keyboard paths, reduced motion.
33. 404 page, error states, skeleton loaders, empty states.

---

## 5. Non-negotiables

- Replace code, never append. Every rewritten file loses its old version.
- No file over ~300 lines. `portfolio_views.py` is 1,950 and splits into a package.
- Comments explain *why*. The stripper is never run again.
- No API keys touched. Only the dead model identifiers change.
- Verified in the browser before anything is called done.
