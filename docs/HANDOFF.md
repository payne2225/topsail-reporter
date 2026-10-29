# Topsail Reporter: handoff

Living state. Read this first; update it in the same commit as anything
that changes how the Reporter works.

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
"The numbers" (six tiles, then a tide chart per station with every tide
listed under it), the write-up, the detail cards (wind by the hour and the
marine forecast, water, surf; the island's weather and beach), the week as
day cards, and Sources folded shut. From 1080px wide the write-up runs on
the left and all the numbers ride a sidebar. Every page is one
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
closed for the season) shows only in one "Closed for the season" line; picks sort first, then by Google
rating. Every place shows its whole posted week (Monday first, days with the
same hours run together: "Mon closed · Tue–Sat 11 AM–9 PM · Sun 10 AM–3 PM")
in its tap-open details and under Call first, and the "Closed today" list
names the days each one does open. Refresh hours and ratings by editing the
JSON and its `read` date.

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
