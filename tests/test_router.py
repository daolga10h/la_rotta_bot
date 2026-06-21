import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models.user_profile import UserProfileData, Objective

PROFILE_COMPLETE = UserProfileData(
    telegram_id=12345,
    objectives=[Objective(title="Vendere negozio", rank=1)],
    motivation_anchor="Casa a Marta",
    user_context="Bottega",
    onboarding_complete=True,
)

PROFILE_INCOMPLETE = UserProfileData(
    telegram_id=12345,
    user_context="Bottega",
    onboarding_complete=False,
    onboarding_step=2,
)


def _make_update(text="ciao"):
    update = MagicMock()
    update.effective_user.id = 12345
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.callback_query = None
    return update


def _make_callback(data="Sì"):
    update = MagicMock()
    update.effective_user.id = 12345
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.message = None
    return update


@pytest.mark.asyncio
async def test_route_idle_to_free_message():
    update = _make_update("Ho un'idea nuova")
    with patch("utils.router.get_or_create_user", return_value={"id": "uuid-1", "telegram_id": 12345}), \
         patch("utils.router.get_state", return_value="IDLE"), \
         patch("services.memory.get_or_create_profile", return_value=PROFILE_COMPLETE), \
         patch("handlers.free_message.handle_free_message", new_callable=AsyncMock) as mock_free:
        from utils.router import handle_message
        context = MagicMock()
        await handle_message(update, context)
        mock_free.assert_called_once()


@pytest.mark.asyncio
async def test_route_onboarding_state_to_onboarding_handler():
    update = _make_update("Sono un'imprenditrice")
    with patch("utils.router.get_or_create_user", return_value={"id": "uuid-1", "telegram_id": 12345}), \
         patch("utils.router.get_state", return_value="ONBOARDING_2"), \
         patch("services.memory.get_or_create_profile", return_value=PROFILE_COMPLETE), \
         patch("handlers.onboarding.handle_step", new_callable=AsyncMock) as mock_ob:
        from utils.router import handle_message
        context = MagicMock()
        await handle_message(update, context)
        mock_ob.assert_called_once()


@pytest.mark.asyncio
async def test_route_checkin_evening_state():
    update = _make_update("Ho lavorato sull'operativo")
    with patch("utils.router.get_or_create_user", return_value={"id": "uuid-1", "telegram_id": 12345}), \
         patch("utils.router.get_state", return_value="CHECKIN_EVENING_A_1"), \
         patch("services.memory.get_or_create_profile", return_value=PROFILE_COMPLETE), \
         patch("handlers.checkin_evening.handle_step", new_callable=AsyncMock) as mock_ev:
        from utils.router import handle_message
        context = MagicMock()
        await handle_message(update, context)
        mock_ev.assert_called_once()


@pytest.mark.asyncio
async def test_route_incomplete_onboarding_redirects():
    update = _make_update("ciao")
    with patch("utils.router.get_or_create_user", return_value={"id": "uuid-1", "telegram_id": 12345}), \
         patch("utils.router.get_state", return_value="IDLE"), \
         patch("services.memory.get_or_create_profile", return_value=PROFILE_INCOMPLETE), \
         patch("handlers.onboarding.resume_onboarding", new_callable=AsyncMock) as mock_resume:
        from utils.router import handle_message
        context = MagicMock()
        await handle_message(update, context)
        mock_resume.assert_called_once()


@pytest.mark.asyncio
async def test_callback_answers_query_and_routes():
    update = _make_callback("Ho lavorato sull'operativo")
    with patch("utils.router.get_or_create_user", return_value={"id": "uuid-1", "telegram_id": 12345}), \
         patch("utils.router.get_state", return_value="CHECKIN_EVENING_1"), \
         patch("services.memory.get_or_create_profile", return_value=PROFILE_COMPLETE), \
         patch("handlers.checkin_evening.handle_step", new_callable=AsyncMock):
        from utils.router import handle_callback
        context = MagicMock()
        await handle_callback(update, context)
        update.callback_query.answer.assert_called_once()
