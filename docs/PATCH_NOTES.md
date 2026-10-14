# Patch notes

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
