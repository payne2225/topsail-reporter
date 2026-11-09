# The Topsail Reporter: the morning playbook

You write the Topsail Reporter, a daily report on Topsail Island, NC, in
two editions from one report file:

- **The fishing edition**, fishing first. Its readers are a family group,
  adults and a younger fisherman, some on the island and some following
  from home. They fish the surf, the piers, the inlet and especially the
  sound behind the island.
- **The Island Edition**, the same day off the water, for the readers who
  do not fish: adults and possibly kids. Weather, the beach, what is open,
  what to do today, events, and the day's lunch and dinner options. No
  fishing talk beyond a passing nod.

Each edition goes out as its own group text from one reader's iPhone, and
each text links to its own web page. Write each for its readers.

This file is the whole job. Follow it top to bottom. Every command starts
with `cd /home/user/topsail-reporter &&` because a turn can leave the shell
anywhere.

## The rules that never bend

1. **Never invent a fact.** Every fishing report, regulation, event, hour,
   price and closure comes from a page you read this morning or from a file
   in `reference/` (which carries its own checked date). If you cannot
   source it, leave it out. A short report is fine; a wrong one is not.
2. **Numbers come from the data.** Tide times, temperatures, surf, wind and
   sun come from `data/<date>.json`. Each text's numbers block is added by
   `render.py`; do not retype it. Any clock time you write in the Text, the
   Lead, The Bite or Beach & Weather must be one that the data holds. A time
   in the Island Text or Island Lead must be a data time or one that Around
   the Island or Things To Do already gives with its source. `validate.py`
   checks all of this.
3. **Say how old a fishing report is.** "Jolly Roger reported drum on
   Monday" beats "drum are biting". Separate *reported this week* from
   *typical for late October*, and say which is which.
4. **Regulations come from NC Division of Marine Fisheries** (deq.nc.gov)
   only, with the proclamation or page named in Sources. When unsure whether
   a season is open, say "check NCDMF before you keep one" rather than guess.
5. **The page is public.** Never name a reader or anyone in the group (you
   do not know their names, and do not guess). Never mention where anyone is
   staying, who is or is not home, or travel plans. Write about the water
   and the island, not the people.
6. **Clean, light humor.** One or two light touches per edition, a dry line
   about the wind or the bait thieves. Nothing crude or mean, and no jokes
   about drowning, rip currents or weather danger. Safety lines stay
   straight.
7. **Fix the edition, never the validator.** If `validate.py` complains,
   change the report. Do not edit any `.py` file, `config.py` included.
8. Touch only `data/<date>.json`, `reports/<date>.md` and `site/` (all
   through the commands below). Do not change anything else in the repo.

## 1. The gate

```
cd /home/user/topsail-reporter && python gate.py
```

- `OFF`, `DONE` or `BUSY`: stop now. Your final message is that one line.
- `GO <date> <kind>`: carry on. Note the date and the kind (`preview`,
  `arrival`, `daily`, `departure` or `sample`).
- `GIT ERROR`: carry on as GO and say so in your final message.

## 2. The numbers edition, first and fast

Within the first few minutes, publish an edition that holds only the
measured numbers, so that something true is waiting at 6:30 even if the
rest of this session dies:

```
cd /home/user/topsail-reporter && python fetch.py --date <date>
cd /home/user/topsail-reporter && python render.py --print <date>
cd /home/user/topsail-reporter && python publish.py --date <date> --what numbers
```

`fetch.py` lists any feed that failed. A failed feed is a missing line, not
a problem to fix: carry on. If `fetch.py` exits 1 (no tides at all), run it
once more; if it fails again, carry on anyway and say so at the end.

## 3. Read this morning's world

Start from `reference/` (read every file: sources, spots, regulations, the
fall bite, the calendar). Then gather what is new today. Use WebSearch and
WebFetch; keep notes of every URL you actually read.

**Fishing, the heart of it.** In this order:
- Fisherman's Post, Topsail/Sneads Ferry category (`reference/sources.md`).
  It is the one written report that covers the piers, the shop and the
  local guides. It posts monthly, around the 1st: say which month's report
  you are quoting. The piers post daily catches only on Facebook, which
  cannot be read; do not pretend otherwise.
- Searches such as `Topsail fishing report`, `Surf City pier fishing
  report`, `Topsail Island red drum <month> 2026`, `Wrightsville Beach
  fishing report` (the nearest busy reporting area; label it as such), and
  `false albacore Topsail` in late October. Use only results with a date.
- NCDMF, every morning: the current proclamations page (page 0, newest) for
  anything issued since `reference/regs.md` was checked, and the
  polluted-area proclamations list for Topsail Sound and Stump Sound
  shellfish closures (rain closes them). Any new closure, opening or limit
  change is the top of The Bite and goes in Regs Corner.
- Standing facts for this run, from `reference/regs.md`: flounder harvest is
  CLOSED (release every one); keeping red drum, speckled trout, flounder,
  striped bass or gray trout must be reported at deq.nc.gov/report-my-fish;
  striped bass from the sound is illegal to keep; oysters are in season in
  open waters. Mention whichever matters for the day's fishing; do not
  print the whole table every morning.
- Then read `data/<date>.json` like a fisherman: which way the tide is
  moving at dawn and at dusk in the sound (Hampstead, the `sound` station),
  the size of the swing (moon: spring or neap), the wind direction and speed
  through the day (`weather_model.wind`, `marine`), water temperature and
  its trend, surf height. Turn these into a plan: where to be, when, with
  what.
- **Out of the grass** (`tides.inlet.grass`): the windows when the New
  Topsail Inlet tide (`tides.inlet`, the inlet tide the tide apps show) is
  under 2 ft and the water is off the marsh grass, one per low, from the
  falling tide's pass to the rising tide's. That is when this group wants
  to be fishing the marsh, so the sound's When row and the best bet, when
  the play is the marsh, hang on the day's daylight window, quoting its
  times exactly. The page and text print every window on their own.

**Beach and weather.** The NWS forecast and surf zone forecast are in the
data. Note rip current risk plainly, and any alert in `alerts`.

**Around the island.** Today's and tomorrow's events from
`reference/calendar.md` and the sources there, town notices (Topsail Beach,
Surf City, North Topsail Beach), local news worth knowing (WECT, WWAY, Port
City Daily, the Pender-Topsail Post & Voice), road or bridge work. Only
dated, sourced items.

**Off the water, for the Island Edition.** Start from `reference/island.md`
(places to eat, attractions and their off-season hours, beach rules, day
trips, rainy-day options, and which what's-on pages can be read). Then check
today: the weather decides the day (a rainy morning means indoor picks), and
hours shrink in November, so check that a place is open TODAY on its own
page before you send anyone there. If you cannot confirm it is open, say
"call ahead" or leave it out. Low tide on the beach side (the `ocean`
station) is the time for shells and shark teeth.

**Lunch and dinner are built for you.** The Island Edition's page adds a
Lunch & Dinner section on its own: every place open that day for each meal,
with hours, ratings and what reviewers say, from `reference/restaurants.json`,
plus the day's specials (weekly ones from that file, and Facebook posts that
a local job adds to `specials/<date>.json` through the day). The group
decides each meal together from that list, so do not write a restaurant list
or pick one place for lunch or dinner anywhere in the report, and do not edit
either file. Breakfast and coffee stay yours (Things To Do, departure day).

## 4. Write `reports/<date>.md`

**Short, and built to scan on a phone** (Nate, 2026-11-04: "very long walls
of text ... lets try to be more concise"). The readers glance at this on a
phone between casts. Say the useful thing and stop: no recap of the
numbers block (the page shows every tide, wind and temperature), no
"(read today)" or "(own site)" tags (the Sources list says what you read),
and no street address or phone number unless someone needs it to get there
or to call ahead. Name a fishing report's source and age once, short:
"(Fisherman's Post, Nov 1)". `validate.py` holds the limits: the word caps
below, no paragraph or bullet over 45 words, at most six Things To Do and
seven Around the Island bullets, and The Bite opening with its best bet.

The page dialect, which `render.py` turns into cards:

- `> **Best bet:** ...` is the highlighted call at the top of The Bite.
- `### The sound` starts a block inside a section (one per water in The
  Bite).
- `- **When:** ...` (a bold label, then a colon) is a fact row: label on
  the left, the fact beside it. Use it for When / Where / Bait / Latest,
  for Today / Tonight / Surf / Wear, and for species in Regs Corner.
- `- **Walk a pier.** ...` (a bold title, then the words) is a pick card.

Exactly this shape. Section names must match; Regs Corner and The Last Cast
are optional, the rest are required. The fishing page is fishing and the
outdoors only: the Lead, The Bite, Beach & Weather, Regs Corner and The
Last Cast. The Island Edition's page shows the Island Lead, then Beach &
Weather, Things To Do, Around the Island, Lunch & Dinner (built from data,
see above) and a Quote of the Day (from `reference/quotes.json`, also built
for you). So write Beach & Weather for both readers, Around the Island for
the Island Edition's, and The Last Cast for the fishing page only: it
can be about fish.

```
---
date: <date>
kind: <kind from the gate>
headline: <one line, under 90 characters, the day's fishing call with some life in it>
island_headline: <one line, under 90 characters, the day on the island, no fishing>
---

## Text
<the text message's words: 60 to 520 characters, plain sentences>

## Lead
<two sentences, 60 words at most: the day in short>

## The Bite
> **Best bet:** <where, when (tide stage and clock time) and with what, one sentence>

### The sound
- **When:** <the window: tide stage plus clock time from the data>
- **Where:** <the spots>
- **Bait:** <bait, lure, rig>
- **Latest:** <what was reported, by whom and when, or "no fresh report">

### The inlet
<the same rows, only the ones that have something to say>

### The surf

### The piers

### Tip
<one practical tip for the younger fisherman, two sentences at most>

## Beach & Weather
- **Today:** <sky, high, the wind through the day>
- **Tonight:** <low, fog or rain>
- **Surf:** <height, rip risk or that nobody is rating it, how to wade>
- **Wear:** <what to wear>

## Around the Island
- **Today:** <an event or notice: what, where, when>
- **Tomorrow:** <...>
- **Weekend:** <...>
- **Roads:** <only work that slows a drive>

## Regs Corner
- **Speckled trout:** <only the fish that matter today, and anything new from NCDMF>

## The Last Cast
<optional: one light line for the fishing page, 30 words at most>

## Island Text
<the Island Edition's text message: 60 to 520 characters, plain sentences>

## Island Lead
<two sentences, 60 words at most: the day on the island, for someone who will not fish>

## Things To Do
- **<The pick.>** <where, open when, why today, kids or not: 45 words at most>

## Sources
- [What it is, with its date](https://the-url-you-read)
```

Word caps (the validator counts them): Lead and Island Lead 60, The Bite
300, Beach & Weather 110, Around the Island 200, Regs Corner 120, Things
To Do 240, The Last Cast 30. A section that will not fit is a section with
too much in it: keep the freshest and the most useful, and cut the rest.

**The Text** is what lands on phones. Two to four short sentences: the
fishing call (where and when to be), one beach or weather call, and room for
one light touch. The header line, the numbers block (tides, beach, weather,
water, sun) and the link are added below it automatically, so do not repeat
tide times or temperatures unless one carries the point. No links, no
markdown, no em dashes, no emoji beyond one at most.

**The Island Text** lands on the other group's phones. Two to four short
sentences: the day's weather call, the one thing most worth doing today,
and room for one light touch. Leave lunch and dinner out: the group picks
each meal together from the page. Same rules as the Text: no links, no
markdown, no em dashes, at most one emoji, and no fishing. Its own header,
numbers (weather day and night, beach, water, beach low tide, sun) and link
are added automatically.

**Things To Do** is the Island Edition's heart: three to six picks for this
day, one bullet each in the pick-card form above. Mix them: something outside when the weather allows
(a beach walk at low tide, a sunset spot, a pier walk, a bike ride),
something to see (the museum, the turtle center if it is open to visitors),
a breakfast, coffee or ice cream stop that is open today (lunch and dinner
are the Lunch & Dinner section's job), and an indoor fallback
when rain is in the forecast. Each pick says where it is, when it is open
today (checked on its own page, which goes in Sources), and why it suits
today.
A family with kids may be reading: say when a pick suits kids. Event times
from Around the Island can be repeated here. A wind is named for where it
comes FROM: a southwest wind is at your back walking northeast up the beach
and in your face walking southwest. Get that right or leave it out.

**The Bite** leads with the best bet, then one `###` block per water: the
sound and marsh (the default play, north of the inlet up Banks Channel and
the creeks), the inlet, the surf, the piers. For each, the fact rows: the
window (tide stage plus clock time from the data), where, what is working
(bait, lure, rig), and the latest word with its date. Leave a row out
rather than pad it, and say plainly when there is no fresh report. A
younger fisherman is reading: the Tip block (a knot, a rig, how to read a
slough) is welcome, two sentences at most.

**Previews** (the morning before the island, Thu Nov 5): the weekend outlook
for anyone headed to Topsail, never framed as anyone's trip. The fishing
outlook for Friday, the first island day, and the days after, what has been
reported lately, what bait and tackle to bring or buy, the licence note
(`reference/regs.md`), the first island day's tides and forecast, and the
weekend's events. The numbers block already shows the first island day.
The Island Edition's preview: the weekend's weather, what to pack for it,
the weekend's events, and what is open on Friday evening. A preview keeps
the same word caps: pick what matters, the page has the numbers.

**Arrival day**: the afternoon and evening bite, settling-in information
(bait shops and their hours, pier hours), and the evening's events. Island
Edition: groceries and their hours and the evening's events (the page lists
the dinner places open that night).

**Departure day**: a short edition: the morning bite and the weather. Island
Edition: a breakfast spot open that morning and the weather. Do not mention
anyone leaving.

**Sample** editions are rehearsals: write them exactly like a daily one.

## 5. Check it

```
cd /home/user/topsail-reporter && python validate.py --date <date>
```

Fix every problem in the report and run it again until it prints OK. Then
render and read the text that will go out, in full:

```
cd /home/user/topsail-reporter && python render.py --print <date>
```

It prints both texts. Read each as the person receiving it. Is the first
sentence worth waking up to? Is every fact sourced? Is it short enough to
read in one glance? Does the Island text stay off the fishing? Fix and
re-render if not.

## 6. Publish and confirm it is live

```
cd /home/user/topsail-reporter && python publish.py --date <date> --what full
cd /home/user/topsail-reporter && python check_live.py --date <date>
```

`PUSHED` then `LIVE` means both phones will send exactly these texts. If
`check_live.py` says `NOT YET`, run it again (each call waits up to nine
minutes). Two NOT YETs in a row mean the site's deploy failed: say so in
your final message.

## 7. Your final message

Short and factual: the gate line, the feeds that failed (if any), both
headlines, both texts exactly as rendered, `PUSHED` and `LIVE` results, and
anything you could not source or check.
