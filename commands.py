from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import config
import db
import kb

router = Router()

SEND_METHODS = {
    "photo": "send_photo",
    "video": "send_video",
    "animation": "send_animation",
    "document": "send_document",
    "audio": "send_audio",
    "voice": "send_voice",
    "video_note": "send_video_note",
    "sticker": "send_sticker",
}
NO_CAPTION = {"video_note", "sticker"}


async def deliver(bot: Bot, chat_id: int, rec) -> None:
    """QR orqali kelgan odamga saqlangan faylni yuboradi."""
    ftype = rec["file_type"]
    kwargs = {ftype: rec["file_id"]}
    if rec["caption"] and ftype not in NO_CAPTION:
        kwargs["caption"] = rec["caption"]
    await getattr(bot, SEND_METHODS[ftype])(chat_id=chat_id, **kwargs)


async def welcome(message: Message) -> None:
    await message.answer(config.WELCOME_TEXT, reply_markup=kb.main_menu())


@router.message(CommandStart(deep_link=True))
async def start_deeplink(message: Message, command: CommandObject, bot: Bot):
    db.add_user(message.from_user.id)
    args = command.args or ""
    if args.startswith("f_"):
        rec = db.get_file(args[2:])
        if not rec:
            await message.answer("😕 Fayl topilmadi yoki o'chirilgan.")
            return
        await deliver(bot, message.chat.id, rec)
        return
    await welcome(message)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    db.add_user(message.from_user.id)
    await welcome(message)


@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(config.HELP_TEXT)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


@router.message(Command("id"))
async def my_id(message: Message):
    await message.answer(f"Sizning Telegram ID: {message.from_user.id}")


@router.message(Command("admin"))
async def admin_cmd(message: Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔ Bu buyruq faqat admin uchun.")
        return
    await state.clear()
    await message.answer(kb.PANEL_TEXT, reply_markup=kb.admin_home())
