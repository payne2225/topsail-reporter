"""Everything fixed about the Topsail Reporter: where, which stations, when.

The repo is PUBLIC. Nothing in it names a reader, says who is on the island,
or carries an address. The report is about the water, not the people.
"""

from __future__ import annotations

import datetime as dt

SITE_BASE = "https://payne2225.github.io/topsail-reporter"

# The first line of every text. The iPhone Shortcut only sends a text that
# BEGINS with this, so a GitHub 404 page can never go out as a message.
TEXT_MARKER = "Topsail Reporter"

# Two editions a morning from one report (Nate, 2026-10-16: "the current
# one stays as is for us who fish, but we could have a non-fishing one for
# everyone else"). The Island Edition is the same day off the water: its
# own text, page and numbers, and its own Shortcut and group.
ISLAND_NAME = "Island Edition"
EDITIONS = ("fishing", "island")


def text_file(date_iso: str, edition: str = "fishing") -> str:
    """The text's file name under site/text/: '2026-10-29.txt' or '2026-10-29-island.txt'."""
    return f"{date_iso}.txt" if edition == "fishing" else f"{date_iso}-{edition}.txt"


def page_path(date_iso: str, edition: str = "fishing") -> str:
    """The page's folder under the site: '2026-10-29/' or '2026-10-29/island/'."""
    return f"{date_iso}/" if edition == "fishing" else f"{date_iso}/{edition}/"

PLACE = "Topsail Beach, NC"
LAT, LON = 34.3669, -77.6300

# NWS Wilmington (ILM). Checked live 2026-10-14: points/34.3669,-77.63 gives
# gridpoint ILM 100,83 and forecast zone NCZ106 (Coastal Pender), and the
# surf zone forecast's NCZ106 block reads "Including the beaches of Surf City
# and Topsail Beach". The marine zone for the water off Topsail Beach is
# AMZ250 (AMZ158 is the zone north of Surf City).
NWS_GRID = ("ILM", 100, 83)
LAND_ZONE = "NCZ106"
SURF_OFFICE = "ILM"
MARINE_ZONE = "AMZ250"
MARINE_ZONE_NAME = "Surf City to Cape Fear, out 20 nm"

# Tides. NOAA has no station at New Topsail Inlet; these two bracket it.
# The SOUND station leads: it is inside the same water as the sound fishing
# north of the inlet and runs over an hour behind the oceanfront.
TIDE_STATIONS = [
    {"key": "sound", "id": "8657813", "name": "Hampstead",
     "label": "Sound (Hampstead)",
     "note": "inside Topsail Sound and the ICWW; runs over an hour behind the beach"},
    {"key": "ocean", "id": "8657419", "name": "Ocean City Beach pier",
     "label": "Ocean (Ocean City pier)",
     "note": "oceanfront, the surf and inlet-mouth read"},
]
TIDE_DAYS = 4  # the edition day and the three after it

# Measured ocean water temperature and waves: NDBC 41110, the Masonboro
# Inlet buoy, about 16 miles down the coast. Its file is in metres and C.
BUOY = {"id": "41110", "name": "Masonboro Inlet buoy", "miles": 16,
        "bearing": "down the coast"}

# Sound-side water temperature has no gauge near Topsail. Beaufort (Duke
# Marine Lab) is estuarine, so it is the honest proxy, credited as such.
SOUND_TEMP_STATION = {"id": "8656483", "name": "Beaufort", "miles": 60,
                      "bearing": "up the coast"}

# Open-Meteo marine model grid point just off the beach (modelled, not
# measured: the page labels it so).
MARINE_MODEL_POINT = (34.35, -77.60)

# ------------------------------------------------------------------ the run
# Moved one week later on 2026-10-23 (was Oct 29 - Nov 7).
FIRST_EDITION = "2026-11-05"
LAST_EDITION = "2026-11-14"
PREVIEW_DATES = ("2026-11-05", "2026-11-06")
ARRIVAL_DATE = "2026-11-07"
DEPARTURE_DATE = "2026-11-14"

# Rehearsal editions outside the run, built end to end like a real one so
# the whole chain is proven before the first preview. Kind "sample".
# 2026-10-16 rehearses the Island Edition; 2026-10-20 is the island
# Shortcut test with a real reader on the group.
SAMPLE_DATES = ("2026-10-14", "2026-10-15", "2026-10-16", "2026-10-20")

# The text. The writer's part is short on purpose: the numbers block and
# the link are added by render.py, and a group MMS that scrolls forever is
# a group MMS nobody reads.
TEXT_PROSE_MIN = 60
TEXT_PROSE_MAX = 520
HEADLINE_MAX = 90

# Two fires a morning, 08:30 and 09:30 UTC (4:30 and 5:30 AM EDT; 3:30 and
# 4:30 AM EST). The second stands down while the first is working: a quick
# edition younger than this means an earlier fire is on it.
BUSY_MINUTES = 75


def kind_for(date_iso: str) -> str | None:
    """'preview', 'arrival', 'daily', 'departure', 'sample' or None (no edition)."""
    if date_iso in SAMPLE_DATES:
        return "sample"
    if not FIRST_EDITION <= date_iso <= LAST_EDITION:
        return None
    if date_iso in PREVIEW_DATES:
        return "preview"
    if date_iso == ARRIVAL_DATE:
        return "arrival"
    if date_iso == DEPARTURE_DATE:
        return "departure"
    return "daily"


# ------------------------------------------------------------------ clocks
def _nth_sunday(year: int, month: int, n: int) -> dt.date:
    first = dt.date(year, month, 1)
    return first + dt.timedelta(days=(6 - first.weekday()) % 7 + 7 * (n - 1))


def et_offset_hours(utc: dt.datetime) -> int:
    """-4 (EDT) or -5 (EST) at a UTC instant, by the US rule.

    Done by rule rather than zoneinfo so Windows without tzdata and the
    cloud sandbox agree. EDT runs from 2 AM EST on the second Sunday of
    March to 2 AM EDT on the first Sunday of November.
    """
    year = utc.year
    start = dt.datetime.combine(_nth_sunday(year, 3, 2), dt.time(7, 0), dt.timezone.utc)
    end = dt.datetime.combine(_nth_sunday(year, 11, 1), dt.time(6, 0), dt.timezone.utc)
    return -4 if start <= utc < end else -5


def eastern(utc: dt.datetime | None = None) -> dt.datetime:
    """The Eastern wall clock at `utc` (default now), as a naive datetime."""
    utc = utc or dt.datetime.now(dt.timezone.utc)
    return (utc + dt.timedelta(hours=et_offset_hours(utc))).replace(tzinfo=None)


def clock(t: dt.datetime | dt.time) -> str:
    """'6:12 AM': no leading zero, on every platform."""
    hour = t.hour % 12 or 12
    return f"{hour}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"


def short_clock(text: str) -> str:
    """'6:12 AM' -> '6:12a' for the text, where every character counts."""
    text = text.strip()
    for full, short in ((" AM", "a"), (" PM", "p")):
        if text.endswith(full):
            return text[: -len(full)] + short
    return text


def weekday_label(date_iso: str) -> str:
    """'Thu Oct 29'."""
    d = dt.date.fromisoformat(date_iso)
    return f"{d.strftime('%a')} {d.strftime('%b')} {d.day}"
