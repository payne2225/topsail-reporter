# Topsail Reporter

A fishing-first morning report on Topsail Island, NC: tides, water, surf,
wind, what is biting and what is going on around the island. One edition a
morning, written by a scheduled Claude routine, published here and sent as
a group text by an iPhone Shortcut at 6:30 AM Eastern.

Site: https://payne2225.github.io/topsail-reporter/

## How a morning runs

1. `gate.py` decides whether this fire writes today (two fires a morning).
2. `fetch.py` pulls every number (NOAA tides, NWS forecasts and surf zone
   forecast, the Masonboro Inlet buoy, Open-Meteo) into `data/<date>.json`.
3. `render.py` + `publish.py` put a numbers-only edition live within minutes.
4. The routine researches the day (reports, regulations, events) and writes
   `reports/<date>.md` following `instructions/report.md`.
5. `validate.py` holds the report to its own data; `render.py` builds the page
   and the text; `publish.py` pushes; `check_live.py` confirms the live text.
6. GitHub Actions runs the tests and deploys `site/` to Pages.
7. At 6:30 the Shortcut fetches `text/<date>.txt` and sends it
   (`docs/SHORTCUT.md`).

## Layout

| Path | What |
|---|---|
| `config.py` | Place, stations, zones, the run's dates, the text limits |
| `instructions/report.md` | The routine's playbook. Tune the paper here |
| `reference/` | Checked background: sources, spots, regulations, the fall bite, the calendar |
| `data/`, `reports/` | Each morning's numbers and words |
| `site/` | What Pages serves (rendered, committed) |
| `docs/HANDOFF.md` | How it all fits, and what to do when it breaks |

Tests: `python -m pytest -q` (offline; fixtures in `tests/fixtures/`).
