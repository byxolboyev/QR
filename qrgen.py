from io import BytesIO

import qrcode


def make_qr(data: str) -> bytes:
    """Istalgan matndan QR kod (PNG) yaratadi."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def wifi_escape(s: str) -> str:
    for ch in '\\;,:"':
        s = s.replace(ch, "\\" + ch)
    return s


def vcard(first: str, last: str, phone: str) -> str:
    phone = phone if phone.startswith("+") else "+" + phone
    full = f"{first} {last}".strip()
    return (
        "BEGIN:VCARD\nVERSION:3.0\n"
        f"N:{last};{first};;;\nFN:{full}\nTEL;TYPE=CELL:{phone}\n"
        "END:VCARD"
    )
