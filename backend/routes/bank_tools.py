"""REST endpoints for banking tools (used by agent and direct API access)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import banking_tools
from services.debug_flags import should_fail

router = APIRouter(prefix="/api/bank", tags=["bank"])


class VerifyUserRequest(BaseModel):
    call_id: str
    phone: str = Field(..., min_length=10, max_length=15)
    birth_year: str = Field(..., min_length=4, max_length=4)


class ComplaintRequest(BaseModel):
    call_id: str
    complaint_type: str
    description: str = Field(..., min_length=5)


class EscalateRequest(BaseModel):
    call_id: str
    reason: str = Field(..., min_length=3)


class ToolRequest(BaseModel):
    call_id: str


@router.post("/verify")
async def verify_user(body: VerifyUserRequest):
    result = banking_tools.verify_user(
        body.call_id,
        body.phone,
        body.birth_year,
        simulate_failure=should_fail(body.call_id, "tool_failure"),
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post("/balance")
async def get_balance(body: ToolRequest):
    result = banking_tools.get_balance(
        body.call_id,
        simulate_failure=should_fail(body.call_id, "tool_failure"),
    )
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result)
    return result


@router.post("/block-card")
async def block_card(body: ToolRequest):
    result = banking_tools.block_card(
        body.call_id,
        simulate_failure=should_fail(body.call_id, "tool_failure"),
    )
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result)
    return result


@router.post("/complaint")
async def create_complaint(body: ComplaintRequest):
    result = banking_tools.create_complaint(
        body.call_id,
        body.complaint_type,
        body.description,
        simulate_failure=should_fail(body.call_id, "tool_failure"),
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result)
    return result


@router.post("/escalate")
async def escalate(body: EscalateRequest):
    result = banking_tools.escalate(
        body.call_id,
        body.reason,
        simulate_failure=should_fail(body.call_id, "tool_failure"),
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result)
    return result


@router.get("/branch-hours")
async def branch_hours():
    return banking_tools.get_branch_hours()
