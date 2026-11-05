# Patch notes

## 2026-11-05

- The texts close with "Click the link below for the Full Daily Topsail
  Report:" and the link on its own line under it (Nate, exactly that
  wording, after a first pass read "Click the link below for the full
  report"; it was "Full report: <link>"). Every `site/text/*.txt`
  re-rendered; the routine's runs from Nov 6 on write it the new way.
- The file-instead-of-words fix works: Nate's test on the fishing
  shortcut (Text holding Get Text from Input's token, Set Variable
  `Message`, If and Send Message both on `Message`) sent the words. Swapping
  the If's input resets its condition to "is", which fails every day ("No
  Topsail Reporter today"), so "begins with" has to be picked again.
  `docs/SHORTCUT.md` now says so, and builds the Island shortcut by
  duplicating the fixed fishing one.
- The Nov 5 file-instead-of-words texts: Nate's screenshots show the
  shortcut wired right (Get Text from Input, Send Message sends Text), so
  the guide now blames iOS 27 handing the `.txt` file through, and the fix
  being tried is a fresh Text action and a `Message` variable before the
  If and Send Message, tested on a duplicate with only one's own number.
- `docs/SHORTCUT.md` rewritten for iOS 27 (Nate: "Apple updated their
  Shortcuts app"): the Time of Day trigger is now an action at the top of
  the shortcut, the Automation list holds every shortcut with one, running
  without asking is Info, Privacy, Allow Running When Locked, variables go
  in by Select Variable and the blue token, Send Message can send to a
  group conversation. The file-instead-of-words fix has its own section.
- The Nov 5 texts went out as two `.txt` attachments (801 and 750 bytes,
  the right files, served as text/plain) instead of the words: a Shortcut
  wiring slip, not the site. The fix is in `docs/SHORTCUT.md` and HANDOFF
  §5.
- Ready to pick up from any machine (Nate: "so that I can pick up at any
  point from my Mac"): `CLAUDE.md` at the root sends every session to the
  handoff first and asks for the patch notes and handoff in the same
  commit as a change; `docs/HANDOFF.md` gains §0, a resume point
  rewritten at the end of each session, and §6, the setup on another
  machine.

## 2026-11-04

- The section links fit a phone ("can you make these fit better?"): the
  chips share the row and shrink to fit (all six on the island page from
  a 360px screen up, no sideways scroll), with less space above the row
  and before the numbers. Desktop keeps its fixed chips.
- "Also worth trying" is now "Around the Topsail area" (Nate).
- Lunch & Dinner opens on Lunch until 3 PM and on Dinner from 3 PM
  (Nate), now by island time instead of the phone's own clock, so a phone
  set to Central switches at 3 PM Eastern too.
- Max's Pizza joins Our favorites (Nate: "so we have an even number"):
  six now, Riverview, Low Tide, Daddy Mac's, Sears Landing, Max's and
  Breezeway.
- Lunch & Dinner, on Nate's next pass: "Closed today" is a list; the
  favorites stay in Our favorites even when closed, with a red Closed
  pill; and every place gets a live pill worked out on the device at
  load, in Eastern time: green Open, yellow Opening soon (within the
  hour), red Closed. An edition opened later in its week moves "Today"
  to the real day. Checked in a browser on a Central-time clock at 8:30,
  10:15 and 11:15 AM Wed and 4:20 PM Thu (ET).
- Desktop restaurants ("doesnt look very clean on the desktop version.
  lots of gaps and spaces"): from 1360px each place is a card, two to a
  row, the two in a row the same height, with "Click for details" pinned
  to the bottom so the pills line up. The 9bfe129 Pages deploy timed out
  on GitHub's side (tests passed); this push deploys it.
- Lunch & Dinner gets a Day row (Nate, passing on a reader's idea: "the
  days they are open too since it all changes in the fall"): Today and the
  next six days, as a switch under Lunch | Dinner. Each place is built once
  with its days and meals as classes, its hours and weekly special per day,
  and a closed line per day; CSS shows the chosen day's, no script. "Our
  picks" is now "Our favorites"; a favorite closed today is starred in the
  closed line. Breezeway and Daddy Mac's were favorites already: Breezeway
  shows on its open nights, Thu to Mon.
- On Nate's next pass: the Editions at the foot of both pages are a
  dropdown, newest first ("should look cleaner like that"). The island
  sidebar loses its Weather and The beach cards ("they're redundant"; the
  Surf tile still shows the rip risk whenever NWS rates one). On a phone
  the island Outlook is a card between Beach & Weather and Things To Do,
  and its Week chip follows Beach. The fishing page's Parting Shot is now
  The Last Cast; `## Parting Shot` in an older report reads as the new
  name.
- The Island Edition, on Nate's review: Beach & Weather first, then Things
  To Do, Around the Island and Lunch & Dinner; the Outlook moves into the
  numbers sidebar; the fishing Parting Shot is off the island page, which
  closes on a Quote of the Day from the new `reference/quotes.json` (19
  hand-checked beach, sea and sailing lines with authors, one a day in
  turn). Breezeway is `open` on its posted hours ("we're going to just
  assume its open"), so it lists on its dinner nights, Thu to Mon.
- Desktop scales ("feels like a cheap non-scalable mobile version"): from
  1080px the root type grows with the window (16px at 1440 to 21px at
  2400 and up), the page fills up to 96rem or 94% of the window, the
  sidebar is 29% of it, and from 1360px The Bite's waters, the label
  rows, Around the Island, the Things To Do cards and the restaurants run
  two to a row. Fixed font sizes moved to rem so they scale with it.
- Shorter pages, built to scan (Nate: "very long walls of text ... lets
  try to be more concise" and "use styling to break up the continuous
  text-heavy look"). The Nov 4 sample's report ran 5,300 words, The Bite
  1,700 of them. Now each section is a card; a sticky row of section links
  sits under the lead; The Bite opens with a highlighted best bet and runs
  one block per water with When / Where / Bait / Latest rows; Beach &
  Weather, Around the Island and Regs Corner are label rows; Things To Do
  are pick cards; the Parting Shot is a pull quote. `instructions/report.md`
  gives the dialect and the caps, and `validate.py` holds them (words per
  section, 45 words per paragraph or bullet, bullet counts, the best bet
  first). A phone-width mockup of today's facts in the new form ran 6,100
  px tall against 12,900.
- Restaurants open from a "Click for details" pill instead of the "+"
  (Nate's words); it reads "Hide details" while open. Sources open from a
  Show pill the same way.

- A sample edition today, Wed Nov 4, for Nate to test the Shortcuts the
  day before the first preview ("make a preview today that I can test
  out"). `config.SAMPLE_DATES` gains 2026-11-04 and the routine is run by
  hand; like the earlier samples it is written like a daily morning and
  drops out of the archive once the Nov 5 preview exists. The cron and the
  run's dates are unchanged.

## 2026-10-29

- Arrival moved a day earlier (Nate: "We're driving down on Friday the
  6th"): one preview Thu Nov 5, arrival day Fri Nov 6, daily Nov 7-13, last
  morning Sat Nov 14 unchanged. `config.py` (`PREVIEW_DATES`,
  `ARRIVAL_DATE`), the kind test, the preview wording in
  `instructions/report.md` (Friday, not Saturday), and the specials task's
  first day (`install_task.ps1 -First 2026-11-06`). The routine's cron and
  the Nov 5 hours check are unchanged.

## 2026-10-28

- Restaurant news shows one hours item and one menu item per place, the
  newest of each (d574bb2). Jolly Roger reposts the same grill hours every
  week (Oct 25 and Oct 26), which showed twice in its details. The 21-day
  window and `until` rules are unchanged.

## 2026-10-23 (the run moves)

- The run moved one week later (Nate: "we need to change the dates to 11/7
  to 11/14"): previews Thu Nov 5 and Fri Nov 6, arrival Sat Nov 7, daily
  Nov 8-13, last morning Sat Nov 14. `config.py` run dates, the routine's
  cron (`30 8,9 5-14 11 *` UTC, 3:30 and 4:30 AM EST), the specials task
  (Nov 7-14, 11:15 AM and 4:15 PM) and the tests that pin run days. The
  reference files are re-researched for the new window.
- Reference files re-read for Nov 5-14 (all sources read 2026-10-23):
  `calendar.md` rebuilt (Nov 6-8 surf and pier challenge on all three
  piers, Sat Nov 7 Spot Festival / Holly Ridge Live / veterans parades,
  Veterans Day closures, roadwork); `regs.md` gains a "does anything change
  in the window" section (no recreational change; FF-45-2026 black sea
  bass row; commercial Spanish mackerel closes 8 PM Nov 13); `sources.md`
  almanac recomputed (new moon Nov 9, sunrise 6:34-6:43 AM after the clock
  change); `spots.md` and `island.md` open-in-the-window lines (Bush Marina
  ramp closed from Nov 2, free parking in Topsail Beach and Surf City,
  turtle hospital no tours until Nov 27).
- Hours check before the run (Nate asked for it after Breezeway's page
  showed no closing notice): `local/fb_hours.py` reads the picks' Facebook
  pages two weeks back and alerts Nate once, Thu Nov 5 at 11:15 AM ET,
  with any post about closing, cut-back days or hours, or reopening (or
  that there were none). Task "Topsail Reporter hours check" via
  `install_task.ps1`. `read_page` takes a `scrolls` limit (default 14,
  unchanged for the specials check).
- 2026-10-24: the three jobs back on (Nate: "Yes to both"). The 13 items
  the interrupted run found are on the site (`reference/fb_news.json`).
  New status `season` for a place that has said it is closed for the
  season (Island Delights, last day Oct 25): one "Closed for the season"
  line, not Call first. Coastal Wing's hours from its own Oct 19 post.
- FIX (alert flood, 2026-10-23 evening): the first live news run ran the
  tests in the job's clone; one test called the specials check expecting it
  to refuse a working copy, but in the clone it ran live, which ran the
  tests again, in a loop, each level sending "the tests failed" to Nate's
  channel. Stopped by hand; nothing was pushed. Now: tests/conftest.py sets
  TOPSAIL_IN_TESTS, under which no check runs live and send_alert sends
  nothing; the test points the check at a temp folder; send_alert sends at
  most 6 alerts an hour whatever happens; the guards run before any file
  is read. The news job's first run looks two weeks back by itself.
- Restaurant news, daily until the last edition (Nate: "Start collecting
  data from the restaurants daily until the end of our trip because some
  places made off season menu postings today like Daddy Mac's"):
  `local/fb_news.py` reads every place's Facebook page each evening at
  8:30 PM ET, archives every post locally (never committed), and has Opus
  5.5 keep hours, season and menu news as one plain sentence each in
  `reference/fb_news.json`. The Island Edition shows them on the place
  ("On Facebook, Oct 23: Off-season lunch specials start Tuesday, Oct
  27..."); hours news shows without a tap; a one-time closure disappears
  after its date. New items alert Nate. `read_page` gains `stop_before`
  (stops once two posts older than the window have gone by).
- Every restaurant shows its open days and hours (Nate: "i want all the
  restaurants (not just the fave list) to have their open hours and days"):
  the whole posted week in each place's details and under Call first, and
  the days each closed-today place opens ("Beach Shop & Grill (open
  Thu–Sun)"). A place open only for breakfast says "no lunch or dinner"
  instead of looking closed. The in-run note now gives the real check times
  (about 11:15 AM and 4:15 PM, not 10:30 and 3:30).
- Every place's hours re-checked: own sites re-read (no change), and the
  hours each restaurant posts on its own Facebook Page read for the ones
  whose sites block readers. Island Delights posted fall hours today (Fri
  now 11-3, Sat 11-7); Margaritas' Monday and Tuesday filled (11-10, from
  a 2022 Visit Pender article; Wanderlog's were garbled); Riverview and
  Shuckin' Shack confirmed by their pages; conflicts named in the notes
  (Splash, Coastal Wing, Shaka Taco, Sears Landing, Fancy Sushi's
  Tuesday). Ocean's Edge has no hours anyone stands behind: listings
  disagree and two say temporarily closed, so it stays under Call first.
  The list's `read` date is now Oct 23.
- `restaurants.json` hours re-synced to the restaurants' own sites: Beach
  Shop & Grill closed Mon-Wed with lunch Fri-Sat only, Breezeway Sunday
  5-8:30, Daddy Mac's no Sunday dinner this fall.

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
