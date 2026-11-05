# Topsail Reporter: handoff

Living state. Read this first; update it in the same commit as anything
that changes how the Reporter works. `CLAUDE.md` at the root says the same
to any session on any machine; §6 is the setup on a new one.

## 0. Resume point

Rewritten at the end of every session. As of Thu 2026-11-05, 4:15 PM ET:

- **The run is live.** The Thu Nov 5 preview published both editions
  (numbers 564ddaf, full 3d17327). Next: arrival day Fri Nov 6, then daily
  to the last morning Sat Nov 14. The routine fires at 3:30 and 4:30 AM ET;
  the Shortcuts text at 6:30.
- **The Shortcuts are fixed.** The Nov 5 texts arrived as `.txt`
  attachments; the fresh-string fix in `docs/SHORTCUT.md` (Text, Set
  Variable `Message`, If "begins with" re-picked) worked on the fishing
  shortcut, and the Island shortcut was rebuilt as a duplicate of it,
  tested, and given its whole group (Nate, 4:15 PM); the old Island
  shortcut is deleted and the fishing one has its full group back. The
  Fri Nov 6 texts are the first real check of both.
- **Latest work:** the 2026-11-05 entries in `docs/PATCH_NOTES.md` (the
  texts now close "Click the link below for the Full Daily Topsail
  Report:" with the link under it; the Shortcut fix; the Mac pickup
  setup), then the 2026-11-04 ones (the restyle, the Day row, Our
  favorites, the live pills, the phone fixes).
- **Next:** after the Nov 14 edition, disable the routine (RemoteTrigger
  update `{"enabled": false}` on the trigger in §3) and turn off both
  Shortcut automations.
- **Open, no action yet:** NY Corner Deli and Margherita have no Facebook
  page found; Topsail Steamer and Seaview Pier hours could not be
  verified; Ocean's Edge has no reliable hours. The restaurant news
  commits read "7:30 PM ET check" since the clocks changed; not looked at.
- **Decided, don't reopen:** the fishing page keeps its Outlook where it
  is (2026-11-04). Breezeway is treated as open on its posted hours.

## 1. What it is

A morning report on Topsail Island, NC. Ten mornings: a preview Thu Nov 5,
arrival day Fri Nov 6, daily Nov 7-13, last morning Sat Nov 14 (2026;
moved one week later on 2026-10-23, from Oct 29 - Nov 7; arrival moved a
day earlier on 2026-10-29, from Sat Nov 7, so Fri Nov 6 is no longer a
preview).
Clean voice, light humor.

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

The pages (since 2026-10-20) are built for a phone first. Order on a phone
or iPad: the Fishing | Island switch, any alert, the headline and lead,
a sticky row of section links (Numbers, The Bite, Beach, Regs, Week; on
the island To Do, Eat, Beach, Around, Week), "The numbers" (six tiles,
then a tide chart per station with every tide listed under it), the
write-up, the detail cards (wind by the hour and the marine forecast,
water, surf; the island's weather and beach), the week as day cards, and
Sources folded shut behind a Show pill. From 1080px wide the write-up runs
on the left and all the numbers ride a sidebar.

**Short sections as cards (since 2026-11-04**, Nate: "very long walls of
text ... lets try to be more concise"; the Nov 4 sample ran 5,300 words).
Each write-up section is a card. The report's dialect (`render.block_md`):
`> ` is a highlighted callout (The Bite's best bet), `### ` opens a block
(one per water), `- **Label:** ...` is a fact row, `- **Title.** ...` is a
pick card. `validate.py` caps the words per section (The Bite 300, Things
To Do 240, Around the Island 200, Regs 120, Beach & Weather 110, the leads
60, The Last Cast 30), every paragraph or bullet at 45, the bullets in
Things To Do (6) and Around the Island (7), and requires The Bite to open
with its best bet. Restaurants open from a "Click for details" pill (Nate's
words), which reads "Hide details" while open.

**The Island Edition's order (Nate, 2026-11-04):** the Island Lead, Beach
& Weather, Things To Do, Around the Island, Lunch & Dinner, then a **Quote
of the Day** instead of The Last Cast (which stays on the fishing page:
the island's "shouldnt be about fishing"). The Last Cast was the Parting
Shot until 2026-11-04 (Nate); `render.OLD_NAMES` reads `## Parting Shot`
as `## The Last Cast`, so the older editions show the new name. The quote comes from
`reference/quotes.json` (19 hand-checked beach, sea and sailing lines with
their authors), one a day in turn by date; the routine never writes or
edits it. The island's Outlook rides with the rest of the numbers in the
sidebar. Breezeway is `open` on its posted hours since 2026-11-04 (Nate:
"we're going to just assume its open"), so it shows in the main list on
the nights it opens (Thu to Mon dinner).

**Island cards and the phone order (Nate, 2026-11-04):** the island
sidebar is the tiles, the beach tides and the Outlook; the Weather and
The beach cards are gone ("they're redundant": the tiles, the Outlook and
Beach & Weather carry them, and the Surf tile shows the rip risk when NWS
rates one). On a phone the island Outlook sits between Beach & Weather and
Things To Do (`.page.isl` flattens `.body` and orders it in CSS), and its
Week chip follows Beach. The Editions at the foot of both pages are a
dropdown, newest first.

**Desktop (since 2026-11-04**, Nate: "feels like a cheap non-scalable
mobile version"): from 1080px the root type scales with the window
(16px at 1440, about 18.6px at 1920, 21px from 2400), the page is up to
96rem or 94% of the window wide, and the sidebar is 29% of it. From 1360px
the write-up uses the width: The Bite's waters, the label rows, Around the
Island and the Things To Do cards run two to a row, and so do the
restaurants. Every page is one
self-contained file: inline CSS, inline SVG, and a small inline script for
the chart's hover and tap readout (the page reads fine without it).
Restyle by editing `CSS` in `render.py`; every number on the page still
comes from `data/<date>.json`.

The fishing page is fishing and the outdoors only (since 2026-10-21):
Around the Island moved to the Island Edition. The Island Edition also
carries a Lunch & Dinner section that the writer never writes: `render.py`
builds it from `reference/restaurants.json` (33 places: hours per weekday,
status open/call/closed, Google and Tripadvisor ratings, a review summary,
weekly specials from a place's own site, and a `pick` flag for the
group's favorites) and from `specials/<date>.json` when one exists (the
day's Facebook specials, written through the day by a local job on the
home PC; the page names when it last checked). A place counts for lunch
when it is open across 12:30-1:30 and for dinner when it is open at 6:30
and stays open to 7; a `meals` list overrides that. The page opens on
Dinner after 3 PM. Places with unknown hours or a `call` status are listed
under "Call first" with their number; a `season` place (it has said it is
closed for the season) shows only in one "Closed for the season" line; picks sort first, under
"Our favorites" (Nate's name since 2026-11-04; it was "Our picks"), then by Google
rating. Every place shows its whole posted week (Monday first, days with the
same hours run together: "Mon closed · Tue–Sat 11 AM–9 PM · Sun 10 AM–3 PM")
in its tap-open details and under Call first, and the "Closed today" list
names the days each one does open. Refresh hours and ratings by editing the
JSON and its `read` date.

**Sort row (since 2026-11-04**, Nate: "ordering the restaurants either by
distance or alphabetical ... or have a sort option for either one"): under
the Lunch | Dinner switch, Sort: Top rated (the order the page is built in)
· A–Z · Closest to me. Picks stay first in every order. Closest asks the
phone for its location and shows straight-line miles on each place, worked
out from each place's `lat` / `lon` in `restaurants.json` (ArcGIS address
points, cross-checked against the Census geocoder; a new place needs both or
it sorts last). No starting point is ever published (public repo), so the
distance is from wherever the reader is. The choice is remembered on that
phone; Closest re-sorts itself on the next visit only if location is already
allowed. The row stays hidden without the script.

**Day row (since 2026-11-04**, Nate, from a reader: "the days they are open
too since it all changes in the fall"): between Lunch | Dinner and Sort, a
switch for the week ahead, Today then the next six weekdays. Each place open
some day that week is built once, with a class per day and meal (`l0`..`l6`,
`d0`..`d6`, 0 being the edition's day), an hours span per day (`.h0`..) and
its weekly special per day (`.w0`..); `render.DAY_CSS` shows the chosen
day's, and the closed line for each day (`.c0`..) sits inside `.meals` so
the radios reach it.

**Favorites always listed, live pills (Nate, 2026-11-04):** the favorites
stay in Our favorites on every day and meal ("keep restaurants in the our
favorites sections even when closed, just give it a closed pill"), with a
static red Closed pill (`.st.cx`, CSS) when they are not open for the chosen
day and meal, and "open Thu–Mon" in place of hours on their closed days.
They are never on the closed lists, which are lists now, not a sentence.
Every place carries its week in minutes (`data-hours`, null = unknown), and
the script, at load, works out Eastern time on the reader's device whatever
its time zone: green Open, yellow Opening soon (opens within the hour), red
Closed (`.st.lv`). It also moves "Today" to the reader's real day when the
edition is from earlier in that week (chips, the closed-list heading and
the weekly specials' day words, the `.dl` spans) and selects it. The live
pills show only while that day is chosen (`.meals.live`); another day shows
the static pills. An edition whose week has passed gets no live pills.

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
secrets: it only pushes here). Disable it after Nov 14 with
`{"enabled": false}` (the API has no delete).

Fable 5.1, cron `30 8,9 5-14 11 *` (UTC): 3:30 and 4:30 AM EST (the
whole run is after the Nov 1 clock change). The cron fires only on the
run's ten days; the gate still turns away any other day (`OFF`).

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

**Specials through the day (home PC, not the routine).** The cloud routine
cannot read Facebook, so `local/fb_specials.py` runs on the home PC in its
own clone (`%LOCALAPPDATA%\topsail-reporter\repo`), signed in to a
personal Facebook account in a browser profile beside it (`fb-profile`;
sign in once with `python local/fb_login.py`; the session never leaves that
folder). Each check reads every place's `facebook` page, keeps that
page's own posts from today, has Opus 5.5 keep only the ones about eating or
drinking there that day (specials, deals, hours changes; not events, party
booking, history or hiring; the keyword filter stands in if Claude cannot
be reached), merges them into `specials/<date>.json`, re-renders, runs the tests, pushes, and sends the
new posts to one person through `alert.json` in the same folder (ntfy or a
Discord webhook; never committed). Some places (SurfDog) post the day's
specials only as a photo of their board: a photo Facebook says shows text,
on a post from today, is read by Opus 5.5 through the home PC's Claude CLI
(image passed inline, no tools, told to copy only what is written and
answer NONE for a photo with no menu); the page then says "read from the
photo posted ...". A check resets its clone to GitHub's
main first, so it never conflicts with the routine, and it refuses to push
from any other checkout. A lapsed sign-in or a failed push sends an alert
instead. A post kept at an earlier check is reused, not re-read. The
hidden scheduled task "Topsail Reporter specials" is installed by
`local/install_task.ps1` (its `-Times` are the check times; `-First` to
`-Last` are the island days, Fri Nov 6 to Sat Nov 14); its log is
`specials.log` beside the clone.

**Hours check before the run (home PC, once).** The specials check keeps
only the day's posts, so a "closed for the season" post made before the run
would reach no one. `local/fb_hours.py` reads the pages of the places marked
`pick: true`, back two weeks (posts read as text, a photo with little text
read by Opus 5.5 for a notice), has Opus 5.5 keep the posts about closing,
cut-back days or hours, or reopening (keyword filter as stand-in), and sends
one alert either way, with each page's newest post date. It writes nothing
to the repo. `install_task.ps1` registers it as "Topsail Reporter hours
check", once at `-HoursCheck` (Thu Nov 5, 11:15 AM ET); same log.

**Restaurant news, daily (home PC).** Off-season hours and menus show up on
Facebook first. `local/fb_news.py` runs every evening (8:30 PM ET, Oct 24 to
the last edition) over every place's page, two days back (`--days 14` for
the first run). Every own post it finds goes into a local archive,
`%LOCALAPPDATA%\topsail-reporter\posts\<id>.json`, never committed (post text
can name customers). Opus 5.5 keeps the posts that are news about the place
(hours or days changing, closing for the season, reopening, a temporary
closure, a new or off-season menu) and writes each as one plain sentence,
naming no one, with relative days turned into dates and an `until` date for
a one-time closure. Those go into `reference/fb_news.json` (30 days kept).
The Island Edition shows a place's items from the 21 days before the
edition in its details and under Call first; an hours item also shows on
the place's line without a tap; nothing shows past its `until`. New items
are pushed (same clone, reset, test and retry rules as the specials check)
and sent to the alert channel. If Claude cannot be reached nothing is
published and the posts wait for the next run (`news_seen.json` beside the
archive marks what Claude has judged). Task "Topsail Reporter restaurant
news" via `install_task.ps1` (`-NewsTime`, `-NewsFirst`).

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
- The texts arrive as `.txt` file attachments (Nov 5): the site is fine;
  the Shortcut's Send Message is sending Contents of URL instead of the
  Text from Get Text from Input (`docs/SHORTCUT.md`).
- A feed is down: its line drops out of the text and the page says
  "no reading". Nothing to fix unless it lasts. Every fetch retries twice
  on 429 / 5xx (15 s, then 45 s, or the server's Retry-After up to 60 s).
- Open-Meteo refused (429, as in the 2026-10-16 rehearsal): sunrise and
  sunset are computed locally from NOAA's solar equations (within a minute
  of the USNO almanac for the run) and the page credits them; the hourly
  wind row and the model waves are lost for that morning.
- The NWS stops issuing the surf zone forecast for the season: the beach
  line falls back to model waves; rip risk drops out.
- Deploy failed (red Actions run): the fix is a code fix; run the tests
  locally, push, and the deploy re-runs on push.
- No specials on the island page: check `specials.log` beside the job's
  clone. "Signed in: no" means the Facebook session lapsed: run
  `python local/fb_login.py` on the home PC. A page that moved: fix its
  `facebook` URL in `reference/restaurants.json`. Try one place with
  `python local/fb_specials.py --dry-run --debug --ids <id>`.

## 6. Picking up on another machine

The Reporter runs without any of our machines: the routine writes and
pushes, Actions tests and deploys, the Shortcuts read Pages. A laptop (the
Mac) is only for changing it.

1. `git clone https://github.com/payne2225/topsail-reporter.git`, or
   `git pull --rebase origin main` in an existing clone.
2. Read §0, then the top of `docs/PATCH_NOTES.md`.
3. Python 3.11 (what CI uses) and `pip install pytest`. The paper itself is
   the standard library only. Tests: `python3 -m pytest -q`.
4. A page change: edit `render.py`, run `python3 render.py` (it rebuilds
   every edition into `site/`), open `site/<date>/island/index.html` in a
   browser, then commit `site/` with the change and push to `main`.
5. Stays on the home PC: the `local/` Facebook jobs (Task Scheduler, the
   signed-in profile and the alert webhook under
   `%LOCALAPPDATA%\topsail-reporter`, never copied) and Playwright with them.
