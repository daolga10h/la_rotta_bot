from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    classified_as: Optional[str] = None
    flow_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckinSession(BaseModel):
    type: Literal["evening", "morning"]
    date: str  # ISO date YYYY-MM-DD
    scenario: Optional[str] = None
    intention_declared: Optional[str] = None
    data: dict = Field(default_factory=dict)
    completed: bool = False
