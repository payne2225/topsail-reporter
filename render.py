"""Turn data/<date>.json (+ reports/<date>.md when written) into the site.

    python render.py                 # every edition, the index, every text
    python render.py --print 2026-10-29   # also print that day's text

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
import os
import re
import sys

import config

HERE = os.path.dirname(os.path.abspath(__file__))
SECTIONS = ["Text", "Lead", "The Bite", "Beach & Weather", "Around the Island",
            "Regs Corner", "Parting Shot", "Island Text", "Island Lead",
            "Things To Do", "Sources"]
REQUIRED_SECTIONS = ["Text", "Lead", "The Bite", "Beach & Weather",
                     "Around the Island", "Island Text", "Island Lead",
                     "Things To Do", "Sources"]
PAGE_SECTIONS = ["The Bite", "Beach & Weather", "Around the Island",
                 "Regs Corner", "Parting Shot"]
# The Island Edition shares Beach & Weather, Around the Island and the
# Parting Shot with the fishing page, and has its own lead and picks.
ISLAND_PAGE_SECTIONS = ["Things To Do", "Beach & Weather", "Around the Island",
                        "Parting Shot"]
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


def alert_when(a: dict, data: dict) -> str:
    """' from Sat 2:00p' when it has not started, else ' until Mon 6:00a'."""
    def stamp(iso: str) -> str:
        t = dt.datetime.fromisoformat(iso)
        day = "" if t.date().isoformat() == data["date"] else f"{t.strftime('%a')} "
        return f"{day}{config.short_clock(config.clock(t))}"
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
    parts.append(f"Full report: {url}")
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


def block_md(text: str) -> str:
    """Paragraphs, '- ' bullets and '### ' subheads; that is the whole dialect."""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append(f"<p>{inline_md(' '.join(para))}</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline_md(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in text.split("\n"):
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("### "):
            flush()
            out.append(f"<h3>{inline_md(s[4:])}</h3>")
        elif s.startswith("- "):
            if para:
                flush()
            items.append(s[2:])
        elif items and line.startswith("  "):
            items[-1] += " " + s
        else:
            if items:
                flush()
            para.append(s)
    flush()
    return "\n".join(out)


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def tide_table(data: dict, day: str, keys: tuple[str, ...] = ("sound", "ocean")) -> str:
    rows = []
    for st in (s for s in config.TIDE_STATIONS if s["key"] in keys):
        events = tides_for(data, st["key"], day)
        if not events:
            rows.append(f"<tr><th>{esc(st['label'])}</th><td colspan=4 class=muted>no reading</td></tr>")
            continue
        cells = "".join(
            f"<td><span class='tt {e['type']}'>{e['type'][0].upper()}</span> {esc(e['time'])}"
            f"{' <small>' + esc(e['day']) + '</small>' if e.get('day') else ''}"
            f"<br><small>{e['height_ft']:g} ft</small></td>" for e in events)
        rows.append(f"<tr><th>{esc(st['label'])}</th>{cells}</tr>")
    return "<table class=tides>" + "".join(rows) + "</table>"


def sun_card(data: dict, day: str) -> str:
    sun = sun_for(data, day)
    source = (data.get("weather_model") or {}).get("sun_source")
    note = f"<p class=muted>Sun times {esc(source)}: Open-Meteo did not answer.</p>" if source and sun else ""
    return ("<div class=card><h3>Sun</h3><ul>"
            + (f"<li><b>Sunrise</b> {esc(sun['sunrise'])}</li><li><b>Sunset</b> "
               f"{esc(sun['sunset'])}</li>" if sun else "<li class=muted>no reading</li>")
            + "</ul>" + note + "</div>")


def numbers_panel(data: dict) -> str:
    day = numbers_date(data)
    ahead = day != data["date"]
    when = config.weekday_label(day)
    cards = []
    sound_note = config.TIDE_STATIONS[0]["note"]
    cards.append(f"<div class='card wide'><h3>Tides, {esc(when)}</h3>{tide_table(data, day)}"
                 f"<p class=muted>Sound station leads: {esc(sound_note)}. "
                 f"Moon: {esc((data.get('moon') or {}).get('phase', 'no reading'))}, "
                 f"{esc((data.get('moon') or {}).get('tides', ''))}.</p></div>")

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

    wind_bits = []
    marine = data.get("marine") or {}
    if marine.get("periods") and not ahead:
        p0 = marine["periods"][0]
        wind_bits.append(f"<li><b>{esc(p0['name'])}:</b> {esc(p0['text'])}</li>")
        if len(marine["periods"]) > 1:
            p1 = marine["periods"][1]
            wind_bits.append(f"<li><b>{esc(p1['name'])}:</b> {esc(p1['headline'])}</li>")
    hourly = (data.get("weather_model") or {}).get("wind") or []
    if hourly and not ahead:
        cells = "".join(f"<td>{esc(config.short_clock(h['time']))}<br><b>{esc(h['from'])} "
                        f"{h['speed_mph']}</b><br><small>g{h['gust_mph']}</small></td>"
                        for h in hourly)
        wind_bits.append(f"</ul><table class=wind><tr>{cells}</tr></table><ul>")
    fc = day_forecast(data, day)
    if fc:
        wind_bits.append(f"<li><b>Forecast:</b> {esc(fc['detailed'])}</li>")
    cards.append("<div class='card wide'><h3>Wind &amp; weather</h3><ul>"
                 + ("".join(wind_bits) or "<li class=muted>no reading</li>")
                 + f"</ul><p class=muted>Marine zone {esc(config.MARINE_ZONE)} "
                   f"({esc(config.MARINE_ZONE_NAME)}). Wind row in mph, g = gusts.</p></div>")

    cards.append(sun_card(data, day))
    return "<section class=numbers>" + "".join(cards) + "</section>"


def island_numbers_panel(data: dict) -> str:
    """The Island Edition's cards: weather day and night, the beach, the
    sun, and the beach-side tides."""
    day = numbers_date(data)
    ahead = day != data["date"]
    when = config.weekday_label(day)
    cards = []

    weather = []
    for label, p in (("Day", day_forecast(data, day)), ("Night", night_forecast(data, day))):
        if p:
            weather.append(f"<li><b>{esc(p['name'] if not ahead else label)}:</b> "
                           f"{esc(p['detailed'])}</li>")
    cards.append(f"<div class='card wide'><h3>Weather, {esc(when)}</h3><ul>"
                 + ("".join(weather) or "<li class=muted>no reading</li>") + "</ul></div>")

    beach = []
    sp = surf_period(data, day)
    if sp:
        f = sp["fields"]
        for key, label in (("surf_height", "Surf"), ("rip_current_risk", "Rip current risk"),
                           ("uv_index", "UV")):
            if f.get(key):
                beach.append(f"<li><b>{label}:</b> {esc(f[key])}</li>")
    buoy = data.get("buoy")
    if buoy and buoy.get("water_temp_f") is not None and not ahead:
        beach.append(f"<li><b>Ocean {buoy['water_temp_f']}&deg;F</b>, measured "
                     f"{esc(buoy['observed_et'])} ET</li>")
    elif sp and sp["fields"].get("water_temp"):
        beach.append(f"<li><b>Ocean:</b> {esc(sp['fields']['water_temp'].lower())}</li>")
    cards.append("<div class=card><h3>The beach</h3><ul>"
                 + ("".join(beach) or "<li class=muted>no reading</li>") + "</ul></div>")

    cards.append(sun_card(data, day))

    cards.append(f"<div class='card wide'><h3>Beach tides, {esc(when)}</h3>"
                 f"{tide_table(data, day, ('ocean',))}<p class=muted>Low tide uncovers the "
                 "most beach.</p></div>")
    return "<section class=numbers>" + "".join(cards) + "</section>"


def outlook_table(data: dict) -> str:
    rows = []
    for p in (data.get("forecast") or [])[:10]:
        pop = f"{p['pop_pct']}%" if p.get("pop_pct") else ""
        rows.append(f"<tr><th>{esc(p['name'])}</th><td>{esc(p['temp_f'])}&deg;</td>"
                    f"<td>{esc(p['short'])}</td><td>{esc(p['wind'])}</td><td>{pop}</td></tr>")
    if not rows:
        return ""
    return ("<section><h2>Outlook</h2><table class=outlook>" + "".join(rows)
            + "</table><p class=muted>NWS Wilmington point forecast for Topsail Beach.</p></section>")


CSS = """
:root{--bg:#f6f3ec;--ink:#1d2a33;--muted:#5d6b75;--card:#fffdf8;--line:#e2dccf;--sea:#0d5c75;--accent:#c9572b;--hi:#0d5c75;--lo:#8a6d3b}
@media (prefers-color-scheme:dark){:root{--bg:#0f1a20;--ink:#e8eef1;--muted:#97a6ae;--card:#16242c;--line:#24363f;--sea:#6cc3dc;--accent:#f08a5d;--hi:#6cc3dc;--lo:#d6b47a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 Georgia,'Times New Roman',serif}
main{max-width:760px;margin:0 auto;padding:20px 16px 48px}
header.mast{border-bottom:3px double var(--ink);padding-bottom:10px;margin-bottom:18px;text-align:center}
.mast h1{font:700 2.1rem/1.1 Georgia,serif;letter-spacing:.02em;margin:0}
.mast .sub{font:600 .78rem/1.4 system-ui,sans-serif;text-transform:uppercase;letter-spacing:.14em;color:var(--muted);margin-top:6px}
h2.headline{font-size:1.55rem;line-height:1.25;margin:.2em 0 .5em}
h2{font:700 1.15rem/1.3 system-ui,sans-serif;color:var(--sea);border-top:1px solid var(--line);padding-top:14px;margin-top:28px}
h3{font:700 .95rem/1.3 system-ui,sans-serif;margin:.2em 0 .5em}
a{color:var(--sea)}
.lead{font-size:1.08rem}
.alert{background:var(--accent);color:#fff;font:600 .95rem/1.4 system-ui,sans-serif;padding:10px 14px;border-radius:8px;margin:12px 0}
.numbers{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;font:15px/1.45 system-ui,sans-serif;min-width:0}
.card.wide{grid-column:1/-1}.card ul{margin:0;padding-left:18px}.card li{margin:2px 0}
table{border-collapse:collapse;width:100%;font:14px/1.35 system-ui,sans-serif}
.tides th{text-align:left;font-weight:600;padding:6px 6px 6px 0;width:28%;vertical-align:top}
.tides td{padding:6px 4px;vertical-align:top}
.tt{display:inline-block;width:1.4em;text-align:center;border-radius:4px;color:#fff;font-weight:700;font-size:.8em}
.tt.high{background:var(--hi)}.tt.low{background:var(--lo)}
.wind{margin:8px 0;text-align:center}.wind td{padding:4px 2px;border-left:1px solid var(--line)}.wind td:first-child{border-left:0}
.outlook th{text-align:left;padding:5px 8px 5px 0;white-space:nowrap}.outlook td{padding:5px 6px;border-top:1px solid var(--line)}.outlook th{border-top:1px solid var(--line)}
.muted{color:var(--muted);font-size:.85rem}
.sources{font:14px/1.5 system-ui,sans-serif}
footer{margin-top:32px;border-top:1px solid var(--line);padding-top:12px;font:13px/1.5 system-ui,sans-serif;color:var(--muted)}
footer a{margin-right:10px;white-space:nowrap}
@media (max-width:560px){.numbers{grid-template-columns:1fr}.mast h1{font-size:1.7rem}body{font-size:16px}.wind{font-size:12px}}
"""


def page(data: dict, report: dict | None, editions: list[str], date_iso: str,
         edition: str = "fishing", root: str | None = None) -> str:
    """One edition's page. `root` is the relative way back to the site root
    from where the page is served ('../' for site/<date>/, '../../' for
    site/<date>/island/, './' for site/index.html); every link is built on it."""
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
        other = (f"<p class=muted><a href='{root}{config.page_path(date_iso)}'>"
                 "Fishing? Today's fishing edition is here.</a></p>")
    else:
        headline = meta.get("headline") or "The numbers"
        lead = sec.get("Lead")
        panel, sections = numbers_panel(data), PAGE_SECTIONS
        name = "Topsail Reporter"
        other = (f"<p class=muted><a href='{root}{config.page_path(date_iso, 'island')}'>"
                 f"Not fishing? Today's {config.ISLAND_NAME} is here.</a></p>")
    title = f"{name}, {config.weekday_label(date_iso)}"
    sub = f"{config.ISLAND_NAME} &middot; " if island else ""
    parts = [f"<header class=mast><h1>Topsail Reporter</h1><div class=sub>{sub}"
             f"Topsail Island, NC &middot; {esc(config.weekday_label(date_iso))}, "
             f"{date_iso[:4]} &middot; {esc(KIND_LABEL.get(kind, kind))}</div></header>"]
    for a in alerts_for(data, edition):
        parts.append(f"<div class=alert>{esc(a['event'])}: {esc(a.get('headline') or '')}</div>")
    parts.append(f"<h2 class=headline>{inline_md(headline)}</h2>")
    if lead:
        parts.append(f"<div class=lead>{block_md(lead)}</div>")
    elif not report:
        parts.append("<p class=lead>Numbers only so far. The write-up lands here when it is done.</p>")
    parts.append(other)
    parts.append(panel)
    for section in sections:
        if sec.get(section):
            parts.append(f"<section><h2>{esc(section)}</h2>{block_md(sec[section])}</section>")
    parts.append(outlook_table(data))
    if sec.get("Sources"):
        parts.append(f"<section class=sources><h2>Sources</h2>{block_md(sec['Sources'])}</section>")
    archive = " ".join(
        f"<a href='{root}{config.page_path(d, edition)}'>{esc(config.weekday_label(d))}</a>"
        if d != date_iso else f"<b>{esc(config.weekday_label(d))}</b>" for d in editions)
    care = ("Hours change in the off-season: call ahead before you drive anywhere."
            if island else
            "Size and bag limits change by proclamation: check NC Division of Marine "
            "Fisheries before you keep a fish.")
    parts.append(
        "<footer><p>Tides: NOAA CO-OPS. Forecasts, surf and alerts: NWS Wilmington. "
        "Buoy: NDBC. Sun and model waves: Open-Meteo. Numbers fetched "
        f"{esc(data.get('generated_et'))}. All times Eastern.</p>"
        f"<p>{care} Swim near a lifeguard or not at all when the rip risk is up.</p>"
        f"<p>Editions: {archive}</p></footer>")
    body = "\n".join(p for p in parts if p)
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{esc(title)}</title><meta name=description content='{esc(headline)}'>"
            f"<style>{CSS}</style></head><body><main>{body}</main></body></html>\n")


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
               page(data, report, shown, d, edition="island"))
        _write(os.path.join(site, "text", config.text_file(d)), build_text(data, report))
        _write(os.path.join(site, "text", config.text_file(d, "island")),
               build_island_text(data, report))
    if dates:
        latest = shown[-1]
        data, report = load_data(latest, root), load_report(latest, root)
        _write(os.path.join(site, "index.html"), page(data, report, shown, latest, root="./"))
        _write(os.path.join(site, "island", "index.html"),
               page(data, report, shown, latest, edition="island", root="../"))
    else:
        _write(os.path.join(site, "index.html"), EMPTY_INDEX)
        _write(os.path.join(site, "island", "index.html"), EMPTY_INDEX)
    return dates


EMPTY_INDEX = (
    "<!doctype html><html lang=en><head><meta charset=utf-8>"
    "<meta name=viewport content='width=device-width,initial-scale=1'>"
    f"<title>Topsail Reporter</title><style>{CSS}</style></head><body><main>"
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
