"""Caractere speciale pentru LCD și conversia textului în ASCII.

Controllerul HD44780 al LCD-ului nu are diacritice, dar permite 8 caractere
desenate de noi (5x8 pixeli), adresate cu codurile 0..7.
"""

LCD_COLS = 16

ROCKET = "\x00"
FLAME = "\x01"

# Fiecare rând este o linie de 5 pixeli (bitul 4 = stânga).
BITMAPS = (
    # ROCKET
    (0b00100, 0b01110, 0b01110, 0b01110, 0b01110, 0b11111, 0b11011, 0b10001),
    # FLAME
    (0b00100, 0b00100, 0b01010, 0b01010, 0b10101, 0b10101, 0b01110, 0b00100),
)

# Cum arată caracterele speciale în terminal și pe pagina web.
ASCII_FALLBACK = {ROCKET: "^", FLAME: "*"}

_DIACRITICS = str.maketrans("ăâîșşțţĂÂÎȘŞȚŢ", "aaisstt" "AAISSTT")


def lcd_safe(text: str) -> str:
    """Taie/completează textul la 16 caractere și înlocuiește diacriticele."""
    text = text.translate(_DIACRITICS)
    return text[:LCD_COLS].ljust(LCD_COLS)


def to_ascii(text: str) -> str:
    """Înlocuiește caracterele speciale cu echivalente ASCII (pentru terminal/web)."""
    for glyph, fallback in ASCII_FALLBACK.items():
        text = text.replace(glyph, fallback)
    return text
