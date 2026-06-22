import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models.user_profile import UserProfileData, Objective, ParkingItem


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


def _make_update(text=""):
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.text = text
    update.callback_query = None
    return update


def _make_callback(data):
    update = MagicMock()
    update.message = None
    update.callback_query.data = data
    update.callback_query.message.reply_text = AsyncMock()
    return update


def _classify_result(category, confidence=0.95, alt=None):
    return {"category": category, "confidence": confidence, "alternative_category": alt}


# ── handle_free_message: alta confidence ─────────────────────────────────────

@pytest.mark.asyncio
async def test_high_confidence_shows_confirmation():
    profile = _make_profile()
    update = _make_update("Ho pensato di fare un open day")
    with patch("handlers.free_message.classify_message", return_value=_classify_result("IDEA")), \
         patch("handlers.free_message.save_message"), \
         patch("handlers.free_message.get_recent_messages", return_value=[]), \
         patch("handlers.free_message.save_profile"), \
         patch("handlers.free_message.set_state") as mock_state:
        from handlers.free_message import handle_free_message
        await handle_free_message(update, MagicMock(), "uid", 12345, "Ho pensato di fare un open day", profile)
        mock_state.assert_called_once_with("uid", "FREE_MSG_CONFIRM")
        reply = update.message.reply_text.call_args[0][0]
        assert "parcheggiare" in reply


@pytest.mark.asyncio
async def test_low_confidence_asks_clarification():
    profile = _make_profile()
    update = _make_update("Oggi ho incontrato un'azienda")
    with patch("handlers.free_message.classify_message", return_value=_classify_result("AMBIGUO", 0.5)), \
         patch("handlers.free_message.save_message"), \
         patch("handlers.free_message.get_recent_messages", return_value=[]), \
         patch("handlers.free_message.save_profile"), \
         patch("handlers.free_message.set_state") as mock_state:
        from handlers.free_message import handle_free_message
        await handle_free_message(update, MagicMock(), "uid", 12345, "Oggi ho incontrato un'azienda", profile)
        mock_state.assert_called_once_with("uid", "FREE_MSG_CORRECT_CAT")


# ── Conferma ✓ / ✗ ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirm_corretto_routes_to_parking():
    profile = _make_profile()
    profile.free_msg_pending = {"text": "Open day", "category": "IDEA"}
    update = _make_callback("✓ Corretto")
    with patch("handlers.free_message.save_profile"), \
         patch("handlers.free_message.clear_state"), \
         patch("handlers.parking.start_parking", new_callable=AsyncMock) as mock_park:
        from handlers.free_message import _confirm
        await _confirm(update, MagicMock(), "uid", 12345, "✓ Corretto", profile)
        mock_park.assert_called_once()
        assert profile.free_msg_pending is None


@pytest.mark.asyncio
async def test_confirm_non_e_questo_asks_category():
    profile = _make_profile()
    profile.free_msg_pending = {"text": "test", "category": "IDEA"}
    update = _make_callback("✗ Non è questo")
    with patch("handlers.free_message.set_state") as mock_state:
        from handlers.free_message import _confirm
        await _confirm(update, MagicMock(), "uid", 12345, "✗ Non è questo", profile)
        mock_state.assert_called_once_with("uid", "FREE_MSG_CORRECT_CAT")


# ── Correzione categoria ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_correct_category_blocco_routes_to_scenario_c():
    profile = _make_profile()
    profile.free_msg_pending = {"text": "Non riesco ad andare avanti", "category": "IDEA"}
    update = _make_callback("Ho un blocco")
    with patch("handlers.free_message.save_profile"), \
         patch("handlers.free_message.clear_state"), \
         patch("handlers.scenario_c.start_scenario_c", new_callable=AsyncMock) as mock_sc:
        from handlers.free_message import _correct_category
        await _correct_category(update, MagicMock(), "uid", 12345, "Ho un blocco", profile)
        mock_sc.assert_called_once()


@pytest.mark.asyncio
async def test_correct_category_aggiornamento_routes_to_update():
    profile = _make_profile()
    profile.free_msg_pending = {"text": "Ho finito la scaletta", "category": "IDEA"}
    update = _make_callback("Un aggiornamento")
    with patch("handlers.free_message.save_profile"), \
         patch("handlers.free_message.clear_state"), \
         patch("handlers.free_message.generate_response", return_value=("Bene.", False)), \
         patch("handlers.free_message.set_state") as mock_state, \
         patch("handlers.free_message.save_message"):
        from handlers.free_message import _correct_category
        await _correct_category(update, MagicMock(), "uid", 12345, "Un aggiornamento", profile)
        mock_state.assert_called_once_with("uid", "FREE_MSG_UPDATE_INT")


# ── UPDATE ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_uses_claude_and_asks_intention():
    profile = _make_profile()
    update = _make_update("Ho finito la scaletta del modulo 1")
    with patch("handlers.free_message.generate_response", return_value=("Ottimo.", False)), \
         patch("handlers.free_message.save_profile"), \
         patch("handlers.free_message.save_message"), \
         patch("handlers.free_message.set_state") as mock_state:
        from handlers.free_message import _handle_update
        await _handle_update(update, MagicMock(), "uid", 12345, "Ho finito la scaletta del modulo 1", profile)
        mock_state.assert_called_once_with("uid", "FREE_MSG_UPDATE_INT")
        reply = update.message.reply_text.call_args[0][0]
        assert "Ottimo." in reply


@pytest.mark.asyncio
async def test_update_intention_yes_goes_to_checkin_int():
    profile = _make_profile()
    profile.free_msg_pending = {"text": "update test", "category": "UPDATE"}
    update = _make_callback("Sì")
    with patch("handlers.free_message.save_profile"), \
         patch("handlers.free_message.clear_state"), \
         patch("handlers.free_message.set_state") as mock_state:
        from handlers.free_message import _update_intention
        await _update_intention(update, MagicMock(), "uid", 12345, "Sì", profile)
        mock_state.assert_called_once_with("uid", "CHECKIN_EVENING_INT_TEXT")


# ── DOMANDA ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_domanda_parcheggio_returns_count():
    profile = _make_profile()
    profile.parking_lot = [ParkingItem(content="Open day", category="NEGOZIO")]
    update = _make_update("Quante idee ho nel parcheggio?")
    from handlers.free_message import _handle_domanda
    await _handle_domanda(update, MagicMock(), "uid", 12345, "Quante idee ho nel parcheggio?", profile)
    reply = update.message.reply_text.call_args[0][0]
    assert "1" in reply
    assert "Open day" in reply


@pytest.mark.asyncio
async def test_domanda_obiettivi_returns_list():
    profile = _make_profile()
    update = _make_update("Quali sono i miei obiettivi?")
    from handlers.free_message import _handle_domanda
    await _handle_domanda(update, MagicMock(), "uid", 12345, "Quali sono i miei obiettivi?", profile)
    reply = update.message.reply_text.call_args[0][0]
    assert "Vendere negozio" in reply
    assert "Oltre la Bottega" in reply


@pytest.mark.asyncio
async def test_domanda_streak_returns_counter():
    profile = _make_profile()
    profile.streak_strategic = 5
    profile.counters.total_strategic_sessions = 12
    update = _make_update("Quante sessioni strategiche ho fatto?")
    from handlers.free_message import _handle_domanda
    await _handle_domanda(update, MagicMock(), "uid", 12345, "Quante sessioni strategiche ho fatto?", profile)
    reply = update.message.reply_text.call_args[0][0]
    assert "12" in reply


# ── FEEDBACK ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_feedback_asks_what_preferred():
    profile = _make_profile()
    update = _make_update("Quella risposta non era quello che intendevo")
    with patch("handlers.free_message.save_message"), \
         patch("handlers.free_message.set_state") as mock_state:
        from handlers.free_message import _handle_feedback
        await _handle_feedback(update, "uid", 12345, "Quella risposta non era quello che intendevo", profile)
        mock_state.assert_called_once_with("uid", "FREE_MSG_FEEDBACK_1")
        reply = update.message.reply_text.call_args[0][0]
        assert "preferito" in reply.lower()


@pytest.mark.asyncio
async def test_feedback_text_saves_and_thanks():
    profile = _make_profile()
    update = _make_update("Avrei preferito una domanda invece di una risposta")
    with patch("handlers.free_message.save_message") as mock_save, \
         patch("handlers.free_message.clear_state") as mock_clear:
        from handlers.free_message import _feedback_text
        await _feedback_text(update, MagicMock(), "uid", 12345, "Avrei preferito una domanda invece di una risposta", profile)
        mock_save.assert_called_once()
        mock_clear.assert_called_once_with("uid")
        reply = update.message.reply_text.call_args[0][0]
        assert "grazie" in reply.lower()
