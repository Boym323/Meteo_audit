"""Transparent rule components; flags are screening evidence, never automatic corrections."""
from dataclasses import dataclass
from enum import StrEnum

class Quality(StrEnum):
    CONFIRMED_ERROR = "CONFIRMED_ERROR"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    SUSPECTED = "SUSPECTED"
    UNRESOLVED = "UNRESOLVED"
    VALIDATED = "VALIDATED"

@dataclass(frozen=True)
class RainPoint:
    epoch: int
    interval_minutes: int
    rain: float | None
    rain_rate: float | None

@dataclass(frozen=True)
class Finding:
    epoch: int
    variable: str
    value: float | None
    quality: Quality
    reason: str
    proposed_value: float | None = None

def screen_rain(points: list[RainPoint]) -> list[Finding]:
    """Flag missing values, impossible isolated accumulation/rate combinations and time gaps.

    Thresholds here only create review candidates. No finding is labeled a confirmed error.
    Rain is assumed already normalized to mm only when caller explicitly does so.
    """
    findings: list[Finding] = []
    ordered = sorted(points, key=lambda p: p.epoch)
    for i, p in enumerate(ordered):
        if p.rain is None:
            findings.append(Finding(p.epoch, "rain", None, Quality.UNRESOLVED, "missing measurement; do not treat as zero"))
        elif i and p.epoch - ordered[i-1].epoch > max(p.interval_minutes, 5) * 60 * 1.5:
            findings.append(Finding(p.epoch, "rain", p.rain, Quality.SUSPECTED, "timestamp gap around observation"))
        if p.rain is not None and p.rain_rate is not None and p.rain > 20 and p.rain_rate == 0:
            findings.append(Finding(p.epoch, "rain", p.rain, Quality.SUSPECTED, "large interval amount with zero reported rainRate; inspect source counter and references"))
        if p.rain is not None and p.rain_rate is not None and p.rain > 0 and p.rain_rate > 0:
            implied_mm_h = p.rain * 60 / p.interval_minutes
            # Ratio mismatch is a flag only: rainRate may use a different averaging window.
            if max(implied_mm_h, p.rain_rate) / min(implied_mm_h, p.rain_rate) > 12:
                findings.append(Finding(p.epoch, "rainRate", p.rain_rate, Quality.UNRESOLVED, "rain and rainRate differ materially; historical rainRate semantics unknown"))
    return findings
