---
name: bank-credit-workflow
description: Run bank credit workflow cases.
version: 0.1.0
author: Local demo
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [banking, credit, workflow, human-in-the-loop]
    category: banking
    related_skills: []
---

# Bank Credit Workflow Skill

Use this skill to help a relationship manager advance a bank credit workflow
case through Hermes. It covers the MVP plugin workflow and does not authorize
Hermes to operate unrelated bank systems directly.

## When to Use

Use this skill when the user asks to create, inspect, advance, unblock, or
monitor a bank loan or credit workflow case.

Use the dashboard for visual inspection when the user wants to see the task
list, but use the tools below when the user asks to work conversationally.

## Prerequisites

The `bank-credit-mvp` plugin must be enabled before its tools are available in
chat or cron jobs:

```bash
hermes plugins enable bank-credit-mvp
```

If the toolset is not visible after enabling, start a new Hermes session. The
plugin toolset is named `bank_credit`.

## How to Run

Start by listing or selecting a case:

```text
bank_credit_list_cases
bank_credit_get_case
```

Then advance the selected case:

```text
bank_credit_advance_case
```

For scheduled polling, use:

```text
bank_credit_poll_cases
```

## Quick Reference

Tools:

- `bank_credit_list_cases`: list workflow cases and current status.
- `bank_credit_get_case`: inspect one case, its steps, fields, and events.
- `bank_credit_advance_case`: advance one case until complete or blocked.
- `bank_credit_poll_cases`: scan non-completed cases and advance those whose
  external blocking condition is now satisfied.
- `bank_credit_mock_customer_created`: demo-only helper for simulating the
  external customer-number system.

Step types:

- `internal_api`: Hermes may complete this through the bank system API.
- `external_blocking`: Hermes must stop and ask the relationship manager to
  operate the external system.
- `external_optional`: Hermes may mention it, but it must not block the main
  workflow if the data is not ready.

## Procedure

1. Identify the case.
   If the user names a customer, call `bank_credit_list_cases` and match the
   customer name. If ambiguous, ask which case to use.

2. Inspect the case.
   Call `bank_credit_get_case` before changing state. Summarize the current
   step and whether the case is blocked, pending, or completed.

3. Advance carefully.
   Call `bank_credit_advance_case` only when the user asks to proceed or when a
   scheduled polling task is checking existing cases.

4. Handle blocking external steps.
   If a step is `external_blocking` and `action_required`, tell the user:
   the step title, why it blocks, the external link if present, and that Hermes
   can continue after the external condition is detected.

5. Handle optional external steps.
   If a step is `external_optional`, do not block the workflow. Say that it can
   be completed for better data quality, but the core process can continue.

6. For cron polling.
   In a cron job, call `bank_credit_poll_cases`, report how many cases were
   checked, and mention only cases whose status changed or remain blocked.

## Pitfalls

Do not pretend an external bank system action has been completed unless a tool
result says so.

Do not use the demo helper `bank_credit_mock_customer_created` in a real bank
workflow. It exists only for local MVP verification.

Do not mark optional financial data as required unless the case definition says
the step is blocking.

Do not expose customer-sensitive fields beyond what the user requested.

## Verification

For local MVP verification:

1. Call `bank_credit_list_cases`.
2. Pick the demo case.
3. Call `bank_credit_advance_case`.
4. Confirm it stops at `open_customer_no` with `action_required`.
5. In the dashboard or demo flow, simulate customer number creation.
6. Call `bank_credit_poll_cases` or `bank_credit_advance_case`.
7. Confirm the case reaches `completed`.
