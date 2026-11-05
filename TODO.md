# TODO - Copenhagen Re-Commerce Matrix

Single source of truth for everything left to do: bug fixes first, then the product roadmap.
Merged on 2026-11-05 from (a) the static review of the repo and (b) the "Mega-Roadmap" written by Rob.
Updated 2026-11-05 with the real Supabase table definitions (no RLS policies included in that export).
Companion file: `DECISIONS.md` (why things are the way they are).

## How to use this file

- Work top to bottom. Each phase must be finished (or consciously skipped) before the next.
- Every item has an ID (e.g. `1.04`). Ask for work by ID: "let's do 1.04".
- One change at a time, each with a verification command (`pytest`, `mypy`, `streamlit run dashboard.py`).
- At the end of every important session: tick items, add new ones, update `DECISIONS.md`.
- Hard rules: **budget zero**, **no real secrets anywhere**, **no invented numbers or claims**.

Legend: `[ ]` todo, `[~]` partly done, `[x]` done. **VERIFY** = I could not confirm it from the code; check it before relying on it.

## Where the old roadmap stands today

| Roadmap item | Status | Notes |
|---|---|---|
| Business personas / dynamic weights | [~] | 4 profiles in `cpi_engine.py`; weights are arbitrary and unvalidated; no onboarding quiz |
| Live data (Overpass, Open Data) | [ ] | Zone data is hand-written in `seed_data.py`, which is currently broken |
| Time series | [ ] | No history table |
| Commercial real estate data | [ ] | Not started; API availability unknown (VERIFY) |
| Saturation index | [ ] | Needs monthly competitor snapshots first |
| Multi-city schema | [ ] | Schema has no city concept |
| Telegram quiz | [ ] | Bot has a menu + business-type choice + lead funnel only |
| Competitor / real-estate alerts | [ ] | Needs data pipeline + opt-in |
| NLP in the bot | [ ] | Not started |
| Telegram paywall | [ ] | Today: report gated behind lead capture, no payment |
| Favorites (`/salva`) | [ ] | Not started |
| Auth, saved scenarios | [ ] | Not started |
| 3D map | [~] | PyDeck ColumnLayer on a CARTO basemap works; no competitor pins |
| Responsive / iPad | [ ] | Not tested (VERIFY) |
| Next.js migration | [ ] | Deferred, see "Roadmap items re-evaluated" |
| Dark/light theme | [x] | `st-theme` + fallbacks; enterprise branding not started |
| PDF report | [~] | 1-page fpdf2 report with AI text; no charts, no cover |
| White-label, PPTX, newsletter | [ ] | Not started |
| Rate limiting, cache, API protection | [ ] | Dashboard has a 60 s `st.cache_data`; API is open |
| Sentry | [ ] | Not started |
| CI | [~] | Workflow exists but is almost certainly failing (see 1.01) |
| CD, DB backups | [ ] | VERIFY what Render/Supabase do today |
| Landing page, pricing, API-as-a-service | [ ] | Not started |
| GDPR | [ ] | Nothing implemented yet |

## Confirmed database facts (from the Supabase table definitions)

- `copenhagen_zones` columns: `id`, `name`, `district_code` (UNIQUE, NOT NULL), `population_gen_z` (integer count), `avg_income_dkk`, `waste_supply_score`, `market_gap_score`, `cpi_score` (default 0), `created_at`.
- **There is no `demographics_score` column.** The engine therefore uses the stored `cpi_score` as the Demographics pillar (bug 1.02 is confirmed, not a hypothesis).
- `population_gen_z` is an absolute count, not a share of residents, so populous districts are favoured by construction.
- No city column, no snapshot date, no history: multi-city and time series need the schema work in Phase 3.
- `leads` columns: `id`, `telegram_user_id`, `telegram_username`, `full_name`, `email`, `business_type`, `interested_district`, `created_at`. No unique constraint on `telegram_user_id` (so duplicates are possible), no consent or notice-version columns.
- Until 2026-11-05 RLS was OFF with full privileges for `anon` and `authenticated`; it is now ON with those privileges revoked (see 1.16). Still unknown: project region, which key the API and bot use.

---

## Phase 1 - Stop the bleeding (bugs, security, CI)

Done when: CI is green, the bot answers every button without freezing the API, nobody can write to the DB through an open endpoint, and the data model is honest.

### Correctness
- [ ] **1.01 CI red.** `mypy` and `pytest-cov` are used by `.github/workflows/ci.yml` but missing from `requirements.txt`. Create `requirements-dev.txt` (pytest, pytest-cov, mypy, ruff), install it in CI, keep runtime requirements lean. Verify on the Actions tab.
- [ ] **1.02 Demographics pillar is circular (CONFIRMED: the column does not exist).** Today the Demographics input is the stored `cpi_score`, an old overall CPI, and in the dashboard it is even the API's already-overwritten `curated_vintage` CPI. Steps:
  - [ ] a. Decide and write in `DECISIONS.md` how Demographics is derived from `population_gen_z` and `avg_income_dkk` (normalization, relative weight of the two, 0-10 output). Prefer the share of 18-35 residents over the absolute count (see 3.03). Rob confirms the formula.
  - [ ] b. Add the column (`demographics_score numeric`) with a migration committed in `supabase/schema.sql`, and fill it from the seed script, never by hand.
  - [ ] c. Remove the `cpi_score` fallback in `calculate_dynamic_cpi`: a missing pillar must raise or log an error, not silently use another number.
  - [ ] d. Decide the fate of the stored `cpi_score` column (legacy baseline: rename or drop). The API field `cpi_score` is always the computed one.
  - [ ] e. Update `test_main.py` for the new behaviour (the test `test_demographics_falls_back_to_cpi_score` must change).
- [ ] **1.03 Dashboard double-computes the CPI.** Call `/zones?business_type=...` and remove the local `calculate_dynamic_cpi` pass in `dashboard.py` (or stop the API from overwriting `cpi_score`). One place computes the CPI.
- [ ] **1.04 `seed_data.py` is broken** (imports non-existent `compute_cpi`) and wipes the whole table with `delete()`. Rewrite it to upsert on `district_code` (the UNIQUE column), use `calculate_dynamic_cpi`, include `demographics_score`, and require an explicit `--reset` flag to delete. The `district_code` values look like postal codes plus invented suffixes (e.g. `DK-2300-E`): document what they mean.
- [ ] **1.05 PDF crash for "Vesterbro / Kongens Enghave".** The `/` ends up in the filename. Generate the PDF in memory (`BytesIO`/`output()` bytes) or in `tempfile`, never from user/DB text; also fixes concurrent users overwriting each other.
- [ ] **1.06 Event loop blocked.** PDF + Gemini run synchronously inside an async handler on the same loop as the API. Wrap with `asyncio.to_thread`.
- [ ] **1.07 Telegram Markdown breaks on user names** (`_`, `*`). Use HTML parse mode with `html.escape`, or `telegram.helpers.escape_markdown`.
- [ ] **1.08 Wrong district in the PDF.** `receive_email` falls back to `zones[0]` when the name is not found. Show an error instead.
- [ ] **1.09 Silent bot branches.** Non-200 responses from the API leave the user without any message (`calc_top`, `list_zones`, PDF flow). Always answer.
- [ ] **1.10 Stuck conversation** (confirmed 2026-11-05: after an unfinished PDF request the bot ignored `/start` until `/cancel` was sent). While waiting for name/email, `/start` and the buttons do nothing. Add `/start` to fallbacks and a `conversation_timeout`.
- [ ] **1.11 Bot reachability.** `httpx` timeout 10 s is shorter than a Render cold start (up to about a minute). Raise it and add one retry.
- [ ] **1.12 Duplicate bot polling.** Start the bot in exactly one place (API `lifespan` OR the compose `telegram-bot` service, not both, and not from a local `--reload` with the production token). Keep a reference to the task and shut the bot down cleanly in `lifespan`.
- [ ] **1.13 Leads inserted twice.** Same user, many rows. `leads` has no unique constraint on `telegram_user_id`: first deduplicate existing rows, then add the constraint (migration in `supabase/schema.sql`), then switch the bot to upsert.
- [ ] **1.14 Gemini model default is deprecated** (`gemini-3.7-flash` is auto-routed to 3.8 Flash). Set the default to the current model after checking it is available on the free tier (VERIFY in AI Studio) and surface API errors in logs, not only `print`.

### Security
- [ ] **1.15 `.env` baked into the Docker image.** Add `.env` (and tests/docs) to `.dockerignore`. Replace `load_dotenv(override=True)` with `load_dotenv()` in `bot.py`/`main.py`/`database.py` so compose/Render variables win.
- [~] **1.16 Supabase keys and RLS.** Status 2026-11-05: RLS was OFF and `anon`/`authenticated` had every privilege on both tables (anyone with the public key could read, modify or delete leads). Fixed by Rob: RLS enabled and all privileges revoked; `rowsecurity` is now true on both tables, and the bot's Top 5 screen still works afterwards (zones are read by the API). Done: (a) lead insert from the bot tested on 2026-11-05, the row appears in `leads` (timestamps are stored in UTC, so they look one hour behind Italian winter time: correct, convert only when displaying). Still to do: (b) re-run the grants query and confirm no rows for `anon`/`authenticated`; (c) confirm the key on Render is the secret key and keep it out of the repo, chat and screenshots; (d) record the final policy state in `supabase/schema.sql`. Original checklist: RLS must be on for `leads` with no read policy for the public (anon) key; use the service-role key only server-side, never in the dashboard or in a repo. `seed_data.py` deleting with the same key suggests the zones table may be writable by too many roles: check. Run in the Supabase SQL editor and record the result here:
  - `select tablename, rowsecurity from pg_tables where schemaname = 'public';`
  - `select tablename, policyname, roles, cmd from pg_policies where schemaname = 'public';`
  - `select grantee, table_name, privilege_type from information_schema.role_table_grants where table_schema = 'public' and grantee in ('anon', 'authenticated');`
  - Then check in Render/Streamlit secrets whether `SUPABASE_KEY` is the anon key or the service-role key (never paste either in chat).
- [ ] **1.17 `POST /leads` is open and unused.** Remove it (the bot writes directly) or protect it. Validate email (`EmailStr` + `email-validator`) if it stays.
- [ ] **1.18 CORS.** `allow_origins=["*"]` with `allow_credentials=True` is a bad combination. Set credentials to `False` (the API has no cookies) or list real origins.
- [ ] **1.19 No PII or secrets in logs.** Remove the lead dump in `bot.py` and the URL print in `database.py`; stop returning `{e}` to users and in `HTTPException.detail`.
- [ ] **1.20 Secret scan of git history.** `docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:latest detect --source /repo`. Rotate anything found.
- [ ] **1.21 Pin dependencies** (at least `fpdf2`, `supabase`, `python-telegram-bot`, `streamlit`, `google-genai`). Remove unused `plotly` until it is used. `.devcontainer`: re-enable XSRF protection.

### Free-tier survival (budget zero)
- [ ] **1.22 Keep Render + Supabase awake** (observed 2026-11-05: the bot answered only after the dashboard had woken the API). Render free spins down after 15 minutes without traffic and the bot lives in that process; Supabase free pauses after about a week without activity. Use a free external pinger on `/zones` every ~10 minutes (check the free tier's minimum interval, VERIFY). Not a guarantee, so also keep the manual-restore steps in the README.
- [ ] **1.23 Verify Streamlit Community Cloud sleep behaviour** before any demo (VERIFY) and decide the warm-up routine.

---

## Phase 2 - Make the repo tell the truth, and make GDPR real

Done when: README, docs and the Project instructions match the code, and the `leads` flow has notice, consent and deletion.

### GDPR (not legal advice; Rob is the data controller)
- [ ] **2.01 Privacy notice before collection:** who collects, what (name, email, Telegram ID, username, district, profile), why, how long, how to exercise rights, contact.
- [ ] **2.02 Separate consent for being contacted** (distinct from receiving the report); add columns to `leads` for `contact_consent` (boolean), `consent_at` (timestamptz) and `privacy_notice_version` (text); today the table has none of them.
- [ ] **2.03 `/delete_my_data`** command (and email request path) that deletes the lead and every related row (favorites, subscriptions later).
- [ ] **2.04 Retention period** decided and enforced (scheduled delete).
- [ ] **2.05 Data minimization review:** is `telegram_username` needed? Confirm the Supabase region is in the EU (VERIFY).
- [ ] **2.06 Keep PII out of the LLM prompt** (today it is out; keep it that way and note it in `DECISIONS.md`).

### Honesty and documentation
- [ ] **2.07 README:** remove or build the claims about radar chart, GeoJSON choropleth, Plotly, "Premium tier", PDF download from the dashboard, "100% coverage", "mypy 100%". Replace static badges with real ones or delete them.
- [ ] **2.08 Align the CPI documentation with the code:** weights per profile, 0-10 scale (not 0-100), one definition of Market Gap (README, `docs/core_strategy.md` and instructions currently disagree), and which pillar uses `population_gen_z`/`avg_income_dkk` (today none: they are display-only).
- [ ] **2.09 Data provenance.** Write down where each seed number comes from. If it is hand-assigned, say so. Do not cite Open Data DK / Statistikbank / OSM as sources until the pipeline in Phase 3 exists.
- [ ] **2.10 Licence wording.** The repo is MIT: remove "proprietary formula" from `docs/core_strategy.md` or change the licence consciously.
- [ ] **2.11 Fix the Project instructions:** map theme (code is same-theme, instructions say the opposite), `COPENHAGEN_COORDS` always overrides DB coordinates, base weights 0.40/0.35/0.25 do not exist in code, routes list.
- [ ] **2.12 `.env.example`:** add `GEMINI_API_KEY`, `GEMINI_MODEL`; make the three `API_URL` defaults consistent; the dashboard must not default to the production URL.
- [ ] **2.13 PDF footer honesty:** say when the text is template-generated, not AI; real page count; remove the unsupported "high ROI" wording from the fallback text.
- [ ] **2.14 Cleanup:** delete or use `schemas.py` (wire as `response_model`) and the unused GeoJSON (or replace it with real district boundaries and a source).

### Quality
- [ ] **2.15 Tests:** mock Gemini in `test_pdf_generator.py`; add tests for the bot handlers (callbacks, email validation, filename safety); measure real coverage and publish only that number.
- [ ] **2.16 Static checks:** add `ruff` to CI; extend `mypy` beyond `cpi_engine.py` and `schemas.py`.

---

## Phase 3 - Data foundation (what makes the CPI real)

Done when: the CPI is computed from documented, dated data, and history accumulates automatically.

- [ ] **3.01 Schema redesign (also gives multi-city):** `cities`, `zones(city_id, name, geometry/centroid, ...)`, `zone_metrics(zone_id, metric, value, source, snapshot_date)`. Commit as SQL migrations in the repo. A new city then means new rows, not new code. Start from the existing `copenhagen_zones` (keep `district_code` UNIQUE, but make it unique per city) and write a migration that moves the current rows without losing them.
- [ ] **3.02 Define each pillar formula in writing** (inputs, normalization, e.g. percentile within a city, 0-10 output). Supply, Demographics, Market Gap each get one paragraph in `docs/`. Update `core_strategy.md`.
- [ ] **3.03 Demographics from official statistics.** Check Danmarks Statistik / Copenhagen municipality open data for district-level age and income (VERIFY availability, granularity and licence). Replace the hand-written values. Store the **share** of 18-35 residents (not only the absolute count, which favours populous districts) and say whether `avg_income_dkk` is per capita or per household.
- [ ] **3.04 Market Gap from OpenStreetMap (Overpass).** Count second-hand/vintage shops per district. Use a **monthly batch job** (free GitHub Actions cron) instead of live queries per request: respects Overpass fair use and produces the history below. Respect ODbL attribution (VERIFY share-alike implications before selling data/API access).
- [ ] **3.05 Supply data.** Find a real source for textile waste / sorting points; if none exists at district level, say so and keep it explicitly labelled as an estimate.
- [ ] **3.06 Time series (original roadmap item).** Each batch run writes a dated snapshot to `zone_metrics`; add a trend view (Gen Z growing or shrinking, shops opening or closing). Needs several months of snapshots before it means anything.
- [ ] **3.07 Saturation index (original roadmap item).** Derived from snapshot differences of competitor counts over 6 months. Do not promise "a shop just opened" alerts: OSM data is not real time.
- [ ] **3.08 Model validation (strong for ITU).** Sensitivity analysis on the weights (does the Top-3 change?), rank stability across profiles, compare high-CPI districts with where second-hand shops already exist. Document method and limits.
- [ ] **3.09 Justify the profile weights** (four personas): why 0.5/0.3/0.2 for `kilo_sale`, etc. Interview or desk research; write in `DECISIONS.md`.
- [ ] **3.10 Commercial real estate (original roadmap item).** First check whether Ejendomstorvet or any other source has a usable API at zero cost (VERIFY). If not, use publicly available average rent per m2 per district as a static reference, clearly dated.

---

## Phase 4 - Product features

### Telegram bot
- [ ] **4.01 Onboarding quiz** (activity type, budget, floor area). First decide how budget and area affect the result (filters? profile choice?). A quiz whose answers change nothing is theatre.
- [ ] **4.02 Favorites `/salva`** (2-3 districts), stored in a `favorites` table covered by `/delete_my_data`.
- [ ] **4.03 Natural-language search with Gemini.** The LLM only translates the sentence into parameters (profile, filters, sort); the CPI engine does the maths. Validate the JSON output and never let the model invent figures. Watch free-tier rate limits and add a fallback to the menu.
- [ ] **4.04 Proactive alerts** (competitors, real estate): only after 3.04/3.07/3.10, only for users who opted in, with an easy `/stop`.
- [ ] **4.05 Payments in chat:** do not build yet (see "Roadmap items re-evaluated").

### Dashboard
- [ ] **4.06 Two-district benchmark + radar chart** (promised in README and instructions, not implemented). Respect the Executive design system (16 px radius, Salvia `#6E8E80`, light/dark).
- [ ] **4.07 Map quality:** colour scale normalized per profile instead of absolute thresholds, state the elevation baseline, show CARTO/OSM attribution, competitor and sorting-point pins from the OSM data (3.04).
- [ ] **4.08 Add a PDF download button** in the dashboard (same generator as the bot).
- [ ] **4.09 Responsive check on iPad width** (about 1024 px) and fix what breaks.
- [ ] **4.10 Auth and workspaces:** only when there are real users asking for it. Options to evaluate: Supabase Auth (free tier covers 50,000 MAU, VERIFY current limits) or Streamlit's built-in login (VERIFY version support). Then a `scenarios` table with RLS per user ("Scenario Opening 2027").
- [ ] **4.11 Enterprise branding** (custom colours/logo): after auth and a real customer.

### Reports
- [ ] **4.12 PDF redesign:** multi-page layout, cover, a proper TTF font via `add_font` (pick an open-licence font, VERIFY licence), grid layout.
- [ ] **4.13 Charts inside the PDF:** radar + pillar bars as PNG (matplotlib is enough and free), map snapshot later.
- [ ] **4.14 PPTX export** with `python-pptx` (free), after the PDF is stable.
- [ ] **4.15 White-label** (agency logo/branding) and **monthly email recap**: only with auth, a customer asking, and double opt-in; check free email-sending limits first (VERIFY).

---

## Phase 5 - Platform and DevOps

- [ ] **5.01 Protect the API.** A shared secret in a header (`X-API-Key`) between dashboard, bot and API is enough now and free. Move to JWT only when end-user auth exists (4.10).
- [ ] **5.02 Rate limiting** (e.g. `slowapi`) on public routes.
- [ ] **5.03 Cache.** In-process TTL cache (`cachetools`) for `/zones` per `business_type`. Redis is unnecessary with about a dozen rows; revisit when multi-city and traffic justify it.
- [ ] **5.04 Error monitoring.** Evaluate Sentry's free plan (VERIFY limits); at minimum structured logs without PII.
- [ ] **5.05 CD.** Make Render deploy only after CI passes (check the option in Render settings, VERIFY) and add a post-deploy health check on `/`.
- [ ] **5.06 Backups.** Check what the free Supabase plan includes (VERIFY; free plans may have none). If none, scheduled `pg_dump` from GitHub Actions to an encrypted artifact. Backups contain PII: apply the retention rule (2.04).
- [ ] **5.07 Docker cleanup:** non-root user, drop `build-essential` if unneeded, remove obsolete `version:` in compose, split runtime vs dev dependencies.

---

## Phase 6 - Business, growth and competitions (run in parallel from Phase 2)

- [ ] **6.01 Competitor research before any "Blue Ocean" claim.** Verify CARTO and other location-intelligence tools, plus Danish/Nordic alternatives. Then build the strategy canvas and the Eliminate-Reduce-Raise-Create grid on facts. Update `docs/core_strategy.md`.
- [ ] **6.02 Customer discovery.** Talk to real second-hand shop owners/pop-up organisers (remote is fine). Record what they say; this is the traction and the evidence for pricing.
- [ ] **6.03 Pricing is a hypothesis.** The $49 / $299 tiers have no evidence yet. Present them in the pitch as hypotheses until 6.02 supports them.
- [ ] **6.04 Landing page** as a static site on a free host (e.g. GitHub Pages, VERIFY) on a free subdomain. A custom domain costs money, so it conflicts with the budget until funded.
- [ ] **6.05 Freemium tiers in the product:** only after 5.01 and 2.01-2.03. Payments: see "re-evaluated".
- [ ] **6.06 API-as-a-service:** only after 5.01, 5.02, the data licences (3.04, 3.03) are checked and there is a customer.
- [ ] **6.07 Pitch claims audit** (Blue Ocean, IASC, personal statement): every number, source, coverage and feature claim checked against this file. Keep a one-page "what is real today vs what is roadmap".
- [ ] **6.08 IASC framing:** today the AI writes the report commentary on top of a deterministic index. Describe it exactly like that, and decide which AI features (4.03 natural-language search, data extraction) make it genuinely stronger before the pitch.
- [ ] **6.09 Narrative log.** After each significant fix or trade-off (e.g. 1.02, 1.12, 3.08) add a one-line, verifiable fact to `DECISIONS.md` for the personal statement (CBS: business angle; ITU: data/method angle).
- [ ] **6.10 Competition requirements:** upload the official rules/criteria to the Project knowledge; deadlines are not known to this file.

---

## Roadmap items re-evaluated

| Original idea | Decision | Reason |
|---|---|---|
| Redis cache | Replace with in-process TTL cache | About a dozen rows; Redis adds a moving part |
| JWT for the API | Start with a shared API key | Only the dashboard and the bot call the API; JWT when users log in |
| Mapbox | Stay on PyDeck + CARTO/MapLibre-compatible styles | Mapbox free tier limits and terms (VERIFY) vs current zero-cost setup |
| Telegram payments + Stripe | Postpone | Needs a registered activity, tax and legal review, a payment provider and a validated price; fees apply to revenue (VERIFY availability in Italy) |
| Pro $49 / Enterprise $299 | Treat as hypotheses | No customer evidence yet |
| Next.js migration | Postpone | Large rewrite; Streamlit is enough for the competitions; revisit with paying users |
| Live Overpass queries | Replace with monthly batch | Fair use, speed, and it creates the time series |
| OpenAI in the bot | Use Gemini only | Budget zero |
| Custom domain | Postpone | Costs money |
| Real-time competitor alerts | Reframe as "changes since last snapshot" | OSM data is not real time |
| Real estate API (Ejendomstorvet) | Verify first | API existence and cost unknown |

## Verify before claiming (open facts)

- Supabase: region, backup behaviour, key type used by API/bot (table definitions known; RLS verified on 2026-11-05).
- Where each seed number comes from.
- Real test coverage and whether CI is green.
- Render auto-deploy settings and the Streamlit Cloud sleep policy.
- Gemini free-tier quota for the model actually used.
- Open data licences (OSM ODbL, statistics sources) before any data/API product.
- Competitor landscape and competition rules/deadlines.
