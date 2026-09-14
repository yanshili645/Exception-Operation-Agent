# PowerWash Operations Exception Agent — boss demo

## One-minute explanation

The agent reviews ServiceM8 job execution and Deputy workforce records for the
previous operational day. Fixed business rules create the exception register.
AI then converts those verified exceptions into a short management summary and
recommended actions. Version 0.1 is read-only.

## Demonstration

Run:

```bash
PYTHONPATH=src python -m powerwash_report.cli \
  --mode demo --date 2026-09-13 --output outputs/agent_demo
```

Show these results:

- Overall status: Red
- Jobs: 7 scheduled, 6 completed
- Exceptions: 3 Critical, 9 High, 4 Medium
- Labour variance: -6.75 hours, affected by one missing timesheet
- Management attention: no-show, incomplete job, and missing allocation

Open `outputs/agent_demo/daily_exception_report.html`, then show
`outputs/agent_demo/exceptions.csv` to demonstrate that every headline links to
an exception code and evidence record.

## Management decision

Ask the boss to approve or amend the proposed lateness, overtime, duration and
meal-break thresholds on the `Rule Settings` sheet. These values become policy
only after approval.

## Next controlled step

Connect the existing ServiceM8 and Deputy credentials, verify the human staff
mapping, and run one historical live-account day in read-only mode. Compare the
output with the planner's manual assessment before enabling daily delivery.

