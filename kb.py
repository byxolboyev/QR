from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import db

EMOJI = {"success": "🟢", "primary": "🔵", "danger": "🔴"}
NAMES = {"success": "yashil", "primary": "ko'k", "danger": "qizil"}

PANEL_TEXT = "🛠 Admin panel\nMenyu tugmalarini shu yerdan boshqaring."


def _rows(btns: list, n: int = 2) -> list:
    return [btns[i:i + n] for i in range(0, len(btns), n)]


def _cb(text: str, data: str, style: str | None = None) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data, style=style)


def _back() -> list:
    return [_cb("⬅️ Orqaga", "adm:home")]


def main_menu() -> InlineKeyboardMarkup | None:
    """Foydalanuvchilar ko'radigan rangli menyu (Telegram button style)."""
    btns = []
    for r in db.list_buttons():
        if r["kind"] == "url":
            btns.append(InlineKeyboardButton(text=r["label"], url=r["value"], style=r["color"]))
        else:
            btns.append(_cb(r["label"], f"m:{r['id']}", r["color"]))
    return InlineKeyboardMarkup(inline_keyboard=_rows(btns)) if btns else None


def admin_home() -> InlineKeyboardMarkup:
    rows = [
        [_cb("🎨 Ranglar", "adm:colors", "success"), _cb("✏️ Nomini o'zgartirish", "adm:rename", "primary")],
        [_cb("📝 Matnini o'zgartirish", "adm:val", "primary"), _cb("➕ Tugma qo'shish", "adm:add", "success")],
        [_cb("🗑 O'chirish", "adm:del", "danger"), _cb("👁 Menyuni ko'rish", "adm:preview", "primary")],
        [_cb("📊 Statistika", "adm:stats")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def colors_kb() -> InlineKeyboardMarkup:
    """Tugma ustiga bosilganda rang almashadi: yashil -> ko'k -> qizil."""
    btns = [_cb(f"{EMOJI.get(r['color'], '🔵')} {r['label']}", f"adm:c:{r['id']}", r["color"])
            for r in db.list_buttons()]
    return InlineKeyboardMarkup(inline_keyboard=_rows(btns) + [_back()])


def pick_kb(prefix: str) -> InlineKeyboardMarkup:
    btns = [_cb(r["label"], f"adm:{prefix}:{r['id']}", r["color"]) for r in db.list_buttons()]
    return InlineKeyboardMarkup(inline_keyboard=_rows(btns) + [_back()])


def kind_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        _cb("💬 Xabar yuboradi", "adm:k:msg", "primary"),
        _cb("🌐 Havola ochadi", "adm:k:url", "success"),
    ]])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[_back()])
