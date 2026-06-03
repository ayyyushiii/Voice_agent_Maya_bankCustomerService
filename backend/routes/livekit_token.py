"""LiveKit access token generation — API secret never leaves the server."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from livekit import api
from pydantic import BaseModel, Field

logger = logging.getLogger("maya.livekit")

router = APIRouter(prefix="/api/livekit", tags=["livekit"])


class TokenRequest(BaseModel):
    participant_name: str = Field(..., min_length=1, max_length=100)
    room_name: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    room_name: str
    livekit_url: str
    call_id: str
    participant_identity: str


@router.post("/token", response_model=TokenResponse)
async def create_livekit_token(body: TokenRequest) -> TokenResponse:
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not api_key or not api_secret or not livekit_url:
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured on server",
        )

    call_id = f"call_{uuid.uuid4().hex[:12]}"
    room_name = body.room_name or f"maya-bank-{call_id}"
    identity = f"user-{uuid.uuid4().hex[:8]}"

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(body.participant_name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_metadata(f'{{"callId":"{call_id}","role":"user"}}')
        .to_jwt()
    )

    # Dispatch Maya agent to the room
    try:
        from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest

        http_url = livekit_url.replace("wss://", "https://").replace("ws://", "http://")
        lkapi = api.LiveKitAPI(url=http_url, api_key=api_key, api_secret=api_secret)
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                agent_name="maya-bank-agent",
                room=room_name,
                metadata=f'{{"callId":"{call_id}"}}',
            )
        )
        await lkapi.aclose()
        logger.info("Agent dispatch created: %s -> %s", dispatch.id, room_name)
    except Exception as exc:
        logger.error("Agent dispatch failed for room %s: %s", room_name, exc)

    return TokenResponse(
        token=token,
        room_name=room_name,
        livekit_url=livekit_url,
        call_id=call_id,
        participant_identity=identity,
    )
