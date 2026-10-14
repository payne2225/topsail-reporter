"""Turn data/<date>.json (+ reports/<date>.md when written) into the site.

    python render.py                 # every edition, the index, every text
    python render.py --print 2026-10-29   # also print that day's text

Outputs, all under site/ (what GitHub Pages serves):
    site/<date>/index.html   the full report for that morning
    site/index.html          the newest edition, with the archive
    site/text/<date>.txt     the text message the iPhone Shortcut sends

The text is three parts: a header line render.py writes, the writer's short
prose from the report's "## Text" section, and a numbers block render.py
builds from the fetched data. No tide time, temperature or forecast in the
numbers block is ever typed by hand. With no report yet (the quick edition)
the text is the header, the numbers and the link.
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
            "Regs Corner", "Parting Shot", "Sources"]
REQUIRED_SECTIONS = ["Text", "Lead", "The Bite", "Beach & Weather",
                     "Around the Island", "Sources"]
PAGE_SECTIONS = ["The Bite", "Beach & Weather", "Around the Island",
                 "Regs Corner", "Parting Shot"]
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


def tide_line(events: list[dict], short: bool) -> str:
    parts = []
    for e in events:
        t = config.short_clock(e["time"]) if short else e["time"]
        tag = f" {e['day']}" if e.get("day") else ""
        parts.append(f"{e['type'][0].upper()} {t}{tag}")
    return ", ".join(parts)


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


def numbers_block(data: dict) -> list[str]:
    """The text's numbers, every one straight from data/<date>.json."""
    day = numbers_date(data)
    ahead = day != data["date"]

    def lab(label: str) -> str:
        # A preview's lines say whose day they are: "Sat sound tides: ...".
        if ahead:
            return f"{dt.date.fromisoformat(day).strftime('%a')} {label}"
        return label[0].upper() + label[1:]

    lines = []
    for a in data.get("alerts") or []:
        lines.append(f"ALERT: {a['event']}")
    sound = tides_for(data, "sound", day)
    if sound:
        lines.append(f"{lab('sound tides')}: {tide_line(sound, short=True)}")
    beach = []
    sp = surf_period(data, day)
    if sp and sp["fields"].get("surf_height"):
        beach.append(f"surf {feet(sp['fields']['surf_height'])}")
    else:
        w = wave_for(data, day)
        if w and w.get("max_ft") is not None:
            beach.append(f"waves to {w['max_ft']:g} ft (model)")
    if sp and sp["fields"].get("rip_current_risk"):
        beach.append(f"rip risk {sp['fields']['rip_current_risk']}")
    buoy = data.get("buoy") or {}
    if not ahead and buoy.get("water_temp_f") is not None:
        beach.append(f"water {buoy['water_temp_f']}F")
    elif sp and sp["fields"].get("water_temp"):
        beach.append(f"water {sp['fields']['water_temp'].lower()}")
    if beach:
        lines.append(f"{lab('beach')}: " + ", ".join(beach))
    fc = day_forecast(data, day)
    if fc:
        lines.append(f"{lab('weather')}: {fc['short']}, high {fc['temp_f']}, wind {fc['wind']}")
    marine = data.get("marine") or {}
    if not ahead and marine.get("periods"):
        lines.append(f"On the water: {marine['periods'][0]['headline']}")
    sun = sun_for(data, day)
    if sun:
        moon = (data.get("moon") or {}).get("phase")
        tail = f", {moon}" + ("" if moon.endswith("moon") else " moon") if moon else ""
        lines.append(f"{lab('sun')}: up {config.short_clock(sun['sunrise'])}, down "
                     f"{config.short_clock(sun['sunset'])}{tail}")
    return lines


def edition_url(date_iso: str) -> str:
    return f"{config.SITE_BASE}/{date_iso}/"


def build_text(data: dict, report: dict | None) -> str:
    head = f"{config.TEXT_MARKER}, {config.weekday_label(data['date'])}"
    parts = [head]
    prose = (report or {}).get("sections", {}).get("Text", "").strip() if report else ""
    if prose:
        parts.append(prose)
    numbers = numbers_block(data)
    if numbers:
        parts.append("\n".join(numbers))
    parts.append(f"Full report: {edition_url(data['date'])}")
    return "\n\n".join(parts) + "\n"


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


def tide_table(data: dict, day: str) -> str:
    rows = []
    for st in config.TIDE_STATIONS:
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

    sun = sun_for(data, day)
    cards.append("<div class=card><h3>Sun</h3><ul>"
                 + (f"<li><b>Sunrise</b> {esc(sun['sunrise'])}</li><li><b>Sunset</b> "
                    f"{esc(sun['sunset'])}</li>" if sun else "<li class=muted>no reading</li>")
                 + "</ul></div>")
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


def page(data: dict, report: dict | None, editions: list[str], date_iso: str) -> str:
    kind = data.get("kind") or "daily"
    meta = (report or {}).get("meta", {})
    sec = (report or {}).get("sections", {})
    headline = meta.get("headline") or "The numbers"
    title = f"Topsail Reporter, {config.weekday_label(date_iso)}"
    parts = [f"<header class=mast><h1>Topsail Reporter</h1><div class=sub>"
             f"Topsail Island, NC &middot; {esc(config.weekday_label(date_iso))}, "
             f"{date_iso[:4]} &middot; {esc(KIND_LABEL.get(kind, kind))}</div></header>"]
    for a in data.get("alerts") or []:
        parts.append(f"<div class=alert>{esc(a['event'])}: {esc(a.get('headline') or '')}</div>")
    parts.append(f"<h2 class=headline>{inline_md(headline)}</h2>")
    if sec.get("Lead"):
        parts.append(f"<div class=lead>{block_md(sec['Lead'])}</div>")
    elif not report:
        parts.append("<p class=lead>Numbers only so far. The write-up lands here when it is done.</p>")
    parts.append(numbers_panel(data))
    for name in PAGE_SECTIONS:
        if sec.get(name):
            parts.append(f"<section><h2>{esc(name)}</h2>{block_md(sec[name])}</section>")
    parts.append(outlook_table(data))
    if sec.get("Sources"):
        parts.append(f"<section class=sources><h2>Sources</h2>{block_md(sec['Sources'])}</section>")
    archive = " ".join(
        f"<a href='../{d}/'>{esc(config.weekday_label(d))}</a>" if d != date_iso
        else f"<b>{esc(config.weekday_label(d))}</b>" for d in editions)
    parts.append(
        "<footer><p>Tides: NOAA CO-OPS. Forecasts, surf and alerts: NWS Wilmington. "
        "Buoy: NDBC. Sun and model waves: Open-Meteo. Numbers fetched "
        f"{esc(data.get('generated_et'))}. All times Eastern.</p>"
        "<p>Size and bag limits change by proclamation: check NC Division of Marine "
        "Fisheries before you keep a fish. Swim near a lifeguard or not at all when the "
        "rip risk is up.</p>"
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
        _write(os.path.join(site, "text", f"{d}.txt"), build_text(data, report))
    if dates:
        latest = shown[-1]
        html_latest = page(load_data(latest, root), load_report(latest, root), shown, latest)
        # The index sits one level up from the edition folders.
        _write(os.path.join(site, "index.html"), html_latest.replace("href='../", "href='./"))
    else:
        _write(os.path.join(site, "index.html"), EMPTY_INDEX)
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
                        help="print that edition's text after rendering")
    args = parser.parse_args(argv)
    dates = render_all()
    print(f"OK: rendered {len(dates)} edition(s): {', '.join(dates) or 'none'}")
    if args.show:
        with open(os.path.join(HERE, "site", "text", f"{args.show}.txt"), encoding="utf-8") as f:
            text = f.read()
        print("----- text -----")
        print(text, end="")
        print(f"----- {len(text)} characters -----")
    return 0


if __name__ == "__main__":
    sys.exit(main())
