import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models.user_profile import UserProfileData, Objective


def _make_profile(**kwargs) -> UserProfileData:
    defaults = dict(telegram_id=12345, user_context=None, onboarding_complete=False, onboarding_step=0)
    defaults.update(kwargs)
    return UserProfileData(**defaults)


def _make_update(text="ciao"):
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


# ── parse helpers ─────────────────────────────────────────────────────────────

def test_parse_hours_integer():
    from handlers.onboarding import _parse_hours
    assert _parse_hours("6 ore") == 6.0
    assert _parse_hours("circa 4") == 4.0


def test_parse_hours_decimal():
    from handlers.onboarding import _parse_hours
    assert _parse_hours("4,5") == 4.5
    assert _parse_hours("3.5 ore a settimana") == 3.5


def test_parse_hours_none():
    from handlers.onboarding import _parse_hours
    assert _parse_hours("non lo so ancora") is None


def test_parse_time_hhmm():
    from handlers.onboarding import _parse_time
    assert _parse_time("vorrei le 20:30") == "20:30"
    assert _parse_time("21.00") == "21:00"


def test_parse_time_hour_only():
    from handlers.onboarding import _parse_time
    assert _parse_time("preferirei le 22") == "22:00"


def test_parse_review():
    from handlers.onboarding import _parse_review
    day, time = _parse_review("sabato alle 17:00")
    assert day == "sabato"
    assert time == "17:00"


def test_parse_review_default():
    from handlers.onboarding import _parse_review
    day, time = _parse_review("domenica sera")
    assert day == "domenica"


# ── step transitions ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_step0_saves_name_and_asks_gender():
    profile = _make_profile()
    update = _make_update("Olga")
    with patch("handlers.onboarding.save_profile") as mock_save, \
         patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import _step0
        await _step0(update, MagicMock(), "uid", 12345, "Olga", profile)
        assert profile.user_name == "Olga"
        assert profile.onboarding_step == 0
        mock_save.assert_called_once()
        mock_state.assert_called_once_with("uid", "ONBOARDING_0B")


@pytest.mark.asyncio
async def test_step0b_saves_gender_and_advances():
    profile = _make_profile()
    profile.user_name = "Olga"
    update = _make_callback("Al femminile")
    with patch("handlers.onboarding.save_profile") as mock_save, \
         patch("handlers.onboarding.set_state") as mock_state, \
         patch("handlers.onboarding.generate_response", return_value=("Ciao Olga! Cosa fai?", False)):
        from handlers.onboarding import _step0b
        await _step0b(update, MagicMock(), "uid", 12345, "Al femminile", profile)
        assert profile.user_gender == "F"
        assert profile.onboarding_step == 1
        mock_state.assert_called_once_with("uid", "ONBOARDING_1")


@pytest.mark.asyncio
async def test_step1_saves_context_and_advances():
    profile = _make_profile()
    update = _make_update("Gestisco una bottega artigianale")
    with patch("handlers.onboarding.save_profile") as mock_save, \
         patch("handlers.onboarding.set_state") as mock_state, \
         patch("handlers.onboarding.generate_response", return_value=("Capisco. Qual è l'obiettivo più importante?", False)):
        from handlers.onboarding import _step1
        await _step1(update, MagicMock(), "uid", 12345, "Gestisco una bottega artigianale", profile)
        assert profile.user_context == "Gestisco una bottega artigianale"
        assert profile.onboarding_step == 2
        mock_save.assert_called_once()
        mock_state.assert_called_once_with("uid", "ONBOARDING_2")


@pytest.mark.asyncio
async def test_step2_saves_first_objective():
    profile = _make_profile()
    update = _make_update("Portare il negozio a livello premium")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state") as mock_state, \
         patch("handlers.onboarding.generate_response", return_value=("Obiettivo chiaro. Ce n'è un secondo?", False)):
        from handlers.onboarding import _step2
        await _step2(update, MagicMock(), "uid", 12345, "Portare il negozio a livello premium", profile)
        assert len(profile.objectives) == 1
        assert profile.objectives[0].rank == 1
        assert profile.objectives[0].title == "Portare il negozio a livello premium"
        mock_state.assert_called_once_with("uid", "ONBOARDING_2_MORE")


@pytest.mark.asyncio
async def test_step2_more_yes_goes_to_2b():
    profile = _make_profile(objectives=[Objective(title="Obj1", rank=1)])
    update = _make_callback("Sì")
    with patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import _step2_more
        await _step2_more(update, MagicMock(), "uid", 12345, "Sì", profile)
        mock_state.assert_called_once_with("uid", "ONBOARDING_2B")


@pytest.mark.asyncio
async def test_step2_more_no_goes_to_step4():
    profile = _make_profile(objectives=[Objective(title="Obj1", rank=1)])
    update = _make_callback("No, per ora è uno solo")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import _step2_more
        await _step2_more(update, MagicMock(), "uid", 12345, "No, per ora è uno solo", profile)
        mock_state.assert_called_once_with("uid", "ONBOARDING_4")


@pytest.mark.asyncio
async def test_step2b_more_no_asks_hours_for_obj2():
    profile = _make_profile(objectives=[
        Objective(title="Obj1", rank=1),
        Objective(title="Lanciare corso online", rank=2),
    ])
    update = _make_callback("No, è tutto")
    with patch("handlers.onboarding.set_state") as mock_state, \
         patch("handlers.onboarding._is_actionable_project", return_value=True):
        from handlers.onboarding import _step2b_more
        await _step2b_more(update, MagicMock(), "uid", 12345, "No, è tutto", profile)
        mock_state.assert_called_once_with("uid", "ONBOARDING_3")


@pytest.mark.asyncio
async def test_step3_saves_hours_and_goes_to_step4_if_no_obj3():
    profile = _make_profile(objectives=[
        Objective(title="Obj1", rank=1),
        Objective(title="Oltre la Bottega", rank=2),
    ])
    update = _make_update("6 ore a settimana")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import _step3
        await _step3(update, MagicMock(), "uid", 12345, "6 ore a settimana", profile)
        obj2 = next(o for o in profile.objectives if o.rank == 2)
        assert obj2.weekly_hours_target == 6.0
        mock_state.assert_called_once_with("uid", "ONBOARDING_4")


@pytest.mark.asyncio
async def test_step4_saves_anchor_and_asks_checkin_time():
    profile = _make_profile()
    update = _make_update("Casa a Marta e più tempo per me")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state") as mock_state, \
         patch("handlers.onboarding.generate_response", return_value=("Questo conta. A che ora il check-in?", False)):
        from handlers.onboarding import _step4
        await _step4(update, MagicMock(), "uid", 12345, "Casa a Marta e più tempo per me", profile)
        assert profile.motivation_anchor == "Casa a Marta e più tempo per me"
        mock_state.assert_called_once_with("uid", "ONBOARDING_5")


@pytest.mark.asyncio
async def test_step5_default_time_keeps_2130():
    profile = _make_profile()
    update = _make_callback("21:30 va bene")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import _step5
        await _step5(update, MagicMock(), "uid", 12345, "21:30 va bene", profile)
        assert profile.checkin_time_evening == "21:30"
        mock_state.assert_called_once_with("uid", "ONBOARDING_6")


@pytest.mark.asyncio
async def test_step5b_parses_custom_time():
    profile = _make_profile()
    update = _make_update("20:00")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock), \
         patch("handlers.onboarding.set_state_async", new_callable=AsyncMock):
        from handlers.onboarding import _step5b
        await _step5b(update, MagicMock(), "uid", 12345, "20:00", profile)
        assert profile.checkin_time_evening == "20:00"


@pytest.mark.asyncio
async def test_step7_completes_onboarding():
    profile = _make_profile(
        objectives=[Objective(title="Obj1", rank=1)],
        motivation_anchor="Casa a Marta",
        checkin_time_evening="21:30",
        review_day="domenica",
        review_time="18:00",
    )
    update = _make_callback("Sì, iniziamo")
    with patch("handlers.onboarding.save_profile") as mock_save, \
         patch("handlers.onboarding.clear_state") as mock_clear, \
         patch("handlers.onboarding.get_or_create_user", return_value={"id": "uuid-1"}), \
         patch("handlers.onboarding.supabase") as mock_sb:
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = {}
        from handlers.onboarding import _step7
        await _step7(update, MagicMock(), "uid", 12345, "Sì, iniziamo", profile)
        assert profile.onboarding_complete is True
        mock_clear.assert_called_once_with("uid")
        mock_save.assert_called_once()
