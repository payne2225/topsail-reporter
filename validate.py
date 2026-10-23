"""Check a written report against its own morning's data before it ships.

    python validate.py --date 2026-11-05

Prints OK, or every problem found and exits 2. Fix the REPORT, never this
file: each rule is here because a text that breaks it should not reach a
phone.

What it holds the writer to:
  - the front matter (date, kind, a headline and an island_headline that fit),
  - the sections, all of them, in plain prose,
  - both texts' prose (Text, Island Text): short, plain, no link (render
    adds it), no em dash,
  - every clock time in the text, the lead, The Bite and Beach & Weather
    matches a time in data/<date>.json (a tide, the surf forecast's inlet
    tide, sunrise or sunset). Event times belong in Around the Island and
    Things To Do, which are exempt. A time in the Island Text or the Island
    Lead may be a data time or one those two sections already carry (an
    event or an opening hour, sourced there),
  - at least two real source links,
  - no placeholder left behind.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

import config
import render

HERE = os.path.dirname(os.path.abspath(__file__))
TIME_CHECKED_SECTIONS = ["Text", "Lead", "The Bite", "Beach & Weather"]
# The Island Edition's own words may also repeat a time the sourced
# sections give (the museum opens at 11:00 AM).
ISLAND_TIME_SECTIONS = ["Island Text", "Island Lead"]
EVENT_SECTIONS = ["Around the Island", "Things To Do"]
TEXT_SECTIONS = ["Text", "Island Text"]
CLOCK = re.compile(r"\b(\d{1,2}):(\d{2})\s*([AaPp])?\.?\s*(?:[Mm]\.?)?(?![\w:])")
PLACEHOLDERS = re.compile(r"\b(TODO|TBD|TK|XX+|lorem ipsum)\b|\{\{|\}\}|<insert", re.I)


def _norm(h: str, m: str, ap: str | None) -> tuple[str, str | None]:
    return f"{int(h)}:{m}", (ap.lower() if ap else None)


def data_times(data: dict) -> set[tuple[str, str]]:
    """Every (H:MM, a/p) the morning's data holds."""
    times: set[tuple[str, str]] = set()

    def add(text: str):
        for mm in CLOCK.finditer(text or ""):
            hm, ap = _norm(*mm.groups())
            if ap:
                times.add((hm, ap))
    for st in (data.get("tides") or {}).values():
        for day in st.get("days", []):
            for e in day["events"]:
                add(e["time"])
    for s in ((data.get("weather_model") or {}).get("sun") or []):
        add(s["sunrise"])
        add(s["sunset"])
    for p in ((data.get("surf_zone") or {}).get("periods") or []):
        add(p["fields"].get("tides", ""))
    return times


def check(date_iso: str, data: dict, report: dict | None) -> list[str]:
    problems: list[str] = []
    if report is None:
        return [f"reports/{date_iso}.md does not exist"]
    meta, sec = report["meta"], report["sections"]

    if meta.get("date") != date_iso:
        problems.append(f"front matter date is {meta.get('date')!r}, not {date_iso}")
    kind = config.kind_for(date_iso)
    if meta.get("kind") != kind:
        problems.append(f"front matter kind is {meta.get('kind')!r}; today's kind is {kind!r}")
    for key in ("headline", "island_headline"):
        value = meta.get(key, "")
        if not value:
            problems.append(f"front matter has no {key}")
        elif len(value) > config.HEADLINE_MAX:
            problems.append(f"{key} is {len(value)} characters (max {config.HEADLINE_MAX})")
    headline = meta.get("headline", "") + "\n" + meta.get("island_headline", "")

    for name in render.REQUIRED_SECTIONS:
        if not sec.get(name, "").strip():
            problems.append(f"section '## {name}' is missing or empty")
    for name in sec:
        if name not in render.SECTIONS:
            problems.append(f"unknown section '## {name}' (allowed: {', '.join(render.SECTIONS)})")

    for name in TEXT_SECTIONS:
        text = sec.get(name, "").strip()
        if not text:
            continue
        n = len(text)
        if n < config.TEXT_PROSE_MIN or n > config.TEXT_PROSE_MAX:
            problems.append(f"{name} is {n} characters; keep it between "
                            f"{config.TEXT_PROSE_MIN} and {config.TEXT_PROSE_MAX}")
        if re.search(r"https?://|www\.", text):
            problems.append(f"{name} carries a link; render.py adds the report link itself")
        if re.search(r"\*\*|\[|\]|^#|^- ", text, re.M):
            problems.append(f"{name} has markdown in it; a text message is plain words")
        if "—" in text:
            problems.append(f"{name} has an em dash; use a comma or a full stop")
        if text.lower().startswith(config.TEXT_MARKER.lower()):
            problems.append(f"{name} starts with '{config.TEXT_MARKER}'; render.py writes that line")

    known = data_times(data)
    sourced = set()
    for name in EVENT_SECTIONS:
        for mm in CLOCK.finditer(sec.get(name, "")):
            sourced.add(_norm(*mm.groups()))
    for names, pool, where in (
            (TIME_CHECKED_SECTIONS, known, "(event times go in Around the Island)"),
            (ISLAND_TIME_SECTIONS, known | sourced,
             "or in Around the Island or Things To Do (put the event there first)")):
        pool_bare = {hm for hm, _ in pool}
        for name in names:
            for mm in CLOCK.finditer(sec.get(name, "")):
                hm, ap = _norm(*mm.groups())
                ok = (hm, ap) in pool or (hm, None) in pool if ap else hm in pool_bare
                if not ok:
                    problems.append(f"'{mm.group(0).strip()}' in '## {name}' matches no tide, "
                                    f"sun or surf-forecast time in today's data {where}")

    links = re.findall(r"\]\((https?://[^)\s]+)\)", sec.get("Sources", ""))
    if len(links) < 2:
        problems.append(f"Sources has {len(links)} link(s); list at least two you read today")

    whole = "\n".join(sec.values()) + "\n" + headline
    for mm in PLACEHOLDERS.finditer(whole):
        problems.append(f"placeholder left in the report: {mm.group(0)!r}")
    return problems


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", required=True)
    parser.add_argument("--root", default=HERE, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    data = render.load_data(args.date, args.root)
    problems = check(args.date, data, render.load_report(args.date, args.root))
    if problems:
        print(f"PROBLEMS in reports/{args.date}.md ({len(problems)}). Fix the report, "
              "never the validator:")
        for p in problems:
            print(f"  - {p}")
        return 2
    print(f"OK: reports/{args.date}.md passes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
