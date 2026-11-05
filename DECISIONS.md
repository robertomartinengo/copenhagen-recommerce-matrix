# DECISIONS

Why the project is the way it is. One entry per decision: what, why, what was discarded, status.
Companion file: `TODO.md`.

Reconstructed from the codebase and the Supabase table definitions on 2026-11-05.
Reasons marked "(inferred)" were not stated by the author: confirm or delete them.
Add a new entry (next free number) at the end of every important session, and never rewrite history:
if a decision changes, add a new entry and mark the old one "Superseded by D-0XX".

## D-001 CPI = weighted sum of three 0-10 pillars, with weights per business profile
- Status: Accepted in code; documentation out of date.
- Decision: `calculate_dynamic_cpi` in `cpi_engine.py` uses four independent weight sets
  (waste / demo / gap): vintage_premium 0.20/0.40/0.40, kilo_sale 0.50/0.30/0.20,
  upcycling 0.40/0.20/0.40, curated_vintage 0.33/0.33/0.34. Each row sums to 1.
- Reason: the best district depends on the business model (inferred). Covered by
  `test_business_type_changes_ranking`.
- Discarded: single fixed weights 0.40 / 0.35 / 0.25. They are still described in README,
  `docs/core_strategy.md` and the Project instructions, but do not exist in the code.
- Open: the weight values themselves are not yet justified (see TODO 3.09).

## D-002 CPI is computed at read time, not stored
- Status: Accepted.
- Decision: the API recomputes the CPI per request and per profile. The stored `cpi_score` column is a legacy baseline.
- Open: see D-003, because the stored value is currently used as an input.

## D-003 Demographics pillar has no real input (known defect)
- Status: Defect, to be fixed (TODO 1.02).
- Fact (confirmed from the schema): `copenhagen_zones` has no `demographics_score` column.
  `calculate_dynamic_cpi` falls back to the stored `cpi_score`, so the Demographics pillar is
  actually an old overall CPI. In the dashboard it is even the already-overwritten API value.
  `population_gen_z` and `avg_income_dkk` are only displayed.
- Planned decision (to confirm): derive Demographics from the share of 18-35 residents and
  income, with an explicit documented formula; remove the silent fallback.
- Do not present the Demographics pillar as "Gen Z + income" in any pitch or statement until this is fixed.

## D-004 Telegram bot runs inside the API process
- Status: Under review.
- Reason: a single free Render web service (inferred).
- Costs: the bot stops when the free service sleeps; synchronous PDF/Gemini work blocks the shared
  event loop; `docker-compose.yml` also defines a separate `telegram-bot` service, so the token can be polled twice.

## D-005 Leads are written directly from the bot to Supabase
- Status: Accepted. `POST /leads` in `main.py` is unused and is to be removed or protected.
- Fact (confirmed from the schema): `leads` has no unique constraint on `telegram_user_id` and
  no consent or notice-version columns.

## D-006 Gemini is used only for the report commentary, with a deterministic fallback
- Status: Accepted.
- Decision: `ai_reporter.py` produces ~70 words of text from four numbers; any error or empty
  answer falls back to a template. The model comes from `GEMINI_MODEL`.
- Facts: the default `gemini-3.7-flash` is deprecated (routed to 3.8 Flash). No personal data is sent to the model.
- Honest framing: the AI does not compute the CPI. It writes commentary on top of a deterministic index.

## D-007 PyDeck ColumnLayer instead of a GeoJSON choropleth
- Status: Accepted.
- Reason: 3D columns are readable with few districts (inferred).
- Fact: `copenhagen_districts.geojson` exists but is unused, and its polygons are rough rectangles, not official boundaries.

## D-008 Map and theme follow the browser theme
- Status: Accepted in code. A light browser gets a light basemap, a dark browser a dark one.
  The Project instructions say the opposite: fix the instructions, not the code, unless Rob says otherwise.
- Implementation: `st-theme` with fallbacks to `st.context.theme.type` and `theme.base`.

## D-009 Budget zero
- Status: Hard constraint.
- Stack: Render free, Supabase free, Streamlit Community Cloud, Gemini free tier, GitHub Actions, Telegram.
- Known limits: Render free sleeps after 15 minutes without traffic; Supabase free pauses after about a week
  of inactivity; Streamlit Cloud sleep policy and Gemini free-tier quotas to be verified.

## D-010 Zone data is hand-curated
- Status: Open.
- Fact: all values come from `INITIAL_ZONES` in `seed_data.py` (which currently does not run). No source is documented.
- Rule: do not cite Open Data DK, Statistikbank or OpenStreetMap as data sources until a pipeline
  that really uses them exists (TODO Phase 3).

## D-011 Repository licence is MIT
- Status: Accepted.
- Consequence: the CPI formula is public. "Proprietary formula" wording in `docs/core_strategy.md` must go
  (or the licence must be changed on purpose).

## D-012 Supabase access model: RLS on, no public policies, server-side key only
- Status: Accepted 2026-11-05; the lead insert from the bot still has to be tested (TODO 1.16).
- Fact found in a review: both tables had RLS off and `anon`/`authenticated` held every privilege
  (including delete and truncate), so anyone with the public key could read or alter the leads.
- Decision: RLS enabled on `leads` and `copenhagen_zones`, all privileges revoked from `anon` and
  `authenticated`, no policies. Only the backend (API and bot) talks to the database, with the
  secret key stored in Render and in the local `.env`, never in the repo, chat or screenshots.
- Discarded: policies that let `anon` insert leads directly (they would allow public writes and spam).
- Consequence: if a browser client ever talks to Supabase (e.g. user login, TODO 4.10), policies per user must be designed first.

## Narrative log (facts usable for pitch and personal statement)
Only verifiable facts. Add one line after each significant fix or trade-off.

- 2026-11-05: the same zone data produces different rankings for four business models (proved by `test_business_type_changes_ranking`).
- 2026-11-05: the PDF report keeps working when the AI service fails, thanks to a tested fallback.
- 2026-11-05: a security review found the leads table readable and deletable with the public key; row-level security was enabled and the privileges revoked the same day.
