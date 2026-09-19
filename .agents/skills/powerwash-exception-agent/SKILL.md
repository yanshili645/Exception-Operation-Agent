---
name: powerwash-exception-agent
description: Generate, review, and explain PowerWash daily operations exception reports from ServiceM8 jobs and Deputy rosters/timesheets. Use for scheduled or on-demand exception runs, report-status checks, exception investigation, staff-mapping checks, and proposed threshold changes. Do not use to optimize weekend routes or write operational changes back to either source system.
---

# PowerWash Operations Exception Agent

Produce an auditable daily exception report for PowerWash. Treat the Python rule
engine as the authority for exception existence, code, severity, owner, variance,
and evidence. Use AI only to summarize those fixed results, identify patterns,
and suggest actions.

## Choose the run mode

- Use `live` for scheduled and operational runs. If any required connection or
  credential is unavailable, stop and report the missing prerequisite. Never
  substitute demo data.
- Use `demo` only when the user explicitly asks for a demonstration, sample, or
  boss preview.
- Use `files` when the user supplies four source exports or asks to rerun a
  historical snapshot.

Read [references/operating-rules.md](references/operating-rules.md) before
interpreting exceptions or changing rules. Read
[references/live-runbook.md](references/live-runbook.md) for a live or scheduled
run. Read [references/report-contract.md](references/report-contract.md) when
creating, reviewing, or explaining the management output.

## Run the deterministic workflow

From the repository root:

```bash
PYTHONPATH=src python -m powerwash_report.cli \
  --mode <live|files|demo> --date <YYYY-MM-DD> --output <output-directory>
```

Omit `--date` only when the requested period is yesterday in
`Pacific/Auckland`. After code or rule changes, run:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Inspect `management_summary.json` and `exceptions.csv` after every run. Confirm
that total exceptions equal the four severity counts. Do not claim success if
the source mode, date, or reconciliation is wrong.

## Present the result

Lead with overall status, completed jobs, critical/high counts, labour variance,
and the top three actions. Separate these sections explicitly:

1. **Rule-detected exceptions** — fixed facts from the engine.
2. **Suggested interpretation** — AI analysis grounded only in those facts.
3. **Manager decisions required** — unresolved thresholds, causes, or approvals.

Always preserve job numbers, source record IDs, employee identity, calculated
variance, and owner where present. Label low-confidence causal inferences. Do not
infer misconduct, payroll liability, customer fault, or a disciplinary outcome.

## Safety and authority

- Version 0.1 is read-only. Do not update ServiceM8, Deputy, Google Sheets,
  payroll, schedules, jobs, employees, notes, badges, or timesheets.
- Do not reveal credentials, tokens, raw authorization headers, or unnecessary
  employee comments.
- Threshold edits require an explicit user request. Report the old and new value
  and rerun tests afterward.
- Staff names are validation aids, not join keys. Match ServiceM8 staff UUID to
  Deputy employee ID through `config/staff_mapping.csv`. Never map Truck 1–Truck
  10 as employees.
- If the source records conflict, emit or preserve a data-quality exception and
  request human review rather than choosing a convenient value.
