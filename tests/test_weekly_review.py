import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from models.user_profile import UserProfileData, Objective, ParkingItem, Counters


def _make_profile(**kwargs) -> UserProfileData:
    defaults = dict(
        telegram_id=12345,
        objectives=[
            Objective(title="Vendere negozio", rank=1),
            Objective(title="Oltre la Bottega", rank=2, weekly_hours_target=6),
        ],
        motivation_anchor="Casa a Marta",
        user_context="Bottega",
        onboarding_complete=True,
    )
    defaults.update(kwargs)
    return UserProfileData(**defaults)


def _make_callback(data):
    update = MagicMock()
    update.message = None
    update.callback_query.data = data
    update.callback_query.message.reply_text = AsyncMock()
    return update


def _make_update(text):
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.text = text
    update.callback_query = None
    return update


def _parking_item(content="Idea test", status="parked", days_old=0) -> ParkingItem:
    created = datetime.now(timezone.utc) - timedelta(days=days_old)
    return ParkingItem(content=content, category="NEGOZIO", status=status, created_at=created)


# ── Progress question ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_progress_q_saves_highlight_and_shows_summary():
    profile = _make_profile()
    profile.weekly_review_data = {"strategic_sessions": 3}
    update = _make_update("Ho completato il primo modulo del corso")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state") as mock_state:
        from handlers.weekly_review import _progress_q
        await _progress_q(update, MagicMock(), "uid", 12345, "Ho completato il primo modulo del corso", profile)
        assert profile.weekly_review_data["week_highlight"] == "Ho completato il primo modulo del corso"
        mock_state.assert_called_once_with("uid", "WEEKLY_REVIEW_EVAL")
        reply = update.message.reply_text.call_args[0][0]
        assert "Ho completato il primo modulo del corso" in reply


# ── Evaluation ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evaluation_buona_goes_to_hours():
    profile = _make_profile()
    profile.weekly_review_data = {"evaluation": "buona"}
    update = _make_callback("Buona")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state") as mock_state:
        from handlers.weekly_review import _evaluation
        await _evaluation(update, MagicMock(), "uid", 12345, "Buona", profile)
        mock_state.assert_called_once_with("uid", "WEEKLY_REVIEW_HOURS")


@pytest.mark.asyncio
async def test_evaluation_triggers_pattern_operative():
    profile = _make_profile()
    profile.weekly_review_data = {}
    profile.counters.consecutive_operative_days = 6
    update = _make_callback("Mista")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state") as mock_state:
        from handlers.weekly_review import _evaluation
        await _evaluation(update, MagicMock(), "uid", 12345, "Mista", profile)
        mock_state.assert_called_once_with("uid", "WEEKLY_REVIEW_PATTERN_OP")


# ── Hours response ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_hours_diversamente_asks_why():
    profile = _make_profile()
    profile.weekly_review_data = {}
    update = _make_callback("Potevo gestirlo diversamente")
    with patch("handlers.weekly_review.set_state") as mock_state:
        from handlers.weekly_review import _hours_response
        await _hours_response(update, MagicMock(), "uid", 12345, "Potevo gestirlo diversamente", profile)
        mock_state.assert_called_once_with("uid", "WEEKLY_REVIEW_HOURS_WHY")


@pytest.mark.asyncio
async def test_hours_necessarie_resets_counter():
    profile = _make_profile()
    profile.counters.consecutive_weeks_under_target = 2
    profile.weekly_review_data = {}
    update = _make_callback("Erano necessarie")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state"):
        from handlers.weekly_review import _hours_response
        await _hours_response(update, MagicMock(), "uid", 12345, "Erano necessarie", profile)
        assert profile.counters.consecutive_weeks_under_target == 0


@pytest.mark.asyncio
async def test_hours_why_increments_weeks_counter():
    profile = _make_profile()
    profile.weekly_review_data = {}
    profile.counters.consecutive_weeks_under_target = 1
    update = _make_update("Il negozio era pieno tutto il giorno")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state"):
        from handlers.weekly_review import _hours_why
        await _hours_why(update, MagicMock(), "uid", 12345, "Il negozio era pieno tutto il giorno", profile)
        assert profile.counters.consecutive_weeks_under_target == 2


# ── Parcheggio ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parking_yn_dopo_skips():
    profile = _make_profile()
    profile.parking_lot = [_parking_item("Idea 1")]
    profile.weekly_review_data = {}
    update = _make_callback("Dopo")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state") as mock_state:
        from handlers.weekly_review import _parking_yn
        await _parking_yn(update, MagicMock(), "uid", 12345, "Dopo", profile)
        mock_state.assert_called_once_with("uid", "WEEKLY_REVIEW_CLOSE")


@pytest.mark.asyncio
async def test_parking_yn_si_sets_review_index():
    profile = _make_profile()
    profile.parking_lot = [_parking_item("Idea 1"), _parking_item("Idea 2")]
    profile.weekly_review_data = {}
    update = _make_callback("Sì, le vedo tutte")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state") as mock_state:
        from handlers.weekly_review import _parking_yn
        await _parking_yn(update, MagicMock(), "uid", 12345, "Sì, le vedo tutte", profile)
        assert profile.weekly_review_data["review_index"] == 0
        assert len(profile.weekly_review_data["items_to_review"]) == 2
        mock_state.assert_called_once_with("uid", "WEEKLY_REVIEW_PARKING_ITEM")


@pytest.mark.asyncio
async def test_parking_item_elimina_marks_deleted():
    profile = _make_profile()
    item = _parking_item("Idea da eliminare")
    profile.parking_lot = [item]
    profile.weekly_review_data = {"items_to_review": [item.id], "review_index": 0}
    update = _make_callback("Elimina")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state"):
        from handlers.weekly_review import _parking_item as _item_step
        await _item_step(update, MagicMock(), "uid", 12345, "Elimina", profile)
        deleted = next(p for p in profile.parking_lot if p.id == item.id)
        assert deleted.status == "deleted"


@pytest.mark.asyncio
async def test_parking_item_sviluppa_goes_to_dev1():
    profile = _make_profile()
    item = _parking_item("Corso online")
    profile.parking_lot = [item]
    profile.weekly_review_data = {"items_to_review": [item.id], "review_index": 0}
    update = _make_callback("Sviluppa questa settimana")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state") as mock_state:
        from handlers.weekly_review import _parking_item as _item_step
        await _item_step(update, MagicMock(), "uid", 12345, "Sviluppa questa settimana", profile)
        mock_state.assert_called_once_with("uid", "WEEKLY_REVIEW_PARKING_DEV1")
        assert profile.weekly_review_data["developing_item_id"] == item.id


@pytest.mark.asyncio
async def test_parking_dev3_promotes_idea():
    profile = _make_profile()
    item = _parking_item("Corso online")
    profile.parking_lot = [item]
    profile.weekly_review_data = {
        "items_to_review": [item.id],
        "review_index": 0,
        "developing_item_id": item.id,
    }
    update = _make_update("Ho già provato qualcosa di simile ma non ho finito")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.set_state"):
        from handlers.weekly_review import _parking_dev3
        await _parking_dev3(update, MagicMock(), "uid", 12345, "Ho già provato", profile)
        promoted = next(p for p in profile.parking_lot if p.id == item.id)
        assert promoted.status == "promoted"


# ── Chiusura ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_close_no_calls_finish():
    profile = _make_profile()
    profile.weekly_review_data = {"evaluation": "buona", "week_highlight": "test"}
    update = _make_callback("No, va bene così")
    with patch("handlers.weekly_review.save_profile"), \
         patch("handlers.weekly_review.clear_state") as mock_clear, \
         patch("services.weekly_summary.generate_narrative", return_value=("Settimana buona.", "good")), \
         patch("services.weekly_summary.save_weekly_summary"), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}), \
         patch("db.queries.get_recent_weekly_summaries", return_value=[]):
        from handlers.weekly_review import _close
        await _close(update, MagicMock(), "uid", 12345, "No, va bene così", profile)
        mock_clear.assert_called_once_with("uid")
        assert profile.weekly_review_data is None
