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


def _parking_item(content="Test idea", category="NEGOZIO") -> ParkingItem:
    return ParkingItem(content=content, category=category)


# ── start_parking ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_parking_from_button_asks_idea():
    profile = _make_profile()
    update = _make_callback("Sì, ho un'idea")
    with patch("handlers.parking.set_state") as mock_state:
        from handlers.parking import start_parking
        await start_parking(update, MagicMock(), "uid", 12345, "Sì, ho un'idea", profile)
        mock_state.assert_called_once_with("uid", "PARKING_CAPTURE")


@pytest.mark.asyncio
async def test_start_parking_from_free_message_classifies():
    profile = _make_profile()
    update = _make_update("Ho pensato di fare un open day tematico")
    with patch("handlers.parking.classify_parking_category", return_value="NEGOZIO"), \
         patch("handlers.parking.save_profile"), \
         patch("handlers.parking.set_state") as mock_state:
        from handlers.parking import start_parking
        await start_parking(update, MagicMock(), "uid", 12345, "Ho pensato di fare un open day tematico", profile)
        mock_state.assert_called_once_with("uid", "PARKING_1")


# ── Conferma categoria ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirm_correct_saves_idea():
    profile = _make_profile()
    profile.parking_pending = {"text": "Open day", "category": "NEGOZIO"}
    update = _make_callback("✓ Corretto")
    with patch("handlers.parking.save_profile") as mock_save, \
         patch("handlers.parking.set_state") as mock_state:
        from handlers.parking import _confirm
        await _confirm(update, MagicMock(), "uid", 12345, "✓ Corretto", profile)
        assert len(profile.parking_lot) == 1
        assert profile.parking_lot[0].content == "Open day"
        assert profile.parking_lot[0].category == "NEGOZIO"
        assert profile.parking_pending is None
        mock_state.assert_called_once_with("uid", "PARKING_REDIRECT")


@pytest.mark.asyncio
async def test_confirm_incorrect_asks_category():
    profile = _make_profile()
    profile.parking_pending = {"text": "Open day", "category": "NEGOZIO"}
    update = _make_callback("✗ Non è questo")
    with patch("handlers.parking.set_state") as mock_state:
        from handlers.parking import _confirm
        await _confirm(update, MagicMock(), "uid", 12345, "✗ Non è questo", profile)
        mock_state.assert_called_once_with("uid", "PARKING_CORRECT")


@pytest.mark.asyncio
async def test_correct_category_negozio():
    profile = _make_profile()
    profile.parking_pending = {"text": "Open day", "category": "OLTRE_LA_BOTTEGA"}
    update = _make_callback("Per il Negozio")
    with patch("handlers.parking.save_profile") as mock_save, \
         patch("handlers.parking.set_state"):
        from handlers.parking import _correct_category
        await _correct_category(update, MagicMock(), "uid", 12345, "Per il Negozio", profile)
        assert profile.parking_lot[0].category == "NEGOZIO"


@pytest.mark.asyncio
async def test_correct_category_oltre_la_bottega():
    profile = _make_profile()
    profile.parking_pending = {"text": "Corso online", "category": "NEGOZIO"}
    update = _make_callback("Per Oltre la Bottega")
    with patch("handlers.parking.save_profile"), \
         patch("handlers.parking.set_state"):
        from handlers.parking import _correct_category
        await _correct_category(update, MagicMock(), "uid", 12345, "Per Oltre la Bottega", profile)
        assert profile.parking_lot[0].category == "OLTRE_LA_BOTTEGA"


# ── Redirect post-parcheggio ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_redirect_no_closes():
    profile = _make_profile()
    update = _make_callback("No, grazie")
    with patch("handlers.parking.clear_state") as mock_clear:
        from handlers.parking import _redirect
        await _redirect(update, MagicMock(), "uid", 12345, "No, grazie", profile)
        mock_clear.assert_called_once_with("uid")


@pytest.mark.asyncio
async def test_redirect_si_asks_what():
    profile = _make_profile()
    update = _make_callback("Sì, torno a qualcosa")
    with patch("handlers.parking.clear_state"):
        from handlers.parking import _redirect
        await _redirect(update, MagicMock(), "uid", 12345, "Sì, torno a qualcosa", profile)
        reply = update.callback_query.message.reply_text.call_args[0][0]
        assert "vuoi tornare" in reply.lower() or "cosa" in reply.lower()


# ── Parking pieno ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parking_full_shows_remove_buttons():
    profile = _make_profile()
    profile.parking_lot = [_parking_item(f"Idea {i}") for i in range(10)]
    update = _make_update("Nuova idea numero 11")
    with patch("handlers.parking.classify_parking_category", return_value="NEGOZIO"), \
         patch("handlers.parking.save_profile"), \
         patch("handlers.parking.set_state"):
        from handlers.parking import start_parking
        await start_parking(update, MagicMock(), "uid", 12345, "Nuova idea numero 11", profile)
        reply_text = update.message.reply_text.call_args[0][0]
        assert "10" in reply_text


# ── Contatori ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_idea_increments_counter():
    profile = _make_profile()
    profile.parking_pending = {"text": "Open day", "category": "NEGOZIO"}
    assert profile.counters.total_ideas_parked == 0
    update = _make_callback("✓ Corretto")
    with patch("handlers.parking.save_profile"), \
         patch("handlers.parking.set_state"):
        from handlers.parking import _confirm
        await _confirm(update, MagicMock(), "uid", 12345, "✓ Corretto", profile)
        assert profile.counters.total_ideas_parked == 1


# ── Rimozione idea ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remove_idea_marks_as_deleted():
    profile = _make_profile()
    item = _parking_item("Idea da rimuovere")
    profile.parking_lot = [item]
    profile.parking_pending = {"text": "Nuova idea", "category": "NEGOZIO"}
    update = _make_callback(f"REMOVE_{item.id}")
    with patch("handlers.parking.save_profile"), \
         patch("handlers.parking.set_state"):
        from handlers.parking import _remove_idea
        await _remove_idea(update, "uid", 12345, f"REMOVE_{item.id}", profile)
        removed = next(p for p in profile.parking_lot if p.id == item.id)
        assert removed.status == "deleted"
