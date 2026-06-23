"""
Test di robustezza per l'onboarding — copre tutte le modifiche recenti:
- Validazione input con domande di chiarimento
- Rilevamento errori di battitura
- Async-safety (nessun freeze)
- Rilevamento genere
- Rilevamento outcome vs progetto
- Correzioni in mid-flow
- Step7 resiliente agli errori dello scheduler
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from models.user_profile import UserProfileData, Objective


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_profile(**kwargs) -> UserProfileData:
    defaults = dict(
        telegram_id=12345,
        user_name="Olga",
        user_gender="F",
        objectives=[Objective(title="Vendere negozio", rank=1)],
        motivation_anchor="Casa a Marta",
        user_context="Bottega artigianale",
        onboarding_complete=False,
    )
    defaults.update(kwargs)
    return UserProfileData(**defaults)


def _msg(text=""):
    u = MagicMock()
    u.message.reply_text = AsyncMock()
    u.message.text = text
    u.callback_query = None
    return u


def _cb(data):
    u = MagicMock()
    u.message = None
    u.callback_query.data = data
    u.callback_query.message.reply_text = AsyncMock()
    return u


def _last_reply(update):
    """Testo dell'ultimo reply_text chiamato (message o callback)."""
    if update.message:
        return update.message.reply_text.call_args[0][0]
    return update.callback_query.message.reply_text.call_args[0][0]


# ── _parse_time ───────────────────────────────────────────────────────────────

def test_parse_time_hhmm():
    from handlers.onboarding import _parse_time
    assert _parse_time("22:30") == "22:30"
    assert _parse_time("9.00") == "09:00"
    assert _parse_time("alle 20:00") == "20:00"


def test_parse_time_hour_only():
    from handlers.onboarding import _parse_time
    assert _parse_time("20") == "20:00"
    assert _parse_time("vorrei le 22") == "22:00"


def test_parse_time_unrecognizable_returns_default():
    from handlers.onboarding import _parse_time
    assert _parse_time("sera") == "21:30"
    assert _parse_time("220") == "21:30"   # il typo che causava il freeze
    assert _parse_time("duecento") == "21:30"


# ── _parse_hours ──────────────────────────────────────────────────────────────

def test_parse_hours_various():
    from handlers.onboarding import _parse_hours
    assert _parse_hours("6 ore") == 6.0
    assert _parse_hours("circa 4") == 4.0
    assert _parse_hours("4,5") == 4.5
    assert _parse_hours("3.5 ore a settimana") == 3.5


def test_parse_hours_returns_none_on_text():
    from handlers.onboarding import _parse_hours
    assert _parse_hours("non lo so ancora") is None
    assert _parse_hours("qualcosa") is None
    assert _parse_hours("una sessione") is None


# ── _is_yes ───────────────────────────────────────────────────────────────────

def test_is_yes_variants():
    from handlers.onboarding import _is_yes
    assert _is_yes("Sì, iniziamo") is True
    assert _is_yes("Si, iniziamo") is True      # senza accento
    assert _is_yes("sì") is True
    assert _is_yes("si") is True
    assert _is_yes("iniziamo") is True


def test_is_yes_false():
    from handlers.onboarding import _is_yes
    assert _is_yes("No") is False
    assert _is_yes("Voglio correggere qualcosa") is False
    assert _is_yes("forse") is False


# ── Rilevamento genere ────────────────────────────────────────────────────────

def test_infer_gender_female():
    from handlers.onboarding import _infer_gender
    assert _infer_gender("Olga") == "F"
    assert _infer_gender("Marina") == "F"
    assert _infer_gender("Marta") == "F"


def test_infer_gender_male():
    from handlers.onboarding import _infer_gender
    assert _infer_gender("Lorenzo") == "M"
    assert _infer_gender("Marco") == "M"
    assert _infer_gender("Vasco") == "M"


def test_infer_gender_non_italian():
    from handlers.onboarding import _infer_gender
    # Nomi non italiani: fallback euristica senza crash
    result = _infer_gender("Machelle")
    assert result in ("M", "F")  # non crasha


def test_extract_name_from_mi_chiamo():
    from handlers.onboarding import _extract_name_from_text
    assert _extract_name_from_text("mi chiamo Olga") == "Olga"
    assert _extract_name_from_text("Mi chiamo Lorenzo") == "Lorenzo"
    assert _extract_name_from_text("sono Marta") == "Marta"


def test_extract_name_returns_none_on_plain_name():
    from handlers.onboarding import _extract_name_from_text
    assert _extract_name_from_text("Olga") is None


# ── Rilevamento correzione ────────────────────────────────────────────────────

def test_correction_detected():
    from handlers.onboarding import _is_correction_request
    assert _is_correction_request("ho sbagliato") is True
    assert _is_correction_request("scusa") is True
    assert _is_correction_request("il nome è errato") is True
    assert _is_correction_request("è sbagliato") is True
    assert _is_correction_request("mi chiamo Lorenzo") is True  # contiene "mi chiamo"
    assert _is_correction_request("aspetta ho scritto male") is True


def test_correction_not_detected_on_normal_input():
    from handlers.onboarding import _is_correction_request
    assert _is_correction_request("220") is False
    assert _is_correction_request("gestisco un'officina") is False
    assert _is_correction_request("vorrei avere più tempo") is False
    assert _is_correction_request("Sì, iniziamo") is False


def test_correction_target_nome():
    from handlers.onboarding import _correction_target
    assert _correction_target("il nome è errato") == "nome"
    assert _correction_target("mi chiamo Lorenzo") == "nome"
    assert _correction_target("ho sbagliato nome") == "nome"


def test_correction_target_obiettivi():
    from handlers.onboarding import _correction_target
    assert _correction_target("gli obiettivi sono sbagliati") == "obiettivi"


# ── Step 0: nome vuoto ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_step0_empty_input_asks_again():
    profile = _make_profile()
    update = _msg("   ")  # solo spazi
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state"):
        from handlers.onboarding import _step0
        await _step0(update, MagicMock(), "uid", 12345, "   ", profile)
        reply = _last_reply(update)
        assert "chiami" in reply.lower()  # chiede di nuovo il nome


@pytest.mark.asyncio
async def test_step0_mi_chiamo_extracts_correctly():
    profile = _make_profile()
    update = _msg("mi chiamo Machelle")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state"):
        from handlers.onboarding import _step0
        await _step0(update, MagicMock(), "uid", 12345, "mi chiamo Machelle", profile)
        assert profile.user_name == "Machelle"


# ── Step 3: ore — nessun numero trovato ──────────────────────────────────────

@pytest.mark.asyncio
async def test_step3_no_number_asks_clarification():
    profile = _make_profile(objectives=[
        Objective(title="Vendere negozio", rank=1),
        Objective(title="Oltre la Bottega", rank=2),
    ])
    update = _msg("non lo so, qualcosa")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock), \
         patch("handlers.onboarding.set_state_async", new_callable=AsyncMock):
        from handlers.onboarding import _step3
        await _step3(update, MagicMock(), "uid", 12345, "non lo so, qualcosa", profile)
        reply = _last_reply(update)
        assert "numero" in reply.lower() or "ore" in reply.lower()
        # Stato NON avanza — aspetta ancora una risposta valida
        obj2 = next(o for o in profile.objectives if o.rank == 2)
        assert obj2.weekly_hours_target is None


@pytest.mark.asyncio
async def test_step3_valid_number_saves_and_advances():
    profile = _make_profile(objectives=[
        Objective(title="Vendere negozio", rank=1),
        Objective(title="Oltre la Bottega", rank=2),
    ])
    update = _msg("6 ore a settimana")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock) as mock_save, \
         patch("handlers.onboarding._go_to_hours_or_anchor", new_callable=AsyncMock) as mock_go:
        from handlers.onboarding import _step3
        await _step3(update, MagicMock(), "uid", 12345, "6 ore a settimana", profile)
        obj2 = next(o for o in profile.objectives if o.rank == 2)
        assert obj2.weekly_hours_target == 6.0
        mock_save.assert_called_once()
        mock_go.assert_called_once()


# ── Step 5b: orario non riconoscibile ────────────────────────────────────────

@pytest.mark.asyncio
async def test_step5b_typo_220_asks_again():
    profile = _make_profile()
    update = _msg("220")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock), \
         patch("handlers.onboarding.set_state_async", new_callable=AsyncMock):
        from handlers.onboarding import _step5b
        await _step5b(update, MagicMock(), "uid", 12345, "220", profile)
        reply = _last_reply(update)
        assert "orario" in reply.lower() or "22:00" in reply or "capito" in reply.lower()


@pytest.mark.asyncio
async def test_step5b_valid_time_saves():
    profile = _make_profile()
    update = _msg("20:00")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock) as mock_save, \
         patch("handlers.onboarding.set_state_async", new_callable=AsyncMock):
        from handlers.onboarding import _step5b
        await _step5b(update, MagicMock(), "uid", 12345, "20:00", profile)
        assert profile.checkin_time_evening == "20:00"
        mock_save.assert_called_once()


# ── Step 6b: giorno e ora ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_step6b_neither_day_nor_time_asks_both():
    profile = _make_profile()
    update = _msg("boh quando vuoi tu")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock):
        from handlers.onboarding import _step6b
        await _step6b(update, MagicMock(), "uid", 12345, "boh quando vuoi tu", profile)
        reply = _last_reply(update)
        assert "giorno" in reply.lower() or "ora" in reply.lower()


@pytest.mark.asyncio
async def test_step6b_day_only_asks_time():
    profile = _make_profile()
    update = _msg("domenica")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock):
        from handlers.onboarding import _step6b
        await _step6b(update, MagicMock(), "uid", 12345, "domenica", profile)
        reply = _last_reply(update)
        assert "ora" in reply.lower() or "17:00" in reply or "domenica" in reply


@pytest.mark.asyncio
async def test_step6b_time_only_asks_day():
    profile = _make_profile()
    update = _msg("alle 17:00")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock):
        from handlers.onboarding import _step6b
        await _step6b(update, MagicMock(), "uid", 12345, "alle 17:00", profile)
        reply = _last_reply(update)
        assert "giorno" in reply.lower()


@pytest.mark.asyncio
async def test_step6b_complete_saves_and_shows_summary():
    profile = _make_profile()
    update = _msg("sabato 17:00")
    with patch("handlers.onboarding.save_profile_async", new_callable=AsyncMock) as mock_save, \
         patch("handlers.onboarding.set_state_async", new_callable=AsyncMock) as mock_state:
        from handlers.onboarding import _step6b
        await _step6b(update, MagicMock(), "uid", 12345, "sabato 17:00", profile)
        assert profile.review_day == "sabato"
        assert profile.review_time == "17:00"
        mock_save.assert_called_once()
        mock_state.assert_called_once_with("uid", "ONBOARDING_7")


# ── Step 7: resilienza scheduler ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_step7_completes_even_if_scheduler_crashes():
    profile = _make_profile(
        objectives=[Objective(title="Obj1", rank=1)],
        motivation_anchor="Casa a Marta",
        checkin_time_evening="21:30",
        review_day="domenica",
        review_time="18:00",
        user_name="Olga",
    )
    update = _cb("Sì, iniziamo")
    with patch("handlers.onboarding.save_profile") as mock_save, \
         patch("handlers.onboarding.clear_state") as mock_clear, \
         patch("handlers.onboarding.get_or_create_user", return_value={"id": "uuid-1"}), \
         patch("handlers.onboarding.supabase") as mock_sb, \
         patch("services.scheduler.setup_user_jobs", side_effect=Exception("scheduler crash")):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = {}
        from handlers.onboarding import _step7
        await _step7(update, MagicMock(spec=["application"]), "uid", 12345, "Sì, iniziamo", profile)
        assert profile.onboarding_complete is True
        mock_save.assert_called_once()
        mock_clear.assert_called_once_with("uid")
        update.callback_query.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_step7_reply_arrives_before_clear_state():
    """clear_state deve essere chiamato DOPO reply, non prima."""
    profile = _make_profile(
        objectives=[Objective(title="Obj1", rank=1)],
        motivation_anchor="test",
        checkin_time_evening="21:30",
        review_day="domenica",
        review_time="18:00",
        user_name="Olga",
    )
    call_order = []
    update = _cb("Sì, iniziamo")

    async def fake_reply(text, **kw):
        call_order.append("reply")

    update.callback_query.message.reply_text = fake_reply

    def fake_clear(uid):
        call_order.append("clear")

    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.clear_state", side_effect=fake_clear), \
         patch("handlers.onboarding.get_or_create_user", return_value={"id": "uuid-1"}), \
         patch("handlers.onboarding.supabase") as mock_sb, \
         patch("services.scheduler.setup_user_jobs"):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = {}
        from handlers.onboarding import _step7
        await _step7(update, MagicMock(spec=["application"]), "uid", 12345, "Sì, iniziamo", profile)

    assert call_order == ["reply", "clear"], f"Ordine errato: {call_order}"


# ── Outcome vs progetto ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_outcome_keywords_no_hours_question():
    """Obiettivi outcome → _go_to_hours_or_anchor va a ONBOARDING_4 (motivazione)."""
    outcomes = [
        "avere più tempo libero",
        "vorrei andare al concerto di vasco",
        "mettere da parte i soldi per un viaggio",
        "guadagnare di più",
        "avere piá tempo libero",  # typo con accento sbagliato
    ]
    from handlers.onboarding import _is_actionable_project
    profile = _make_profile()
    for text in outcomes:
        result = await _is_actionable_project(text, profile)
        assert result is False, f"'{text}' classificato come project — dovrebbe essere outcome"


@pytest.mark.asyncio
async def test_project_keywords_asks_hours():
    """Obiettivi progetto → _is_actionable_project restituisce True."""
    projects = [
        "lanciare un corso online",
        "costruire un e-commerce",
        "sviluppare il sito web",
        "creare il primo modulo del corso",
    ]
    from handlers.onboarding import _is_actionable_project
    profile = _make_profile()
    for text in projects:
        result = await _is_actionable_project(text, profile)
        assert result is True, f"'{text}' classificato come outcome — dovrebbe essere project"


# ── generate_response: risposta vuota ────────────────────────────────────────

def test_generate_response_empty_content_returns_fallback():
    """Claude restituisce content vuoto → fallback, non crash IndexError."""
    import anthropic
    from models.user_profile import UserProfileData, Objective

    profile = UserProfileData(
        telegram_id=12345,
        objectives=[Objective(title="Test", rank=1)],
        user_context="test",
    )
    mock_response = MagicMock()
    mock_response.content = []  # content vuoto → causerebbe IndexError

    with patch("services.response_generator._client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        from services.response_generator import generate_response
        text, is_fallback = generate_response(
            profile=profile,
            flow_name="TEST",
            flow_instructions="test",
            session_messages=[{"role": "user", "content": "test"}],
        )
        assert is_fallback is True
        assert text  # non è stringa vuota


# ── Correzione in mid-flow ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_correction_nome_in_step1_goes_back_to_step0():
    """'ho sbagliato nome' durante step 1 → torna a ONBOARDING_0."""
    profile = _make_profile(user_name="Olgs", onboarding_step=1)
    update = _msg("ho sbagliato nome")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import handle_step
        await handle_step(update, MagicMock(), "uid", 12345, "ONBOARDING_1", "ho sbagliato nome", profile)
        mock_state.assert_called_with("uid", "ONBOARDING_0")


@pytest.mark.asyncio
async def test_mi_chiamo_in_step1_updates_name():
    """'mi chiamo Olga' durante step 1 → estrae nome e va avanti."""
    profile = _make_profile(user_name="Olgs", onboarding_step=1)
    update = _msg("mi chiamo Olga")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import handle_step
        await handle_step(update, MagicMock(), "uid", 12345, "ONBOARDING_1", "mi chiamo Olga", profile)
        assert profile.user_name == "Olga"
        mock_state.assert_called_with("uid", "ONBOARDING_1")


@pytest.mark.asyncio
async def test_correction_not_triggered_in_onboarding0():
    """In ONBOARDING_0, 'mi chiamo X' è risposta normale — non correzione."""
    profile = _make_profile(user_name=None, onboarding_step=0)
    update = _msg("mi chiamo Olga")
    with patch("handlers.onboarding.save_profile"), \
         patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import handle_step
        await handle_step(update, MagicMock(), "uid", 12345, "ONBOARDING_0", "mi chiamo Olga", profile)
        # Deve andare a ONBOARDING_0B (step nome), non a correzione
        mock_state.assert_called_with("uid", "ONBOARDING_0B")


@pytest.mark.asyncio
async def test_correction_shows_menu_when_unspecific():
    """'ho sbagliato' senza specificare cosa → mostra menu correzione."""
    profile = _make_profile(onboarding_step=4)
    update = _msg("ho sbagliato")
    with patch("handlers.onboarding.set_state") as mock_state:
        from handlers.onboarding import handle_step
        await handle_step(update, MagicMock(), "uid", 12345, "ONBOARDING_4", "ho sbagliato", profile)
        mock_state.assert_called_with("uid", "ONBOARDING_CORRECT")
