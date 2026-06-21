import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from models.user_profile import UserProfileData, Objective, UnlockEntry


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


# ── start_scenario_c ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_without_library_goes_to_classify():
    profile = _make_profile()
    update = _make_callback("Non ho voglia / ho dubbi")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import start_scenario_c
        await start_scenario_c(update, MagicMock(), "uid", 12345, profile)
        mock_state.assert_called_once_with("uid", "SCENARIO_C_CLASSIFY")


@pytest.mark.asyncio
async def test_start_with_library_shows_unlock():
    profile = _make_profile()
    profile.unlock_library = [UnlockEntry(insight="Ce la faccio", context="paura")]
    update = _make_callback("Non ho voglia / ho dubbi")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import start_scenario_c
        await start_scenario_c(update, MagicMock(), "uid", 12345, profile)
        mock_state.assert_called_once_with("uid", "SCENARIO_C_UNLOCK")
        reply = update.callback_query.message.reply_text.call_args[0][0]
        assert "Ce la faccio" in reply


# ── Branch stanchezza ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_classify_stanchezza_goes_to_intention():
    profile = _make_profile()
    profile.scenario_c_data = {}
    update = _make_callback("Stanchezza fisica — il corpo non ce la fa")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _classify
        await _classify(update, MagicMock(), "uid", 12345, "Stanchezza fisica — il corpo non ce la fa", profile)
        assert profile.scenario_c_data["branch"] == "stanchezza"
        mock_state.assert_called_once_with("uid", "SCENARIO_C_STANCHEZZA_INT")


@pytest.mark.asyncio
async def test_stanchezza_intention_saves_and_asks_anchor():
    profile = _make_profile()
    profile.scenario_c_data = {"branch": "stanchezza"}
    update = _make_update("Mandare 3 email")
    with patch("handlers.scenario_c.save_profile") as mock_save, \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _stanchezza_intention
        await _stanchezza_intention(update, MagicMock(), "uid", 12345, "Mandare 3 email", profile)
        assert profile.last_intention_declared is not None
        assert profile.last_intention_declared.text == "Mandare 3 email"
        mock_state.assert_called_once_with("uid", "SCENARIO_C_STANCHEZZA_ANCHOR")


@pytest.mark.asyncio
async def test_stanchezza_anchor_yes_shows_motivation():
    profile = _make_profile(motivation_anchor="Casa a Marta")
    profile.scenario_c_data = {"branch": "stanchezza"}
    update = _make_callback("Sì")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _stanchezza_anchor
        await _stanchezza_anchor(update, MagicMock(), "uid", 12345, "Sì", profile)
        reply = update.callback_query.message.reply_text.call_args_list[0][0][0]
        assert "Casa a Marta" in reply
        # Then offers toolkit
        mock_state.assert_called_once_with("uid", "SCENARIO_C_TOOLKIT")


# ── Branch paura ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_classify_paura_goes_to_paura_1():
    profile = _make_profile()
    profile.scenario_c_data = {}
    update = _make_callback("Paura — c'è qualcosa di specifico che mi spaventa")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _classify
        await _classify(update, MagicMock(), "uid", 12345, "Paura — c'è qualcosa di specifico che mi spaventa", profile)
        assert profile.scenario_c_data["branch"] == "paura"
        mock_state.assert_called_once_with("uid", "SCENARIO_C_PAURA_1")


@pytest.mark.asyncio
async def test_paura_1_saves_and_goes_to_2():
    profile = _make_profile()
    profile.scenario_c_data = {"branch": "paura"}
    update = _make_update("Ho paura di fallire")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _paura_1
        await _paura_1(update, MagicMock(), "uid", 12345, "Ho paura di fallire", profile)
        assert profile.scenario_c_data["paura_1"] == "Ho paura di fallire"
        mock_state.assert_called_once_with("uid", "SCENARIO_C_PAURA_2")


@pytest.mark.asyncio
async def test_paura_3_asks_to_save():
    profile = _make_profile()
    profile.scenario_c_data = {"branch": "paura", "paura_1": "x", "paura_2": "y"}
    update = _make_update("Direi di andare avanti un passo alla volta")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _paura_3
        await _paura_3(update, MagicMock(), "uid", 12345, "Direi di andare avanti un passo alla volta", profile)
        assert profile.scenario_c_data["paura_3"] == "Direi di andare avanti un passo alla volta"
        mock_state.assert_called_once_with("uid", "SCENARIO_C_PAURA_SAVE")


@pytest.mark.asyncio
async def test_paura_save_yes_adds_to_library():
    profile = _make_profile()
    profile.scenario_c_data = {"branch": "paura", "paura_3": "Un passo alla volta"}
    update = _make_callback("Sì, salvala")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state"):
        from handlers.scenario_c import _paura_save
        await _paura_save(update, MagicMock(), "uid", 12345, "Sì, salvala", profile)
        assert len(profile.unlock_library) == 1
        assert profile.unlock_library[0].insight == "Un passo alla volta"
        assert profile.unlock_library[0].context == "paura"


@pytest.mark.asyncio
async def test_paura_save_no_skips_library():
    profile = _make_profile()
    profile.scenario_c_data = {"branch": "paura", "paura_3": "risposta"}
    update = _make_callback("No")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state"):
        from handlers.scenario_c import _paura_save
        await _paura_save(update, MagicMock(), "uid", 12345, "No", profile)
        assert len(profile.unlock_library) == 0


# ── Branch confusione ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_classify_confusione_goes_to_confusione_1():
    profile = _make_profile()
    profile.scenario_c_data = {}
    update = _make_callback("Confusione — non so da dove iniziare")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _classify
        await _classify(update, MagicMock(), "uid", 12345, "Confusione — non so da dove iniziare", profile)
        assert profile.scenario_c_data["branch"] == "confusione"
        mock_state.assert_called_once_with("uid", "SCENARIO_C_CONFUSIONE_1")


@pytest.mark.asyncio
async def test_confusione_1_saves_and_asks_step():
    profile = _make_profile()
    profile.scenario_c_data = {"branch": "confusione"}
    update = _make_update("So che devo aggiornare il listino prezzi")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _confusione_1
        await _confusione_1(update, MagicMock(), "uid", 12345, "So che devo aggiornare il listino prezzi", profile)
        assert profile.scenario_c_data["confusione_1"] == "So che devo aggiornare il listino prezzi"
        mock_state.assert_called_once_with("uid", "SCENARIO_C_CONFUSIONE_INT")


@pytest.mark.asyncio
async def test_confusione_intention_saves_and_offers_toolkit():
    profile = _make_profile()
    profile.scenario_c_data = {"branch": "confusione"}
    update = _make_update("Aggiornare il listino per 20 minuti")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _confusione_intention
        await _confusione_intention(update, MagicMock(), "uid", 12345, "Aggiornare il listino per 20 minuti", profile)
        assert profile.last_intention_declared.text == "Aggiornare il listino per 20 minuti"
        mock_state.assert_called_once_with("uid", "SCENARIO_C_TOOLKIT")


# ── Toolkit ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_toolkit_yes_shows_technique():
    profile = _make_profile()
    profile.scenario_c_data = {"toolkit_branch": "confusione"}
    update = _make_callback("Sì, mostrami")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.set_state") as mock_state:
        from handlers.scenario_c import _toolkit_response
        await _toolkit_response(update, MagicMock(), "uid", 12345, "Sì, mostrami", profile)
        mock_state.assert_called_once_with("uid", "SCENARIO_C_TOOLKIT_DONE")
        reply = update.callback_query.message.reply_text.call_args[0][0]
        assert "5%" in reply or "non ancora" in reply.lower() or "respiro" in reply.lower()


@pytest.mark.asyncio
async def test_toolkit_no_closes():
    profile = _make_profile()
    profile.scenario_c_data = {"toolkit_branch": "stanchezza"}
    update = _make_callback("No grazie")
    with patch("handlers.scenario_c.save_profile"), \
         patch("handlers.scenario_c.clear_state") as mock_clear:
        from handlers.scenario_c import _toolkit_response
        await _toolkit_response(update, MagicMock(), "uid", 12345, "No grazie", profile)
        mock_clear.assert_called_once_with("uid")
        assert profile.scenario_c_data is None
