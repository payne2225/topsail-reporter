# Topsail Reporter

A morning report on Topsail Island, NC, in two editions: the fishing
edition (tides, water, surf, wind, what is biting) and the Island Edition
(the same day off the water: weather, the beach, what is open, things to
do). Written each morning by a scheduled Claude routine, published here,
and sent as two group texts by iPhone Shortcuts.

Site: https://payne2225.github.io/topsail-reporter/ (fishing) and
https://payne2225.github.io/topsail-reporter/island/ (Island Edition)

## How a morning runs

1. `gate.py` decides whether this fire writes today (two fires a morning).
2. `fetch.py` pulls every number (NOAA tides, NWS forecasts and surf zone
   forecast, the Masonboro Inlet buoy, Open-Meteo) into `data/<date>.json`.
3. `render.py` + `publish.py` put a numbers-only edition live within minutes.
4. The routine researches the day (reports, regulations, events) and writes
   `reports/<date>.md` following `instructions/report.md`.
5. `validate.py` holds the report to its own data; `render.py` builds the page
   and both texts; `publish.py` pushes; `check_live.py` confirms both live.
6. GitHub Actions runs the tests and deploys `site/` to Pages.
7. The Shortcuts fetch `text/<date>.txt` (6:30 AM) and
   `text/<date>-island.txt` and send them (`docs/SHORTCUT.md`).

## Layout

| Path | What |
|---|---|
| `config.py` | Place, stations, zones, the run's dates, the text limits |
| `instructions/report.md` | The routine's playbook. Tune the paper here |
| `reference/` | Checked background: sources, spots, regulations, the fall bite, the calendar, off the water |
| `data/`, `reports/` | Each morning's numbers and words |
| `site/` | What Pages serves (rendered, committed) |
| `docs/HANDOFF.md` | How it all fits, and what to do when it breaks |

Tests: `python -m pytest -q` (offline; fixtures in `tests/fixtures/`).
