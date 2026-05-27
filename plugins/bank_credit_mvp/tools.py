"""Agent tool wrappers for the bank credit MVP workflow."""

from __future__ import annotations

import json
from typing import Any, Dict

from plugins.bank_credit_mvp import workflow


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _list_cases(args: Dict[str, Any], **_kw: Any) -> str:
    return _json({"success": True, "cases": workflow.list_cases()})


def _get_case(args: Dict[str, Any], **_kw: Any) -> str:
    case_id = str(args.get("case_id") or "").strip()
    if not case_id:
        return _json({"success": False, "error": "case_id is required"})
    try:
        return _json({"success": True, "case": workflow.get_case(case_id)})
    except KeyError:
        return _json({"success": False, "error": f"case not found: {case_id}"})


def _advance_case(args: Dict[str, Any], **_kw: Any) -> str:
    case_id = str(args.get("case_id") or "").strip()
    if not case_id:
        return _json({"success": False, "error": "case_id is required"})
    try:
        return _json({
            "success": True,
            "case": workflow.advance_case(case_id, args.get("report_fields") or {}),
        })
    except KeyError:
        return _json({"success": False, "error": f"case not found: {case_id}"})


def _mock_customer_created(args: Dict[str, Any], **_kw: Any) -> str:
    case_id = str(args.get("case_id") or "").strip()
    customer_no = str(args.get("customer_no") or "").strip() or None
    if not case_id:
        return _json({"success": False, "error": "case_id is required"})
    try:
        return _json({"success": True, "case": workflow.mark_customer_created(case_id, customer_no)})
    except KeyError:
        return _json({"success": False, "error": f"case not found: {case_id}"})


TOOLS = (
    (
        "bank_credit_list_cases",
        {
            "name": "bank_credit_list_cases",
            "description": "List MVP bank credit workflow cases and their current status.",
            "parameters": {"type": "object", "properties": {}},
        },
        _list_cases,
    ),
    (
        "bank_credit_get_case",
        {
            "name": "bank_credit_get_case",
            "description": "Get one MVP bank credit workflow case with steps and events.",
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
        "bank_credit_mock_customer_created",
        {
            "name": "bank_credit_mock_customer_created",
            "description": "Demo helper that marks the external customer-number system as completed for a case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "customer_no": {"type": "string"},
                },
                "required": ["case_id"],
            },
        },
        _mock_customer_created,
    ),
)
