# Topsail Reporter: handoff

Living state. Read this first; update it in the same commit as anything
that changes how the Reporter works.

## 1. What it is

A morning report on Topsail Island, NC. Ten mornings: previews Thu Oct 29
and Fri Oct 30, arrival day Sat Oct 31, daily Nov 1-6, last morning Sat
Nov 7 (2026). Clean voice, light humor.

Two editions a morning from one report file (since 2026-10-16, Nate: "the
current one stays as is for us who fish, but we could have a non-fishing
one for everyone else"):

| Edition | Page | Text | Numbers |
|---|---|---|---|
| Fishing | `<date>/` | `text/<date>.txt` | sound tides, weather, wind, beach, water, marine, sun, moon |
| Island Edition | `<date>/island/` | `text/<date>-island.txt` | weather day and night, wind, beach, water, beach low tide, sun |

Each text goes out from the sender's own number through its own iPhone
Shortcut automation and its own group (`docs/SHORTCUT.md`). Both open
with "Topsail Reporter", so the same begins-with check guards both.

## 2. Hard rules

- The repo and site are PUBLIC: no reader names, no phone numbers, no
  addresses, nothing about who is where or when anyone travels.
- Never invent a fact. Numbers come from `data/<date>.json`; words come from
  sources read that morning or `reference/` (dated).
- Regulations only from NC Division of Marine Fisheries.
- Fix the edition, never the validator. Tune behaviour in
  `instructions/report.md`, not in code.
- `python -m pytest -q` before pushing any `.py` change. CI runs the same
  tests and refuses to deploy on a red run.
- `main` must be runnable by the morning routine after every push.

## 3. How a morning runs

Cloud routine **Topsail Reporter**, `trig_0191168AXrPkqA7rHyQ446eP`
(environment `env_01HRBGRSDmfX7Vur76oE8Lkh`, source this repo only, no
secrets: it only pushes here). Disable it after Nov 7 with
`{"enabled": false}` (the API has no delete).

Fable 5.1, cron `30 8,9 1-7,29-31 10,11 *` (UTC): 4:30 and
5:30 AM EDT through Oct 31, 3:30 and 4:30 AM EST from Nov 1. The day list
in the cron keeps it silent outside the run, except Oct 1-7 and Nov 29-30,
which the gate turns away (`OFF`).

1. `gate.py`: OFF / DONE / BUSY stop the fire; GO carries on.
2. `fetch.py` -> `render.py` -> `publish.py --what numbers`: a numbers-only
   edition is live a few minutes after the fire starts.
3. Research, then `reports/<date>.md` per the playbook: the fishing
   sections, plus `island_headline`, Island Text, Island Lead and Things
   To Do for the Island Edition (`reference/island.md` is its background).
4. `validate.py` until OK, `render.py --print`, `publish.py --what full`,
   `check_live.py` until LIVE (it waits for both texts).
5. Pages deploys `site/` after the tests pass (about two minutes).
6. 6:30 AM: the Shortcut fetches `text/<date>.txt`, checks that it begins
   with "Topsail Reporter", and sends it (`docs/SHORTCUT.md`). The Island
   Edition's Shortcut does the same with `text/<date>-island.txt`, at
   whatever time its owner set.

The second fire stands down (BUSY) while the first fire's numbers edition
is under 75 minutes old, and (DONE) once the full report is on origin.
If the first fire never ran, the second writes the edition.

**Samples.** `config.SAMPLE_DATES` lets a manual run of the routine write a
rehearsal edition outside the run (kind `sample`). Samples drop out of the
archive and the index on their own once the first real edition exists;
their pages stay reachable by direct link.

**Rehearsal record.** 2026-10-14, 19:00 UTC, session
`cse_01KwGYAL9D7oSbqt1oqo3DUe`: GO sample, 8/8 feeds, numbers edition
pushed 19:01, full report validated first try, PUSHED and LIVE 19:06:57.
About seven minutes from fire to live, so a 4:30 AM fire has two hours of
slack before 6:30 even with the scheduler running late.

## 4. Data sources (all keyless, checked 2026-10-14)

| Feed | Where | Note |
|---|---|---|
| Tides | NOAA CO-OPS 8657813 Hampstead (sound, leads), 8657419 Ocean City Beach pier (ocean) | full 4-event cycle per day, spillover tagged with weekday |
| Surf, rip risk, water temp | NWS ILM surf zone forecast, NCZ106 Coastal Pender | refused if older than 36 h (seasonal product) |
| Marine | NWS AMZ250, Surf City to Cape Fear | |
| Forecast | NWS gridpoint ILM 100,83 | |
| Alerts | NWS active alerts at the point and AMZ250 | |
| Buoy | NDBC 41110 Masonboro Inlet, 16 mi down the coast | measured waves and ocean temp |
| Sound temp proxy | CO-OPS 8656483 Beaufort, 60 mi | estuarine, credited as a proxy |
| Sun, wind by hour, model waves | Open-Meteo | model waves labelled "model" |

## 5. When it breaks

- No text at 6:30: the Shortcut shows "No Topsail Reporter today" and sends
  nothing. Check the routine's session log and the Actions tab.
- A feed is down: its line drops out of the text and the page says
  "no reading". Nothing to fix unless it lasts.
- The NWS stops issuing the surf zone forecast for the season: the beach
  line falls back to model waves; rip risk drops out.
- Deploy failed (red Actions run): the fix is a code fix; run the tests
  locally, push, and the deploy re-runs on push.
