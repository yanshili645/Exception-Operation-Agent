# PowerWash Daily Exception Report v0.1

Read-only MVP that combines ServiceM8 job execution with Deputy rosters and
timesheets, applies auditable exception rules, and produces a management-ready
HTML report plus CSV/JSON evidence files.

The repository now includes the **PowerWash Operations Exception Agent**:

- `AGENTS.md` defines the repository-level operating charter.
- `.codex/skills/powerwash-exception-agent/` contains the reusable agent skill,
  UI metadata, PowerWash rules, live runbook and report contract.
- Scheduled runs must use live data and stop visibly when a source is blocked.

## Activate the agent

Open or import this repository as a ChatGPT Work/Codex project. The root
`AGENTS.md` supplies the agent charter and the project skill is discovered from
`.codex/skills/powerwash-exception-agent/`.

Before the first live run, configure the three required source secrets described
in `.env.example` and replace the example staff mapping. Keep the existing
scheduled workflow disabled until one historical live-account day reconciles
with the source systems.

Use `BOSS_DEMO.md` for a short management demonstration.

## What this version proves

- Deterministic rules identify operational exceptions; AI never decides whether
  a rule was breached.
- ServiceM8 staff UUIDs are matched to Deputy employee IDs through a controlled
  mapping file. Truck resources are kept separate from people.
- The report identifies incomplete work, late jobs, priority-site breaches,
  duration overruns, no-shows, late starts, overtime, missing breaks, unapproved
  timesheets and cross-system mismatches.
- An optional AI step turns the fixed exception register into a concise
  management narrative. Without AI credentials, a deterministic summary is used.
- No records are written back to ServiceM8 or Deputy.

## Run the boss demo

```bash
PYTHONPATH=src python -m powerwash_report.cli \
  --mode demo --date 2026-09-13 --output outputs/demo
```

Open `outputs/demo/daily_exception_report.html`. Supporting files are:

- `exceptions.csv` — auditable exception register
- `management_summary.json` — headline results and narrative
- `source_snapshot.json` — counts and source mode, without credentials

## Run from exported JSON files

Place four JSON arrays in one directory:

- `servicem8_jobs.json`
- `servicem8_activities.json`
- `deputy_rosters.json`
- `deputy_timesheets.json`

Then run:

```bash
PYTHONPATH=src python -m powerwash_report.cli \
  --mode files --input-dir data/your_export --date 2026-09-13 \
  --output outputs/2026-09-13
```

## Run against live APIs

Copy `.env.example` values into your secret store. Do not commit credentials.
The program reads environment variables directly.

```bash
PYTHONPATH=src python -m powerwash_report.cli \
  --mode live --date 2026-09-13 --output outputs/2026-09-13
```

ServiceM8 uses `X-API-Key`. Deputy uses a bearer token and the account install
URL. Live normalization is deliberately tolerant of common field aliases, but
the first account run must be reconciled against the ServiceM8 and Deputy UI.

## Optional AI summary

Set `AI_API_KEY` and `AI_MODEL`. `AI_BASE_URL` defaults to the OpenAI Responses
API base URL. Only the exception register and aggregate counts are sent to the
model. Raw source payloads and API credentials are not sent.

The AI output is placed under **Suggested interpretation**. It cannot change
the exception code, severity, owner, evidence, or calculated variance.

## Configuration

- `config/rules.json` contains proposed thresholds. Management approval is
  required before the pilot.
- `config/staff_mapping.csv` maps ServiceM8 human staff UUIDs to Deputy employee
  IDs. Never add Truck 1–Truck 10 as employees.

## First live-run checklist

1. Add the ServiceM8 API key, Deputy install URL and Deputy token to secrets.
2. Replace the example staff mapping with verified IDs.
3. Run one historical day and compare every exception with the source systems.
4. Have the planner approve late-arrival, overtime and break thresholds.
5. Demonstrate read-only results to management before enabling alerts.

## Current limitations

- ServiceM8 customer names depend on the company record being available.
- Route travel and GPS-based deviations are not included in v0.1.
- Deputy OAuth refresh is outside this first version; use a securely managed
  access token for the controlled demonstration.
- The GitHub workflow uses UTC scheduling. Adjust the cron when New Zealand
  daylight-saving time changes, or use a timezone-aware scheduler later.
