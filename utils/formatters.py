from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from models.user_profile import UserProfileData


def make_keyboard(
    rows: list[list[str]],
    callback_data: list[list[str]] | None = None,
) -> InlineKeyboardMarkup:
    keyboard = []
    for r_idx, row in enumerate(rows):
        kb_row = []
        for b_idx, label in enumerate(row):
            cb = callback_data[r_idx][b_idx] if callback_data else label
            kb_row.append(InlineKeyboardButton(text=label, callback_data=cb))
        keyboard.append(kb_row)
    return InlineKeyboardMarkup(keyboard)


def format_objectives_summary(profile: UserProfileData) -> str:
    lines = ["*I tuoi obiettivi:*"]
    for obj in sorted(profile.objectives, key=lambda o: o.rank):
        hours = f" ({obj.weekly_hours_target}h/sett.)" if obj.weekly_hours_target else ""
        lines.append(f"{obj.rank}. {obj.title}{hours}")
    if profile.motivation_anchor:
        lines.append(f"\n_Perché: {profile.motivation_anchor}_")
    return "\n".join(lines)


def format_parking_list(profile: UserProfileData) -> str:
    active = [p for p in profile.parking_lot if p.status == "parked"]
    if not active:
        return "Il parcheggio è vuoto."
    lines = [f"*Idee nel parcheggio ({len(active)}/10):*"]
    for item in active:
        lines.append(f"• {item.content} _{item.category}_")
    return "\n".join(lines)
