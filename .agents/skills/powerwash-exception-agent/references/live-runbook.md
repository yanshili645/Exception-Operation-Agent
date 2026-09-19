# Live runbook

Use this procedure for a live or scheduled report.

## Preconditions

Confirm the following environment variables exist without displaying their
values:

- `SERVICEM8_API_KEY`
- `DEPUTY_INSTALL_URL`
- `DEPUTY_ACCESS_TOKEN`
- `POWERWASH_TIMEZONE` set to `Pacific/Auckland`

`AI_API_KEY` and `AI_MODEL` are optional. If absent, the rule engine still
produces a deterministic management summary. State that AI interpretation was
not generated; do not treat this as a failed operational report.

Confirm `config/staff_mapping.csv` contains verified active human mappings. Do
not proceed silently when allocated staff are unmapped; preserve `DAT-02`.

## Execution

1. Resolve the operational date in Auckland time.
2. Run the CLI in `live` mode.
3. Confirm `source_snapshot.json` says `live` and `read_only: true`.
4. Confirm jobs, rosters, and timesheets were returned. A legitimate zero-job day
   is allowed only when the user or manager confirms no work was scheduled.
5. Reconcile total exception count to Critical + High + Medium + Low.
6. Deliver the management summary and detailed evidence file.

## Stop conditions

Stop and report a blocker when:

- authentication fails;
- source data cannot be retrieved;
- the report date is ambiguous;
- the source snapshot is demo or files during a requested live run;
- identity mappings are broadly missing;
- output reconciliation fails.

Do not retry authentication repeatedly, seek credentials outside the configured
secret store, downgrade to demo mode, or claim that a partial report is complete.

## Escalation wording

State the blocked component, the missing or failed prerequisite, the affected
report date, and the exact human action required. Never include a secret value.
