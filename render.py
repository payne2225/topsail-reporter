"""Turn data/<date>.json (+ reports/<date>.md when written) into the site.

    python render.py                 # every edition, the index, every text
    python render.py --print 2026-11-05   # also print that day's text

Outputs, all under site/ (what GitHub Pages serves):
    site/<date>/index.html          the fishing edition's full report
    site/<date>/island/index.html   the Island Edition (the day off the water)
    site/index.html                 the newest fishing edition, with the archive
    site/island/index.html          the newest Island Edition
    site/text/<date>.txt            the fishing text the iPhone Shortcut sends
    site/text/<date>-island.txt     the Island Edition's text, its own Shortcut

Each text is three parts: a header line render.py writes, the writer's short
prose from the report ("## Text" or "## Island Text"), and a numbers block
render.py builds from the fetched data. No tide time, temperature or
forecast in a numbers block is ever typed by hand. With no report yet (the
quick edition) a text is the header, the numbers and the link.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import html
import json
import math
import os
import re
import sys

import config

HERE = os.path.dirname(os.path.abspath(__file__))
SECTIONS = ["Text", "Lead", "The Bite", "Beach & Weather", "Around the Island",
            "Regs Corner", "The Last Cast", "Island Text", "Island Lead",
            "Things To Do", "Sources"]
REQUIRED_SECTIONS = ["Text", "Lead", "The Bite", "Beach & Weather",
                     "Around the Island", "Island Text", "Island Lead",
                     "Things To Do", "Sources"]
# The fishing page is fishing and the outdoors only (Nate, 2026-10-21: "maybe
# the fishing side of it is just fishing info and outdoor conditions");
# Around the Island lives on the Island Edition.
PAGE_SECTIONS = ["The Bite", "Beach & Weather", "Regs Corner", "The Last Cast"]
# The fishing page's closing line was the Parting Shot until 2026-11-04 (Nate:
# call it "The Last Cast"); the old heading still reads as the new one, so
# the editions before then and a run that slips both show it.
OLD_NAMES = {"Parting Shot": "The Last Cast"}
# The Island Edition shares Beach & Weather with the fishing page and has its
# own lead and picks. Since 2026-11-04 (Nate) it runs Beach & Weather, Things
# To Do, Around the Island, then Lunch & Dinner, and closes on a Quote of the
# Day instead of the fishing page's Last Cast ("shouldnt be about fishing").
ISLAND_PAGE_SECTIONS = ["Beach & Weather", "Things To Do", "Around the Island"]
# Each page section's anchor, and its chip in the sticky row of section links
# (None: no chip). Since 2026-11-04.
SECTION_IDS = {"The Bite": ("bite", "The Bite"), "Beach & Weather": ("beach", "Beach"),
               "Regs Corner": ("regs", "Regs"), "The Last Cast": ("shot", None),
               "Things To Do": ("todo", "To Do"), "Around the Island": ("around", "Around")}
KIND_LABEL = {"preview": "Preview", "arrival": "Arrival day", "daily": "Daily",
              "departure": "Last morning", "sample": "Sample"}


# ------------------------------------------------------------------ loading

def load_data(date_iso: str, root: str = HERE) -> dict:
    with open(os.path.join(root, "data", f"{date_iso}.json"), encoding="utf-8") as f:
        return json.load(f)


def parse_report(text: str) -> dict:
    """{'meta': {...}, 'sections': {name: body}} from a report's markdown."""
    meta: dict = {}
    body = text.replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n", body, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        body = body[m.end():]
    sections: dict = {}
    current = None
    for line in body.split("\n"):
        h = re.match(r"^## (.+?)\s*$", line)
        if h:
            current = h.group(1).strip()
            current = OLD_NAMES.get(current, current)
            sections[current] = []
        elif current:
            sections[current].append(line)
    return {"meta": meta,
            "sections": {k: "\n".join(v).strip() for k, v in sections.items()}}


def load_report(date_iso: str, root: str = HERE) -> dict | None:
    path = os.path.join(root, "reports", f"{date_iso}.md")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return parse_report(f.read())


# ------------------------------------------------------------------ numbers

def feet(text: str) -> str:
    """'1 to 2 feet' -> '1-2 ft'."""
    t = re.sub(r"\s+to\s+", "-", text.strip())
    t = re.sub(r"\b(feet|foot)\b", "ft", t)
    return t


def tides_for(data: dict, key: str, date_iso: str) -> list[dict]:
    st = (data.get("tides") or {}).get(key)
    if not st:
        return []
    for day in st["days"]:
        if day["date"] == date_iso:
            return day["events"]
    return []


def surf_period(data: dict, date_iso: str) -> dict | None:
    surf = data.get("surf_zone")
    if not surf:
        return None
    for p in surf.get("periods", []):
        if p.get("date") == date_iso and p.get("is_day"):
            return p
    return None


def day_forecast(data: dict, date_iso: str) -> dict | None:
    for p in data.get("forecast") or []:
        if p.get("start") == date_iso and p.get("is_day"):
            return p
    return None


def night_forecast(data: dict, date_iso: str) -> dict | None:
    for p in data.get("forecast") or []:
        if p.get("start") == date_iso and not p.get("is_day"):
            return p
    return None


def sun_for(data: dict, date_iso: str) -> dict | None:
    for s in ((data.get("weather_model") or {}).get("sun") or []):
        if s["date"] == date_iso:
            return s
    return None


def wave_for(data: dict, date_iso: str) -> dict | None:
    for w in data.get("waves") or []:
        if w["date"] == date_iso:
            return w
    return None


def numbers_date(data: dict) -> str:
    """Previews look ahead to the first island day; every other edition is today."""
    return config.ARRIVAL_DATE if data.get("kind") == "preview" else data["date"]


MOON_EMOJI = {"new": "🌑", "waxing crescent": "🌒", "first quarter": "🌓",
              "waxing gibbous": "🌔", "full": "🌕", "waning gibbous": "🌖",
              "last quarter": "🌗", "third quarter": "🌗", "waning crescent": "🌘"}


def sky_emoji(short: str) -> str:
    """An emoji for the NWS short forecast; the worst weather named wins."""
    s = short.lower()
    for words, emoji in ((("thunder",), "⛈️"), (("snow",), "🌨️"),
                         (("rain", "shower", "drizzle"), "🌧️"), (("fog",), "🌫️"),
                         (("mostly cloudy", "overcast"), "☁️"),
                         (("partly",), "⛅"), (("mostly sunny", "mostly clear"), "🌤️"),
                         (("sunny", "clear"), "☀️")):
        if any(w in s for w in words):
            return emoji
    return "🌤️"


def grass_for(data: dict, day: str) -> tuple[float, list[dict]] | None:
    """(the height, the windows listed on `day`) for Out of the grass: when
    the tide is under that height and the water is off the marsh grass
    (config.GRASS). None when the data has no such reading."""
    grass = ((data.get("tides") or {}).get(config.GRASS["station"]) or {}).get("grass")
    if not grass:
        return None
    for d in grass["days"]:
        if d["date"] == day:
            return grass["under_ft"], d["windows"]
    return None


def grass_span(w: dict, short: bool = False) -> str:
    """'10:56 AM–4:11 PM', or '9:40p Sun–2:59a' for the text."""
    def end(key):
        t = config.short_clock(w[key]) if short else w[key]
        return f"{t} {w[key + '_day']}" if w.get(key + "_day") else t
    return f"{end('from')}–{end('to')}"


def tide_rows(events: list[dict]) -> list[str]:
    """Two tides a row, in order, so each row fits a phone screen."""
    cells = []
    for e in events:
        tag = f" {e['day']}" if e.get("day") else ""
        cells.append(f"{e['type'].capitalize()} {config.short_clock(e['time'])}{tag}")
    return [" · ".join(cells[i:i + 2]) for i in range(0, len(cells), 2)]


def alerts_for(data: dict, edition: str = "fishing") -> list[dict]:
    """Every alert for the fishing edition; the Island Edition leaves out
    the marine-zone ones (a Gale Warning for the water on a sunny beach
    day only confuses someone who is not going out in a boat)."""
    alerts = data.get("alerts") or []
    return [a for a in alerts if a.get("where") != "water"] if edition == "island" else alerts


def alert_when(a: dict, data: dict, short: bool = True) -> str:
    """' from Sat 2:00p' when it has not started, else ' until Mon 6:00a'
    (the page, with room to spare, says '6:00 AM')."""
    def stamp(iso: str) -> str:
        t = dt.datetime.fromisoformat(iso)
        day = "" if t.date().isoformat() == data["date"] else f"{t.strftime('%a')} "
        return f"{day}{config.short_clock(config.clock(t)) if short else config.clock(t)}"
    try:
        made = dt.datetime.fromisoformat(data["generated_utc"].replace("Z", "+00:00"))
        if a.get("onset") and dt.datetime.fromisoformat(a["onset"]) > made:
            return f" from {stamp(a['onset'])}"
        if a.get("ends"):
            return f" until {stamp(a['ends'])}"
    except (KeyError, ValueError):
        pass
    return ""


def _opening_lines(data: dict, day: str, edition: str = "fishing") -> list[str]:
    lines = []
    if day != data["date"]:
        # A preview shows the first island day, and says so once.
        lines.append(f"📅 {config.weekday_label(day)} outlook")
    for a in alerts_for(data, edition):
        lines.append(f"⚠️ {a['event']}{alert_when(a, data)}")
    return lines


def _sky_line(data: dict, day: str) -> list[str]:
    fc = day_forecast(data, day)
    return [f"{sky_emoji(fc['short'])} {fc['short']}, high {fc['temp_f']}°"] if fc else []


def _wind_line(data: dict, day: str) -> list[str]:
    fc = day_forecast(data, day)
    return [f"💨 Wind {fc['wind']}"] if fc else []


def _beach_lines(data: dict, day: str) -> list[str]:
    """Surf and rip risk, then the water temperature."""
    ahead = day != data["date"]
    lines, beach = [], []
    sp = surf_period(data, day)
    if sp and sp["fields"].get("surf_height"):
        beach.append(f"Surf {feet(sp['fields']['surf_height'])}")
    else:
        w = wave_for(data, day)
        if w and w.get("max_ft") is not None:
            beach.append(f"Waves to {w['max_ft']:g} ft (model)")
    if sp and sp["fields"].get("rip_current_risk"):
        beach.append(f"rip risk {sp['fields']['rip_current_risk'].lower()}")
    if beach:
        lines.append("🏖️ " + ", ".join(beach))
    buoy = data.get("buoy") or {}
    if not ahead and buoy.get("water_temp_f") is not None:
        lines.append(f"🌡️ Water {buoy['water_temp_f']}°")
    elif sp and sp["fields"].get("water_temp"):
        lines.append(f"🌡️ Water {sp['fields']['water_temp'].lower()}")
    return lines


def _sun_line(data: dict, day: str) -> list[str]:
    sun = sun_for(data, day)
    if not sun:
        return []
    return [f"🌅 Sun up {config.short_clock(sun['sunrise'])}, down "
            f"{config.short_clock(sun['sunset'])}"]


def numbers_block(data: dict) -> list[str]:
    """The fishing text's numbers, every one straight from data/<date>.json.

    One short line per thing, an emoji up front, so each reads at a glance
    on a phone without wrapping.
    """
    day = numbers_date(data)
    ahead = day != data["date"]
    lines = _opening_lines(data, day)
    sound = tides_for(data, "sound", day)
    if sound:
        lines.append("🌊 Sound tides")
        lines.extend(tide_rows(sound))
    grass = grass_for(data, day)
    if grass and grass[1]:
        spans = [grass_span(w, short=True) for w in grass[1]]
        lines.append(f"🌾 Out of the grass (under {grass[0]:g} ft)")
        lines.extend(" · ".join(spans[i:i + 2]) for i in range(0, len(spans), 2))
    lines += _sky_line(data, day) + _wind_line(data, day) + _beach_lines(data, day)
    marine = data.get("marine") or {}
    if not ahead and marine.get("periods"):
        lines.append(f"⛵ {marine['periods'][0]['headline']}")
    lines += _sun_line(data, day)
    # The moon in the data is today's, so a preview leaves it out.
    moon = None if ahead else (data.get("moon") or {}).get("phase")
    if moon:
        name = moon if moon.endswith("moon") else f"{moon} moon"
        emoji = MOON_EMOJI.get(moon.removesuffix(" moon").lower(), "🌙")
        lines.append(f"{emoji} {name[0].upper()}{name[1:]}")
    return lines


def island_numbers_block(data: dict) -> list[str]:
    """The Island Edition's numbers: the day and night ashore, the beach,
    the beach-side low tides (for walking the flats and hunting shells and
    shark teeth), and the sun. No sound tides, marine forecast or moon."""
    day = numbers_date(data)
    ahead = day != data["date"]
    lines = _opening_lines(data, day, "island") + _sky_line(data, day)
    night = night_forecast(data, day)
    if night:
        when = f"{dt.date.fromisoformat(day).strftime('%a')} night" if ahead else "Tonight"
        lines.append(f"🌙 {when} {night['short'].lower()}, low {night['temp_f']}°")
    lines += _wind_line(data, day) + _beach_lines(data, day)
    # The ocean station's lows on this date; a spillover tide tagged with
    # another weekday belongs to that day, not this one.
    lows = [e for e in tides_for(data, "ocean", day) if e["type"] == "low" and not e.get("day")]
    if lows:
        lines.append("🐚 Beach low tide " + ", ".join(config.short_clock(e["time"]) for e in lows))
    return lines + _sun_line(data, day)


def edition_url(date_iso: str, edition: str = "fishing") -> str:
    return f"{config.SITE_BASE}/{config.page_path(date_iso, edition)}"


def _text(head: str, prose: str, numbers: list[str], url: str) -> str:
    parts = [head]
    if prose:
        parts.append(prose)
    if numbers:
        parts.append("\n".join(numbers))
    # The link on its own line under its cue (Nate, 2026-11-05, exactly
    # this wording; it was "Full report: <link>").
    parts.append(f"Click the link below for the Full Daily Topsail Report:\n{url}")
    return "\n\n".join(parts) + "\n"


def _prose(report: dict | None, section: str) -> str:
    return (report or {}).get("sections", {}).get(section, "").strip()


def build_text(data: dict, report: dict | None) -> str:
    """The fishing edition's text."""
    return _text(f"{config.TEXT_MARKER}, {config.weekday_label(data['date'])}",
                 _prose(report, "Text"), numbers_block(data), edition_url(data["date"]))


def build_island_text(data: dict, report: dict | None) -> str:
    """The Island Edition's text. It opens with the same marker, so the same
    Shortcut check guards it."""
    return _text(f"{config.TEXT_MARKER}, {config.ISLAND_NAME}, "
                 f"{config.weekday_label(data['date'])}",
                 _prose(report, "Island Text"), island_numbers_block(data),
                 edition_url(data["date"], "island"))


# ------------------------------------------------------------------ HTML

def inline_md(text: str) -> str:
    out = html.escape(text, quote=True)
    out = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                 lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", out)
    return out


# A bullet that opens with a bold label and a colon is a fact row
# ("**When:** 10:14 AM to 4:07 PM"); one that opens with a bold title is an
# item card ("**Walk a pier.** Surf City Ocean Pier, ..."). Since 2026-11-04,
# when Nate found the pages "very long walls of text" on a phone.
FACT = re.compile(r"^\*\*([^*]{1,40}?):\*\*\s*(.*)$|^\*\*([^*]{1,40}?)\*\*:\s*(.*)$")
TITLED = re.compile(r"^\*\*([^*]+?)\*\*\s*(.+)$")


def _li(item: str) -> str:
    m = FACT.match(item)
    if m:
        label, rest = (m.group(1), m.group(2)) if m.group(1) is not None else (m.group(3), m.group(4))
        return (f"<li class=fact><span class=fk>{inline_md(label)}</span>"
                f"<span class=fv>{inline_md(rest)}</span></li>")
    m = TITLED.match(item)
    if m:
        return f"<li class=item><b class=it>{inline_md(m.group(1))}</b> {inline_md(m.group(2))}</li>"
    return f"<li class=pl>{inline_md(item)}</li>"


def block_md(text: str) -> str:
    """Paragraphs, '- ' bullets, '> ' callouts and '### ' subheads; that is the
    whole dialect. Each subhead opens a block that runs to the next one."""
    out, para, items, note = [], [], [], []
    in_sub = False

    def flush():
        if para:
            joined = " ".join(para)
            cls = " class=li" if joined.startswith("**") else ""
            out.append(f"<p{cls}>{inline_md(joined)}</p>")
            para.clear()
        if items:
            out.append("<ul class=list>" + "".join(_li(i) for i in items) + "</ul>")
            items.clear()
        if note:
            out.append(f"<div class=callout>{inline_md(' '.join(note))}</div>")
            note.clear()

    for line in text.split("\n"):
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("### "):
            flush()
            if in_sub:
                out.append("</div>")
            out.append(f"<div class=sub><h3>{inline_md(s[4:])}</h3>")
            in_sub = True
        elif s.startswith(">"):
            if para or items:
                flush()
            note.append(s[1:].strip())
        elif s.startswith("- "):
            if para or note:
                flush()
            items.append(s[2:])
        elif items and line.startswith("  "):
            items[-1] += " " + s
        else:
            if items or note:
                flush()
            para.append(s)
    flush()
    if in_sub:
        out.append("</div>")
    return "\n".join(out)


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def _minutes(clock_text: str) -> int:
    """'3:47 AM' -> 227, minutes after midnight."""
    t = dt.datetime.strptime(clock_text.strip(), "%I:%M %p")
    return t.hour * 60 + t.minute


def _range(text: str) -> str:
    """'N 7 to 10 mph' -> 'N 7–10 mph'."""
    return re.sub(r"\s+to\s+", "–", text.strip())


# ---- the tide chart

def tide_timeline(data: dict, key: str, day: str) -> list[tuple]:
    """Every tide the data holds for a station, in order, as (minutes after
    `day`'s midnight, feet, 'high' or 'low', '3:47 AM'). A spillover tide,
    tagged with another weekday, lands on its own day."""
    st = (data.get("tides") or {}).get(key)
    if not st:
        return []
    d0 = dt.date.fromisoformat(day)
    seen = {}
    for block in st["days"]:
        base = dt.date.fromisoformat(block["date"])
        for e in block["events"]:
            when = base
            for step in ((-1, 1) if e.get("day") else ()):
                near = base + dt.timedelta(days=step)
                if near.strftime("%a") == e["day"]:
                    when = near
            m = (when - d0).days * 1440 + _minutes(e["time"])
            seen[m] = (m, e["height_ft"], e["type"], e["time"])
    return sorted(seen.values())


def tide_height(timeline: list[tuple], m: float) -> float | None:
    """The height at minute m on the smooth (cosine) curve between the
    predicted tides either side of it, the usual way to draw a tide."""
    for (m0, h0, *_), (m1, h1, *_) in zip(timeline, timeline[1:]):
        if m0 <= m <= m1:
            return h0 + (h1 - h0) * (1 - math.cos(math.pi * (m - m0) / (m1 - m0))) / 2
    return None


# One chart per station, drawn in a 340-wide box (about its size on a phone,
# beside its twin on an iPad, and in the desktop sidebar, so its labels stay
# near 12px everywhere). The day runs from the hour of the first tide to
# midnight; side-by-side stations share the time and height scales.
TC_W, TC_H = 340, 142
TC_X0, TC_X1, TC_YT, TC_YB = 12, 328, 42, 106
TIDE_CURVE_NOTE = ("Curves are drawn smooth between NOAA's predicted highs and lows; "
                   "shading marks the hours before sunrise and after sunset.")


def tide_domain(data: dict, day: str, keys: tuple[str, ...]) -> tuple | None:
    """(start minute, low ft, high ft) shared by the charts for `keys`."""
    starts, heights = [], []
    for key in keys:
        tl = tide_timeline(data, key, day)
        inside = [m for m, *_ in tl if 0 <= m < 1440]
        if not inside:
            continue
        starts.append(0 if any(m < 0 for m, *_ in tl) else inside[0] // 60 * 60)
        heights += [h for m, h, *_ in tl if -400 <= m <= 1840]
    if not starts:
        return None
    return min(starts), min(0.0, min(heights)), max(heights)


def tide_chart(data: dict, key: str, day: str, dom: tuple, label: str,
               mark_ft: float | None = None) -> str:
    """`mark_ft` draws a dashed line at that height (Out of the grass)."""
    start, lo, hi = dom
    tl = tide_timeline(data, key, day)
    if not tl:
        return ""
    first, last = max(start, tl[0][0]), min(1440, tl[-1][0])
    if last <= first:
        return ""
    span = (hi - lo) or 1.0

    def x(m: float) -> float:
        return TC_X0 + (m - start) / (1440 - start) * (TC_X1 - TC_X0)

    def y(h: float) -> float:
        return TC_YB - (h - lo) / span * (TC_YB - TC_YT)

    pts = [(x(m), y(tide_height(tl, m))) for m in [*range(first, last, 5), last]]
    curve = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = f"{curve} L{pts[-1][0]:.1f},{TC_YB} L{pts[0][0]:.1f},{TC_YB} Z"
    out = []
    sun = sun_for(data, day)
    if sun:
        rise, sets = _minutes(sun["sunrise"]), _minutes(sun["sunset"])
        if rise > start:
            out.append(f'<rect class="night" x="{x(start):.1f}" y="0" '
                       f'width="{x(rise) - x(start):.1f}" height="{TC_YB}"/>')
        out.append(f'<rect class="night" x="{x(sets):.1f}" y="0" '
                   f'width="{x(1440) - x(sets):.1f}" height="{TC_YB}"/>')
    out.append(f'<path class="area" d="{area}"/>')
    out.append(f'<line class="base" x1="{TC_X0}" y1="{TC_YB}" x2="{TC_X1}" y2="{TC_YB}"/>')
    # A low's label sits under its dot; a clock label that would land on
    # one is left out (its tick stays).
    low_labels = [x(m) for m, h, kind, _ in tl
                  if kind == "low" and start <= m < 1440 and y(h) > TC_YB - 30]
    for m, tick in ((360, "6a"), (720, "noon"), (1080, "6p")):
        if m - start >= 45:
            out.append(f'<line class="base" x1="{x(m):.1f}" y1="{TC_YB}" x2="{x(m):.1f}" '
                       f'y2="{TC_YB + 4}"/>')
            if all(abs(x(m) - lx) > 34 for lx in low_labels):
                out.append(f'<text class="ax" x="{x(m):.1f}" y="{TC_YB + 16}" '
                           f'text-anchor="middle">{tick}</text>')
    if mark_ft is not None and lo < mark_ft < hi:
        gy = y(mark_ft)
        out.append(f'<line class="gl" x1="{TC_X0}" y1="{gy:.1f}" x2="{TC_X1}" y2="{gy:.1f}"/>'
                   f'<text class="gt" x="{TC_X1}" y="{gy - 4:.1f}" text-anchor="end">'
                   f'{mark_ft:g} ft</text>')
    out.append(f'<path class="curve" d="{curve}"/>')
    for m, h, kind, clk in tl:
        if not start <= m < 1440:
            continue
        px, py = x(m), y(h)
        if px < 34:
            anchor, tx = "start", px - 6
        elif px > TC_W - 34:
            anchor, tx = "end", px + 6
        else:
            anchor, tx = "middle", px
        t1, t2 = (py - 23, py - 10) if kind == "high" else (py + 19, py + 32)
        out.append(f'<circle class="mk" cx="{px:.1f}" cy="{py:.1f}" r="4"/>'
                   f'<text class="tm" x="{tx:.1f}" y="{t1:.1f}" text-anchor="{anchor}">'
                   f'{esc(config.short_clock(clk))}</text>'
                   f'<text x="{tx:.1f}" y="{t2:.1f}" text-anchor="{anchor}">{h:g} ft</text>')
    out.append(f'<line class="xh" x1="0" y1="0" x2="0" y2="{TC_YB}" visibility="hidden"/>'
               '<circle class="xd" cx="0" cy="0" r="4" visibility="hidden"/>')
    cfg = {"s": start, "a": first, "b": last, "lo": lo, "hi": hi, "w": TC_W,
           "x0": TC_X0, "x1": TC_X1, "yt": TC_YT, "yb": TC_YB,
           "ev": [[m, h] for m, h, *_ in tl]}
    said = ", ".join(f"{kind} {clk} {h:g} ft" for m, h, kind, clk in tl if 0 <= m < 1440)
    return (f"<figure class=tidechart tabindex=0 role=group "
            f"aria-label='{esc(label)} tide curve: {esc(said)}'>"
            f"<svg viewBox='0 0 {TC_W} {TC_H}' aria-hidden=true "
            f"data-tide='{esc(json.dumps(cfg))}'>{''.join(out)}</svg>"
            "<div class=tip aria-live=polite hidden></div></figure>")


def tide_list(data: dict, key: str, day: str) -> str:
    """The chart's table twin: every tide, its time and height."""
    return "<ul class=tidelist>" + "".join(
        f"<li><span class='tt {e['type']}'>{e['type'][0].upper()}</span> <b>{esc(e['time'])}</b>"
        f"{' <small>' + esc(e['day']) + '</small>' if e.get('day') else ''} "
        f"<small>{e['height_ft']:g} ft</small></li>" for e in tides_for(data, key, day)) + "</ul>"


def grass_line(data: dict, day: str) -> str:
    """Out of the grass under its station's tides: each window, or that the
    tide stays in the grass."""
    grass = grass_for(data, day)
    if not grass:
        return ""
    under, windows = grass
    said = (", ".join(f"<b>{esc(grass_span(w))}</b>" for w in windows) if windows
            else "the tide stays above it today")
    return f"<p class=grass>🌾 Out of the grass, under {under:g} ft: {said}</p>"


def tides_card(data: dict, day: str, keys: tuple[str, ...], title: str, note: str,
               grass: bool = False) -> str:
    """`note` is HTML, escaped by the caller. `grass` adds Out of the grass
    (the fishing edition) to its station."""
    dom = tide_domain(data, day, keys)
    stations = []
    for st in (s for s in config.TIDE_STATIONS if s["key"] in keys):
        if not tides_for(data, st["key"], day):
            stations.append(f"<div class=station><h4>{esc(st['label'])}</h4>"
                            "<p class=muted>no reading</p></div>")
            continue
        here = grass and st["key"] == config.GRASS["station"] and grass_for(data, day)
        chart = (tide_chart(data, st["key"], day, dom, st["label"],
                            here[0] if here else None) if dom else "")
        stations.append(f"<div class=station><h4>{esc(st['label'])}</h4>{chart}"
                        f"{tide_list(data, st['key'], day)}"
                        f"{grass_line(data, day) if here else ''}</div>")
    return (f"<div class='card wide'><h3>{esc(title)}</h3><div class=stations>"
            f"{''.join(stations)}</div><p class=muted>{note}</p></div>")


# ---- the wind by the hour

COMPASS = {n: i * 22.5 for i, n in enumerate(
    "N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW".split())}
# A down arrow, turned by the bearing the wind comes FROM, points the way it blows.
ARROW = ("<svg viewBox='0 0 16 16' aria-hidden=true style='transform:rotate({deg}deg)'>"
         "<path d='M8 2v11M3.5 8.5 8 13l4.5-4.5'/></svg>")


def wind_row(hourly: list[dict]) -> str:
    cells = []
    for h in hourly:
        deg = COMPASS.get(h["from"])
        arrow = ARROW.format(deg=f"{deg:g}") if deg is not None else "<span>&middot;</span>"
        when = config.short_clock(h["time"]).replace(":00", "")
        cells.append(f"<li><span class=t>{esc(when)}</span>{arrow}<b>{esc(h['speed_mph'])}</b>"
                     f"<small>g{esc(h['gust_mph'])}</small><span class=d>{esc(h['from'])}</span></li>")
    return "<ol class=windrow>" + "".join(cells) + "</ol>"


# ---- at a glance

def _tile(label: str, value: str, sub: str = "") -> str:
    """`value` is HTML (it may carry an emoji or &deg;); the rest is escaped here."""
    return (f"<li class=tile><span class=k>{esc(label)}</span><span class=v>{value}</span>"
            + (f"<span class=s>{esc(sub)}</span>" if sub else "") + "</li>")


def glance(data: dict, edition: str = "fishing") -> str:
    """The tiles at the top of the numbers: the day in six numbers, every one
    from data/<date>.json."""
    day = numbers_date(data)
    ahead = day != data["date"]
    island = edition == "island"
    tiles = []
    fc, night = day_forecast(data, day), night_forecast(data, day)
    if fc:
        sub = fc["short"] + (f"; tonight {night['short'].lower()}, {night['temp_f']}°"
                             if night else "")
        tiles.append(_tile(dt.date.fromisoformat(day).strftime("%A") if ahead else "Today",
                           f"{sky_emoji(fc['short'])} {esc(fc['temp_f'])}&deg;", sub))
        wind_sub = ""
        gust = re.search(r"gusts as high as (\d+) mph", fc.get("detailed") or "")
        if gust:
            wind_sub = f"Gusts to {gust.group(1)} mph"
        marine = data.get("marine") or {}
        if not island and not ahead and marine.get("periods"):
            m = re.match(r"([NSEW]{1,3}) winds? (\d+(?: to \d+)?) kt",
                         marine["periods"][0]["headline"])
            if m:
                wind_sub = f"On the water {m.group(1)} {_range(m.group(2))} kt"
        tiles.append(_tile("Wind", esc(_range(fc["wind"])), wind_sub))
    sp = surf_period(data, day)
    f = sp["fields"] if sp else {}
    if f.get("surf_height"):
        tiles.append(_tile("Surf", esc(feet(f["surf_height"]).replace("-", "–")),
                           f"Rip risk {f['rip_current_risk'].lower()}"
                           if f.get("rip_current_risk") else ""))
    else:
        w = wave_for(data, day)
        if w and w.get("max_ft") is not None:
            tiles.append(_tile("Waves", f"{w['max_ft']:g} ft", "Model, just offshore"))
    buoy = data.get("buoy") or {}
    if not ahead and buoy.get("water_temp_f") is not None:
        sound = data.get("sound_temp")
        sub = (f"Ocean; sound side ~{sound['water_temp_f']:.0f}°" if sound and not island
               else "Ocean, at the buoy")
        tiles.append(_tile("Water", f"{esc(buoy['water_temp_f'])}&deg;", sub))
    elif f.get("water_temp"):
        n = re.search(r"\d+", f["water_temp"])
        if n:
            tiles.append(_tile("Water", f"~{n.group()}&deg;", "NWS surf forecast"))
    sun = sun_for(data, day)
    if sun:
        tiles.append(_tile("Sunset", esc(sun["sunset"]), f"Sunrise {sun['sunrise']}") if island
                     else _tile("Sunrise", esc(sun["sunrise"]), f"Sunset {sun['sunset']}"))
    if island:
        lows = [e for e in tides_for(data, "ocean", day) if e["type"] == "low" and not e.get("day")]
        if lows:
            tiles.append(_tile("Low tide", esc(lows[0]["time"]),
                               "And " + ", ".join(e["time"] for e in lows[1:]) if lows[1:]
                               else "Beach side"))
    else:
        moon = data.get("moon") or {}
        # The moon in the data is the morning's, so a preview leaves it out.
        if not ahead and moon.get("phase"):
            emoji = MOON_EMOJI.get(moon["phase"].removesuffix(" moon").lower(), "🌙")
            lit = f" {moon['illumination_pct']}%" if moon.get("illumination_pct") is not None else ""
            tiles.append(_tile("Moon", f"{emoji}{esc(lit)}",
                               ", ".join(p for p in (moon["phase"].capitalize(),
                                                     (moon.get("tides") or "").split(" (")[0]) if p)))
    source = (data.get("weather_model") or {}).get("sun_source")
    note = (f"<p class=muted>Sun times {esc(source)}: Open-Meteo did not answer.</p>"
            if source and sun else "")
    return "<ul class=tiles>" + "".join(tiles) + "</ul>" + note


# ---- the numbers, in cards

def numbers_panel(data: dict) -> tuple[str, str]:
    """The fishing edition's cards: (the tides, which ride up with the tiles;
    the rest, which follow the write-up on a phone)."""
    day = numbers_date(data)
    ahead = day != data["date"]
    cards = []
    moon = data.get("moon") or {}
    moon_note = (f"Moon: {esc(moon['phase'])}, {esc(moon.get('tides', ''))}. "
                 if moon.get("phase") and not ahead else "")
    # The second chart is New Topsail Inlet from 2026-11-09 on; a morning
    # fetched before then has only the oceanfront station.
    inlet = (data.get("tides") or {}).get("inlet")
    second = "inlet" if inlet else "ocean"
    st = next(s for s in config.TIDE_STATIONS if s["key"] == second)
    grass = grass_for(data, day)
    grass_note = (f"Out of the grass: the {esc(st['name'])} tide under {grass[0]:g} ft, when "
                  f"the water is off the marsh grass (it clears the grass near "
                  f"{config.GRASS['grass_ft']:g} ft). "
                  if grass else "")
    inlet_note = f"New Topsail Inlet: {esc(st['note'])}. " if inlet else ""
    tides = tides_card(data, day, ("sound", second), "Tides",
                       f"The sound station leads: {esc(config.TIDE_STATIONS[0]['note'])}. "
                       f"{inlet_note}{grass_note}{moon_note}{TIDE_CURVE_NOTE}", grass=True)

    wind_bits = []
    hourly = (data.get("weather_model") or {}).get("wind") or []
    if hourly and not ahead:
        wind_bits.append(wind_row(hourly))
    items = []
    marine = data.get("marine") or {}
    if marine.get("periods") and not ahead:
        p0 = marine["periods"][0]
        items.append(f"<li><b>{esc(p0['name'])}, on the water:</b> {esc(p0['text'])}</li>")
        if len(marine["periods"]) > 1:
            p1 = marine["periods"][1]
            items.append(f"<li><b>{esc(p1['name'])}:</b> {esc(p1['headline'])}</li>")
    fc = day_forecast(data, day)
    if fc:
        items.append(f"<li><b>Ashore:</b> {esc(fc['detailed'])}</li>")
    if items:
        wind_bits.append("<ul>" + "".join(items) + "</ul>")
    cards.append("<div class='card wide'><h3>Wind &amp; weather</h3>"
                 + ("".join(wind_bits) or "<p class=muted>no reading</p>")
                 + f"<p class=muted>Marine zone {esc(config.MARINE_ZONE)} "
                   f"({esc(config.MARINE_ZONE_NAME)}). "
                 + ("Hourly row in mph, g = gusts; arrows point the way the wind blows."
                    if hourly and not ahead else "") + "</p></div>")

    water = []
    buoy = data.get("buoy")
    if buoy and buoy.get("water_temp_f") is not None:
        water.append(f"<li><b>Ocean {buoy['water_temp_f']}&deg;F</b> measured at the "
                     f"{esc(buoy['station'])}, {buoy['miles']} mi {esc(buoy['bearing'])}, "
                     f"{esc(buoy['observed_et'])} ET</li>")
    st = data.get("sound_temp")
    if st:
        water.append(f"<li><b>Sound-side proxy {st['water_temp_f']:.0f}&deg;F</b> at "
                     f"{esc(st['station'])}, {st['miles']} mi {esc(st['bearing'])} "
                     f"(no gauge in Topsail Sound)</li>")
    sp = surf_period(data, day)
    if sp and sp["fields"].get("water_temp"):
        water.append(f"<li>NWS surf forecast: {esc(sp['fields']['water_temp'].lower())}</li>")
    cards.append("<div class=card><h3>Water temp</h3><ul>"
                 + ("".join(water) or "<li class=muted>no reading</li>") + "</ul></div>")

    surf = []
    if sp:
        f = sp["fields"]
        for key, label in (("surf_height", "Surf"), ("rip_current_risk", "Rip current risk"),
                           ("uv_index", "UV"), ("waterspouts", "Waterspout risk")):
            if f.get(key):
                surf.append(f"<li><b>{label}:</b> {esc(f[key])}</li>")
    if buoy and buoy.get("wave_ft") is not None and not ahead:
        surf.append(f"<li><b>Buoy waves:</b> {buoy['wave_ft']:g} ft at "
                    f"{esc(buoy.get('period_s') and int(buoy['period_s']))} s from "
                    f"{esc(buoy.get('wave_from') or '?')}</li>")
    w = wave_for(data, day)
    if w and w.get("max_ft") is not None:
        surf.append(f"<li><b>Model waves:</b> up to {w['max_ft']:g} ft from "
                    f"{esc(w.get('from') or '?')}</li>")
    surf_src = (f"<p class=muted>NWS Wilmington surf zone forecast, Coastal Pender, "
                f"issued {esc((data.get('surf_zone') or {}).get('issued'))}</p>" if sp else
                "<p class=muted>No NWS surf zone forecast for this day.</p>")
    cards.append("<div class=card><h3>Surf</h3><ul>" + ("".join(surf) or
                 "<li class=muted>no reading</li>") + "</ul>" + surf_src + "</div>")
    return tides, "<div class=numbers>" + "".join(cards) + "</div>"


def island_numbers_panel(data: dict) -> tuple[str, str]:
    """The Island Edition's cards: (the beach-side tides; nothing else). The
    day and night forecast and the beach card are gone since 2026-11-04 (Nate:
    "they're redundant"): the tiles, the Outlook and Beach & Weather carry
    them, and the Surf tile shows the rip risk whenever NWS rates one."""
    tides = tides_card(data, numbers_date(data), ("ocean",), "Beach tides",
                       f"Low tide uncovers the most beach. {TIDE_CURVE_NOTE}")
    return tides, ""


# ---- the week

def outlook_days(data: dict) -> list[dict]:
    """The NWS periods paired into days: each daytime period and the night
    after it. A lone night at the head of the list (an 'Overnight') is left out."""
    days = []
    for p in data.get("forecast") or []:
        if p.get("is_day"):
            days.append({"date": p["start"], "day": p, "night": None})
        elif days and days[-1]["date"] == p["start"] and days[-1]["night"] is None:
            days[-1]["night"] = p
    return days[:7]


def outlook(data: dict) -> str:
    items = []
    for d in outlook_days(data):
        p, n = d["day"], d["night"]
        name = ("Today" if d["date"] == data["date"]
                else dt.date.fromisoformat(d["date"]).strftime("%a"))
        low = f" <small>{esc(n['temp_f'])}&deg;</small>" if n else ""
        rain = max(p.get("pop_pct") or 0, (n or {}).get("pop_pct") or 0)
        items.append(f"<li><b class=dn>{name}</b><span class=sk aria-hidden=true>"
                     f"{sky_emoji(p['short'])}</span><span class=hl>{esc(p['temp_f'])}&deg;{low}</span>"
                     f"<span class=sh>{esc(p['short'])}"
                     f"{f' <span class=rain>Rain {rain}%</span>' if rain >= 10 else ''}</span>"
                     f"<span class=wd>{esc(_range(p['wind']))}</span></li>")
    if not items:
        return ""
    return ("<section class=out id=week><h2>Outlook</h2><ol class=outlook>" + "".join(items)
            + "</ol><p class=muted>NWS Wilmington point forecast for Topsail Beach: "
              "the day's high, then the night's low.</p></section>")


CSS = """
:root{color-scheme:light dark;--bg:#f6f3ec;--ink:#1d2a33;--muted:#59666f;--card:#fffdf8;--line:#e2dccf;--chip:#ebe5d8;--sea:#0d5c75;--tide:#0b6e96;--night:rgba(29,42,51,.07);--hi:#0d5c75;--lo:#8a6d3b;--warn-bg:#fbe9df;--warn:#b4461c;--open:#1e7b46;--soon:#8a5a00;--shut:#b42318;--sans:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;--serif:Georgia,'Times New Roman',serif}
@media (prefers-color-scheme:dark){:root{--bg:#0f1a20;--ink:#e8eef1;--muted:#9aa9b1;--card:#16242c;--line:#263a44;--chip:#1d3039;--sea:#6cc3dc;--tide:#2f9ccc;--night:rgba(0,0,0,.32);--hi:#2a85a8;--lo:#9a7a44;--warn-bg:#3a2119;--warn:#f08a5d;--open:#6fd59a;--soon:#f2c45a;--shut:#ff8f84}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:1.0625rem/1.6 var(--serif)}
.wrap{max-width:760px;margin:0 auto;padding:18px 16px 40px}
a{color:var(--sea);text-underline-offset:2px}p{margin:0 0 .9em;text-wrap:pretty}
.mast{text-align:center;padding-bottom:14px;border-bottom:3px double var(--ink)}
.mast h1{font:700 2.1rem/1.1 var(--serif);margin:0;letter-spacing:.01em}
.mast .sub{font:600 .72rem/1.6 var(--sans);text-transform:uppercase;letter-spacing:.12em;color:var(--muted);margin-top:6px}
.mast .sub span{white-space:nowrap}
.switch{display:flex;gap:4px;max-width:340px;margin:14px auto 0;padding:4px;background:var(--chip);border-radius:999px;font:600 .95rem/1 var(--sans)}
.switch a,.switch span{flex:1;display:flex;align-items:center;justify-content:center;min-height:44px;border-radius:999px;text-decoration:none;color:var(--muted)}
.switch a:hover{color:var(--ink)}
.switch span[aria-current]{background:var(--card);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.18)}
.alert{display:flex;flex-wrap:wrap;gap:2px 8px;align-items:baseline;background:var(--warn-bg);border-left:4px solid var(--warn);border-radius:10px;padding:10px 14px;margin:16px 0 0;font:.95rem/1.45 var(--sans)}
.alert .w{color:var(--muted);font-size:.85rem}
.lead{font-size:1.06rem}
h2{font:700 .82rem/1.3 var(--sans);text-transform:uppercase;letter-spacing:.12em;color:var(--sea);margin:0 0 12px;padding-top:12px;border-top:2px solid var(--ink)}
h3{font:700 1.02rem/1.3 var(--sans);margin:1.3em 0 .4em}
h2.headline{font:700 1.8rem/1.2 var(--serif);margin:20px 0 12px;padding:0;border:0;text-transform:none;letter-spacing:0;color:var(--ink);text-wrap:balance}
section,.side,.more{margin-top:34px}
.side{margin-top:18px}
.page{display:flex;flex-direction:column}.col-main,.col-side{display:contents}
.top{order:1}.side{order:3}.body{order:4}.more{order:5}.out{order:6}.src{order:7}
.isl .body{display:contents}.isl .body>section{order:6}.isl #beach{order:4}.isl .out{order:5}
.isl .out{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 16px 12px;margin-top:18px}.isl .out>h2{border:0;padding:0}.isl .out>h2::before{content:"🗓️ "}
.body ul{padding-left:1.25em}.body li{margin:.4em 0}
.tiles{list-style:none;margin:0 0 12px;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.tile{display:flex;flex-direction:column;gap:2px;min-width:0;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;font-family:var(--sans)}
.tile .k{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.tile .v{font-size:1.45rem;font-weight:650;line-height:1.25}
.tile .s{font-size:.82rem;line-height:1.35;color:var(--muted)}
.tiles .tile:last-child:nth-child(odd){grid-column:1/-1}
.numbers{display:grid;grid-template-columns:minmax(0,1fr);gap:12px}
.card{min-width:0;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;font:.9375rem/1.5 var(--sans)}
.card h3{margin:0 0 8px}.card h4{margin:0;font-size:.85rem;color:var(--muted)}
.card ul{margin:0;padding-left:18px}.card li{margin:4px 0}
.muted{color:var(--muted);font-size:.85rem;font-family:var(--sans)}.card p.muted{margin:10px 0 0}
.stations{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px 24px}
.tidelist{list-style:none;padding:0!important;margin:2px 0 0!important;display:grid;grid-template-columns:1fr 1fr;gap:2px 12px}
.tidelist li{margin:0;white-space:nowrap}
.tt{display:inline-block;width:1.4em;text-align:center;border-radius:4px;color:#fff;font-weight:700;font-size:.75em;line-height:1.5}
.tt.high{background:var(--hi)}.tt.low{background:var(--lo)}
.tidechart{position:relative;margin:4px 0 2px;border-radius:8px}
.tidechart svg{display:block;width:100%;max-width:520px;height:auto;touch-action:pan-y;overflow:visible}
.tidechart .night{fill:var(--night)}
.tidechart .area{fill:var(--tide);fill-opacity:.12}
.tidechart .curve{fill:none;stroke:var(--tide);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.tidechart .base{stroke:var(--line);stroke-width:1}
.tidechart .mk,.tidechart .xd{fill:var(--tide);stroke:var(--card);stroke-width:2}
.tidechart .xh{stroke:var(--muted);stroke-width:1}
.tidechart text{font:11px var(--sans);fill:var(--muted)}
.tidechart text.tm{font-size:12px;font-weight:700;fill:var(--ink)}
.tidechart text.ax{font-size:10.5px}
.tidechart .gl{stroke:var(--muted);stroke-width:1;stroke-dasharray:4 3}
.tidechart text.gt{font-size:10.5px}
.grass{margin:6px 0 0!important;font:.9rem/1.4 var(--sans)}.grass b{white-space:nowrap}
.tip{position:absolute;top:-4px;transform:translate(-50%,-100%);background:var(--ink);color:var(--bg);font:600 .8rem/1.3 var(--sans);padding:5px 9px;border-radius:6px;white-space:nowrap;pointer-events:none}
.windrow{list-style:none;padding:0!important;margin:2px 0 12px!important;display:grid;grid-template-columns:repeat(auto-fit,minmax(44px,1fr));text-align:center;border:1px solid var(--line);border-radius:10px}
.windrow li{display:flex;flex-direction:column;align-items:center;gap:1px;margin:0;padding:6px 2px;border-left:1px solid var(--line)}
.windrow li:first-child{border-left:0}
.windrow .t,.windrow small,.windrow .d{font-size:.72rem;color:var(--muted)}
.windrow svg{width:18px;height:18px;fill:none;stroke:var(--tide);stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.windrow b{font-size:1.05rem;line-height:1.2}
.outlook{list-style:none;margin:0;padding:0;font-family:var(--sans)}
.outlook li{display:grid;grid-template-columns:3.2em 1.9em 4.9em minmax(0,1fr);grid-template-areas:"dn sk hl sh" "dn sk hl wd";column-gap:8px;align-items:center;padding:9px 0;border-top:1px solid var(--line)}
.outlook li:first-child{border-top:0}
.outlook .dn{grid-area:dn}.outlook .sk{grid-area:sk;font-size:1.3rem;line-height:1}
.outlook .hl{grid-area:hl;font-size:1.1rem;font-weight:650}.outlook .hl small{font-size:.85em;font-weight:500;color:var(--muted)}
.outlook .sh{grid-area:sh;font-size:.92rem;line-height:1.3}.outlook .wd{grid-area:wd;font-size:.8rem;color:var(--muted)}
.outlook .rain{color:var(--tide);font-weight:600;white-space:nowrap}
.out p.muted{margin-top:8px}
.src details{font:.875rem/1.55 var(--sans)}
.src summary{cursor:pointer;list-style:none}.src summary h2{margin:0}.src details[open] summary h2{margin-bottom:12px}.src summary::-webkit-details-marker{display:none}
.src summary{display:flex;align-items:center;gap:12px;padding-top:12px;border-top:2px solid var(--ink)}.src summary h2{border:0;padding:0}
.src ul{padding-left:0}
footer{margin-top:44px;padding-top:14px;border-top:1px solid var(--line);font:.85rem/1.55 var(--sans);color:var(--muted)}
.archive{margin-top:14px}
.archive summary{display:inline-flex;align-items:center;gap:10px;min-height:44px;padding:0 18px;border-radius:999px;background:var(--chip);color:var(--ink);font-weight:600;cursor:pointer;list-style:none}
.archive summary::-webkit-details-marker{display:none}
.archive summary::after{content:"";width:.45em;height:.45em;margin-left:2px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:translateY(-.15em) rotate(45deg)}
.archive details[open] summary::after{transform:translateY(.12em) rotate(-135deg)}
.archive .k{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.archive ul{list-style:none;margin:8px 0 0;padding:6px;width:max-content;min-width:14rem;max-width:100%;background:var(--card);border:1px solid var(--line);border-radius:14px}
.archive li a,.archive li span{display:flex;align-items:center;min-height:44px;padding:0 14px;border-radius:10px;color:var(--ink);text-decoration:none;font-weight:600}
.archive li a:hover{background:var(--chip)}
.archive li span[aria-current]{background:var(--sea);color:var(--card)}
.eats h3{font:700 1rem/1.3 var(--sans);margin:20px 0 6px}
.specials{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--tide);border-radius:12px;padding:12px 16px;font:.9375rem/1.5 var(--sans)}
.specials h3{margin:0 0 4px}.specials p{margin:4px 0 0}
.specials small{color:var(--muted)}
.specials .sps{list-style:none;margin:2px 0 0;padding:0}
.specials .spc{margin:0;padding:11px 0;border-top:1px solid var(--line)}.specials .spc:first-child{border-top:0;padding-top:6px}
.specials .sh{display:flex;flex-wrap:wrap;align-items:baseline;gap:0 8px}.specials .sh small{font-size:.8rem}
.specials .spc>p{margin:3px 0 0}
.specials .board{list-style:none;margin:6px 0 0;padding:0;max-width:34rem}
.specials .board li{display:flex;justify-content:space-between;align-items:baseline;gap:14px;margin:0;padding:4px 0;border-bottom:1px dotted var(--line)}
.specials .board li:last-child{border-bottom:0}
.specials .board .pr{white-space:nowrap;font-variant-numeric:tabular-nums;font-weight:600}
.specials .more{margin:0}.specials .more summary{display:inline-flex;align-items:center;min-height:36px;margin-top:2px;color:var(--sea);font-weight:700;font-size:.85rem;cursor:pointer}
.specials .more[open] summary{display:none}
.meals>input{position:absolute;opacity:0;pointer-events:none}
.tabs{display:flex;gap:4px;max-width:280px;margin:18px 0 2px;padding:4px;background:var(--chip);border-radius:999px;font:600 .95rem/1 var(--sans)}
.tabs label{flex:1;display:flex;align-items:center;justify-content:center;min-height:44px;border-radius:999px;cursor:pointer;color:var(--muted)}
#meal-l:checked~.tabs [for=meal-l],#meal-d:checked~.tabs [for=meal-d]{background:var(--card);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.18)}
#meal-l:focus-visible~.tabs [for=meal-l],#meal-d:focus-visible~.tabs [for=meal-d]{outline:2px solid var(--sea);outline-offset:2px}
.places .hd,.places .wk,.meals .cl{display:none}
.days{display:flex;gap:2px;max-width:30rem;margin:10px 0 2px;padding:4px;background:var(--chip);border-radius:999px;font:600 .85rem/1 var(--sans)}
.days label{flex:1;display:flex;align-items:center;justify-content:center;min-width:0;min-height:40px;border-radius:999px;cursor:pointer;color:var(--muted)}
.sort{display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin:10px 0 2px;font:600 .85rem/1 var(--sans)}
.sort[hidden],.sortmsg[hidden]{display:none}
.sort .k{color:var(--muted);margin-right:2px}
.sort button{min-height:40px;padding:0 14px;border:0;border-radius:999px;background:var(--chip);color:var(--ink);font:inherit;cursor:pointer}
.sort button[aria-pressed=true]{background:var(--sea);color:var(--card)}
.sort button:focus-visible{outline:2px solid var(--sea);outline-offset:2px}
.sortmsg{margin:6px 0 0;font:.85rem/1.45 var(--sans);color:var(--muted)}
.places{list-style:none;margin:0;padding:0!important;font-family:var(--sans)}
.places>li{margin:0!important;border-top:1px solid var(--line)}
.places summary{display:flex;flex-direction:column;gap:1px;padding:11px 0;cursor:pointer;list-style:none}
.places summary::-webkit-details-marker{display:none}
.places .pn{font-weight:700;font-size:1.02rem}
.places .ph{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px}
.st{display:none;align-items:center;min-height:22px;padding:0 9px;border-radius:999px;font:700 .7rem/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
.meals.live .st.lv:not([hidden]){display:inline-flex}.meals.live .st.cx{display:none!important}
.st.o{color:var(--open);background:color-mix(in srgb,var(--open) 16%,transparent)}
.st.s{color:var(--soon);background:color-mix(in srgb,var(--soon) 18%,transparent)}
.st.c,.st.cx{color:var(--shut);background:color-mix(in srgb,var(--shut) 14%,transparent)}
.cl ul{margin:4px 0 0;padding-left:1.2em}.cl li{margin:2px 0}
.pill{display:inline-flex;align-items:center;align-self:flex-start;min-height:30px;padding:0 13px;border-radius:999px;background:var(--chip);color:var(--sea);font:700 .8rem/1 var(--sans);white-space:nowrap}
.pill .pc,details[open]>summary .pill .po{display:none}details[open]>summary .pill .pc{display:inline}
.places .pls{display:flex;flex-wrap:wrap;gap:8px;margin-top:7px}.places .sx{display:none}
a.pill{text-decoration:none}a.pill:hover{background:color-mix(in srgb,var(--sea) 16%,var(--chip))}
.places .pm,.places .pr{font-size:.85rem;color:var(--muted)}
.places .sp{align-self:flex-start;margin-top:5px;padding:4px 9px;border-radius:6px;font-size:.88rem;background:color-mix(in srgb,var(--tide) 14%,transparent)}
.places .pd{padding:0 0 12px;font-size:.92rem;line-height:1.5}.places .pd p{margin:0 0 6px}
.places li.none{padding:11px 0;color:var(--muted);font-size:.9rem}
.call{font:.9rem/1.5 var(--sans);color:var(--muted);margin:16px 0 0}.call b{color:var(--ink)}
.nw{white-space:nowrap}.call ul{list-style:none;margin:6px 0 0;padding:0!important}.call li{margin:0 0 8px!important}
.eats>p.muted:last-child{margin-top:16px;font-size:.85rem}
.jump{order:2;position:sticky;top:0;z-index:5;display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;margin:4px 0 0;padding:8px 0;background:var(--bg);border-bottom:1px solid var(--line);font:600 .82rem/1 var(--sans)}
.jump::-webkit-scrollbar{display:none}
.jump a{flex:1 1 auto;min-width:0;display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:0 8px;border-radius:999px;background:var(--chip);color:var(--ink);text-decoration:none;white-space:nowrap}
section,.side,.more{scroll-margin-top:70px}
.body section{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 16px 4px;margin-top:18px}
.body section>h2{border:0;padding:0}
#bite>h2::before{content:"🎣 "}#beach>h2::before{content:"🌤️ "}#regs>h2::before{content:"📏 "}
#todo>h2::before{content:"📍 "}#eats>h2::before{content:"🍽️ "}#around>h2::before{content:"📰 "}
.callout{background:color-mix(in srgb,var(--tide) 13%,var(--card));border-left:4px solid var(--tide);border-radius:10px;padding:11px 14px;margin:0 0 14px;font:600 1rem/1.45 var(--sans)}
.callout strong{color:var(--sea)}
.sub{border-top:1px solid var(--line);padding-top:12px;margin-top:4px}.sub>h3{margin:0 0 6px;font-size:1rem}
.list{list-style:none;margin:0 0 12px;padding:0!important}
.list>li{margin:0!important;padding:8px 0;border-top:1px solid var(--line)}.list>li:first-child{border-top:0;padding-top:2px}
.fact{display:flex;flex-direction:column;gap:2px}
.fk{font:700 .72rem/1.4 var(--sans);text-transform:uppercase;letter-spacing:.09em;color:var(--sea)}.fv::first-letter{text-transform:uppercase}
.item .it{display:block;font:700 1rem/1.35 var(--sans);margin-bottom:2px}
.list .pl{position:relative;padding-left:1.1em}.list .pl::before{content:"•";position:absolute;left:.15em;color:var(--sea)}
p.li>strong:first-child{display:block;font:700 1rem/1.35 var(--sans);margin-bottom:2px}
#shot{background:transparent;border:0;border-left:4px solid var(--sea);border-radius:0;padding:4px 0 2px 16px}
#shot>h2{font-size:.72rem}#shot p{font:italic 1.12rem/1.5 var(--serif)}
#quote{background:transparent;border:0;border-left:4px solid var(--sea);border-radius:0;padding:4px 0 2px 16px}
#quote>h2{font-size:.72rem}#quote>h2::before{content:"🐚 "}#quote blockquote{margin:0}
#quote blockquote p{font:italic 1.15rem/1.5 var(--serif);margin:0 0 6px}
#quote .by{font:600 .85rem/1.4 var(--sans);color:var(--muted)}#quote cite{font-style:italic}
@media (min-width:520px){.fact{display:grid;grid-template-columns:7.5em minmax(0,1fr);column-gap:14px}.fk{padding-top:.25em}}
@media (min-width:700px){
body{font-size:1.125rem}.wrap{padding:28px 28px 56px}
.mast h1{font-size:2.6rem}h2.headline{font-size:2.2rem}
.tiles{grid-template-columns:repeat(3,minmax(0,1fr))}.tiles .tile:last-child:nth-child(odd){grid-column:auto}
.numbers{grid-template-columns:repeat(2,minmax(0,1fr))}.card.wide{grid-column:1/-1}
.outlook{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:8px}
.outlook li{grid-template-columns:minmax(0,1fr);grid-template-areas:"dn" "sk" "hl" "sh" "wd";align-content:start;row-gap:3px;text-align:center;padding:12px 4px;background:var(--card);border:1px solid var(--line);border-radius:12px}
}
@media (min-width:1080px){
html{font-size:clamp(16px,calc(8px + .55vw),21px)}
.wrap{max-width:min(96rem,94vw);padding:2rem 2.5rem 4rem}
.page{display:grid;grid-template-columns:minmax(0,1fr) clamp(360px,29vw,540px);column-gap:clamp(36px,3.5vw,80px);align-items:start}
.isl .out>h2::before{content:none}.col-main,.col-side,.isl .body{display:block}.side{margin-top:20px}.jump{margin-top:18px;font-size:.9rem;gap:6px}.jump a{flex:none;padding:0 15px}.more{margin-top:12px}
.mast h1{font-size:clamp(2.8rem,3.4vw,4rem)}h2.headline{font-size:clamp(2.2rem,2.3vw,2.9rem);max-width:30em}
.lead{font-size:1.15rem;max-width:46em}.switch{max-width:24rem}
.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}.tiles .tile:last-child:nth-child(odd){grid-column:1/-1}
.numbers{grid-template-columns:minmax(0,1fr)}.tidechart svg{max-width:none}
.col-side .out{margin-top:12px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.col-side .out h2{border:0;padding:0}
.col-side .outlook{display:block}
.col-side .outlook li{grid-template-columns:3.2em 1.9em 4.9em minmax(0,1fr);grid-template-areas:"dn sk hl sh" "dn sk hl wd";row-gap:0;text-align:left;padding:9px 0;background:none;border:0;border-top:1px solid var(--line);border-radius:0}
.col-side .outlook li:first-child{border-top:0}
}
@media (min-width:1360px){
#bite{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:2.25rem;align-items:start}
#bite>h2,#bite>.callout{grid-column:1/-1}
.body section>.list:has(>.fact),#around>.list,#todo>.list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:2.25rem;align-content:start}
.body section>.list:has(>.fact)>li:nth-child(2),#around>.list>li:nth-child(2){border-top:0;padding-top:2px}
.body section>.list>.fact,#bite .fact{display:flex}
#todo>.list{gap:14px}#todo>.list>li{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--bg)}
.places{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:stretch;margin-top:4px}
.places>li.place{display:flex;flex-direction:column;border:1px solid var(--line);border-radius:12px;background:var(--bg);padding:0 14px}
.places>li.place>details{flex:1;display:flex;flex-direction:column}
.places>li.place summary{flex:1;padding:12px 0}
.places>li.place .sx{display:block;flex:1;min-height:9px}.places>li.place .pls{margin-top:0}
.places>li.none{grid-column:1/-1;border:0;padding:4px 0}
}
@media print{.switch,.tip{display:none}.src details>*{display:block}}
"""

# The tide chart's hover and tap readout. The page works without it: every
# tide is printed under its chart.
TIDE_JS = """
(function(){
function clock(m){m=((m%1440)+1440)%1440;var h=Math.floor(m/60),n=m%60;return (h%12||12)+':'+(n<10?'0':'')+n+(h<12?' AM':' PM');}
document.querySelectorAll('.tidechart').forEach(function(fig){
var svg=fig.querySelector('svg'),c=JSON.parse(svg.getAttribute('data-tide')),xh=svg.querySelector('.xh'),xd=svg.querySelector('.xd'),tip=fig.querySelector('.tip'),cur=null;
function x(m){return c.x0+(m-c.s)/(1440-c.s)*(c.x1-c.x0);}
function y(h){return c.yb-(h-c.lo)/((c.hi-c.lo)||1)*(c.yb-c.yt);}
function at(m){var e=c.ev;for(var i=0;i<e.length-1;i++){if(m>=e[i][0]&&m<=e[i+1][0]){var f=(1-Math.cos(Math.PI*(m-e[i][0])/(e[i+1][0]-e[i][0])))/2;return {h:e[i][1]+(e[i+1][1]-e[i][1])*f,up:e[i+1][1]>e[i][1]};}}return null;}
function hide(){cur=null;xh.setAttribute('visibility','hidden');xd.setAttribute('visibility','hidden');tip.hidden=true;}
function show(m){m=Math.max(c.a,Math.min(c.b,Math.round(m/5)*5));var p=at(m);if(!p){hide();return;}cur=m;
var px=x(m),r=svg.getBoundingClientRect();xh.setAttribute('x1',px);xh.setAttribute('x2',px);xh.setAttribute('visibility','visible');
xd.setAttribute('cx',px);xd.setAttribute('cy',y(p.h));xd.setAttribute('visibility','visible');
tip.textContent=clock(m)+' · about '+p.h.toFixed(1)+' ft, '+(p.up?'rising':'falling');tip.hidden=false;
var half=tip.offsetWidth/2;tip.style.left=Math.max(half,Math.min(r.width-half,px/c.w*r.width))+'px';}
function from(ev){var r=svg.getBoundingClientRect();show(c.s+((ev.clientX-r.left)/r.width*c.w-c.x0)/(c.x1-c.x0)*(1440-c.s));}
svg.addEventListener('pointermove',from);svg.addEventListener('pointerdown',from);
svg.addEventListener('pointerleave',function(ev){if(ev.pointerType==='mouse')hide();});
fig.addEventListener('keydown',function(ev){if(ev.key!=='ArrowLeft'&&ev.key!=='ArrowRight')return;ev.preventDefault();show((cur===null?c.a:cur)+(ev.key==='ArrowRight'?15:-15));});
fig.addEventListener('blur',hide);
});
})();
"""


# ---- lunch and dinner (the Island Edition)

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
# A place counts for lunch when it is open across 12:30-1:30, for dinner
# when it is open at 6:30 and stays open to at least 7.
LUNCH, DINNER = (12 * 60 + 30, 13 * 60 + 30), (18 * 60 + 30, 19 * 60)


def load_restaurants(root: str = HERE) -> dict:
    """reference/restaurants.json: every place, its hours, ratings and picks."""
    path = os.path.join(root, "reference", "restaurants.json")
    if not os.path.exists(path):
        return {"places": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Hours, season and menu news from each place's own Facebook page
    # (reference/fb_news.json, written daily by local/fb_news.py).
    news_path = os.path.join(root, "reference", "fb_news.json")
    if os.path.exists(news_path):
        with open(news_path, encoding="utf-8") as f:
            news = json.load(f).get("news", [])
        for p in data.get("places", []):
            p["news"] = [n for n in news if n.get("id") == p["id"]]
    return data


def load_specials(date_iso: str, root: str = HERE) -> dict | None:
    """specials/<date>.json, written through the day by local/fb_specials.py."""
    path = os.path.join(root, "specials", f"{date_iso}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _hm(text: str) -> int:
    h, m = text.split(":")
    return int(h) * 60 + int(m)


def _spans(place: dict, weekday: str) -> list[tuple[int, int]] | None:
    """That day's open spans in minutes; None when the hours are unknown ('?')."""
    hours = (place.get("hours") or {}).get(weekday)
    if hours == "?":
        return None
    return [(_hm(a), _hm(b)) for a, b in (s.split("-") for s in hours or [])]


def meals_open(place: dict, weekday: str) -> set[str] | None:
    spans = _spans(place, weekday)
    if spans is None:
        return None
    meals = set()
    for a, b in spans:
        if a <= LUNCH[1] and b >= LUNCH[0]:
            meals.add("lunch")
        if a <= DINNER[0] and b >= DINNER[1]:
            meals.add("dinner")
    if place.get("meals"):
        meals &= set(place["meals"])
    return meals


def _clock(mins: int) -> str:
    """690 -> '11:30 AM', 720 -> 'noon', 1440 -> 'midnight'."""
    if mins % 1440 == 0:
        return "midnight"
    h, m = divmod(mins, 60)
    if (h, m) == (12, 0):
        return "noon"
    return f"{h % 12 or 12}{f':{m:02d}' if m else ''} {'AM' if h < 12 else 'PM'}"


def hours_today(place: dict, weekday: str) -> str:
    return ", ".join(f"{_clock(a)}–{_clock(b)}" for a, b in _spans(place, weekday) or [])


def _days(run: list[str]) -> str:
    """A run of days in a row: ['Tue', 'Wed', 'Thu'] -> 'Tue–Thu'."""
    return run[0] if len(run) == 1 else f"{run[0]}–{run[-1]}"


def week_hours(place: dict) -> str:
    """The posted week, Monday first, days with the same hours run together:
    'Mon closed · Tue–Sat 11 AM–9 PM · Sun 10 AM–3 PM'. '' when no hours
    are posted."""
    hours = place.get("hours") or {}
    if not hours or all(v == "?" for v in hours.values()):
        return ""
    runs: list[tuple[list[str], str]] = []
    for day in WEEKDAYS:
        v = hours.get(day)
        text = "hours not posted" if v == "?" else hours_today(place, day) if v else "closed"
        if runs and runs[-1][1] == text:
            runs[-1][0].append(day)
        else:
            runs.append(([day], text))
    if len(runs) == 1:
        return f"Every day {runs[0][1]}"
    return " · ".join(f"{_days(days)} {text}" for days, text in runs)


def _week_html(place: dict) -> str:
    """week_hours with each run kept on one line ('11 AM–9 PM' never splits)."""
    return " · ".join(f"<span class=nw>{esc(run)}</span>" for run in week_hours(place).split(" · "))


def open_days(place: dict) -> str:
    """The days a place opens, runs joined and wrapping past Sunday:
    'Thu–Sun', 'Fri–Mon', 'Tue, Thu–Sat'; 'every day'."""
    hours = place.get("hours") or {}
    is_open = [bool(hours.get(d)) and hours.get(d) != "?" for d in WEEKDAYS]
    if all(is_open):
        return "every day"
    start = (is_open.index(False) + 1) % 7         # begin just after a closed day
    runs: list[list[str]] = []
    for k in range(7):
        i = (start + k) % 7
        if is_open[i]:
            if runs and runs[-1][-1] == WEEKDAYS[(i - 1) % 7]:
                runs[-1].append(WEEKDAYS[i])
            else:
                runs.append([WEEKDAYS[i]])
    return ", ".join(_days(r) for r in runs)


def _rating(place: dict) -> str:
    bits = []
    for key, label in (("google", "Google"), ("tripadvisor", "Tripadvisor")):
        if place.get(key):
            score, count = place[key]
            bits.append(f"{label} {score:g} <small>({count:,})</small>")
    return " &middot; ".join(bits)


def _when(i: int, d: dt.date, ahead: bool) -> str:
    """'today' for the edition's own day, else the weekday ('Thursday')."""
    return "today" if i == 0 and not ahead else d.strftime("%A")


def _dl(i: int, d: dt.date, ahead: bool, cap: bool = False) -> str:
    """A day word ('today' or 'Thursday') the script re-reads against the
    reader's own day, so an edition opened a day late still says 'today'
    of the right day."""
    word = _when(i, d, ahead)
    return (f"<span class=dl data-i={i} data-day={d.strftime('%A')}{' data-cap' if cap else ''}>"
            f"{word.capitalize() if cap else word}</span>")


def _place_item(place: dict, week: list[tuple[int, dt.date]], meals: dict[int, set[str]],
                specials: dict[int, str], day: str = "", ahead: bool = False) -> str:
    """One place, built once for the whole week: its classes say which days
    (0 is the edition's own) it is open for lunch (l0..l6) and dinner
    (d0..d6), and its hours and weekly special carry one span per day. The
    Day row shows the chosen day's (Nate, 2026-11-04)."""
    cls = " ".join(["place"] + [f"{m[0]}{i}" for i, _ in week for m in sorted(meals[i])]
                   + (["pick"] if place.get("pick") else []))
    # Where it is, for "Closest to me" (the distance fills in on the reader's phone).
    where = (f" data-lat={place['lat']} data-lon={place['lon']}"
             if place.get("lat") is not None and place.get("lon") is not None else "")
    # The week in minutes, for the live Open / Opening soon / Closed pill
    # (null where the hours are unknown, [] where it is closed).
    week_spans = json.dumps({wd: _spans(place, wd) for wd in WEEKDAYS}, separators=(",", ":"))
    hours = []
    for i, d in week:
        if _spans(place, d.strftime("%a")):
            hours.append(f"<span class='hd h{i}'>{esc(hours_today(place, d.strftime('%a')))}</span>")
        elif place.get("pick") and open_days(place):    # a favorite stays listed on its closed days
            hours.append(f"<span class='hd h{i}'>open {esc(open_days(place))}</span>")
    head = (f"<span class=ph><span class=pn>{'★ ' if place.get('pick') else ''}{esc(place['name'])}</span>"
            f"<span class='st lv' hidden></span>"
            + ("<span class='st cx'>Closed</span>" if place.get("pick") else "") + "</span>"
            f"<span class=pm>{esc(place['town'])} &middot; {''.join(hours)}"
            f"<span class=mi hidden></span></span>")
    rating = _rating(place)
    if rating:
        head += f"<span class=pr>{rating}</span>"
    for i, d in week:
        if specials.get(i):
            head += (f"<span class='sp wk w{i}'>{_dl(i, d, ahead, cap=True)}: "
                     f"{esc(specials[i])}</span>")
    # Hours news decides whether to go, so it shows without a tap.
    hours_news = [n for n in place_news(place, day, limit=5) if n["kind"] == "hours"][:1] if day else []
    for n in hours_news:
        head += f"<span class=sp>{esc(_short_day(n['date']))} on Facebook: {esc(n['line'])}</span>"
    detail = [f"<p>{esc(place['style'])}.</p>"]
    if place.get("reviews"):
        detail.append(f"<p><b>Reviewers say:</b> {esc(place['reviews'])}</p>")
    if place.get("order"):
        detail.append(f"<p><b>Often ordered:</b> {esc(place['order'])}</p>")
    if week_hours(place):
        detail.append(f"<p><b>Hours:</b> {_week_html(place)}</p>")
    if day:
        detail.append(_news_html(place, day))
    links = [esc(place["address"])]
    if place.get("phone"):
        links.append(f"<a href='tel:{esc(re.sub(r'[^0-9]', '', place['phone']))}'>{esc(place['phone'])}</a>")
    if place.get("website"):
        links.append(f"<a href='{esc(place['website'])}'>Website</a>")
    if place.get("facebook"):
        links.append(f"<a href='{esc(place['facebook'])}'>Facebook</a>")
    detail.append(f"<p class=muted>{' &middot; '.join(links)}</p>")
    if place.get("hours_note"):
        detail.append(f"<p class=muted>{esc(place['hours_note'])}</p>")
    # A "Menu" pill beside the details one, straight to the place's own menu
    # (Nate, 2026-11-07). A link inside the summary opens the menu without
    # opening the card; a new tab keeps the paper where the reader left it.
    pills = DETAILS_PILL
    if place.get("menu"):
        pills += (f"<a class='pill mn' href='{esc(place['menu'])}' target=_blank rel=noopener>"
                  "Menu</a>")
    return (f"<li class='{cls}'{where} data-hours='{esc(week_spans)}'><details><summary>{head}<span class=sx></span>"
            f"<span class=pls>{pills}</span></summary>"
            f"<div class=pd>{''.join(detail)}</div></details></li>")


# The tap target that opens a place (Nate, 2026-11-04: "change the + to a pill
# that says click for details"). It reads "Hide details" while open.
DETAILS_PILL = ("<span class=pill><span class=po>Click for details</span>"
                "<span class=pc>Hide details</span></span>")


NEWS_DAYS = 21                      # a place's Facebook news shows this long


def place_news(place: dict, day: str, limit: int = 2) -> list[dict]:
    """The place's newest hours item and newest menu item from the NEWS_DAYS
    before day (never a post dated after the edition, never one whose until
    has passed). One of each kind: places repost the same hours weekly."""
    first = (dt.date.fromisoformat(day) - dt.timedelta(days=NEWS_DAYS)).isoformat()
    items = [n for n in place.get("news") or [] if first <= n.get("date", "") <= day
             and (n.get("until") or day) >= day]
    newest: dict[str, dict] = {}
    for n in sorted(items, key=lambda n: n["date"], reverse=True):
        newest.setdefault(n.get("kind", ""), n)
    return sorted(newest.values(), key=lambda n: n["date"], reverse=True)[:limit]


def _news_html(place: dict, day: str, tag: str = "p") -> str:
    out = []
    for n in place_news(place, day):
        link = f" <a href='{esc(n['url'])}'>Post</a>" if n.get("url") else ""
        out.append(f"{'<br>' if tag == 'span' else ''}<{tag} class=news><b>On Facebook, "
                   f"{esc(_short_day(n['date']))}:</b> {esc(n['line'])}{link}</{tag}>")
    return "".join(out)


def _closed_name(place: dict, weekday: str) -> str:
    """A name in the closed list, with the days it does open."""
    name = ("★ " if place.get("pick") else "") + esc(place["name"])
    if _spans(place, weekday):                     # open, but not at lunch or dinner time
        return f"{name} (no lunch or dinner)"
    days = open_days(place)
    return f"{name} (open {esc(days)})" if days else name


def _ranked(places: list[dict]) -> list[dict]:
    """Best rated first (count breaks a tie); unrated places last."""
    return sorted(places, key=lambda p: (-(p.get("google") or [0, 0])[0],
                                         -(p.get("google") or [0, 0])[1], p["name"]))


def _short_day(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}"


BOARD_SHOWN = 6          # a board's first items; the rest behind "All N items"


def _post_parts(post: dict) -> tuple[str, list[str]]:
    """A posted special's own words, and the items of a board read off its
    photo when it has two or more (the job keeps the board in `board`, and
    `text` ends with it)."""
    text = " ".join(post.get("text", "").split())
    board = " ".join((post.get("board") or "").split())
    if board and text.endswith(board):
        items = [x.strip() for x in board.split(";") if x.strip()]
        if len(items) >= 2:
            return text[: len(text) - len(board)].strip(), items
    if len(text) > 700:
        text = text[:697].rsplit(" ", 1)[0] + "…"
    return text, []


def _board_item(item: str) -> str:
    """One board line, its price (the last '$12.95' or '$9 / $14') pushed right."""
    m = re.fullmatch(r"(.+?)\s+(\$\s?\d[\d.,]*(?:\s*(?:/|or|-)\s*\$?\d[\d.,]*)*)", item)
    if m:
        return f"<li><span>{esc(m.group(1))}</span><span class=pr>{esc(m.group(2))}</span></li>"
    return f"<li><span>{esc(item)}</span></li>"


def _special_html(name: str, meta: str, words: str, items: list[str] | None = None,
                  meta_is_html: bool = False) -> str:
    """One special: the place and where it came from, its words, its board."""
    out = (f"<li class=spc><div class=sh><b>{esc(name)}</b>"
           f"<small>{meta if meta_is_html else esc(meta)}</small></div>")
    if words:
        out += f"<p>{esc(words)}</p>"
    items = items or []
    if items:
        shown = items if len(items) <= BOARD_SHOWN + 2 else items[:BOARD_SHOWN]
        out += f"<ul class=board>{''.join(_board_item(x) for x in shown)}</ul>"
        if len(shown) < len(items):
            out += (f"<details class=more><summary>All {len(items)} items</summary><ul class=board>"
                    + "".join(_board_item(x) for x in items[len(shown):]) + "</ul></details>")
    return out + "</li>"


def eats_section(data: dict, restaurants: dict, specials: dict | None = None) -> str:
    """Lunch & Dinner: the day's specials, then the places (the paper's
    favorites first) with a Lunch | Dinner switch and a Day row for the week
    ahead (Nate, 2026-11-04, from a reader: "the days they are open too since
    it all changes in the fall"). Every place open some day this week is
    built once; the chosen day and meal show the ones open then, in CSS.
    Hours, ratings and weekly specials come from reference/restaurants.json;
    the day's posted specials from specials/<date>.json."""
    day = numbers_date(data)
    ahead = day != data["date"]
    start = dt.date.fromisoformat(day)
    week = [(i, start + dt.timedelta(days=i)) for i in range(7)]
    weekday = start.strftime("%a")
    places = [p for p in restaurants.get("places", []) if p.get("status") != "closed"]
    by_id = {p["id"]: p for p in places}

    known, call, season = [], [], []
    meals_of: dict[str, dict[int, set[str]]] = {}
    for p in places:
        if p.get("status") == "season":             # closed until spring: one line, no hours
            season.append(p)
            continue
        meals = meals_open(p, weekday) if p.get("status") == "open" else None
        if p.get("status") == "call" or meals is None:
            call.append(p)
            continue
        known.append(p)
        meals_of[p["id"]] = {i: meals_open(p, d.strftime("%a")) or set() for i, d in week}
    listed = [p for p in known if any(meals_of[p["id"]].values())]
    weekly_of = {p["id"]: {i: p["weekly"][d.strftime("%a")] for i, d in week
                           if meals_of[p["id"]][i] and (p.get("weekly") or {}).get(d.strftime("%a"))}
                 for p in listed}

    # Specials: the weekly ones for this weekday, then what was posted today.
    # Each is its own block, the place and where it came from on top, then
    # its words, then a board read off a photo one item a line (Nate,
    # 2026-11-07: "the wall of text is hard to read").
    weekly = {pid: w[0] for pid, w in weekly_of.items() if 0 in w}
    lines = [_special_html(by_id[i]["name"],
                           f"every {dt.date.fromisoformat(day).strftime('%A')}, from its "
                           + ("Facebook page" if "facebook.com" in by_id[i].get("weekly_source", "")
                              else "own site"), text)
             for i, text in weekly.items()]
    posted = (specials or {}).get("posts", []) if specials and not ahead and specials.get("date") == day else []
    for post in posted:
        place = by_id.get(post.get("id"))
        if not place:
            continue
        words, items = _post_parts(post)
        link = f" on <a href='{esc(post['url'])}'>Facebook</a>" if post.get("url") else ""
        how = "read from the photo posted" if post.get("from_photo") else "posted"
        lines.append(_special_html(place["name"], f"{how} {esc(post.get('posted_et', 'today'))}{link}",
                                   words, items, meta_is_html=True))
    checked = (specials.get("checked_et") if specials and not ahead
               and specials.get("date") == day else None)
    in_run = config.FIRST_EDITION <= day <= config.LAST_EDITION and not ahead
    if checked:
        status = f"Restaurant Facebook pages checked at {', '.join(checked)}."
    elif in_run:
        status = ("Specials the restaurants post on Facebook are added here through the "
                  "day (checked about 11:15 AM and 4:15 PM).")
    else:
        status = ""
    parts = ["<section class=eats id=eats><h2>Lunch &amp; Dinner</h2>"]
    if lines or status:
        parts.append("<div class=specials><h3>Specials today</h3>"
                     + (f"<ul class=sps>{''.join(lines)}</ul>" if lines else
                        "<p>None posted yet.</p>" if checked else "")
                     + (f"<p class=muted>{esc(status)}</p>" if status else "") + "</div>")

    # The favorites are always listed, open or not, with a pill to say which
    # (Nate, 2026-11-04: "keep restaurants in the our favorites sections even
    # when closed, just give it a closed pill").
    picks = _ranked([p for p in known if p.get("pick")])
    others = _ranked([p for p in listed if not p.get("pick")])

    def group(title: str, group_places: list[dict], empty: str) -> str:
        items = [_place_item(p, week, meals_of[p["id"]], weekly_of[p["id"]], day, ahead)
                 for p in group_places]
        for i, d in week:
            for meal in ("lunch", "dinner"):
                if empty and not any(meal in meals_of[p["id"]][i] for p in group_places):
                    items.append(f"<li class='none {meal[0]}{i}'>"
                                 + esc(empty.format(meal=meal, when="\0")).replace("\0", _dl(i, d, ahead))
                                 + "</li>")
        return f"<h3>{esc(title)}</h3><ol class=places>{''.join(items)}</ol>"

    days = "".join(f"<input type=radio name=day id=day-{i} data-date={d.isoformat()} "
                   f"data-short={d.strftime('%a')}{' checked' if i == 0 else ''}>"
                   for i, d in week)
    chips = "".join(f"<label for=day-{i}>{'Today' if i == 0 and not ahead else d.strftime('%a')}</label>"
                    for i, d in week)
    parts.append(f"<div class=meals>{days}<input type=radio name=meal id=meal-l checked>"
                 "<input type=radio name=meal id=meal-d>"
                 "<div class=tabs role=group aria-label='Meal'><label for=meal-l>Lunch</label>"
                 "<label for=meal-d>Dinner</label></div>"
                 f"<div class=days role=group aria-label='Day'>{chips}</div>"
                 + SORT_ROW)
    if picks:
        # "Our favorites" (Nate, 2026-11-04; it was "Our picks").
        parts.append(group("Our favorites", picks, ""))
        # "Around the Topsail area" (Nate, 2026-11-04; it was "Also worth trying").
        parts.append(group("Around the Topsail area", others, "Nothing else open for {meal}."))
    else:
        parts.append(group("The places", others, "Nothing listed is open for {meal} {when}."))
    # Each day's closed list, as a list (Nate, 2026-11-04); the favorites
    # are not on it, they stay in their own list with a Closed pill.
    for i, d in week:
        shut = [p for p in known if not p.get("pick") and not meals_of[p["id"]][i]]
        if shut:
            parts.append(f"<div class='call cl c{i}'><b>Closed {_dl(i, d, ahead)}</b><ul>"
                         + "".join(f"<li>{_closed_name(p, d.strftime('%a'))}</li>"
                                   for p in sorted(shut, key=lambda p: p["name"]))
                         + "</ul></div>")
    parts.append("</div>")
    if call:
        def tel(p: dict) -> str:
            return (f" <a href='tel:{esc(re.sub(r'[^0-9]', '', p['phone']))}'>{esc(p['phone'])}</a>"
                    if p.get("phone") else "")
        def posted(p: dict) -> str:
            return f"<br>Posted hours: {_week_html(p)}" if week_hours(p) else ""
        def menu(p: dict) -> str:
            return (f" <a class='pill mn' href='{esc(p['menu'])}' target=_blank rel=noopener>Menu</a>"
                    if p.get("menu") else "")
        parts.append("<div class=call><b>Call first</b><ul>" + "".join(
            f"<li><b>{'★ ' if p.get('pick') else ''}{esc(p['name'])}</b>{tel(p)}{menu(p)}<br>"
            f"{esc(p.get('hours_note') or 'Hours not published.')}{posted(p)}"
            f"{_news_html(p, day, tag='span')}</li>"
            for p in sorted(call, key=lambda p: p["name"])) + "</ul></div>")
    if season:
        parts.append("<p class=call><b>Closed for the season:</b> "
                     + ", ".join(f"{'★ ' if p.get('pick') else ''}{esc(p['name'])}"
                                 for p in sorted(season, key=lambda p: p["name"])) + ".</p>")
    read = restaurants.get("read")
    parts.append("<p class=muted>Hours as each place published them"
                 + (f" (read {esc(_short_day(read))})" if read else "")
                 + "; off-season hours change, so call ahead. Ratings: Google and Tripadvisor "
                   "as Wanderlog shows them (Topsail Guide's Google figure where Wanderlog has "
                   "none). Tap a place for what reviewers say.</p></section>")
    return "".join(parts)


# The Day row and the Lunch | Dinner switch, one set of rules per day of the
# week ahead: a place shows when it carries the chosen day's meal class (a
# favorite always shows, with a Closed pill when it does not), and so do its
# hours, its weekly special and that day's closed list.
DAY_CSS = "".join(
    f"#day-{i}:checked~#meal-l:checked~.places>li:not(.l{i}):not(.pick),"
    f"#day-{i}:checked~#meal-d:checked~.places>li:not(.d{i}):not(.pick){{display:none}}"
    f"#day-{i}:checked~#meal-l:checked~.places>li.pick:not(.l{i}) .cx,"
    f"#day-{i}:checked~#meal-d:checked~.places>li.pick:not(.d{i}) .cx{{display:inline-flex}}"
    f"#day-{i}:checked~.places .h{i},#day-{i}:checked~.places .w{i}{{display:inline}}"
    f"#day-{i}:checked~.c{i}{{display:block}}"
    f"#day-{i}:checked~.days [for=day-{i}]{{background:var(--card);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.18)}}"
    f"#day-{i}:focus-visible~.days [for=day-{i}]{{outline:2px solid var(--sea);outline-offset:2px}}"
    for i in range(7))


def load_quotes(root: str = HERE) -> list[dict]:
    path = os.path.join(root, "reference", "quotes.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("quotes", [])


def quote_for(date_iso: str, quotes: list[dict]) -> dict | None:
    """One quote a day, in turn by date, so ten days never repeat one."""
    if not quotes:
        return None
    return quotes[dt.date.fromisoformat(date_iso).toordinal() % len(quotes)]


def quote_section(date_iso: str, quotes: list[dict] | None = None) -> str:
    """The Island Edition's close: a sea, beach or sailing line from
    reference/quotes.json, never written by the routine, so every quote and
    its attribution is one checked by hand (Nate, 2026-11-04)."""
    q = quote_for(date_iso, load_quotes() if quotes is None else quotes)
    if not q:
        return ""
    lines = "<br>".join(esc(line) for line in q["text"].split("\n"))
    who = esc(q["author"]) + (f", <cite>{esc(q['work'])}</cite>" if q.get("work") else "")
    return (f"<section id=quote><h2>Quote of the Day</h2><blockquote><p>{lines}</p>"
            f"<p class=by>{who}</p></blockquote></section>")


# Sort the places (Nate, 2026-11-04: "ordering the restaurants either by
# distance or alphabetical ... or have a sort option for either one"). Top
# rated is the order the page is built in; A-Z and Closest to me re-order each
# list on the phone, picks still first. Closest uses the phone's own location
# and each place's lat / lon from reference/restaurants.json, so no starting
# point is ever published. The row stays hidden until the script shows it.
SORT_ROW = ("<div class=sort role=group aria-label='Sort the places' hidden><span class=k>Sort</span>"
            "<button type=button data-sort=rated aria-pressed=true>Top rated</button>"
            "<button type=button data-sort=az aria-pressed=false>A–Z</button>"
            "<button type=button data-sort=near aria-pressed=false>Closest to me</button></div>"
            "<p class=sortmsg role=status hidden></p>")

# The page opens on Lunch until 3 PM and on Dinner from 3 PM, island time
# (Nate, 2026-11-04), whatever zone the phone is set to.
EATS_JS = ("(function(){var d=document.getElementById('meal-d'),h=new Date().getHours();"
           "try{h=+new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',hour:'2-digit',"
           "hourCycle:'h23'}).format(new Date())%24;}catch(e){}"
           "if(d&&h>=15){d.checked=true;}})();") + r"""
(function(){
var box=document.querySelector('.eats .sort');if(!box)return;
var msg=document.querySelector('.eats .sortmsg'),KEY='tr-eats-sort';
var lists=[].slice.call(document.querySelectorAll('.eats ol.places'));
lists.forEach(function(ol){[].forEach.call(ol.children,function(li,i){li.setAttribute('data-i',i);});});
box.hidden=false;
function say(t){msg.textContent=t;msg.hidden=!t;}
function nm(li){var n=li.querySelector('.pn');return n?n.textContent.replace(/^\u2605\s*/,''):'';}
function order(key){lists.forEach(function(ol){
 var items=[].slice.call(ol.children);
 items.sort(function(p,q){
  var pn=p.classList.contains('none'),qn=q.classList.contains('none');
  if(pn!==qn)return pn?1:-1;
  if(key==='az'){var c=nm(p).localeCompare(nm(q));if(c)return c;}
  if(key==='near'){var a=parseFloat(p.getAttribute('data-mi')),b=parseFloat(q.getAttribute('data-mi'));
   if(isNaN(a))a=1e9;if(isNaN(b))b=1e9;if(a!==b)return a-b;}
  return p.getAttribute('data-i')-q.getAttribute('data-i');});
 items.forEach(function(li){ol.appendChild(li);});});}
function press(key){[].forEach.call(box.querySelectorAll('button'),function(b){
 b.setAttribute('aria-pressed',b.getAttribute('data-sort')===key?'true':'false');});
 try{localStorage.setItem(KEY,key);}catch(e){}}
function miles(a,b,c,d){var r=Math.PI/180,x=Math.sin((c-a)*r/2),y=Math.sin((d-b)*r/2);
 return 7917.6*Math.asin(Math.sqrt(x*x+Math.cos(a*r)*Math.cos(c*r)*y*y));}
function near(){
 if(!navigator.geolocation){say("This phone can't share its location, so the list stays as it was.");return;}
 say('Finding where you are…');
 navigator.geolocation.getCurrentPosition(function(pos){
  var la=pos.coords.latitude,lo=pos.coords.longitude;
  [].forEach.call(document.querySelectorAll('.eats li.place[data-lat]'),function(li){
   var m=miles(la,lo,+li.getAttribute('data-lat'),+li.getAttribute('data-lon')),s=li.querySelector('.mi');
   li.setAttribute('data-mi',m);
   if(s){s.textContent=' \u00b7 '+(m<10?Math.max(m,0.1).toFixed(1):Math.round(m))+' mi';s.hidden=false;}});
  order('near');press('near');say('Straight-line miles from where you are now.');},
 function(){say("Couldn't get your location. To sort by distance, let this page use it: on an iPhone, Settings > Privacy & Security > Location Services > Safari Websites > While Using.");},
 {enableHighAccuracy:false,timeout:15000,maximumAge:300000});}
box.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
 var k=b.getAttribute('data-sort');say('');if(k==='near'){near();return;}order(k);press(k);});
var saved=null;try{saved=localStorage.getItem(KEY);}catch(e){}
if(saved==='az'){order('az');press('az');}
else if(saved==='near'&&navigator.permissions&&navigator.permissions.query){
 navigator.permissions.query({name:'geolocation'}).then(function(p){if(p.state==='granted')near();}).catch(function(){});}
})();
""" + r"""
(function(){
var box=document.querySelector('.eats .meals');if(!box)return;
var f={};
try{new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short',year:'numeric',
 month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'})
 .formatToParts(new Date()).forEach(function(p){f[p.type]=p.value;});}catch(e){return;}
var iso=f.year+'-'+f.month+'-'+f.day,wd=f.weekday,now=(+f.hour%24)*60+(+f.minute);
var radios=[].slice.call(box.querySelectorAll('input[name=day]')),t=-1;
radios.forEach(function(r,i){if(r.getAttribute('data-date')===iso)t=i;});
if(t<0)return;
radios.forEach(function(r,i){var l=box.querySelector('label[for='+r.id+']');
 if(l)l.textContent=i===t?'Today':r.getAttribute('data-short');});
[].forEach.call(box.querySelectorAll('.dl'),function(s){var i=+s.getAttribute('data-i');
 s.textContent=i===t?(s.hasAttribute('data-cap')?'Today':'today'):s.getAttribute('data-day');});
if(radios[0].checked)radios[t].checked=true;
[].forEach.call(box.querySelectorAll('li.place[data-hours]'),function(li){
 var h,s=li.querySelector('.st.lv');try{h=JSON.parse(li.getAttribute('data-hours'))[wd];}catch(e){return;}
 if(!s||!h)return;
 var k='c',txt='Closed';
 for(var j=0;j<h.length;j++){
  if(h[j][0]<=now&&now<h[j][1]){k='o';txt='Open';break;}
  if(h[j][0]>now&&h[j][0]-now<=60){k='s';txt='Opening soon';}}
 s.className='st lv '+k;s.textContent=txt;s.hidden=false;});
function live(){box.classList.toggle('live',radios[t].checked);}
radios.forEach(function(r){r.addEventListener('change',live);});live();
})();
"""


def edition_switch(date_iso: str, edition: str, root: str) -> str:
    """Fishing | Island, at the top of every page: the other edition of the same day."""
    out = []
    for ed, label in (("fishing", "🎣 Fishing"), ("island", "🏝️ Island")):
        if ed == edition:
            out.append(f"<span aria-current=page>{label}</span>")
        else:
            out.append(f"<a href='{root}{config.page_path(date_iso, ed)}'>{label}</a>")
    return "<nav class=switch aria-label='Edition'>" + "".join(out) + "</nav>"


def page(data: dict, report: dict | None, editions: list[str], date_iso: str,
         edition: str = "fishing", root: str | None = None,
         specials: dict | None = None) -> str:
    """One edition's page. `root` is the relative way back to the site root
    from where the page is served ('../' for site/<date>/, '../../' for
    site/<date>/island/, './' for site/index.html); every link is built on it.

    One column on a phone and an iPad: the tiles and tides, the write-up,
    then the rest of the numbers and the week. From 1080px wide the write-up
    runs on the left and every number rides a sidebar on the right."""
    island = edition == "island"
    if root is None:
        root = "../../" if island else "../"
    kind = data.get("kind") or "daily"
    meta = (report or {}).get("meta", {})
    sec = (report or {}).get("sections", {})
    if island:
        headline = meta.get("island_headline") or "The day on the island"
        lead = sec.get("Island Lead")
        panel, sections = island_numbers_panel(data), ISLAND_PAGE_SECTIONS
        name = f"Topsail Reporter, {config.ISLAND_NAME}"
    else:
        headline = meta.get("headline") or "The numbers"
        lead = sec.get("Lead")
        panel, sections = numbers_panel(data), PAGE_SECTIONS
        name = "Topsail Reporter"
    title = f"{name}, {config.weekday_label(date_iso)}"
    sub = ([config.ISLAND_NAME] if island else []) + [
        "Topsail Island, NC", f"{config.weekday_label(date_iso)}, {date_iso[:4]}",
        KIND_LABEL.get(kind, kind)]
    mast = ("<header class=mast><h1>Topsail Reporter</h1><div class=sub>"
            + " &middot; ".join(f"<span>{esc(s)}</span>" for s in sub) + "</div>"
            + edition_switch(date_iso, edition, root) + "</header>")

    top = []
    for a in alerts_for(data, edition):
        where = "<span class=w>On the water</span>" if a.get("where") == "water" else ""
        top.append(f"<div class=alert role=note><b>⚠️ {esc(a['event'])}</b>"
                   f"<span>{esc(alert_when(a, data, short=False).strip())}</span>{where}</div>")
    top.append(f"<h2 class=headline>{inline_md(headline)}</h2>")
    if lead:
        top.append(f"<div class=lead>{block_md(lead)}</div>")
    elif not report:
        top.append("<p class=lead>Numbers only so far. The write-up lands here when it is done.</p>")

    when = config.weekday_label(numbers_date(data))
    tides, more = panel
    side = (f"<div class=side id=numbers><h2>The numbers, {esc(when)}</h2>{glance(data, edition)}"
            f"{tides}</div>" + (f"<div class=more>{more}</div>" if more else ""))
    body, jump = [], [("numbers", "Numbers")]
    for s in sections:
        if sec.get(s):
            sid, chip = SECTION_IDS[s]
            body.append(f"<section id={sid}><h2>{esc(s)}</h2>{block_md(sec[s])}</section>")
            if chip:
                jump.append((sid, chip))
    if island:
        body.append(eats_section(data, load_restaurants(), specials))
        jump.append(("eats", "Eat"))
        body.append(quote_section(date_iso))
    body = "".join(body)
    week = outlook(data)
    if week and island:
        # The week rides with the rest of the numbers on a wide screen, and on
        # a phone it comes right after Beach & Weather (Nate, 2026-11-04; the
        # .isl rules in CSS), so its chip follows Beach.
        at = next((i + 1 for i, (sid, _) in enumerate(jump) if sid == "beach"), len(jump))
        jump.insert(at, ("week", "Week"))
        side, week = side + week, ""
    elif week:
        jump.append(("week", "Week"))
    nav = ("<nav class=jump aria-label='Sections'>"
           + "".join(f"<a href='#{sid}'>{esc(chip)}</a>" for sid, chip in jump) + "</nav>")
    sources = (f"<section class=src><details><summary><h2>Sources</h2>"
               f"<span class=pill><span class=po>Show</span><span class=pc>Hide</span></span>"
               f"</summary>{block_md(sec['Sources'])}</details></section>"
               if sec.get("Sources") else "")
    # The editions are a dropdown, newest first (Nate, 2026-11-04: "should
    # look cleaner like that").
    archive = "".join(
        f"<li><a href='{root}{config.page_path(d, edition)}'>{esc(config.weekday_label(d))}</a></li>"
        if d != date_iso else f"<li><span aria-current=page>{esc(config.weekday_label(d))}</span></li>"
        for d in reversed(editions))
    care = ("Hours change in the off-season: call ahead before you drive anywhere."
            if island else
            "Size and bag limits change by proclamation: check NC Division of Marine "
            "Fisheries before you keep a fish.")
    footer = (
        "<footer><p>Tides: NOAA CO-OPS. Forecasts, surf and alerts: NWS Wilmington. "
        "Buoy: NDBC. Sun and model waves: Open-Meteo. Numbers fetched "
        f"{esc(data.get('generated_et'))}. All times Eastern.</p>"
        f"<p>{care} Swim near a lifeguard or not at all when the rip risk is up.</p>"
        f"<nav class=archive aria-label='Editions'><details><summary><span class=k>Editions</span>"
        f"<span class=cur>{esc(config.weekday_label(date_iso))}</span></summary>"
        f"<ul>{archive}</ul></details></nav>"
        "</footer>")
    script = ((TIDE_JS if "class=tidechart" in side else "")
              + (EATS_JS if "class=eats" in body else ""))
    script = f"<script>{script}</script>" if script else ""
    pg_class = "'page isl'" if island else "page"
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{esc(title)}</title><meta name=description content='{esc(headline)}'>"
            f"<style>{CSS}{DAY_CSS}</style></head><body><main class=wrap>{mast}"
            f"<div class={pg_class}><div class=col-main><div class=top>{''.join(top)}</div>\n"
            f"{nav}\n<div class=body>{body}</div>\n{week}\n{sources}</div>\n"
            f"<aside class=col-side>{side}</aside></div>\n"
            f"{footer}</main>{script}</body></html>\n")


# ------------------------------------------------------------------ the site

def edition_dates(root: str = HERE) -> list[str]:
    return sorted(os.path.basename(p)[:-5]
                  for p in glob.glob(os.path.join(root, "data", "*.json"))
                  if re.match(r"^\d{4}-\d{2}-\d{2}\.json$", os.path.basename(p)))


def _write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def listed(dates: list[str]) -> list[str]:
    """The archive: rehearsal (sample) editions drop out once a real one exists.

    Their pages stay where they are; they are just no longer linked or the
    index, so the run starts with a clean archive and nobody has to delete
    anything.
    """
    real = [d for d in dates if config.kind_for(d) != "sample"]
    return real or dates


def render_all(root: str = HERE) -> list[str]:
    dates = edition_dates(root)
    shown = listed(dates)
    site = os.path.join(root, "site")
    for d in dates:
        data = load_data(d, root)
        report = load_report(d, root)
        _write(os.path.join(site, d, "index.html"), page(data, report, shown, d))
        _write(os.path.join(site, d, "island", "index.html"),
               page(data, report, shown, d, edition="island",
                    specials=load_specials(d, root)))
        _write(os.path.join(site, "text", config.text_file(d)), build_text(data, report))
        _write(os.path.join(site, "text", config.text_file(d, "island")),
               build_island_text(data, report))
    if dates:
        latest = shown[-1]
        data, report = load_data(latest, root), load_report(latest, root)
        _write(os.path.join(site, "index.html"), page(data, report, shown, latest, root="./"))
        _write(os.path.join(site, "island", "index.html"),
               page(data, report, shown, latest, edition="island", root="../",
                    specials=load_specials(latest, root)))
    else:
        _write(os.path.join(site, "index.html"), EMPTY_INDEX)
        _write(os.path.join(site, "island", "index.html"), EMPTY_INDEX)
    return dates


EMPTY_INDEX = (
    "<!doctype html><html lang=en><head><meta charset=utf-8>"
    "<meta name=viewport content='width=device-width,initial-scale=1'>"
    f"<title>Topsail Reporter</title><style>{CSS}</style></head><body><main class=wrap>"
    "<header class=mast><h1>Topsail Reporter</h1><div class=sub>Topsail Island, NC</div>"
    "</header><p class=lead>No edition yet. The first one lands here at sunrise.</p>"
    "</main></body></html>\n")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--print", dest="show", metavar="DATE",
                        help="print that day's two texts after rendering")
    args = parser.parse_args(argv)
    dates = render_all()
    print(f"OK: rendered {len(dates)} edition(s): {', '.join(dates) or 'none'}")
    if args.show:
        for edition in config.EDITIONS:
            name = config.text_file(args.show, edition)
            with open(os.path.join(HERE, "site", "text", name), encoding="utf-8") as f:
                text = f.read()
            print(f"----- {edition} text ({name}) -----")
            print(text, end="")
            print(f"----- {len(text)} characters -----")
    return 0


if __name__ == "__main__":
    sys.exit(main())
