from telegram import InlineKeyboardMarkup


def test_make_keyboard_single_row():
    from utils.formatters import make_keyboard
    kb = make_keyboard([["Sì", "No"]])
    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 2
    assert kb.inline_keyboard[0][0].text == "Sì"
    assert kb.inline_keyboard[0][0].callback_data == "Sì"


def test_make_keyboard_multiple_rows():
    from utils.formatters import make_keyboard
    kb = make_keyboard([["Opzione A"], ["Opzione B"], ["Opzione C"]])
    assert len(kb.inline_keyboard) == 3


def test_make_keyboard_custom_callback():
    from utils.formatters import make_keyboard
    kb = make_keyboard([["Testo visibile"]], callback_data=[["cb_testo"]])
    assert kb.inline_keyboard[0][0].text == "Testo visibile"
    assert kb.inline_keyboard[0][0].callback_data == "cb_testo"


def test_format_objectives_summary():
    from utils.formatters import format_objectives_summary
    from models.user_profile import UserProfileData, Objective
    profile = UserProfileData(
        telegram_id=123,
        objectives=[
            Objective(title="Vendere negozio", rank=1),
            Objective(title="Oltre la Bottega", rank=2, weekly_hours_target=6),
        ],
        motivation_anchor="Casa a Marta",
        user_context="Bottega",
    )
    text = format_objectives_summary(profile)
    assert "Vendere negozio" in text
    assert "Oltre la Bottega" in text
    assert "6" in text


def test_format_parking_list_empty():
    from utils.formatters import format_parking_list
    from models.user_profile import UserProfileData
    profile = UserProfileData(telegram_id=123, user_context="test")
    assert format_parking_list(profile) == "Il parcheggio è vuoto."


def test_format_parking_list_with_items():
    from utils.formatters import format_parking_list
    from models.user_profile import UserProfileData, ParkingItem
    profile = UserProfileData(telegram_id=123, user_context="test")
    profile.parking_lot = [ParkingItem(content="Open day", category="NEGOZIO")]
    text = format_parking_list(profile)
    assert "Open day" in text
    assert "1/10" in text
