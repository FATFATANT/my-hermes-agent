"""Durable JSON-backed MVP workflow for bank credit cases."""

from __future__ import annotations

import copy
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_hermes_home


STORE_DIR = get_hermes_home() / "plugins" / "bank-credit-mvp"
STORE_PATH = STORE_DIR / "state.json"


STEP_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "open_customer_no",
        "title": "开立客户号",
        "kind": "external_blocking",
        "status": "pending",
        "blocking": True,
        "external_url": "https://credit-demo.bank.local/customer/open",
        "check": "query_customer_no_exists",
        "summary": "需要客户经理到客户信息系统开立客户号，完成后系统会自动检查。",
    },
    {
        "id": "fill_investigation_report",
        "title": "填写调查报告基础要素",
        "kind": "internal_api",
        "status": "pending",
        "blocking": True,
        "tool": "save_investigation_report_fields",
        "summary": "由 Hermes 收集业务数据，并通过本系统接口保存调查报告字段。",
    },
    {
        "id": "sync_financial_data",
        "title": "同步财报数据",
        "kind": "external_optional",
        "status": "pending",
        "blocking": False,
        "external_url": "https://credit-demo.bank.local/financials",
        "check": "query_financial_data_ready",
        "summary": "客户经理可到财报系统维护数据；未完成也不阻塞主流程。",
    },
    {
        "id": "save_report",
        "title": "保存调查报告草稿",
        "kind": "internal_api",
        "status": "pending",
        "blocking": True,
        "tool": "save_report_draft",
        "summary": "基础要素齐备后自动保存调查报告草稿。",
    },
]


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _default_state() -> Dict[str, Any]:
    case = _new_case(
        applicant_name="上海青禾贸易有限公司",
        amount=500000,
        purpose="流动资金周转",
        seed=True,
    )
    return {
        "cases": [case],
        "mock_external": {
            case["id"]: {
                "customer_no_exists": False,
                "customer_no": None,
                "financial_data_ready": False,
            }
        },
    }


def _read_state() -> Dict[str, Any]:
    if not STORE_PATH.exists():
        state = _default_state()
        _write_state(state)
        return state
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        state = _default_state()
        _write_state(state)
        return state


def _write_state(state: Dict[str, Any]) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STORE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STORE_PATH)


def _new_case(
    applicant_name: str,
    amount: int,
    purpose: str,
    seed: bool = False,
) -> Dict[str, Any]:
    case_id = "loan-demo-001" if seed else f"loan-{uuid.uuid4().hex[:8]}"
    ts = _now()
    return {
        "id": case_id,
        "applicant_name": applicant_name,
        "amount": amount,
        "purpose": purpose,
        "status": "pending",
        "current_step": "open_customer_no",
        "steps": copy.deepcopy(STEP_TEMPLATES),
        "report_fields": {
            "applicant_name": applicant_name,
            "amount": amount,
            "purpose": purpose,
            "customer_no": None,
            "financial_snapshot": None,
        },
        "events": [
            {
                "at": ts,
                "kind": "case_created",
                "message": "信贷业务流程已创建。",
            }
        ],
        "created_at": ts,
        "updated_at": ts,
    }


def _find_case(state: Dict[str, Any], case_id: str) -> Dict[str, Any]:
    for case in state.get("cases", []):
        if case.get("id") == case_id:
            return case
    raise KeyError(case_id)


def _step(case: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    for step in case.get("steps", []):
        if step.get("id") == step_id:
            return step
    raise KeyError(step_id)


def _event(case: Dict[str, Any], kind: str, message: str) -> None:
    case.setdefault("events", []).append({"at": _now(), "kind": kind, "message": message})
    case["updated_at"] = _now()


def _set_current_step(case: Dict[str, Any]) -> None:
    for step in case.get("steps", []):
        if step.get("status") in {"pending", "action_required", "in_progress"} and step.get("blocking", True):
            case["current_step"] = step["id"]
            case["status"] = "blocked" if step.get("status") == "action_required" else "pending"
            return
    case["current_step"] = None
    case["status"] = "completed"


def _normalize_case(case: Dict[str, Any]) -> Dict[str, Any]:
    done = sum(1 for s in case.get("steps", []) if s.get("status") in {"completed", "skipped"})
    total = len(case.get("steps", [])) or 1
    case["progress"] = round(done / total, 2)
    return case


def list_cases() -> List[Dict[str, Any]]:
    state = _read_state()
    return [_normalize_case(copy.deepcopy(c)) for c in state.get("cases", [])]


def get_case(case_id: str) -> Dict[str, Any]:
    state = _read_state()
    return _normalize_case(copy.deepcopy(_find_case(state, case_id)))


def create_case(applicant_name: str, amount: int, purpose: str) -> Dict[str, Any]:
    state = _read_state()
    case = _new_case(applicant_name=applicant_name, amount=amount, purpose=purpose)
    state.setdefault("cases", []).insert(0, case)
    state.setdefault("mock_external", {})[case["id"]] = {
        "customer_no_exists": False,
        "customer_no": None,
        "financial_data_ready": False,
    }
    _write_state(state)
    return _normalize_case(case)


def advance_case(case_id: str, report_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    state = _read_state()
    case = _find_case(state, case_id)
    ext = state.setdefault("mock_external", {}).setdefault(case_id, {})

    if report_fields:
        for key in ("applicant_name", "amount", "purpose"):
            value = report_fields.get(key)
            if value not in (None, ""):
                case["report_fields"][key] = value
                if key in case:
                    case[key] = value

    customer_step = _step(case, "open_customer_no")
    if customer_step["status"] != "completed":
        if ext.get("customer_no_exists"):
            customer_step["status"] = "completed"
            case["report_fields"]["customer_no"] = ext.get("customer_no") or f"CUST-{case_id[-6:].upper()}"
            _event(case, "external_check_passed", "已查询到客户号，流程继续。")
        else:
            was_waiting = customer_step.get("status") == "action_required"
            customer_step["status"] = "action_required"
            customer_step["last_checked_at"] = _now()
            if not was_waiting:
                _event(case, "external_blocked", "等待客户经理在外部系统开立客户号。")
            _set_current_step(case)
            _write_state(state)
            return _normalize_case(copy.deepcopy(case))

    report_step = _step(case, "fill_investigation_report")
    required = ["applicant_name", "amount", "purpose", "customer_no"]
    missing = [k for k in required if not case.get("report_fields", {}).get(k)]
    if missing:
        report_step["status"] = "action_required"
        report_step["missing_fields"] = missing
        _event(case, "input_required", "调查报告基础字段未齐备。")
        _set_current_step(case)
        _write_state(state)
        return _normalize_case(copy.deepcopy(case))
    if report_step["status"] != "completed":
        report_step["status"] = "completed"
        report_step.pop("missing_fields", None)
        _event(case, "internal_api_completed", "调查报告基础要素已保存。")

    finance_step = _step(case, "sync_financial_data")
    if finance_step["status"] not in {"completed", "skipped"}:
        if ext.get("financial_data_ready"):
            finance_step["status"] = "completed"
            case["report_fields"]["financial_snapshot"] = {
                "revenue": 1280000,
                "net_profit": 96000,
                "debt_ratio": 0.42,
            }
            _event(case, "optional_external_completed", "财报数据已同步。")
        else:
            finance_step["status"] = "skipped"
            finance_step["last_checked_at"] = _now()
            _event(case, "optional_external_skipped", "财报数据未就绪，按非阻塞步骤跳过。")

    save_step = _step(case, "save_report")
    if save_step["status"] != "completed":
        save_step["status"] = "completed"
        _event(case, "internal_api_completed", "调查报告草稿已保存。")

    _set_current_step(case)
    _write_state(state)
    return _normalize_case(copy.deepcopy(case))


def mark_customer_created(case_id: str, customer_no: Optional[str] = None) -> Dict[str, Any]:
    state = _read_state()
    _find_case(state, case_id)
    ext = state.setdefault("mock_external", {}).setdefault(case_id, {})
    ext["customer_no_exists"] = True
    ext["customer_no"] = customer_no or f"CUST-{case_id[-6:].upper()}"
    _write_state(state)
    return advance_case(case_id)


def mark_financial_ready(case_id: str) -> Dict[str, Any]:
    state = _read_state()
    _find_case(state, case_id)
    ext = state.setdefault("mock_external", {}).setdefault(case_id, {})
    ext["financial_data_ready"] = True
    _write_state(state)
    return advance_case(case_id)


def poll_cases() -> Dict[str, Any]:
    """Advance all non-completed cases until blocked or complete.

    This is the operation a Hermes cron job should call. In the MVP the
    external system flags are mock state; in production this function should
    query real bank systems before calling ``advance_case``.
    """
    state = _read_state()
    case_ids = [
        str(case.get("id"))
        for case in state.get("cases", [])
        if case.get("id") and case.get("status") != "completed"
    ]
    results: List[Dict[str, Any]] = []
    for case_id in case_ids:
        before = get_case(case_id)
        after = advance_case(case_id)
        results.append({
            "case_id": case_id,
            "before_status": before.get("status"),
            "after_status": after.get("status"),
            "before_step": before.get("current_step"),
            "after_step": after.get("current_step"),
            "changed": before.get("status") != after.get("status")
            or before.get("current_step") != after.get("current_step")
            or before.get("progress") != after.get("progress"),
        })
    return {
        "checked": len(case_ids),
        "changed": sum(1 for item in results if item["changed"]),
        "results": results,
    }


def reset_demo() -> Dict[str, Any]:
    state = _default_state()
    _write_state(state)
    return _normalize_case(copy.deepcopy(state["cases"][0]))
