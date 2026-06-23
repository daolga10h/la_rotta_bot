"""
Conversation simulation tests.
Run all scenarios in a single call:  pytest tests/test_flows.py -v
No Telegram or Supabase connection needed — all I/O is mocked.
"""
import pytest
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
from models.user_profile import UserProfileData, Objective


TEST_UID = "test-uuid"
TEST_TID = 12345
_HANDLERS = ("handlers.free_message", "handlers.parking", "handlers.scenario_c")


def _base_profile(**kwargs) -> UserProfileData:
    defaults = dict(
        telegram_id=TEST_TID,
        user_name="Olga",
        user_gender="F",
        user_context="Bottega artigianale",
        onboarding_complete=True,
        objectives=[
            Objective(title="Vendere il negozio", rank=1),
            Objective(title="Oltre la Bottega", rank=2, weekly_hours_target=6.0),
        ],
        motivation_anchor="Casa a Marta",
    )
    defaults.update(kwargs)
    return UserProfileData(**defaults)


def _make_update(text: str) -> MagicMock:
    u = MagicMock()
    u.message.text = text
    u.callback_query = None
    u.effective_user.id = TEST_TID
    return u


def _make_callback(data: str) -> MagicMock:
    u = MagicMock()
    u.message = None
    u.callback_query.data = data
    u.callback_query.answer = AsyncMock()
    u.effective_user.id = TEST_TID
    return u


class BotSimulator:
    """
    Drives real handler code with mocked I/O.
    Call send() for text messages, tap() for button presses.
    Inspect sim.state and sim.last_reply after each step.
    """

    def __init__(self, profile: UserProfileData | None = None):
        self.state = "IDLE"
        self.profile = profile or _base_profile()
        self.all_replies: list[str] = []
        self._classify_result = {"category": "UPDATE", "confidence": 0.90, "alternative_category": None}
        self._generate_result = ("Risposta simulata.", False)

    @property
    def last_reply(self) -> str | None:
        return self.all_replies[-1] if self.all_replies else None

    def set_classify(self, category: str, confidence: float = 0.90) -> None:
        self._classify_result = {
            "category": category,
            "confidence": confidence,
            "alternative_category": None,
        }

    def _on_set_state(self, uid, new_state):
        self.state = new_state

    def _on_clear_state(self, uid):
        self.state = "IDLE"

    def _capture(self, text, **_kw):
        self.all_replies.append(text)

    async def send(self, text: str) -> str | None:
        u = _make_update(text)
        u.message.reply_text = AsyncMock(side_effect=self._capture)
        await self._dispatch(u, text)
        return self.last_reply

    async def tap(self, data: str) -> str | None:
        u = _make_callback(data)
        u.callback_query.message.reply_text = AsyncMock(side_effect=self._capture)
        await self._dispatch(u, data)
        return self.last_reply

    async def _dispatch(self, update, text: str) -> None:
        from utils.router import _route

        save_mock = lambda tid, p: setattr(self, "profile", p)

        with ExitStack() as stack:
            # Lazy imports inside router._route
            stack.enter_context(
                patch("services.memory.get_or_create_profile", return_value=self.profile)
            )
            stack.enter_context(patch("services.memory.save_profile", side_effect=save_mock))

            # DB (lazy imports inside handlers)
            stack.enter_context(patch("db.queries.get_or_create_user", return_value={"id": TEST_UID}))
            stack.enter_context(patch("db.queries.get_recent_messages", return_value=[]))
            stack.enter_context(patch("db.queries.get_recent_weekly_summaries", return_value=[]))
            stack.enter_context(patch("db.queries.save_message"))

            # State + profile per handler (module-level imports)
            for mod in _HANDLERS:
                stack.enter_context(patch(f"{mod}.set_state", side_effect=self._on_set_state))
                stack.enter_context(patch(f"{mod}.clear_state", side_effect=self._on_clear_state))
                stack.enter_context(patch(f"{mod}.save_profile", side_effect=save_mock))

            # DB per free_message (module-level imports)
            stack.enter_context(patch("handlers.free_message.get_recent_messages", return_value=[]))
            stack.enter_context(patch("handlers.free_message.save_message"))

            # Claude
            stack.enter_context(
                patch("handlers.free_message.classify_message", return_value=self._classify_result)
            )
            stack.enter_context(
                patch("handlers.free_message.generate_response", return_value=self._generate_result)
            )
            stack.enter_context(
                patch("handlers.parking.classify_parking_category", return_value="NEGOZIO")
            )

            # Re-engagement check (called in router else-branch)
            stack.enter_context(
                patch("handlers.re_engagement._detect_spontaneous_return", return_value=False)
            )

            await _route(update, MagicMock(), TEST_UID, TEST_TID, self.state, text)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_classified_shows_confirm():
    """UPDATE ad alta confidence → risposta di conferma, stato FREE_MSG_CONFIRM."""
    sim = BotSimulator()
    sim.set_classify("UPDATE", confidence=0.92)
    reply = await sim.send("ho finito il preventivo")
    assert sim.state == "FREE_MSG_CONFIRM"
    assert "aggiornamento" in reply.lower()


@pytest.mark.asyncio
async def test_update_confirm_asks_intention():
    """Conferma UPDATE → chiede se vuole dichiarare intenzione per domani."""
    sim = BotSimulator()
    sim.set_classify("UPDATE", confidence=0.92)
    await sim.send("ho finito il preventivo")
    await sim.tap("✓ Corretto")
    assert sim.state == "FREE_MSG_UPDATE_INT"


@pytest.mark.asyncio
async def test_update_no_intention_returns_idle():
    """Risposta 'No' all'intenzione → stato torna IDLE."""
    sim = BotSimulator()
    sim.set_classify("UPDATE", confidence=0.92)
    await sim.send("ho finito il preventivo")
    await sim.tap("✓ Corretto")
    await sim.tap("No, grazie")
    assert sim.state == "IDLE"


@pytest.mark.asyncio
async def test_idea_goes_to_parking():
    """IDEA classificata + conferma → entra nel flusso PARKING."""
    sim = BotSimulator()
    sim.set_classify("IDEA", confidence=0.91)
    await sim.send("ho un'idea per un corso online gratuito")
    await sim.tap("✓ Corretto")
    assert sim.state.startswith("PARKING")


@pytest.mark.asyncio
async def test_blocco_goes_to_scenario_c():
    """BLOCCO + conferma → entra in SCENARIO_C."""
    sim = BotSimulator()
    sim.set_classify("BLOCCO", confidence=0.93)
    await sim.send("sono bloccata non so da dove iniziare con tutto questo")
    await sim.tap("✓ Corretto")
    assert sim.state.startswith("SCENARIO_C")


@pytest.mark.asyncio
async def test_low_confidence_asks_clarification():
    """Confidence sotto soglia (0.85) → disambigua subito senza mostrare conferma."""
    sim = BotSimulator()
    sim.set_classify("UPDATE", confidence=0.70)
    await sim.send("ho fatto una cosa")
    assert sim.state == "FREE_MSG_CORRECT_CAT"


@pytest.mark.asyncio
async def test_wrong_category_then_idea():
    """Utente corregge la categoria a IDEA → routing verso PARKING."""
    sim = BotSimulator()
    sim.set_classify("UPDATE", confidence=0.92)
    await sim.send("testo qualsiasi abbastanza lungo per un corso")
    await sim.tap("✗ Non è questo")
    assert sim.state == "FREE_MSG_CORRECT_CAT"
    await sim.tap("Un'idea")
    assert sim.state.startswith("PARKING")


@pytest.mark.asyncio
async def test_domanda_obiettivi_answered_from_profile():
    """Domanda sugli obiettivi → risposta dal profilo strutturato, torna IDLE."""
    sim = BotSimulator()
    sim.set_classify("DOMANDA", confidence=0.95)
    await sim.send("quali sono i miei obiettivi?")
    await sim.tap("✓ Corretto")
    assert sim.state == "IDLE"
    assert "obiettiv" in sim.last_reply.lower()


@pytest.mark.asyncio
async def test_feedback_full_flow():
    """FEEDBACK → chiede preferenza → torna IDLE dopo risposta."""
    sim = BotSimulator()
    sim.set_classify("FEEDBACK", confidence=0.90)
    await sim.send("non mi è piaciuta quella risposta")
    await sim.tap("✓ Corretto")
    assert sim.state == "FREE_MSG_FEEDBACK_1"
    await sim.send("avrei preferito qualcosa di più diretto")
    assert sim.state == "IDLE"
