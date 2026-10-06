"""Telemetria zborului: altitudine și viteză, interpolate între puncte-cheie."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass


@dataclass(frozen=True)
class Telemetry:
    alt_km: float
    vel_ms: float

    @property
    def vel_kmh(self) -> int:
        return round(self.vel_ms * 3.6)


def interpolate(points, t: float) -> Telemetry:
    """Interpolare liniară în tabelul (t, alt_km, vel_ms), limitată la capete."""
    if t <= points[0][0]:
        return Telemetry(points[0][1], points[0][2])
    if t >= points[-1][0]:
        return Telemetry(points[-1][1], points[-1][2])
    i = bisect_right([p[0] for p in points], t)
    (t0, a0, v0), (t1, a1, v1) = points[i - 1], points[i]
    f = (t - t0) / (t1 - t0)
    return Telemetry(a0 + (a1 - a0) * f, v0 + (v1 - v0) * f)


def format_lcd(tel: Telemetry) -> str:
    """Rândul de telemetrie pentru LCD, de ex. `12.3km 1620km/h` (max. 16 caractere)."""
    alt = f"{tel.alt_km:.0f}" if tel.alt_km >= 100 else f"{tel.alt_km:.1f}"
    return f"{alt}km {tel.vel_kmh}km/h"
