import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from models.user_profile import UserProfileData, Objective, Intention


def _make_profile(**kwargs) -> UserProfileData:
    defaults = dict(
        telegram_id=12345,
        objectives=[Objective(title="Vendere negozio", rank=1)],
        motivation_anchor="Casa a Marta",
        user_context="Bottega",
        onboarding_complete=True,
    )
    defaults.update(kwargs)
    return UserProfileData(**defaults)


def _make_intention(text="Lavorare alla scaletta", sent=False) -> Intention:
    return Intention(
        text=text,
        declared_at=datetime.now(timezone.utc),
        morning_reminder_sent=sent,
    )


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


# ── send_if_needed ────────────────────────────────────────────────────────────

def test_send_if_needed_skips_when_no_intention():
    profile = _make_profile()  # no last_intention_declared
    with patch("handlers.checkin_morning.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}):
        import asyncio
        bot = AsyncMock()
        asyncio.run(_run_send_if_needed(12345, bot))
        bot.send_message.assert_not_called()


def test_send_if_needed_skips_when_already_sent():
    profile = _make_profile()
    profile.last_intention_declared = _make_intention(sent=True)
    with patch("handlers.checkin_morning.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}):
        import asyncio
        bot = AsyncMock()
        asyncio.run(_run_send_if_needed(12345, bot))
        bot.send_message.assert_not_called()


async def _run_send_if_needed(telegram_id, bot):
    from handlers.checkin_morning import send_if_needed
    with patch("handlers.checkin_morning.set_state"):
        await send_if_needed(telegram_id, bot)


# ── Scenario: Sì, è il piano ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_si_marks_sent_and_closes():
    profile = _make_profile()
    profile.last_intention_declared = _make_intention()
    update = _make_callback("Sì, è il piano")
    with patch("handlers.checkin_morning.save_profile") as mock_save, \
         patch("handlers.checkin_morning.clear_state") as mock_clear:
        from handlers.checkin_morning import _start
        await _start(update, MagicMock(), "uid", 12345, "Sì, è il piano", profile)
        assert profile.last_intention_declared.morning_reminder_sent is True
        mock_save.assert_called_once()
        mock_clear.assert_called_once_with("uid")
        reply = update.callback_query.message.reply_text.call_args[0][0]
        assert "lupo" in reply.lower()


# ── Scenario: Ho cambiato idea ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_cambiato_asks_new_intention():
    profile = _make_profile()
    profile.last_intention_declared = _make_intention()
    update = _make_callback("Ho cambiato idea")
    with patch("handlers.checkin_morning.set_state") as mock_state:
        from handlers.checkin_morning import _start
        await _start(update, MagicMock(), "uid", 12345, "Ho cambiato idea", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_MORNING_CHANGED")


@pytest.mark.asyncio
async def test_changed_saves_new_intention():
    profile = _make_profile()
    profile.last_intention_declared = _make_intention("vecchia intenzione")
    update = _make_update("Lavorare sul sito web")
    with patch("handlers.checkin_morning.save_profile") as mock_save, \
         patch("handlers.checkin_morning.save_message"), \
         patch("handlers.checkin_morning.clear_state") as mock_clear:
        from handlers.checkin_morning import _changed
        await _changed(update, MagicMock(), "uid", 12345, "Lavorare sul sito web", profile)
        assert profile.last_intention_declared.text == "Lavorare sul sito web"
        assert profile.last_intention_declared.morning_reminder_sent is True
        mock_save.assert_called_once()
        mock_clear.assert_called_once_with("uid")
        reply = update.message.reply_text.call_args[0][0]
        assert "lupo" in reply.lower()


# ── Scenario: Non ce la faccio ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_non_ce_la_faccio_asks_why():
    profile = _make_profile()
    profile.last_intention_declared = _make_intention()
    update = _make_callback("Non ce la faccio oggi")
    with patch("handlers.checkin_morning.set_state") as mock_state:
        from handlers.checkin_morning import _start
        await _start(update, MagicMock(), "uid", 12345, "Non ce la faccio oggi", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_MORNING_CANT_WHY")


@pytest.mark.asyncio
async def test_cant_why_no_closes_and_clears_intention():
    profile = _make_profile()
    profile.last_intention_declared = _make_intention()
    update = _make_callback("No, è così e basta")
    with patch("handlers.checkin_morning.save_profile") as mock_save, \
         patch("handlers.checkin_morning.clear_state") as mock_clear:
        from handlers.checkin_morning import _cant_why
        await _cant_why(update, MagicMock(), "uid", 12345, "No, è così e basta", profile)
        assert profile.last_intention_declared is None
        mock_save.assert_called_once()
        mock_clear.assert_called_once_with("uid")
        reply = update.callback_query.message.reply_text.call_args[0][0]
        assert "domani" in reply.lower()


@pytest.mark.asyncio
async def test_cant_why_yes_asks_for_text():
    profile = _make_profile()
    profile.last_intention_declared = _make_intention()
    update = _make_callback("Sì")
    with patch("handlers.checkin_morning.set_state") as mock_state:
        from handlers.checkin_morning import _cant_why
        await _cant_why(update, MagicMock(), "uid", 12345, "Sì", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_MORNING_CANT_TEXT")


@pytest.mark.asyncio
async def test_cant_text_saves_message_and_closes():
    profile = _make_profile()
    profile.last_intention_declared = _make_intention()
    update = _make_update("Ho avuto un'emergenza in negozio")
    with patch("handlers.checkin_morning.save_message") as mock_msg, \
         patch("handlers.checkin_morning.save_profile"), \
         patch("handlers.checkin_morning.clear_state") as mock_clear:
        from handlers.checkin_morning import _cant_text
        await _cant_text(update, MagicMock(), "uid", 12345, "Ho avuto un'emergenza in negozio", profile)
        mock_msg.assert_called_once()
        assert profile.last_intention_declared is None
        mock_clear.assert_called_once_with("uid")
