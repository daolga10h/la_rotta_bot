import pytest
from datetime import datetime, timezone


def test_objective_model():
    from models.user_profile import Objective
    obj = Objective(title="Oltre la Bottega", rank=2, weekly_hours_target=6)
    assert obj.title == "Oltre la Bottega"
    assert obj.rank == 2
    assert obj.weekly_hours_target == 6


def test_objective_rank1_no_hours_required():
    from models.user_profile import Objective
    obj = Objective(title="Vendere il negozio", rank=1)
    assert obj.weekly_hours_target is None


def test_intention_model():
    from models.user_profile import Intention
    now = datetime.now(timezone.utc)
    intent = Intention(text="lavorare alla scaletta", declared_at=now)
    assert intent.morning_reminder_sent is False


def test_unlock_entry():
    from models.user_profile import UnlockEntry
    entry = UnlockEntry(insight="Ce la faccio", context="paura")
    assert entry.id is not None
    assert entry.saved_at is not None


def test_parking_item():
    from models.user_profile import ParkingItem
    item = ParkingItem(content="Open day Natale", category="NEGOZIO")
    assert item.status == "parked"
    assert item.last_reviewed_at is None


def test_parking_item_invalid_category():
    from models.user_profile import ParkingItem
    with pytest.raises(Exception):
        ParkingItem(content="Test", category="INVALIDA")


def test_counters_default_zero():
    from models.user_profile import Counters
    c = Counters()
    assert c.consecutive_operative_days == 0
    assert c.total_strategic_sessions == 0


def test_reengagement_defaults():
    from models.user_profile import ReEngagement
    r = ReEngagement()
    assert r.day3_message_sent is False
    assert r.pause_until is None


def test_user_profile_data_full():
    from models.user_profile import UserProfileData, Objective
    profile = UserProfileData(
        telegram_id=123456,
        objectives=[Objective(title="Vendere negozio", rank=1)],
        motivation_anchor="Casa a Marta",
        user_context="Imprenditrice con bottega",
    )
    assert profile.objectives_version == 1
    assert profile.onboarding_complete is False
    assert profile.onboarding_step == 0
    assert profile.streak_strategic == 0


def test_user_profile_serializes_to_dict():
    from models.user_profile import UserProfileData, Objective
    profile = UserProfileData(
        telegram_id=123456,
        objectives=[Objective(title="Vendere negozio", rank=1)],
        motivation_anchor="Casa a Marta",
        user_context="Bottega artigianale",
    )
    d = profile.model_dump()
    assert "telegram_id" in d
    assert isinstance(d["objectives"], list)
    assert d["objectives"][0]["rank"] == 1


def test_conversation_message_defaults():
    from models.conversation import ConversationMessage
    msg = ConversationMessage(role="user", content="Ciao")
    assert msg.classified_as is None
    assert msg.created_at is not None


def test_checkin_session_evening():
    from models.conversation import CheckinSession
    s = CheckinSession(type="evening", date="2026-06-20")
    assert s.completed is False
    assert s.scenario is None
