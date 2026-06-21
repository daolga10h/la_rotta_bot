import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from models.user_profile import UserProfileData, Objective, ReEngagement


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


def _make_callback(data):
    update = MagicMock()
    update.message = None
    update.callback_query.data = data
    update.callback_query.message.reply_text = AsyncMock()
    return update


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── check_and_send ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_message_if_no_last_response():
    profile = _make_profile()
    profile.re_engagement.last_response_at = None
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    with patch("handlers.re_engagement.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}), \
         patch("handlers.re_engagement.save_profile"):
        from handlers.re_engagement import check_and_send
        await check_and_send(12345, context)
        context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_no_message_if_recent_response():
    profile = _make_profile()
    profile.re_engagement.last_response_at = _now() - timedelta(days=1)
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    with patch("handlers.re_engagement.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}), \
         patch("handlers.re_engagement.save_profile"):
        from handlers.re_engagement import check_and_send
        await check_and_send(12345, context)
        context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_sends_day3_message_after_3_days():
    profile = _make_profile()
    profile.re_engagement.last_response_at = _now() - timedelta(days=3)
    profile.re_engagement.day3_message_sent = False
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    with patch("handlers.re_engagement.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}), \
         patch("handlers.re_engagement.save_profile"), \
         patch("handlers.re_engagement.set_state"):
        from handlers.re_engagement import check_and_send
        await check_and_send(12345, context)
        context.bot.send_message.assert_called_once()
        args = context.bot.send_message.call_args[1]
        assert "tre giorni" in args["text"]
        assert profile.re_engagement.day3_message_sent is True


@pytest.mark.asyncio
async def test_sends_day7_motivation_after_7_days():
    profile = _make_profile()
    profile.re_engagement.last_response_at = _now() - timedelta(days=7)
    profile.re_engagement.day3_message_sent = True
    profile.re_engagement.day7_message_sent = False
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    with patch("handlers.re_engagement.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}), \
         patch("handlers.re_engagement.save_profile"):
        from handlers.re_engagement import check_and_send
        await check_and_send(12345, context)
        context.bot.send_message.assert_called_once()
        args = context.bot.send_message.call_args[1]
        assert "Casa a Marta" in args["text"]
        assert profile.re_engagement.day7_message_sent is True


@pytest.mark.asyncio
async def test_no_double_day3():
    profile = _make_profile()
    profile.re_engagement.last_response_at = _now() - timedelta(days=4)
    profile.re_engagement.day3_message_sent = True  # già inviato
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    with patch("handlers.re_engagement.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}), \
         patch("handlers.re_engagement.save_profile"):
        from handlers.re_engagement import check_and_send
        await check_and_send(12345, context)
        context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_pause_active_blocks_messages():
    profile = _make_profile()
    profile.re_engagement.last_response_at = _now() - timedelta(days=5)
    profile.re_engagement.pause_until = _now() + timedelta(days=3)  # pausa ancora attiva
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    with patch("handlers.re_engagement.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}), \
         patch("handlers.re_engagement.save_profile"):
        from handlers.re_engagement import check_and_send
        await check_and_send(12345, context)
        context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_pause_expired_sends_return_message():
    profile = _make_profile()
    profile.re_engagement.pause_until = _now() - timedelta(hours=1)  # pausa scaduta
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    with patch("handlers.re_engagement.get_or_create_profile", return_value=profile), \
         patch("db.queries.get_or_create_user", return_value={"id": "uid"}), \
         patch("handlers.re_engagement.save_profile"), \
         patch("handlers.re_engagement.set_state"):
        from handlers.re_engagement import check_and_send
        await check_and_send(12345, context)
        context.bot.send_message.assert_called_once()
        args = context.bot.send_message.call_args[1]
        assert "7 giorni" in args["text"]
        assert profile.re_engagement.pause_until is None


# ── Day3 response ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_day3_si_torno_resets_and_closes():
    profile = _make_profile()
    profile.re_engagement.day3_message_sent = True
    update = _make_callback("Sì, torno")
    with patch("handlers.re_engagement.save_profile"), \
         patch("handlers.re_engagement.clear_state") as mock_clear:
        from handlers.re_engagement import _day3_response
        await _day3_response(update, MagicMock(), "uid", 12345, "Sì, torno", profile)
        assert profile.re_engagement.day3_message_sent is False
        mock_clear.assert_called_once_with("uid")
        reply = update.callback_query.message.reply_text.call_args[0][0]
        assert "bentornata" in reply.lower()


@pytest.mark.asyncio
async def test_day3_pausa_sets_pause_until():
    profile = _make_profile()
    update = _make_callback("Ho bisogno di una pausa")
    with patch("handlers.re_engagement.save_profile"), \
         patch("handlers.re_engagement.clear_state"):
        from handlers.re_engagement import _day3_response
        await _day3_response(update, MagicMock(), "uid", 12345, "Ho bisogno di una pausa", profile)
        assert profile.re_engagement.pause_until is not None
        # Pausa di circa 7 giorni
        delta = profile.re_engagement.pause_until - _now()
        assert 6 <= delta.days <= 7


# ── Pause end response ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pause_end_adesso_resets():
    profile = _make_profile()
    update = _make_callback("Adesso")
    with patch("handlers.re_engagement.save_profile"), \
         patch("handlers.re_engagement.clear_state") as mock_clear:
        from handlers.re_engagement import _pause_end_response
        await _pause_end_response(update, MagicMock(), "uid", 12345, "Adesso", profile)
        assert profile.re_engagement.day3_message_sent is False
        assert profile.re_engagement.last_response_at is not None
        mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_pause_end_fammi_scrivere_sets_silence():
    profile = _make_profile()
    update = _make_callback("Fammi scrivere io quando sono pronta")
    with patch("handlers.re_engagement.save_profile"), \
         patch("handlers.re_engagement.clear_state"):
        from handlers.re_engagement import _pause_end_response
        await _pause_end_response(update, MagicMock(), "uid", 12345, "Fammi scrivere io quando sono pronta", profile)
        assert profile.re_engagement.day7_message_sent is True  # silenzio totale


# ── Detect spontaneous return ─────────────────────────────────────────────────

def test_detect_spontaneous_return_true_when_day7_sent():
    profile = _make_profile()
    profile.re_engagement.day7_message_sent = True
    from handlers.re_engagement import _detect_spontaneous_return
    assert _detect_spontaneous_return(profile) is True


def test_detect_spontaneous_return_false_when_not_silent():
    profile = _make_profile()
    profile.re_engagement.day7_message_sent = False
    from handlers.re_engagement import _detect_spontaneous_return
    assert _detect_spontaneous_return(profile) is False


# ── Scheduler setup ───────────────────────────────────────────────────────────

def test_scheduler_parse_hm():
    from services.scheduler import _parse_hm
    assert _parse_hm("21:30") == (21, 30)
    assert _parse_hm("07:30") == (7, 30)


def test_scheduler_setup_user_jobs():
    from models.user_profile import UserProfileData, Objective
    profile = UserProfileData(
        telegram_id=12345,
        objectives=[Objective(title="Test", rank=1)],
        user_context="test",
        onboarding_complete=True,
        checkin_time_evening="21:30",
        checkin_time_morning="07:30",
        review_day="domenica",
        review_time="18:00",
    )
    mock_app = MagicMock()
    mock_jq = MagicMock()
    mock_app.job_queue = mock_jq
    mock_jq.jobs.return_value = []
    from services.scheduler import setup_user_jobs
    setup_user_jobs(mock_app, 12345, profile)
    assert mock_jq.run_daily.call_count == 5  # 5 job configurati
