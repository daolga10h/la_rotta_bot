import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from models.user_profile import UserProfileData, Objective, Intention


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


# ── Scenario A ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_operativo_sets_a_strategic():
    profile = _make_profile()
    update = _make_callback("Ho lavorato sull'operativo")
    with patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _start
        await _start(update, MagicMock(), "uid", 12345, "Ho lavorato sull'operativo", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_A_STRATEGIC")


@pytest.mark.asyncio
async def test_a_strategic_yes_asks_what():
    profile = _make_profile()
    update = _make_callback("Sì")
    with patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _a_strategic
        await _a_strategic(update, MagicMock(), "uid", 12345, "Sì", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_A_WHAT")


@pytest.mark.asyncio
async def test_a_strategic_no_asks_intention():
    profile = _make_profile()
    update = _make_callback("No")
    with patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _a_strategic
        await _a_strategic(update, MagicMock(), "uid", 12345, "No", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_A_INTENTION")


# ── Scenario B ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_strategico_sets_b_what():
    profile = _make_profile()
    update = _make_callback("Ho lavorato su qualcosa di strategico")
    with patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _start
        await _start(update, MagicMock(), "uid", 12345, "Ho lavorato su qualcosa di strategico", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_B_WHAT")


@pytest.mark.asyncio
async def test_b_what_increments_streak():
    profile = _make_profile(streak_strategic=2)
    update = _make_update("Ho scritto la scaletta del primo modulo")
    with patch("handlers.checkin_evening.save_profile") as mock_save, \
         patch("handlers.checkin_evening.save_message"), \
         patch("handlers.checkin_evening.set_state"), \
         patch("handlers.checkin_evening.generate_response", return_value=("Bene.", False)):
        from handlers.checkin_evening import _b_what
        await _b_what(update, MagicMock(), "uid", 12345, "Ho scritto la scaletta del primo modulo", profile)
        assert profile.streak_strategic == 3
        assert profile.counters.consecutive_operative_days == 0
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_b_what_milestone_streak_adds_message():
    profile = _make_profile(streak_strategic=4)
    update = _make_update("Ho lavorato su Oltre la Bottega")
    with patch("handlers.checkin_evening.save_profile"), \
         patch("handlers.checkin_evening.save_message"), \
         patch("handlers.checkin_evening.set_state"), \
         patch("handlers.checkin_evening.generate_response", return_value=("Ottimo lavoro.", False)):
        from handlers.checkin_evening import _b_what
        await _b_what(update, MagicMock(), "uid", 12345, "Ho lavorato su Oltre la Bottega", profile)
        assert profile.streak_strategic == 5
        # Check milestone message shown
        call_args = update.message.reply_text.call_args[0][0]
        assert "5" in call_args


# ── Scenario C ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_niente_sets_c_blocker():
    profile = _make_profile()
    update = _make_callback("Niente di significativo oggi")
    with patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _start
        await _start(update, MagicMock(), "uid", 12345, "Niente di significativo oggi", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_C_BLOCKER")


@pytest.mark.asyncio
async def test_c_blocker_saves_and_asks_intention():
    profile = _make_profile()
    update = _make_update("Il negozio assorbe tutto")
    with patch("handlers.checkin_evening.save_message"), \
         patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _c_blocker
        await _c_blocker(update, MagicMock(), "uid", 12345, "Il negozio assorbe tutto", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_C_INTENTION")


# ── Intention sub-flow ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_intention_yn_yes_asks_text():
    profile = _make_profile()
    update = _make_callback("Sì")
    with patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _ask_intention_yn
        await _ask_intention_yn(update, MagicMock(), "uid", 12345, "Sì", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_INT_TEXT")


@pytest.mark.asyncio
async def test_intention_yn_no_goes_to_close():
    profile = _make_profile()
    update = _make_callback("No, non ora")
    with patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _ask_intention_yn
        await _ask_intention_yn(update, MagicMock(), "uid", 12345, "No, non ora", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_CLOSE")


@pytest.mark.asyncio
async def test_intention_text_saves_intention():
    profile = _make_profile()
    update = _make_update("Lavorare alla scaletta del modulo 1")
    with patch("handlers.checkin_evening.save_profile") as mock_save, \
         patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _intention_text
        await _intention_text(update, MagicMock(), "uid", 12345, "Lavorare alla scaletta del modulo 1", profile)
        assert profile.last_intention_declared is not None
        assert profile.last_intention_declared.text == "Lavorare alla scaletta del modulo 1"
        mock_save.assert_called_once()
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_INT_TIME")


@pytest.mark.asyncio
async def test_intention_time_saves_time_of_day():
    profile = _make_profile()
    profile.last_intention_declared = Intention(
        text="Lavorare al modulo", declared_at=datetime.now(timezone.utc)
    )
    update = _make_callback("Mattina")
    with patch("handlers.checkin_evening.save_profile") as mock_save, \
         patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _intention_time
        await _intention_time(update, MagicMock(), "uid", 12345, "Mattina", profile)
        assert profile.last_intention_declared.time_of_day == "Mattina"
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_INT_DURATION")


@pytest.mark.asyncio
async def test_intention_duration_saves_and_goes_to_close():
    profile = _make_profile()
    profile.last_intention_declared = Intention(
        text="Lavorare al modulo", declared_at=datetime.now(timezone.utc), time_of_day="Mattina"
    )
    update = _make_callback("Un'ora")
    with patch("handlers.checkin_evening.save_profile") as mock_save, \
         patch("handlers.checkin_evening.set_state") as mock_state:
        from handlers.checkin_evening import _intention_duration
        await _intention_duration(update, MagicMock(), "uid", 12345, "Un'ora", profile)
        assert profile.last_intention_declared.duration == "Un'ora"
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_CLOSE")


# ── Universal closing ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_close_no_says_a_domani():
    profile = _make_profile()
    update = _make_callback("No, buonanotte")
    with patch("handlers.checkin_evening.save_profile"), \
         patch("handlers.checkin_evening.clear_state") as mock_clear:
        from handlers.checkin_evening import _close
        await _close(update, MagicMock(), "uid", 12345, "No, buonanotte", profile)
        mock_clear.assert_called_once_with("uid")
        reply_text = update.callback_query.message.reply_text.call_args[0][0]
        assert "domani" in reply_text.lower()


@pytest.mark.asyncio
async def test_close_yes_routes_to_parking():
    profile = _make_profile()
    update = _make_callback("Sì, ho un'idea")
    with patch("handlers.checkin_evening.save_profile"), \
         patch("handlers.checkin_evening.clear_state"), \
         patch("handlers.parking.start_parking", new_callable=AsyncMock) as mock_park:
        from handlers.checkin_evening import _close
        await _close(update, MagicMock(), "uid", 12345, "Sì, ho un'idea", profile)
        mock_park.assert_called_once()


@pytest.mark.asyncio
async def test_close_updates_reengagement_timestamp():
    profile = _make_profile()
    profile.re_engagement.day3_message_sent = True
    update = _make_callback("No, buonanotte")
    with patch("handlers.checkin_evening.save_profile"), \
         patch("handlers.checkin_evening.clear_state"):
        from handlers.checkin_evening import _close
        await _close(update, MagicMock(), "uid", 12345, "No, buonanotte", profile)
        assert profile.re_engagement.last_response_at is not None
        assert profile.re_engagement.day3_message_sent is False
