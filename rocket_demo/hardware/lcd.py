"""Afișaje: LCD-ul real (I2C) și variantele fără hardware."""

from __future__ import annotations

import logging
import os
import sys
import time

from ..glyphs import BITMAPS, lcd_safe, to_ascii

log = logging.getLogger(__name__)

LCD_ADDRESSES = (0x27, 0x3F)
ERROR_LOG_INTERVAL_S = 30.0


def probe_address(port: int) -> int:
    """Caută adaptorul PCF8574 pe magistrala I2C la adresele uzuale."""
    from smbus2 import SMBus

    with SMBus(port) as bus:
        for address in LCD_ADDRESSES:
            try:
                bus.read_byte(address)
                return address
            except OSError:
                continue
    raise RuntimeError(
        "nu am găsit LCD-ul la 0x27 sau 0x3F; verifică firele și rulează `i2cdetect -y 1`"
    )


class I2cLcd:
    """LCD 1602 cu adaptor I2C PCF8574, prin biblioteca RPLCD."""

    def __init__(self, address: int | None = None, port: int = 1):
        from RPLCD.i2c import CharLCD

        if address is None:
            address = probe_address(port)
        self.address = address
        self._lcd = CharLCD(
            i2c_expander="PCF8574",
            address=address,
            port=port,
            cols=16,
            rows=2,
            charmap="A00",
            auto_linebreaks=False,
        )
        self._setup()
        self._last_error_log = 0.0
        log.info("LCD găsit la adresa 0x%02X", address)

    def _setup(self) -> None:
        self._lcd.clear()
        for i, bitmap in enumerate(BITMAPS):
            self._lcd.create_char(i, bitmap)
        self._rows: list[str | None] = [None, None]

    def show(self, line1: str, line2: str) -> None:
        try:
            for row, text in enumerate((lcd_safe(line1), lcd_safe(line2))):
                if text != self._rows[row]:
                    self._lcd.cursor_pos = (row, 0)
                    self._lcd.write_string(text)
                    self._rows[row] = text
        except OSError as exc:
            # Un fir mișcat nu trebuie să oprească demo-ul: reîncercăm la următorul tick.
            self._rows = [None, None]
            now = time.monotonic()
            if now - self._last_error_log > ERROR_LOG_INTERVAL_S:
                self._last_error_log = now
                log.warning("eroare de comunicare cu LCD-ul: %s", exc)

    def close(self) -> None:
        try:
            self._lcd.clear()
            self._lcd.write_string("Demo oprit")
            self._lcd.close(clear=False)
        except OSError:
            pass


class TerminalDisplay:
    """LCD desenat în terminal, pentru modul --sim."""

    def __init__(self, stream=None):
        self._stream = stream or sys.stdout
        self._tty = self._stream.isatty()
        if self._tty and sys.platform == "win32":
            os.system("")  # activează codurile ANSI în consola Windows
        self._last: tuple[str, str] | None = None
        self._drawn = False

    def show(self, line1: str, line2: str) -> None:
        lines = (to_ascii(lcd_safe(line1)), to_ascii(lcd_safe(line2)))
        if lines == self._last:
            return
        # Fără terminal interactiv redesenăm doar când se schimbă primul rând.
        if not self._tty and self._last and lines[0] == self._last[0]:
            self._last = lines
            return
        self._last = lines
        border = "+" + "-" * 16 + "+"
        box = [border, f"|{lines[0]}|", f"|{lines[1]}|", border]
        out = self._stream
        if self._tty:
            if self._drawn:
                out.write("\x1b[4F")
            out.write("".join(f"\x1b[2K{row}\n" for row in box))
        else:
            out.write("\n".join(box) + "\n")
        out.flush()
        self._drawn = True

    def close(self) -> None:
        pass


class LogDisplay:
    """Folosit când LCD-ul nu e disponibil: scrie textul în log."""

    def __init__(self):
        self._last = None

    def show(self, line1: str, line2: str) -> None:
        lines = (to_ascii(lcd_safe(line1)), to_ascii(lcd_safe(line2)))
        if lines[0] != (self._last or ("",))[0]:
            log.info("LCD | %s | %s |", *lines)
        self._last = lines

    def close(self) -> None:
        pass
