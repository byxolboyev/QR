import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # hosting'da .env bo'lmasligi mumkin, muhit o'zgaruvchilari yetarli
    pass

# --- Maxfiy ma'lumotlar: faqat muhit o'zgaruvchilaridan (secret) olinadi ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()


def _parse_ids(raw: str) -> set[int]:
    ids = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids


# Bitta yoki bir nechta admin: ADMIN_IDS=123456,789012
ADMIN_IDS = _parse_ids(os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID") or "")

# Ma'lumotlar bazasi (tugmalar, fayl kodlari). Hostingda doimiy papkaga yo'naltiring.
DB_PATH = os.getenv("DB_PATH", "data/bot.db")

MAX_TEXT = 1000  # QR ga joylanadigan matn uzunligi chegarasi

WELCOME_TEXT = (
    "👋 Salom! Men QR kod yaratuvchi botman. Xizmat butunlay bepul.\n\n"
    "Menga havola, matn, fayl, rasm, video, kontakt yoki joylashuv yuboring, "
    "men uni QR kodga aylantirib beraman.\n\n"
    "Pastdagi tugmalardan ham foydalanishingiz mumkin 👇"
)

HELP_TEXT = (
    "📌 Menga quyidagilardan istalganini yuboring:\n"
    "• 🔗 havola yoki oddiy matn\n"
    "• 📁 fayl, 🖼 rasm, 🎬 video, 🎵 audio, 🎤 ovozli xabar\n"
    "• 📇 kontakt (📎 → Kontakt)\n"
    "• 📍 joylashuv (📎 → Joylashuv)\n"
    "• 📶 Wi-Fi: menyudagi «Wi-Fi QR» tugmasi orqali\n\n"
    "Fayl QR kodini skanerlagan odam faylni shu bot orqali oladi.\n"
    "Jarayonni to'xtatish: /cancel"
)
