"""Tools for the Yunxiaodai order intake API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "http://158.4.90.21:8084"
DEFAULT_WEB_ORIGIN = "http://158.4.90.21:8087"
BASE_URL_ENV = "YUNXIAODAI_API_BASE_URL"
WEB_ORIGIN_ENV = "YUNXIAODAI_WEB_ORIGIN"

QUERY_AMOUNT_PATH = "/mloan/yxd-channel/apply/queryamount"
SUBMIT_COMPANY_PATH = "/mloan/yxd-channel/apply/submitcompany"
APPLY_INFO_PATH = "/mloan/yxd-channel/apply/applyinfo"


def check_yunxiaodai_available() -> bool:
    """The tools are available when the stdlib HTTP client can be used."""
    return True


def _base_url() -> str:
    return os.getenv(BASE_URL_ENV, DEFAULT_BASE_URL).rstrip("/")


def _web_origin() -> str:
    return os.getenv(WEB_ORIGIN_ENV, DEFAULT_WEB_ORIGIN).rstrip("/")


def _compact(value: dict[str, Any]) -> dict[str, Any]:
    """Drop empty optional values so callers can omit customer ids."""
    return {key: item for key, item in value.items() if item not in (None, "")}


def _require_token(args: dict[str, Any]) -> str | None:
    token = str(args.get("token") or "").strip()
    return token or None


def _headers(token: str) -> dict[str, str]:
    origin = _web_origin()
    return {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux aarch64; rv:75.0) "
            "Gecko/20100101 Firefox/75.0"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json;charset=utf-8",
        "token": token,
        "Origin": origin,
        "Referer": f"{origin}/mloanstatic/",
        "Cookie": f"token={token}",
    }


def _missing_token_result(path: str) -> str:
    return json.dumps(
        {
            "success": False,
            "path": path,
            "error": "Missing token. Ask the user to provide a valid Yunxiaodai token before calling this tool.",
        },
        ensure_ascii=False,
    )


def _post(path: str, payload: dict[str, Any], token: str) -> str:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{_base_url()}{path}",
        data=body,
        headers=_headers(token),
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw_body = response.read().decode("utf-8")
            try:
                data: Any = json.loads(raw_body) if raw_body else None
            except json.JSONDecodeError:
                data = raw_body
            return json.dumps(
                {
                    "success": True,
                    "status": response.status,
                    "path": path,
                    "data": data,
                },
                ensure_ascii=False,
            )
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return json.dumps(
            {
                "success": False,
                "status": exc.code,
                "path": path,
                "error": error_body,
            },
            ensure_ascii=False,
        )
    except urllib.error.URLError as exc:
        return json.dumps(
            {
                "success": False,
                "path": path,
                "error": str(exc.reason),
            },
            ensure_ascii=False,
        )


QUERY_AMOUNT_SCHEMA = {
    "name": "yunxiaodai_query_amount",
    "description": "Run Yunxiaodai amount estimation for a pre-application.",
    "parameters": {
        "type": "object",
        "properties": {
            "token": {
                "type": "string",
                "description": "Required Yunxiaodai login token from the user.",
            },
            "customerNo": {
                "type": "string",
                "description": "Optional customer number.",
            },
            "certNo": {"type": "string", "description": "Customer ID number."},
            "preApplyId": {
                "type": "string",
                "description": "Pre-application id, such as Y20260512YXD000702.",
            },
            "certName": {"type": "string", "description": "Customer name."},
            "mobileNo": {"type": "string", "description": "Customer mobile number."},
            "certValidEndDate": {
                "type": "string",
                "description": "ID card expiration date, such as 2035-12-01.",
            },
            "ocrAddress": {"type": "string", "description": "ID card address."},
            "provCode": {"type": "string", "description": "Province area code."},
            "cityCode": {"type": "string", "description": "City area code."},
            "areaCode": {"type": "string", "description": "District area code."},
        },
        "required": [
            "token",
            "certNo",
            "preApplyId",
            "certName",
            "mobileNo",
            "certValidEndDate",
            "ocrAddress",
            "provCode",
            "cityCode",
            "areaCode",
        ],
    },
}


SUBMIT_COMPANY_SCHEMA = {
    "name": "yunxiaodai_submit_company",
    "description": "Submit Yunxiaodai company information for a pre-application.",
    "parameters": {
        "type": "object",
        "properties": {
            "token": {
                "type": "string",
                "description": "Required Yunxiaodai login token from the user.",
            },
            "customerNo": {
                "type": "string",
                "description": "Optional enterprise customer number.",
            },
            "preApplyId": {
                "type": "string",
                "description": "Pre-application id used by amount estimation.",
            },
            "nsrsbh": {
                "type": "string",
                "description": "Taxpayer id, same as unified social credit code.",
            },
            "customerId": {
                "type": "string",
                "description": "Optional enterprise customer id.",
            },
            "companyAddress": {
                "type": "string",
                "description": "Company address, usually city-level.",
            },
            "companyCode": {
                "type": "string",
                "description": "Area code for the company address.",
            },
            "companyName": {"type": "string", "description": "Company name."},
            "artificialName": {
                "type": "string",
                "description": "Legal representative name.",
            },
        },
        "required": [
            "token",
            "preApplyId",
            "nsrsbh",
            "companyAddress",
            "companyCode",
            "companyName",
            "artificialName",
        ],
    },
}


APPLY_INFO_SCHEMA = {
    "name": "yunxiaodai_apply_info",
    "description": "Submit the final Yunxiaodai order application.",
    "parameters": {
        "type": "object",
        "properties": {
            "token": {
                "type": "string",
                "description": "Required Yunxiaodai login token from the user.",
            },
            "applyId": {
                "type": "string",
                "description": "Application id. If omitted, derive from preApplyId.",
            },
            "preApplyId": {
                "type": "string",
                "description": "Pre-application id, such as Y20260512YXD000702.",
            },
            "custManager": {"type": "string", "description": "Customer manager id."},
            "isAuth": {
                "type": "string",
                "description": "Authorization flag. Enterprise credit authorization uses 1.",
            },
            "companyName": {
                "type": "string",
                "description": "Company name from company submission.",
            },
            "nsrsbh": {
                "type": "string",
                "description": "Taxpayer id from company submission.",
            },
            "channelNo": {
                "type": "string",
                "description": "Channel number.",
                "default": "H5",
            },
        },
        "required": [
            "token",
            "preApplyId",
            "custManager",
            "isAuth",
            "companyName",
            "nsrsbh",
        ],
    },
}


def handle_query_amount(args: dict[str, Any], **kwargs) -> str:
    token = _require_token(args)
    if token is None:
        return _missing_token_result(QUERY_AMOUNT_PATH)

    payload = {
        "common": _compact(
            {
                "txChan": "04",
                "customerNo": args.get("customerNo"),
            }
        ),
        "input": {
            "certNo": args["certNo"],
            "preApplyId": args["preApplyId"],
            "certName": args["certName"],
            "mobileNo": args["mobileNo"],
            "certValidEndDate": args["certValidEndDate"],
            "ocrAddress": args["ocrAddress"],
            "provCode": args["provCode"],
            "cityCode": args["cityCode"],
            "areaCode": args["areaCode"],
        },
    }
    return _post(QUERY_AMOUNT_PATH, payload, token)


def handle_submit_company(args: dict[str, Any], **kwargs) -> str:
    token = _require_token(args)
    if token is None:
        return _missing_token_result(SUBMIT_COMPANY_PATH)

    payload = {
        "common": _compact(
            {
                "txChan": "04",
                "customerNo": args.get("customerNo"),
            }
        ),
        "input": _compact(
            {
                "preApplyId": args["preApplyId"],
                "nsrsbh": args["nsrsbh"],
                "customerId": args.get("customerId"),
                "companyAddress": args["companyAddress"],
                "companyCode": args["companyCode"],
                "companyName": args["companyName"],
                "artificialName": args["artificialName"],
            }
        ),
    }
    return _post(SUBMIT_COMPANY_PATH, payload, token)


def handle_apply_info(args: dict[str, Any], **kwargs) -> str:
    token = _require_token(args)
    if token is None:
        return _missing_token_result(APPLY_INFO_PATH)

    pre_apply_id = args["preApplyId"]
    apply_id = args.get("applyId") or (
        pre_apply_id[1:] if pre_apply_id.startswith("Y") else pre_apply_id
    )
    payload = {
        "common": {
            "txChan": "04",
        },
        "input": {
            "applyId": apply_id,
            "preApplyId": pre_apply_id,
            "custManager": args["custManager"],
            "isAuth": args["isAuth"],
            "companyName": args["companyName"],
            "nsrsbh": args["nsrsbh"],
            "channelNo": args.get("channelNo") or "H5",
        },
    }
    return _post(APPLY_INFO_PATH, payload, token)
