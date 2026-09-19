# PowerWash operating rules

These rules preserve the current PowerWash operating assumptions. Numerical
thresholds remain configurable in `config/rules.json` and require management
approval before a pilot.

## Daily operations

- Timezone: `Pacific/Auckland`.
- Auckland depot: 8 Norman Spencer Drive, Papatoetoe, Auckland 2104.
- Exclude depot-address records from customer-stop exceptions.
- Hamilton postcode 3200 is an operating exception and must be reported
  separately when depot or route comparisons are introduced.
- Paid day starts at 7:30 AM and includes a 30-minute prestart.
- First departure is 8:00 AM.
- A 30-minute lunch is required.
- Target paid run length is 9 hours. Maximum paid day is 12 hours.
- Overtime is not planned or permitted. Actual excess time remains an exception
  requiring manager review rather than an automatic payroll conclusion.

## Customer and allocation constraints

- Moana Fisheries, Cardinal Logistics, and FedEx Highbrook must be the first
  customer stop when scheduled.
- Kalista Drury and T&G Global Mt Wellington must start after 12:00 PM.
- Jobs at the same site/address remain on one truck.
- Tree King and Crown Worldwide remain on the same North Shore truck when both
  are scheduled.
- Same-postcode jobs remain together unless total service time exceeds 10 hours;
  use suburb only when postcode is missing.
- Distinct mandatory-first sites remain separate if grouping would conflict.
- Use ServiceM8 planned duration where available. Known planner durations are:
  Cardinal Logistics 6 hours, T&G Pukekohe 1 hour for two people, and Kalista
  Drury 2 hours.

## Time windows

- A customer with a real time restriction must be reached within its arrival
  window; work may finish after the window.
- Non-priority jobs may be 30–60 minutes late under the current routing
  assumption. Management must confirm the exact reporting threshold before the
  pilot.

## Proposed v0.1 thresholds

| Measure | Proposed value |
| --- | ---: |
| High job lateness | 31 minutes |
| Critical job lateness | 61 minutes |
| Late clock-on | 15 minutes |
| High late clock-on | 30 minutes |
| No-show/missing clock-on | 30 minutes after roster start |
| Material hours variance | More than 30 minutes |
| Duration overrun | More than 20% and at least 30 minutes |
| Minimum meal break | 30 minutes for shifts of 6+ hours |
