import os
import secrets
import sqlite3

import config

COLORS = ["success", "primary", "danger"]  # yashil -> ko'k -> qizil -> yana yashil

DEFAULT_BUTTONS = [
    ("🔗 Havola / matn", "success", "msg",
     "🔗 Menga istalgan havola yoki matn yuboring, men uni QR kodga aylantiraman."),
    ("📁 Fayl / rasm / video", "primary", "msg",
     "📁 Menga fayl, rasm, video, audio yoki ovozli xabar yuboring.\n"
     "QR kodni skanerlagan odam faylni shu bot orqali oladi."),
    ("📶 Wi-Fi QR", "primary", "wifi", ""),
    ("📇 Kontakt / 📍 Joylashuv", "success", "msg",
     "📎 tugmasi orqali kontakt yoki joylashuv yuboring, men QR kod yarataman."),
    ("ℹ️ Yordam", "danger", "msg", config.HELP_TEXT),
]

os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)
_db = sqlite3.connect(config.DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row


def init() -> None:
    _db.executescript(
        """
        CREATE TABLE IF NOT EXISTS buttons(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT 'primary',
            kind TEXT NOT NULL,              -- msg | url | wifi
            value TEXT NOT NULL DEFAULT '',
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS files(
            code TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL,
            caption TEXT,
            owner INTEGER,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            joined TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS meta(
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    if _db.execute("SELECT COUNT(*) FROM buttons").fetchone()[0] == 0:
        for i, (label, color, kind, value) in enumerate(DEFAULT_BUTTONS):
            _db.execute(
                "INSERT INTO buttons(label, color, kind, value, position) VALUES(?,?,?,?,?)",
                (label, color, kind, value, i),
            )
    _db.commit()


# ---------- Tugmalar ----------
def list_buttons():
    return _db.execute("SELECT * FROM buttons ORDER BY position, id").fetchall()


def get_button(bid: int):
    return _db.execute("SELECT * FROM buttons WHERE id=?", (bid,)).fetchone()


def add_button(label: str, kind: str, value: str, color: str = "primary") -> None:
    pos = _db.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM buttons").fetchone()[0]
    _db.execute(
        "INSERT INTO buttons(label, color, kind, value, position) VALUES(?,?,?,?,?)",
        (label, color, kind, value, pos),
    )
    _db.commit()


def update_label(bid: int, label: str) -> None:
    _db.execute("UPDATE buttons SET label=? WHERE id=?", (label, bid))
    _db.commit()


def update_value(bid: int, value: str) -> None:
    _db.execute("UPDATE buttons SET value=? WHERE id=?", (value, bid))
    _db.commit()


def cycle_color(bid: int):
    """yashil -> ko'k -> qizil -> yashil. Yangi rangni qaytaradi."""
    row = get_button(bid)
    if not row:
        return None
    cur = row["color"]
    nxt = COLORS[(COLORS.index(cur) + 1) % len(COLORS)] if cur in COLORS else COLORS[0]
    _db.execute("UPDATE buttons SET color=? WHERE id=?", (nxt, bid))
    _db.commit()
    return nxt


def delete_button(bid: int) -> None:
    _db.execute("DELETE FROM buttons WHERE id=?", (bid,))
    _db.commit()


# ---------- Foydalanuvchilar, fayllar, statistika ----------
def add_user(uid: int) -> None:
    _db.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (uid,))
    _db.commit()


def add_file(file_id: str, file_type: str, caption, owner: int) -> str:
    code = secrets.token_urlsafe(6)  # taxmin qilib bo'lmaydigan qisqa kod
    _db.execute(
        "INSERT INTO files(code, file_id, file_type, caption, owner) VALUES(?,?,?,?,?)",
        (code, file_id, file_type, caption, owner),
    )
    _db.commit()
    return code


def get_file(code: str):
    return _db.execute("SELECT * FROM files WHERE code=?", (code,)).fetchone()


def inc_qr() -> None:
    _db.execute(
        "INSERT INTO meta(key, value) VALUES('qr', 1) "
        "ON CONFLICT(key) DO UPDATE SET value = value + 1"
    )
    _db.commit()


def stats() -> dict:
    q = lambda sql: _db.execute(sql).fetchone()[0]
    return {
        "users": q("SELECT COUNT(*) FROM users"),
        "files": q("SELECT COUNT(*) FROM files"),
        "qr": q("SELECT COALESCE((SELECT value FROM meta WHERE key='qr'), 0)"),
    }
