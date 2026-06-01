"""HTTP client for bank credit workflow cases owned by the mock bank system."""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

from hermes_constants import get_hermes_home


NO_PROXY_OPENER = build_opener(ProxyHandler({}))
LINKS_DIR = get_hermes_home() / "plugins" / "bank-credit-mvp"
SESSION_LINKS_PATH = LINKS_DIR / "session_links.json"
SESSION_LINKS_LOCK = threading.Lock()


def _external_frontend_base() -> str:
    return os.getenv("BANK_CREDIT_EXTERNAL_FRONTEND", "http://127.0.0.1:5174").rstrip("/")


def _external_api_base() -> str:
    return os.getenv("BANK_CREDIT_EXTERNAL_API", "http://127.0.0.1:8080").rstrip("/")


def _url(path: str) -> str:
    return f"{_external_api_base()}{path}"


def _frontend_url(path: str, params: Dict[str, Any]) -> str:
    return f"{_external_frontend_base()}{path}?{urlencode(params)}"


def _request(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body = None
    headers = {"accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["content-type"] = "application/json; charset=utf-8"
    req = Request(_url(path), data=body, headers=headers, method=method)
    try:
        with NO_PROXY_OPENER.open(req, timeout=4) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code} {detail}") from exc


def _read_session_links() -> Dict[str, Any]:
    if not SESSION_LINKS_PATH.exists():
        return {"sessions": {}, "cases": {}, "hidden": {}}
    try:
        data = json.loads(SESSION_LINKS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("sessions", {})
            data.setdefault("cases", {})
            data.setdefault("hidden", {})
            return data
    except Exception:
        pass
    return {"sessions": {}, "cases": {}, "hidden": {}}


def _write_session_links(data: Dict[str, Any]) -> None:
    LINKS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SESSION_LINKS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SESSION_LINKS_PATH)


def associate_session_case(session_id: Optional[str], case_id: Optional[str]) -> None:
    if not session_id or not case_id:
        return
    with SESSION_LINKS_LOCK:
        data = _read_session_links()
        sessions = data.setdefault("sessions", {})
        cases = data.setdefault("cases", {})
        session_cases = sessions.setdefault(str(session_id), [])
        if case_id not in session_cases:
            session_cases.append(case_id)
        hidden_cases = data.setdefault("hidden", {}).setdefault(str(session_id), [])
        data["hidden"][str(session_id)] = [item for item in hidden_cases if item != case_id]
        case_sessions = cases.setdefault(str(case_id), [])
        if session_id not in case_sessions:
            case_sessions.append(session_id)
        _write_session_links(data)


def dissociate_session_case(session_id: Optional[str], case_id: Optional[str]) -> None:
    if not session_id or not case_id:
        return
    with SESSION_LINKS_LOCK:
        data = _read_session_links()
        session_cases = data.setdefault("sessions", {}).get(str(session_id), [])
        data["sessions"][str(session_id)] = [item for item in session_cases if item != case_id]
        hidden_cases = data.setdefault("hidden", {}).setdefault(str(session_id), [])
        if case_id not in hidden_cases:
            hidden_cases.append(case_id)
        case_sessions = data.setdefault("cases", {}).get(str(case_id), [])
        data["cases"][str(case_id)] = [item for item in case_sessions if item != session_id]
        _write_session_links(data)


def session_case_ids(session_id: Optional[str]) -> List[str]:
    if not session_id:
        return []
    with SESSION_LINKS_LOCK:
        data = _read_session_links()
        return list(data.get("sessions", {}).get(str(session_id), []))


def hidden_session_case_ids(session_id: Optional[str]) -> List[str]:
    if not session_id:
        return []
    with SESSION_LINKS_LOCK:
        data = _read_session_links()
        return list(data.get("hidden", {}).get(str(session_id), []))


def list_session_cases(session_id: Optional[str]) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    kept_ids: List[str] = []
    for case_id in session_case_ids(session_id):
        try:
            case = get_case(case_id)
        except KeyError:
            continue
        cases.append(case)
        kept_ids.append(case_id)
    if session_id and len(kept_ids) != len(session_case_ids(session_id)):
        with SESSION_LINKS_LOCK:
            data = _read_session_links()
            data.setdefault("sessions", {})[str(session_id)] = kept_ids
            _write_session_links(data)
    return cases


def list_hidden_session_cases(session_id: Optional[str]) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    kept_ids: List[str] = []
    for case_id in hidden_session_case_ids(session_id):
        try:
            case = get_case(case_id)
        except KeyError:
            continue
        cases.append(case)
        kept_ids.append(case_id)
    if session_id and len(kept_ids) != len(hidden_session_case_ids(session_id)):
        with SESSION_LINKS_LOCK:
            data = _read_session_links()
            data.setdefault("hidden", {})[str(session_id)] = kept_ids
            _write_session_links(data)
    return cases


def _case_from_response(payload: Dict[str, Any], case_id: Optional[str] = None) -> Dict[str, Any]:
    case = payload.get("case")
    if not case:
        raise KeyError(case_id or "")
    return _normalize_case(case)


def _normalize_case(case: Dict[str, Any]) -> Dict[str, Any]:
    for step in case.get("steps", []):
        if str(step.get("external_url") or "").startswith("http"):
            continue
        step["external_url"] = _frontend_url_for_step(case, step)
    return case


def _frontend_url_for_step(case: Dict[str, Any], step: Dict[str, Any]) -> str:
    params = {
        "caseId": case.get("id") or "",
        "customerName": case.get("applicant_name") or "",
    }
    step_id = step.get("id")
    if step_id == "open_customer_no":
        return _frontend_url("/customer/open", params)
    if step_id == "fill_investigation_report":
        return _frontend_url("/credit/report", params)
    if step_id == "risk_admission_review":
        params["task"] = "risk_admission"
        return _frontend_url("/risk/admission", params)
    if step_id == "sync_financial_data":
        params["task"] = "financial_data"
        return _frontend_url("/financials", params)
    if step_id == "collateral_confirmation":
        params["task"] = "collateral_confirmation"
        return _frontend_url("/collateral/confirm", params)
    if step_id == "save_report":
        return _frontend_url("/credit/save", params)
    return _frontend_url("/", params)


def list_cases() -> List[Dict[str, Any]]:
    payload = _request("GET", "/api/bank/credit-cases")
    return [_normalize_case(item) for item in payload.get("cases", [])]


def get_case(case_id: str) -> Dict[str, Any]:
    payload = _request("GET", f"/api/bank/credit-cases/{case_id}")
    return _case_from_response(payload, case_id)


def create_case(applicant_name: str, amount: int, purpose: str) -> Dict[str, Any]:
    payload = _request("POST", "/api/bank/credit-cases", {
        "applicant_name": applicant_name,
        "amount": amount,
        "purpose": purpose,
    })
    return _case_from_response(payload)


def delete_case(case_id: str) -> Dict[str, Any]:
    payload = _request("DELETE", f"/api/bank/credit-cases/{case_id}")
    if not payload.get("deleted"):
        raise KeyError(case_id)
    return {"deleted": True, "case_id": payload.get("case_id") or case_id}


def advance_case(case_id: str, report_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = _request("POST", f"/api/bank/credit-cases/{case_id}/advance", {
        "report_fields": report_fields or {},
    })
    return _case_from_response(payload, case_id)


def mark_customer_created(case_id: str, customer_no: Optional[str] = None) -> Dict[str, Any]:
    params = urlencode({"caseId": case_id, "customerName": "", "customerNo": customer_no or ""})
    _request("POST", f"/api/bank/customer-number/open?{params}")
    return advance_case(case_id)


def mark_financial_ready(case_id: str) -> Dict[str, Any]:
    params = urlencode({"caseId": case_id, "customerName": "", "task": "financial_data"})
    _request("POST", f"/api/bank/external-task/complete?{params}")
    return advance_case(case_id)


def mark_external_task_done(case_id: str, task: str) -> Dict[str, Any]:
    params = urlencode({"caseId": case_id, "customerName": "", "task": task})
    _request("POST", f"/api/bank/external-task/complete?{params}")
    return advance_case(case_id)


def poll_cases() -> Dict[str, Any]:
    payload = _request("POST", "/api/bank/credit-cases/poll")
    return payload.get("poll", payload)


def reset_demo() -> Dict[str, Any]:
    payload = _request("POST", "/api/bank/credit-cases/reset-demo")
    return _case_from_response(payload, "loan-demo-001")
