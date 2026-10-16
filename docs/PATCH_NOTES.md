# Patch notes

## 2026-10-16

- The Island Edition: a second, non-fishing edition every morning from the
  same report (Nate: "the current one stays as is for us who fish, but we
  could have a non-fishing one for everyone else"). Its own page
  (`<date>/island/`, newest at `island/`), its own text
  (`text/<date>-island.txt`, opening "Topsail Reporter, Island Edition") and
  its own numbers: weather day and night, wind, beach, water, the beach-side
  low tides, the sun. No sound tides, marine forecast or moon.
- The report gains `island_headline`, `## Island Text`, `## Island Lead` and
  `## Things To Do`. The validator holds the Island Text to the same text
  rules; a time in the Island Text or Lead may be a data time or one that
  Around the Island or Things To Do already sources.
- `check_live.py` waits for both texts. `render.py --print` prints both.
- `reference/island.md`: off the water (eating, attractions and their
  November hours, beach rules, day trips, rainy days, what's-on sources).
- The fishing page links to the Island Edition and back.
- SHORTCUT.md: a second automation for the island group.

## 2026-10-14

- The text's numbers block reads at a glance: one short line per item with
  an emoji up front, tides two to a row under "Sound tides", the sky emoji
  picked from the forecast and the moon emoji from its phase. A preview
  says "Sat Oct 31 outlook" once instead of prefixing every line, and
  leaves out the moon (the data's moon is the morning's, not Saturday's).
  The old block wrapped mid-line on a phone.
- First build. Fetcher for every Topsail number (NOAA tides at Hampstead and
  Ocean City pier, NWS forecast, AMZ250 marine, the Coastal Pender surf zone
  forecast, NDBC 41110, Beaufort sound proxy, Open-Meteo sun, wind and model
  waves), the gate (OFF/DONE/BUSY/GO), renderer (page, index, text),
  validator, publisher, live check, the morning playbook, and offline tests.
- Pages deploy via Actions, gated on the tests.
- reference/: sources (what is fetchable, what is blocked, an almanac for
  the run), regs (flounder closed for the window, trout open, limits with
  proclamation numbers), spots (piers, fees, blanket licences, the south
  end), fall-bite and calendar, all with source URLs and a 2026-10-14 check.
- Playbook: Fisherman's Post is the fishing report of record; NCDMF
  proclamations and the shellfish closure list are checked every morning.
- Rehearsal (cloud routine, run by hand at 3:00 PM): gate GO sample, 8/8
  feeds, numbers edition live at 3:01, the full report validated first
  try, PUSHED and LIVE at 3:07, 744-character text. The one snag: a fresh
  clone had no reports/ folder (git keeps no empty folders), so the first
  write failed and the session made the folder itself. reports/ and data/
  now carry a .gitkeep.
