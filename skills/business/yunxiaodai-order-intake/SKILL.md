---
name: yunxiaodai-order-intake
description: Complete Yunxiaodai order intake.
version: 0.1.0
author: Your Name, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [yunxiaodai, yxd, order, intake, loan]
    category: business
---

# Yunxiaodai Order Intake Skill

This skill completes the Yunxiaodai order intake workflow through amount
estimation, company submission, and final order application. It does not invent
customer identity, company, tax, address, manager, or authorization data.

## When to Use

Use this skill when the user asks to create, submit, continue, or troubleshoot a
Yunxiaodai order intake.

Use it for requests like:

- "帮我做一笔云小贷订单进件"
- "按云小贷流程提交这个订单"
- "先额度测算，再提交企业信息，最后订单申请"
- "继续这个 preApplyId 的进件"

## Prerequisites

The Yunxiaodai plugin tools should be available:

- `yunxiaodai_query_amount`
- `yunxiaodai_submit_company`
- `yunxiaodai_apply_info`

Configure the API host outside the skill:

```text
YUNXIAODAI_API_BASE_URL=http://158.4.90.21:8084
YUNXIAODAI_WEB_ORIGIN=http://158.4.90.21:8087
```

The user must provide a valid Yunxiaodai login token before any API operation.
The tools send this token in the `token` header and token cookie, matching the
web console request style. Do not run the workflow without a token.

If the internal environment requires extra request signing, gateway headers,
trace IDs, or TLS certificates, implement those details in the plugin tools
rather than in this skill.

## How to Run

Collect the required customer, company, and application fields before starting.
Ask for missing required fields instead of guessing them.

Authentication field:

| Field | Required | Meaning |
|---|---|---|
| `token` | Yes | Yunxiaodai login token provided by the user |

Customer fields for amount estimation:

| Field | Required | Meaning |
|---|---|---|
| `certNo` | Yes | Customer ID number |
| `preApplyId` | Yes | Pre-application id |
| `certName` | Yes | Customer name |
| `mobileNo` | Yes | Customer mobile number |
| `certValidEndDate` | Yes | ID card expiration date |
| `ocrAddress` | Yes | ID card address |
| `provCode` | Yes | Province area code |
| `cityCode` | Yes | City area code |
| `areaCode` | Yes | District area code |
| `customerNo` | No | Customer number |

Company fields:

| Field | Required | Meaning |
|---|---|---|
| `nsrsbh` | Yes | Taxpayer identification number |
| `companyAddress` | Yes | Company address, usually city-level |
| `companyCode` | Yes | Company address area code |
| `companyName` | Yes | Company name |
| `artificialName` | Yes | Legal representative name |
| `customerNo` | No | Enterprise customer number |
| `customerId` | No | Enterprise customer id |

Application fields:

| Field | Required | Meaning |
|---|---|---|
| `custManager` | Yes | Customer manager id |
| `isAuth` | Yes | Authorization flag; enterprise credit authorization uses `1` |
| `channelNo` | Yes | Channel number, usually `H5` |

## Quick Reference

| Step | Tool | API Path |
|---|---|---|
| 1 | `yunxiaodai_query_amount` | `/mloan/yxd-channel/apply/queryamount` |
| 2 | `yunxiaodai_submit_company` | `/mloan/yxd-channel/apply/submitcompany` |
| 3 | `yunxiaodai_apply_info` | `/mloan/yxd-channel/apply/applyinfo` |

## Procedure

1. Extract all available fields from the user request.
2. Confirm the user provided a valid Yunxiaodai token. If no token is present,
   ask the user to provide one and stop.
3. Validate `preApplyId`.
   - It should start with `Y`.
   - It should contain date text and the `YXD` marker.
   - Example: `Y20260512YXD000702`.
4. Derive `applyId` by removing the leading `Y` from `preApplyId`.
   - Example: `Y20260512YXD000702` becomes `20260512YXD000702`.
5. Call `yunxiaodai_query_amount`.
6. Stop if amount estimation fails or returns a blocking business error.
7. Call `yunxiaodai_submit_company` with the same `preApplyId`.
8. Stop if company submission fails or returns a blocking business error.
9. Call `yunxiaodai_apply_info` with the same `preApplyId`, derived `applyId`,
   `companyName`, and `nsrsbh`.
10. Return a concise final summary containing:
   - `preApplyId`
   - `applyId`
   - company name
   - taxpayer id
   - customer manager id
   - final result
   - failed step, if any
   - next action, if any

## Pitfalls

Do not call `yunxiaodai_submit_company` if `yunxiaodai_query_amount` fails.

Do not call `yunxiaodai_apply_info` if `yunxiaodai_submit_company` fails.

Do not use a different `preApplyId` between steps.

Do not call any Yunxiaodai tool without a user-provided token.

Do not store or repeat the token in the final response.

Do not guess ID numbers, phone numbers, tax IDs, legal names, manager IDs, or
authorization flags.

Only pass `isAuth` as `1` when the user or upstream system explicitly confirms
enterprise credit authorization.

If the API reports a duplicate, already-submitted, or already-existing order,
stop and report the existing order information instead of creating a new id.

## Verification

The workflow is complete only after `yunxiaodai_apply_info` returns success.

If any step fails, report:

- failed step
- API error code
- API error message
- whether the user should correct data or retry later

Avoid echoing full identity numbers or mobile numbers in the final response
unless the user explicitly asks for raw request details.
