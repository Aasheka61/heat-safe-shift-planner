"""Supervisor messages (English and Tamil) built from deterministic templates.

No AI model writes the safety instructions. The Tamil text should be reviewed by a native
speaker and a safety officer before any real-world use.
"""
from __future__ import annotations

from .limits import PRESETS, allowed_minutes

TEXT = {
    "en": {
        "title": "HEAT WORK PLAN",
        "site": "Site",
        "normal": "Normal work",
        "stop": "STOP all work. Rest in shade, drink water",
        "limited": ("Heavy work {h} min/hr, medium work {m} min/hr, light work {l} min/hr. "
                    "Rest in shade for the rest of each hour"),
        "footer": ("Drink water every 20 minutes. If anyone feels dizzy or unwell, stop work "
                   "and move them to shade."),
    },
    "ta": {
        "title": "வெப்ப வேலை அட்டவணை",
        "site": "தளம்",
        "normal": "வழக்கமான வேலை",
        "stop": "அனைத்து வேலையும் நிறுத்தவும். நிழலில் ஓய்வெடுங்கள், தண்ணீர் குடியுங்கள்",
        "limited": ("கடின வேலை {h} நிமிடம்/மணி, நடுத்தர வேலை {m} நிமிடம்/மணி, இலகு வேலை {l} நிமிடம்/மணி. "
                    "மீதி நேரம் நிழலில் ஓய்வு"),
        "footer": ("20 நிமிடத்துக்கு ஒருமுறை தண்ணீர் குடியுங்கள். யாருக்காவது தலைசுற்றல் அல்லது "
                   "உடல்நலக்குறைவு இருந்தால் உடனே வேலையை நிறுத்தி நிழலுக்கு அழைத்துச் செல்லுங்கள்."),
    },
}


def hour_allowances(wbgt_by_hour: dict, acclimatized: bool = True, cav: float = 0.0,
                    buffer: float = 0.0) -> dict:
    """{hour: (heavy_min, medium_min, light_min)} allowed per hour."""
    out = {}
    for h in sorted(wbgt_by_hour):
        e = wbgt_by_hour[h] + cav + buffer
        out[h] = tuple(allowed_minutes(PRESETS[k], e, acclimatized) for k in ("heavy", "medium", "light"))
    return out


def merge_blocks(allow: dict) -> list:
    """Merge consecutive hours with identical allowances -> [(start_h, end_h_exclusive, tuple)]."""
    blocks = []
    for h in sorted(allow):
        if blocks and blocks[-1][2] == allow[h] and blocks[-1][1] == h:
            blocks[-1] = (blocks[-1][0], h + 1, allow[h])
        else:
            blocks.append((h, h + 1, allow[h]))
    return blocks


def render_message(site: str, date_str: str, blocks: list, lang: str = "en") -> str:
    t = TEXT[lang]
    lines = [f"{t['title']} | {t['site']}: {site} | {date_str}"]
    for start, end, (h, m, l) in blocks:
        window = f"{start:02d}:00-{end:02d}:00"
        if (h, m, l) == (60, 60, 60):
            what = t["normal"]
        elif (h, m, l) == (0, 0, 0):
            what = t["stop"]
        else:
            what = t["limited"].format(h=h, m=m, l=l)
        lines.append(f"{window}  {what}")
    lines.append(t["footer"])
    return "\n".join(lines)
