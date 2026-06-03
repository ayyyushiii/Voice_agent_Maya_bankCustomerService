"""Banking tool implementations shared by REST API and voice agent."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.user_db import (
    find_user,
    get_verified_user_id,
    is_verified,
    load_users,
    mark_verified,
    save_users,
)

# In-memory complaint and escalation registry
_complaints: list[dict[str, Any]] = []
_escalations: list[dict[str, Any]] = []


def verify_user(
    call_id: str,
    phone: str,
    birth_year: str,
    *,
    simulate_failure: bool = False,
) -> dict[str, Any]:
    if simulate_failure:
        return {"success": False, "error": "Verification service temporarily unavailable"}

    user = find_user(phone=phone)
    if not user:
        return {"success": False, "error": "No account found for this phone number"}

    if str(user.get("birthYear")) != str(birth_year):
        return {"success": False, "error": "Birth year does not match our records"}

    mark_verified(call_id, user["userId"])
    return {
        "success": True,
        "message": f"Identity verified for {user['name']}.",
        "userId": user["userId"],
        "name": user["name"],
    }


def get_balance(call_id: str, *, simulate_failure: bool = False) -> dict[str, Any]:
    if simulate_failure:
        return {"success": False, "error": "Balance service temporarily unavailable"}

    if not is_verified(call_id):
        return {
            "success": False,
            "error": "Verification required before accessing account balance",
        }

    user_id = get_verified_user_id(call_id)
    user = find_user(user_id=user_id)
    if not user:
        return {"success": False, "error": "User not found"}

    return {
        "success": True,
        "balance": user["accountBalance"],
        "currency": "INR",
        "accountHolder": user["name"],
    }


def block_card(call_id: str, *, simulate_failure: bool = False) -> dict[str, Any]:
    if simulate_failure:
        return {"success": False, "error": "Card blocking service temporarily unavailable"}

    if not is_verified(call_id):
        return {
            "success": False,
            "error": "Verification required before blocking card",
        }

    user_id = get_verified_user_id(call_id)
    users = load_users()
    updated = None
    for user in users:
        if user.get("userId") == user_id:
            user["cardBlocked"] = True
            updated = user
            break

    if not updated:
        return {"success": False, "error": "User not found"}

    save_users(users)
    return {
        "success": True,
        "message": f"Card ending in {updated['cardLast4']} has been blocked.",
        "cardLast4": updated["cardLast4"],
    }


def create_complaint(
    call_id: str,
    complaint_type: str,
    description: str,
    *,
    simulate_failure: bool = False,
) -> dict[str, Any]:
    if simulate_failure:
        return {"success": False, "error": "Complaint service temporarily unavailable"}

    complaint_id = f"cmp_{uuid.uuid4().hex[:8]}"
    user_id = get_verified_user_id(call_id) if is_verified(call_id) else None

    complaint = {
        "complaintId": complaint_id,
        "callId": call_id,
        "userId": user_id,
        "type": complaint_type,
        "description": description,
        "status": "open",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    _complaints.append(complaint)

    return {
        "success": True,
        "complaintId": complaint_id,
        "message": f"Complaint registered under reference {complaint_id}.",
        "status": "open",
    }


def escalate(
    call_id: str,
    reason: str,
    *,
    simulate_failure: bool = False,
) -> dict[str, Any]:
    if simulate_failure:
        return {"success": False, "error": "Escalation service temporarily unavailable"}

    escalation_id = f"esc_{uuid.uuid4().hex[:8]}"
    user_id = get_verified_user_id(call_id) if is_verified(call_id) else None

    escalation = {
        "escalationId": escalation_id,
        "callId": call_id,
        "userId": user_id,
        "reason": reason,
        "status": "queued",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    _escalations.append(escalation)

    return {
        "success": True,
        "escalationId": escalation_id,
        "message": "You have been queued for a human agent. Expected wait is 3 minutes.",
        "waitMinutes": 3,
    }


def get_branch_hours() -> dict[str, Any]:
    users = load_users()
    hours = users[0].get("branchHours", "Mon-Sat 9:00 AM - 5:00 PM") if users else "Mon-Sat 9:00 AM - 5:00 PM"
    return {"success": True, "branchHours": hours}
