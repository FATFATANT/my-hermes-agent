"""Agent tool wrappers for the bank credit MVP workflow."""

from __future__ import annotations

import json
from typing import Any, Dict

from plugins.bank_credit_mvp import workflow

_PENDING_CREATES: Dict[str, Dict[str, Any]] = {}


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _pending_key(task_id: Any) -> str:
    return str(task_id or "__default__")


def _list_cases(args: Dict[str, Any], **_kw: Any) -> str:
    return _json({"success": True, "cases": workflow.list_cases()})


def _create_case(args: Dict[str, Any], **kw: Any) -> str:
    key = _pending_key(kw.get("task_id"))
    pending = _PENDING_CREATES.get(key)
    draft = {
        "applicant_name": str(args.get("applicant_name") or "").strip(),
        "amount": args.get("amount"),
        "purpose": str(args.get("purpose") or "").strip(),
    }
    if pending != draft:
        _PENDING_CREATES[key] = draft
        return _json({
            "success": False,
            "needs_confirmation": True,
            "error": "Creating a bank credit workflow case requires explicit user confirmation first.",
            "prompt": "请先向用户确认是否现在创建一笔信贷业务订单；用户确认后再调用本工具，并传入 confirmed=true。",
            "draft": draft,
        })
    if args.get("confirmed") is not True:
        return _json({
            "success": False,
            "needs_confirmation": True,
            "error": "User confirmation is still required before creating this bank credit workflow case.",
            "prompt": "请等待用户明确确认后，再调用本工具并传入 confirmed=true。",
            "draft": draft,
        })
    applicant_name = draft["applicant_name"]
    amount = draft["amount"]
    purpose = draft["purpose"]
    if not applicant_name:
        return _json({"success": False, "error": "applicant_name is required"})
    if not purpose:
        return _json({"success": False, "error": "purpose is required"})
    try:
        normalized_amount = int(amount)
    except (TypeError, ValueError):
        return _json({"success": False, "error": "amount must be an integer"})
    case = workflow.create_case(applicant_name, normalized_amount, purpose)
    workflow.associate_session_case(kw.get("task_id"), case.get("id"))
    _PENDING_CREATES.pop(key, None)
    return _json({"success": True, "case": case})


def _get_case(args: Dict[str, Any], **_kw: Any) -> str:
    case_id = str(args.get("case_id") or "").strip()
    if not case_id:
        return _json({"success": False, "error": "case_id is required"})
    try:
        case = workflow.get_case(case_id)
        workflow.associate_session_case(_kw.get("task_id"), case_id)
        return _json({"success": True, "case": case})
    except KeyError:
        return _json({"success": False, "error": f"case not found: {case_id}"})


def _advance_case(args: Dict[str, Any], **_kw: Any) -> str:
    case_id = str(args.get("case_id") or "").strip()
    if not case_id:
        return _json({"success": False, "error": "case_id is required"})
    try:
        case = workflow.advance_case(case_id, args.get("report_fields") or {})
        workflow.associate_session_case(_kw.get("task_id"), case_id)
        return _json({
            "success": True,
            "case": case,
        })
    except KeyError:
        return _json({"success": False, "error": f"case not found: {case_id}"})


def _delete_case(args: Dict[str, Any], **_kw: Any) -> str:
    case_id = str(args.get("case_id") or "").strip()
    if not case_id:
        return _json({"success": False, "error": "case_id is required"})
    try:
        result = workflow.delete_case(case_id)
        workflow.dissociate_session_case(_kw.get("task_id"), case_id)
        return _json({"success": True, **result})
    except KeyError:
        return _json({"success": False, "error": f"case not found: {case_id}"})


def _poll_cases(args: Dict[str, Any], **_kw: Any) -> str:
    return _json({"success": True, "poll": workflow.poll_cases()})


TOOLS = (
    (
        "bank_credit_list_cases",
        {
            "name": "bank_credit_list_cases",
            "description": "List bank credit workflow cases from the mock bank internal system.",
            "parameters": {"type": "object", "properties": {}},
        },
        _list_cases,
    ),
    (
        "bank_credit_create_case",
        {
            "name": "bank_credit_create_case",
            "description": "Create a new bank credit workflow case in the mock bank internal system and bind it to the current Hermes session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "applicant_name": {"type": "string", "description": "Customer/applicant name."},
                    "amount": {"type": "integer", "description": "Credit amount in yuan."},
                    "purpose": {"type": "string", "description": "Loan or credit purpose."},
                    "confirmed": {
                        "type": "boolean",
                        "description": "Must be true only after the user explicitly confirms that Hermes should create the credit workflow order now.",
                    },
                },
                "required": ["applicant_name", "amount", "purpose", "confirmed"],
            },
        },
        _create_case,
    ),
    (
        "bank_credit_get_case",
        {
            "name": "bank_credit_get_case",
            "description": "Get one bank credit workflow case from the mock bank internal system.",
            "parameters": {
                "type": "object",
                "properties": {"case_id": {"type": "string"}},
                "required": ["case_id"],
            },
        },
        _get_case,
    ),
    (
        "bank_credit_advance_case",
        {
            "name": "bank_credit_advance_case",
            "description": "Advance a bank credit workflow until it completes or reaches a blocking human step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "report_fields": {
                        "type": "object",
                        "description": "Optional report fields collected from the relationship manager.",
                    },
                },
                "required": ["case_id"],
            },
        },
        _advance_case,
    ),
    (
        "bank_credit_delete_case",
        {
            "name": "bank_credit_delete_case",
            "description": "Delete one bank credit workflow case from the mock bank internal system.",
            "parameters": {
                "type": "object",
                "properties": {"case_id": {"type": "string"}},
                "required": ["case_id"],
            },
        },
        _delete_case,
    ),
    (
        "bank_credit_poll_cases",
        {
            "name": "bank_credit_poll_cases",
            "description": "Poll bank credit cases and advance any case whose external blocking condition is now satisfied.",
            "parameters": {"type": "object", "properties": {}},
        },
        _poll_cases,
    ),
)
