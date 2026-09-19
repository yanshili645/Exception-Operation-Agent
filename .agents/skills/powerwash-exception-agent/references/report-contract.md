# Management report contract

## Required headline fields

- Operational date and source mode
- Overall Red/Amber/Green status
- Jobs scheduled, completed, and incomplete
- Staff rostered and timesheets received
- Scheduled hours, actual hours, and variance
- Critical, High, Medium, Low, and total exception counts

Status is deterministic: Red when any Critical exception exists, Amber when no
Critical but at least one High exists, otherwise Green.

## Exception evidence

Every row must retain:

- exception code and severity;
- category;
- job number/customer/truck or employee as applicable;
- planned value, actual value, and variance;
- source evidence identifier;
- responsible owner and recommended action;
- workflow status and resolution field.

The management summary must reconcile to the register. Never suppress a valid
exception merely to shorten the narrative.

## AI boundary

AI may summarize, group related exceptions, describe repeated patterns, and
propose up to three actions. It may not change codes, severities, evidence,
owners, calculated values, payroll outcomes, or job status.

Label AI output `Suggested interpretation`. A possible cause must be written as
an inference and linked to the underlying exception records. When evidence is
insufficient, say that human investigation is required.

## Recommended daily response

Keep the opening concise:

1. One-line operational status.
2. Counts and labour variance.
3. Up to three management-attention items.
4. Up to three recommended actions.
5. Link or attach the full exception register.
