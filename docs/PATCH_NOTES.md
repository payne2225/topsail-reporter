# Patch notes

## 2026-10-23 (the run moves)

- The run moved one week later (Nate: "we need to change the dates to 11/7
  to 11/14"): previews Thu Nov 5 and Fri Nov 6, arrival Sat Nov 7, daily
  Nov 8-13, last morning Sat Nov 14. `config.py` run dates, the routine's
  cron (`30 8,9 5-14 11 *` UTC, 3:30 and 4:30 AM EST), the specials task
  (Nov 7-14, 11:15 AM and 4:15 PM) and the tests that pin run days. The
  reference files are re-researched for the new window.

## 2026-10-23

- Lunch & Dinner on the Island Edition (Nate: "Could we build lunch and
  dinner restaurant options in?"). Built from data, not written:
  - `reference/restaurants.json`: 33 places on and near the island with
    hours per weekday, ratings (Google and Tripadvisor via Wanderlog;
    Topsail Guide's Google figure where Wanderlog has none), what reviewers
    say, what people order, links, and weekly specials where a place posts
    them on its own site (SurfDog, Italian Bistro).
  - A Lunch | Dinner switch (no script needed; the page opens on Dinner
    after 3 PM), the day's specials on top, every open place below with
    tap-to-open details, then "Call first" (with numbers) and "Closed
    today".
  - The day's Facebook specials come from `specials/<date>.json` when it
    exists.
- `local/fb_specials.py`, `local/fb_login.py`, `local/fb_session.py`: the
  home-PC job that reads each restaurant's Facebook page about 10:30 AM
  and 3:30 PM ET, writes the day's specials, pushes, and alerts one
  person (Nate: "just update the page. Maybe alert just me"). Facebook
  URLs for 26 places added to `reference/restaurants.json`. Not scheduled
  yet: it needs the one-time sign-in and an alert channel first.
- Tuned on the signed-in feed: a post's time comes from hovering its time
  link (Facebook shows the full date only as a tooltip), and posts are read
  while on screen (Facebook empties the ones scrolled past). A specials
  board posted as a photo is read by Opus 5.5 through the Claude CLI and
  marked "read from the photo posted" on the page.
- Opus 5.5 keeps or drops each of the day's posts in one call (on Oct 22's
  posts it kept 11 specials and dropped 13: karaoke, a pub crawl, party
  booking, throwbacks, a fish catch); the keyword filter is the fallback.
  Post text loses "See more/less" and hashtags; long Discord alerts are
  split instead of cut. A page Facebook no longer shows is reported as
  unreadable.
- Facebook pages: Daddy Mac's and Max's Pizza had moved; found by Facebook
  search with Sears Landing, Fancy Sushi, SeaView Pier and Ocean's Edge.
  30 of the 32 open places now have one (none found for NY Corner Deli or
  Margherita).
- `local/install_task.ps1`: clones the job's own checkout and registers
  the hidden scheduled task (run-hidden.vbs, wake to run, run late if
  missed).
- The first picks (Nate: "lets start with Sear's Landing, Breezeway
  Restaurant, and Riverview Cafe"), starred and listed first; a pick that
  needs a call is starred under Call first.
- Sears Landing's Wing & Wine Night (half-price wings and wine, every
  Wednesday) from its own Facebook post; a weekly special now says whether
  it came from the place's site or its Facebook page. Breezeway's note now
  says it has posted through Oct 19 with no closing date.
- The check keeps only posts that link to the Page it read them on, and
  stops if Facebook sends it to the home feed, so no one else's post can
  reach the page.
- Check times 11:15 AM and 4:15 PM ET (Nate: "yes"): Riverview posted its
  lunch list at 10:48 and its dinner list at 3:42 on Oct 22, SurfDog
  between 9:20 and 11:30.
- The fishing page is fishing and the outdoors only (Nate: "maybe the
  fishing side of it is just fishing info and outdoor conditions"): Around
  the Island now shows on the Island Edition only.
- The playbook: the writer leaves lunch and dinner to the page and never
  picks one place for a meal (Nate: "we all discuss options for each
  meal").

## 2026-10-20

- The pages, restyled for a phone, an iPad and a computer (Nate: "can we
  pretty it up? Style it better for easier reading on a phone, ipad, and
  computer screen?"). The texts are unchanged.
  - A Fishing | Island switch under the masthead (44px tap targets) in
    place of the cross-link line.
  - Alerts say what and until when ("Small Craft Advisory until Wed
    6:00 PM, on the water") instead of the NWS's long headline sentence.
  - The headline is the paper's serif, in ink.
  - "The numbers": six tiles at a glance (the day, wind, surf and rip risk,
    water, sunrise or sunset, the moon or the beach low tide), every one
    from the data.
  - A tide chart per station: the day's curve drawn smooth between NOAA's
    predicted highs and lows, every high and low labelled, the dark hours
    shaded. Each tide is still listed under its chart. Hover, tap or the
    arrow keys give an estimated height and whether it is rising or falling.
  - Wind by the hour as a strip with arrows pointing the way the wind blows.
  - The outlook as one card per day (high, the night's low, sky, wind,
    rain chance at 10% or more) instead of a wide table.
  - Sources fold shut. The archive is a row of tap-sized pills.
  - On a phone or iPad the tiles and tides come first, then the write-up,
    then the detail cards and the week, so the write-up isn't buried. From
    1080px wide the write-up runs on the left and the numbers ride a sidebar.
  - Dark mode kept; the chart line colour passes the dataviz palette checks
    on both backgrounds. Checked at 320, 390, 820 and 1440px: no sideways
    scroll.

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
- Rehearsal (2026-10-16, session cse_016AFRHJ9FMYnMDgUoNCnj3A): fired
  2:09:12 PM, both texts LIVE 2:15:50 PM, the report validated on the
  second try (an event time in The Bite). Open-Meteo answered the cloud
  sandbox with 429 for both calls, and again on the session's own retry two
  minutes later, so the texts lost their sun line. Fixes: every fetch retries
  twice on 429 / 5xx; when Open-Meteo still refuses, sunrise and sunset are
  computed from NOAA's solar equations (within a minute of the USNO almanac
  on all ten mornings of the run) and the page credits them. The sample's
  data was backfilled the same way.
- Alerts say when: "Gale Warning from Sat 2:00p" before an alert starts,
  "until Mon 6:00a" once it has (fetch.py now keeps `onset`). The Island
  Edition leaves marine-zone alerts out; the rehearsal's island text led
  with a Gale Warning for the water on a sunny beach day.
- Playbook: a wind is named for where it comes from (the sample said a
  southwest wind was at your back walking south).

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
