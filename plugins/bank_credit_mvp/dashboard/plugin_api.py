"""Dashboard API for the bank credit workflow MVP."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from plugins.bank_credit_mvp import workflow


router = APIRouter()


class CreateCaseBody(BaseModel):
    applicant_name: str = Field(default="上海青禾贸易有限公司", min_length=1)
    amount: int = Field(default=500000, ge=1)
    purpose: str = Field(default="流动资金周转", min_length=1)


class AdvanceBody(BaseModel):
    report_fields: Optional[Dict[str, Any]] = None


class CustomerCreatedBody(BaseModel):
    customer_no: Optional[str] = None


@router.get("/cases")
async def cases():
    return {"cases": workflow.list_cases()}


@router.post("/cases")
async def create_case(body: CreateCaseBody):
    return {"case": workflow.create_case(body.applicant_name, body.amount, body.purpose)}


@router.get("/cases/{case_id}")
async def case_detail(case_id: str):
    try:
        return {"case": workflow.get_case(case_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found.") from exc


@router.post("/cases/{case_id}/advance")
async def advance(case_id: str, body: AdvanceBody):
    try:
        return {"case": workflow.advance_case(case_id, body.report_fields or {})}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found.") from exc


@router.post("/cases/{case_id}/mock/customer-created")
async def mock_customer_created(case_id: str, body: CustomerCreatedBody):
    try:
        return {"case": workflow.mark_customer_created(case_id, body.customer_no)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found.") from exc


@router.post("/cases/{case_id}/mock/financial-ready")
async def mock_financial_ready(case_id: str):
    try:
        return {"case": workflow.mark_financial_ready(case_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found.") from exc


@router.post("/poll")
async def poll_cases():
    return {"poll": workflow.poll_cases()}


@router.post("/reset-demo")
async def reset_demo():
    return {"case": workflow.reset_demo()}
