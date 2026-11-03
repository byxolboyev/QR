import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import config
import db
import qrgen

router = Router()


class Wifi(StatesGroup):
    ssid = State()
    password = State()


async def send_qr(message: Message, data: str) -> None:
    if len(data) > config.MAX_TEXT:
        await message.answer(f"⚠️ Matn juda uzun ({len(data)} belgi). {config.MAX_TEXT} belgigacha yuboring.")
        return
    try:
        png = await asyncio.to_thread(qrgen.make_qr, data)
    except Exception:
        logging.exception("QR yaratishda xato")
        await message.answer("😕 QR kod yaratib bo'lmadi. Boshqa ma'lumot bilan urinib ko'ring.")
        return
    db.add_user(message.from_user.id)
    db.inc_qr()
    await message.answer_photo(BufferedInputFile(png, "qrcode.png"), caption="✅ QR kod tayyor!")
    await message.answer_document(BufferedInputFile(png, "qrcode.png"), caption="📎 Yuqori sifatli fayl")


# ---------- Menyu tugmalari ----------
@router.callback_query(F.data.startswith("m:"))
async def menu_press(cb: CallbackQuery, state: FSMContext):
    btn = db.get_button(int(cb.data[2:]))
    if not btn:
        await cb.answer("Tugma topilmadi", show_alert=True)
        return
    await cb.answer()
    if btn["kind"] == "wifi":
        await state.set_state(Wifi.ssid)
        await cb.message.answer("📶 Wi-Fi tarmog'ining nomini (SSID) yuboring.\nBekor qilish: /cancel")
    else:
        await cb.message.answer(btn["value"])


# ---------- Wi-Fi QR ----------
@router.message(Wifi.ssid, F.text)
async def wifi_ssid(message: Message, state: FSMContext):
    await state.update_data(ssid=message.text.strip())
    await state.set_state(Wifi.password)
    await message.answer("🔑 Parolni yuboring. Parolsiz tarmoq bo'lsa, - belgisini yuboring.")


@router.message(Wifi.password, F.text)
async def wifi_password(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    pwd = message.text.strip()
    ssid = qrgen.wifi_escape(data["ssid"])
    if pwd == "-":
        payload = f"WIFI:T:nopass;S:{ssid};;"
    else:
        payload = f"WIFI:T:WPA;S:{ssid};P:{qrgen.wifi_escape(pwd)};;"
    try:
        await message.delete()  # parol chatda qolmasin
    except Exception:
        pass
    await send_qr(message, payload)


# ---------- Fayl, rasm, video va boshqalar ----------
def extract_media(m: Message):
    if m.photo:
        return "photo", m.photo[-1].file_id
    for kind in ("video", "animation", "document", "audio", "voice", "video_note", "sticker"):
        obj = getattr(m, kind)
        if obj:
            return kind, obj.file_id
    return None


@router.message(F.photo | F.video | F.animation | F.document | F.audio | F.voice | F.video_note | F.sticker)
async def media_qr(message: Message, bot: Bot):
    ftype, fid = extract_media(message)
    code = db.add_file(fid, ftype, message.caption, message.from_user.id)
    me = await bot.me()
    # QR ichida fayl emas, botga olib keluvchi havola bo'ladi
    await send_qr(message, f"https://t.me/{me.username}?start=f_{code}")


# ---------- Kontakt va joylashuv ----------
@router.message(F.contact)
async def contact_qr(message: Message):
    c = message.contact
    await send_qr(message, qrgen.vcard(c.first_name or "", c.last_name or "", c.phone_number))


@router.message(F.location)
async def location_qr(message: Message):
    loc = message.location
    await send_qr(message, f"geo:{loc.latitude},{loc.longitude}")


# ---------- Matn va havola ----------
@router.message(F.text)
async def text_qr(message: Message):
    text = message.text.strip()
    if text.lower().startswith("www."):
        text = "https://" + text
    await send_qr(message, text)


@router.message()
async def unsupported(message: Message):
    await message.answer("🤷 Bu turdagi xabar uchun QR yaratib bo'lmaydi. Havola, matn yoki fayl yuboring.")
