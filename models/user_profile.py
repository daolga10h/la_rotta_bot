from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Objective(BaseModel):
    title: str
    rank: int
    weekly_hours_target: Optional[float] = None


class Intention(BaseModel):
    text: str
    declared_at: datetime
    morning_reminder_sent: bool = False
    time_of_day: Optional[Literal["Mattina", "Dopo pranzo", "Sera", "Non so ancora"]] = None
    duration: Optional[Literal["15-20 minuti", "Un'ora", "Più di un'ora", "Vado a occhio"]] = None


class UnlockEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    insight: str
    context: Literal["paura", "stanchezza", "confusione", "generico"]
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ParkingItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    category: Literal["NEGOZIO", "OLTRE_LA_BOTTEGA", "STRATEGICO_GENERICO"]
    status: Literal["parked", "reviewing", "promoted", "deleted"] = "parked"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_reviewed_at: Optional[datetime] = None


class Counters(BaseModel):
    consecutive_operative_days: int = 0
    consecutive_weeks_under_target: int = 0
    total_strategic_sessions: int = 0
    total_checkins_completed: int = 0
    total_ideas_parked: int = 0


class ReEngagement(BaseModel):
    last_response_at: Optional[datetime] = None
    day3_message_sent: bool = False
    day7_message_sent: bool = False
    pause_until: Optional[datetime] = None


class UserProfileData(BaseModel):
    telegram_id: int
    objectives_version: int = 1
    objectives: list[Objective] = Field(default_factory=list)
    motivation_anchor: Optional[str] = None
    user_context: Optional[str] = None
    checkin_time_evening: str = "21:30"
    checkin_time_morning: str = "07:30"
    review_day: str = "domenica"
    review_time: str = "18:00"
    streak_strategic: int = 0
    last_intention_declared: Optional[Intention] = None
    recurring_blocks: list[str] = Field(default_factory=list)
    unlock_library: list[UnlockEntry] = Field(default_factory=list)
    counters: Counters = Field(default_factory=Counters)
    parking_lot: list[ParkingItem] = Field(default_factory=list)
    re_engagement: ReEngagement = Field(default_factory=ReEngagement)
    onboarding_complete: bool = False
    onboarding_step: int = 0
    conversation_state: str = "IDLE"
    state_expires_at: Optional[datetime] = None
    parking_pending: Optional[dict] = None  # {"text": str, "category": str} durante il flusso parcheggio
    scenario_c_data: Optional[dict] = None  # risposte temporanee durante Scenario C
    weekly_review_data: Optional[dict] = None  # dati temporanei durante la revisione settimanale
