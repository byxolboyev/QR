from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import config
import db
import kb


class IsAdmin(BaseFilter):
    async def __call__(self, event) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id in config.ADMIN_IDS)


router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class Rename(StatesGroup):
    label = State()


class EditValue(StatesGroup):
    value = State()


class AddButton(StatesGroup):
    label = State()
    kind = State()
    value = State()


async def show(cb: CallbackQuery, text: str, markup) -> None:
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        pass  # xabar o'zgarmagan bo'lsa Telegram xato qaytaradi, e'tibor bermaymiz


def valid_url(s: str) -> bool:
    return s.startswith(("http://", "https://", "tg://"))


# ---------- Bosh sahifa ----------
@router.callback_query(F.data == "adm:home")
async def home(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await show(cb, kb.PANEL_TEXT, kb.admin_home())
    await cb.answer()


@router.callback_query(F.data == "adm:preview")
async def preview(cb: CallbackQuery):
    markup = kb.main_menu()
    await cb.message.answer("👁 Foydalanuvchilar menyusi shunday ko'rinadi:", reply_markup=markup)
    await cb.answer()


@router.callback_query(F.data == "adm:stats")
async def stats(cb: CallbackQuery):
    s = db.stats()
    text = (f"📊 Statistika\n\n👥 Foydalanuvchilar: {s['users']}\n"
            f"🧾 Yaratilgan QR kodlar: {s['qr']}\n📁 Saqlangan fayllar: {s['files']}")
    await show(cb, text, kb.back_kb())
    await cb.answer()


# ---------- Ranglar: bosgan sari yashil -> ko'k -> qizil ----------
@router.callback_query(F.data == "adm:colors")
async def colors(cb: CallbackQuery):
    await show(
        cb,
        "🎨 Tugma ustiga bosing, rangi almashadi:\n"
        "🟢 yashil → 🔵 ko'k → 🔴 qizil → yana 🟢 yashil",
        kb.colors_kb(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:c:"))
async def cycle(cb: CallbackQuery):
    new = db.cycle_color(int(cb.data.split(":")[2]))
    if new is None:
        await cb.answer("Tugma topilmadi", show_alert=True)
        return
    await cb.answer(f"{kb.EMOJI[new]} {kb.NAMES[new].capitalize()}")
    try:
        await cb.message.edit_reply_markup(reply_markup=kb.colors_kb())
    except TelegramBadRequest:
        pass


# ---------- Nomini o'zgartirish ----------
@router.callback_query(F.data == "adm:rename")
async def rename_list(cb: CallbackQuery):
    await show(cb, "✏️ Qaysi tugma nomini o'zgartiramiz?", kb.pick_kb("r"))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:r:"))
async def rename_pick(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Rename.label)
    await state.update_data(btn=int(cb.data.split(":")[2]))
    await cb.message.answer("✏️ Yangi nomni yuboring (emoji ishlatsangiz bo'ladi).\nBekor qilish: /cancel")
    await cb.answer()


@router.message(Rename.label, F.text)
async def rename_done(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    db.update_label(data["btn"], message.text.strip()[:40])
    await message.answer("✅ Nom o'zgartirildi.", reply_markup=kb.admin_home())


# ---------- Matn / havolani o'zgartirish ----------
@router.callback_query(F.data == "adm:val")
async def value_list(cb: CallbackQuery):
    await show(cb, "📝 Qaysi tugmaning matni yoki havolasini o'zgartiramiz?", kb.pick_kb("v"))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:v:"))
async def value_pick(cb: CallbackQuery, state: FSMContext):
    btn = db.get_button(int(cb.data.split(":")[2]))
    if not btn:
        await cb.answer("Tugma topilmadi", show_alert=True)
        return
    if btn["kind"] == "wifi":
        await cb.answer("Bu tugmaning matni yo'q (Wi-Fi QR yaratadi).", show_alert=True)
        return
    await state.set_state(EditValue.value)
    await state.update_data(btn=btn["id"], kind=btn["kind"])
    what = "havolani (https://...)" if btn["kind"] == "url" else "yangi matnni"
    await cb.message.answer(f"📝 {what} yuboring.\nBekor qilish: /cancel")
    await cb.answer()


@router.message(EditValue.value, F.text)
async def value_done(message: Message, state: FSMContext):
    data = await state.get_data()
    value = message.text.strip()
    if data["kind"] == "url" and not valid_url(value):
        await message.answer("⚠️ Havola http:// yoki https:// bilan boshlanishi kerak. Qayta yuboring.")
        return
    await state.clear()
    db.update_value(data["btn"], value)
    await message.answer("✅ Saqlandi.", reply_markup=kb.admin_home())


# ---------- Tugma qo'shish ----------
@router.callback_query(F.data == "adm:add")
async def add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddButton.label)
    await cb.message.answer("➕ Yangi tugma nomini yuboring.\nBekor qilish: /cancel")
    await cb.answer()


@router.message(AddButton.label, F.text)
async def add_label(message: Message, state: FSMContext):
    await state.update_data(label=message.text.strip()[:40])
    await state.set_state(AddButton.kind)
    await message.answer("Tugma bosilganda nima bo'lsin?", reply_markup=kb.kind_kb())


@router.callback_query(AddButton.kind, F.data.in_({"adm:k:msg", "adm:k:url"}))
async def add_kind(cb: CallbackQuery, state: FSMContext):
    kind = cb.data.split(":")[2]
    await state.update_data(kind=kind)
    await state.set_state(AddButton.value)
    ask = "Havolani yuboring (https://...)" if kind == "url" else "Tugma bosilganda yuboriladigan matnni yuboring"
    await cb.message.answer(ask)
    await cb.answer()


@router.message(AddButton.value, F.text)
async def add_value(message: Message, state: FSMContext):
    data = await state.get_data()
    value = message.text.strip()
    if data["kind"] == "url" and not valid_url(value):
        await message.answer("⚠️ Havola http:// yoki https:// bilan boshlanishi kerak. Qayta yuboring.")
        return
    await state.clear()
    db.add_button(data["label"], data["kind"], value)
    await message.answer("✅ Tugma qo'shildi. Rangini «🎨 Ranglar» bo'limida o'zgartirishingiz mumkin.",
                         reply_markup=kb.admin_home())


# ---------- O'chirish ----------
@router.callback_query(F.data == "adm:del")
async def delete_list(cb: CallbackQuery):
    await show(cb, "🗑 Qaysi tugmani o'chiramiz?", kb.pick_kb("d"))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:d:"))
async def delete_pick(cb: CallbackQuery):
    db.delete_button(int(cb.data.split(":")[2]))
    await cb.answer("🗑 O'chirildi")
    await show(cb, "🗑 Qaysi tugmani o'chiramiz?", kb.pick_kb("d"))
