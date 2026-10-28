from __future__ import annotations

import json
import os

import config
import render
from conftest import GOOD_REPORT


def test_the_numbers_text_is_header_numbers_and_link(data):
    text = render.build_text(data, None)
    assert text == (
        "Topsail Reporter, Wed Oct 14\n\n"
        "🌊 Sound tides\n"
        "Low 5:11a · High 11:28a\n"
        "Low 5:58p · High 11:44p\n"
        "☀️ Sunny, high 83°\n"
        "💨 Wind SW 9 mph\n"
        "🏖️ Surf 1-2 ft, rip risk low\n"
        "🌡️ Water 77°\n"
        "⛵ SW winds 10 kt. Seas 2 ft.\n"
        "🌅 Sun up 7:15a, down 6:37p\n"
        "🌒 Waxing crescent moon\n\n"
        "Full report: https://payne2225.github.io/topsail-reporter/2026-10-14/\n")


def test_the_full_text_puts_the_prose_between_header_and_numbers(data):
    report = render.parse_report(GOOD_REPORT)
    text = render.build_text(data, report)
    head, prose, numbers, link = text.strip().split("\n\n")
    assert head == "Topsail Reporter, Wed Oct 14"
    assert prose.startswith("Sound is the play this morning")
    assert numbers.startswith("🌊 Sound tides")
    assert link.startswith("Full report: ")


def test_the_shortcut_marker_opens_every_text(data):
    for report in (None, render.parse_report(GOOD_REPORT)):
        assert render.build_text(data, report).startswith(config.TEXT_MARKER)


def test_a_preview_reads_the_first_island_day(data, monkeypatch):
    monkeypatch.setattr(config, "ARRIVAL_DATE", "2026-10-16")
    data["kind"] = "preview"
    lines = render.numbers_block(data)
    assert lines[0] == "📅 Fri Oct 16 outlook"
    assert lines[1] == "🌊 Sound tides"
    assert "🏖️ Surf 1-3 ft, rip risk low" in lines
    # No measured buoy temperature, marine line or moon for a day that has not come.
    assert not any("77" in line or line.startswith(("⛵", "🌒")) for line in lines)


def test_an_alert_leads_the_numbers(data):
    data["alerts"] = [{"event": "Small Craft Advisory", "headline": "x", "ends": None,
                       "where": "water"}]
    assert render.numbers_block(data)[0] == "⚠️ Small Craft Advisory"


def test_a_missing_feed_drops_its_line_and_never_prints_none(data):
    data["surf_zone"] = None
    data["buoy"] = None
    data["marine"] = None
    lines = render.numbers_block(data)
    assert "🏖️ Waves to 1.6 ft (model)" in lines
    assert not any(line.startswith("⛵") for line in lines)
    html = render.page(data, None, ["2026-10-14"], "2026-10-14")
    assert "None" not in html


def test_the_page_escapes_the_report_and_keeps_its_links(data):
    report = render.parse_report(GOOD_REPORT.replace(
        "Sunny and warm.", "Sunny <script>alert(1)</script> and **warm**."))
    html = render.page(data, report, ["2026-10-14"], "2026-10-14")
    assert "<script>alert" not in html and "&lt;script&gt;" in html
    assert "<strong>warm</strong>" in html
    assert '<a href="https://topsailbeachnc.gov/">Town of Topsail Beach</a>' in html
    assert "Flat water, falling tide" in html
    for name in ("The Bite", "Beach &amp; Weather", "Sources"):
        assert f"<h2>{name}</h2>" in html
    # Fishing and the outdoors only: the island news lives on the Island Edition.
    assert "<h2>Around the Island</h2>" not in html and "Lunch &amp; Dinner" not in html
    island = render.page(data, report, ["2026-10-14"], "2026-10-14", edition="island")
    assert "<h2>Around the Island</h2>" in island and "<h2>Lunch &amp; Dinner</h2>" in island


def test_render_all_writes_each_edition_the_index_and_the_texts(tmp_path, data):
    root = tmp_path
    (root / "data").mkdir()
    (root / "reports").mkdir()
    for date in ("2026-10-14", "2026-10-15"):
        d = dict(data, date=date)
        (root / "data" / f"{date}.json").write_text(json.dumps(d), encoding="utf-8")
    (root / "reports" / "2026-10-14.md").write_text(GOOD_REPORT, encoding="utf-8")
    assert render.render_all(str(root)) == ["2026-10-14", "2026-10-15"]
    site = root / "site"
    assert (site / "2026-10-14" / "index.html").exists()
    assert (site / "text" / "2026-10-15.txt").read_text(encoding="utf-8").startswith(
        "Topsail Reporter, Thu Oct 15")
    index = (site / "index.html").read_text(encoding="utf-8")
    # The newest edition, with archive links that work one level up.
    assert "Thu Oct 15, 2026" in index and "href='./2026-10-14/'" in index
    page14 = (site / "2026-10-14" / "index.html").read_text(encoding="utf-8")
    assert "href='../2026-10-15/'" in page14


def test_samples_leave_the_archive_once_the_run_starts(tmp_path, data):
    (tmp_path / "data").mkdir()
    for date in ("2026-10-14", "2026-10-29"):
        (tmp_path / "data" / f"{date}.json").write_text(json.dumps(dict(data, date=date)),
                                                        encoding="utf-8")
    render.render_all(str(tmp_path))
    index = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert "Thu Oct 29, 2026" in index and "Oct 14" not in index
    # The sample's own page and text are still there for anyone holding the link.
    assert (tmp_path / "site" / "2026-10-14" / "index.html").exists()
    assert render.listed(["2026-10-14"]) == ["2026-10-14"]


def test_the_page_names_no_one(data):
    html = render.page(data, render.parse_report(GOOD_REPORT), ["2026-10-14"], "2026-10-14")
    for word in ("Nate", "payne", "Kirsten"):
        assert word not in html


def test_every_numbers_line_fits_a_phone_screen(data):
    # About 32 characters fit on one line of a text bubble; the marine
    # headline is the NWS's own sentence and may run longer.
    for line in render.numbers_block(data):
        if not line.startswith("⛵"):
            assert len(line) <= 32, line


def test_the_sky_emoji_follows_the_worst_weather_named():
    assert render.sky_emoji("Sunny") == "☀️"
    assert render.sky_emoji("Partly Cloudy") == "⛅"
    assert render.sky_emoji("Chance Showers And Thunderstorms") == "⛈️"
    assert render.sky_emoji("Slight Chance Rain Showers then Mostly Sunny") == "🌧️"


def test_feet_shortens_the_surf_forecast():
    assert render.feet("1 to 2 feet") == "1-2 ft"
    assert render.feet("around 1 foot") == "around 1 ft"


# ---- the Island Edition (Nate, 2026-10-16) ---------------------------------

def test_the_island_text_is_header_numbers_and_its_own_link(data):
    assert render.build_island_text(data, None) == (
        "Topsail Reporter, Island Edition, Wed Oct 14\n\n"
        "\u2600\ufe0f Sunny, high 83\u00b0\n"
        "\U0001f319 Tonight clear, low 66\u00b0\n"
        "\U0001f4a8 Wind SW 9 mph\n"
        "\U0001f3d6\ufe0f Surf 1-2 ft, rip risk low\n"
        "\U0001f321\ufe0f Water 77\u00b0\n"
        "\U0001f41a Beach low tide 3:45a, 4:51p\n"
        "\U0001f305 Sun up 7:15a, down 6:37p\n\n"
        "Full report: https://payne2225.github.io/topsail-reporter/2026-10-14/island/\n")


def test_the_island_text_carries_its_own_prose_and_the_marker(data):
    report = render.parse_report(GOOD_REPORT)
    text = render.build_island_text(data, report)
    head, prose, numbers, link = text.strip().split("\n\n")
    assert head.startswith(config.TEXT_MARKER)
    assert prose.startswith("Sunny and warm with a light breeze")
    assert "Sound is the play" not in text
    assert link.endswith("/2026-10-14/island/")


def test_the_island_numbers_leave_the_fishing_out(data):
    lines = render.island_numbers_block(data)
    for fishing in ("Sound tides", "\u26f5", "moon", "Low 5:11a"):
        assert not any(fishing in line for line in lines), fishing


def test_the_beach_low_tide_skips_another_days_spillover(data):
    for day in data["tides"]["ocean"]["days"]:
        if day["date"] == "2026-10-14":
            day["events"].insert(0, {"type": "low", "time": "11:59 PM", "height_ft": 0.5,
                                     "day": "Tue"})
    assert "\U0001f41a Beach low tide 3:45a, 4:51p" in render.island_numbers_block(data)


def test_an_island_preview_names_the_night_it_means(data, monkeypatch):
    monkeypatch.setattr(config, "ARRIVAL_DATE", "2026-10-16")
    data["kind"] = "preview"
    lines = render.island_numbers_block(data)
    assert lines[0] == "\U0001f4c5 Fri Oct 16 outlook"
    assert any(line.startswith("\U0001f319 Fri night ") for line in lines)
    assert not any("Tonight" in line or "77" in line for line in lines)


def test_every_island_line_fits_a_phone_screen(data):
    for line in render.island_numbers_block(data):
        assert len(line) <= 32, line


def test_the_island_page_has_its_own_sections_and_links_back(data):
    report = render.parse_report(GOOD_REPORT)
    html = render.page(data, report, ["2026-10-14", "2026-10-15"], "2026-10-14",
                       edition="island")
    assert "Warm sun, small surf" in html and "Island Edition" in html
    assert "<h2>Things To Do</h2>" in html and "<h2>The Bite</h2>" not in html
    assert "Regs Corner" not in html and "Sound (Hampstead)" not in html
    assert "href='../../2026-10-14/'" in html                # the fishing edition
    assert "href='../../2026-10-15/island/'" in html         # the island archive
    fishing = render.page(data, report, ["2026-10-14"], "2026-10-14")
    assert "href='../2026-10-14/island/'" in fishing
    for word in ("Nate", "payne", "Kirsten"):
        assert word not in html


def test_render_all_writes_the_island_edition_too(tmp_path, data):
    (tmp_path / "data").mkdir()
    (tmp_path / "reports").mkdir()
    for date in ("2026-10-14", "2026-10-15"):
        (tmp_path / "data" / f"{date}.json").write_text(json.dumps(dict(data, date=date)),
                                                        encoding="utf-8")
    (tmp_path / "reports" / "2026-10-14.md").write_text(GOOD_REPORT, encoding="utf-8")
    render.render_all(str(tmp_path))
    site = tmp_path / "site"
    assert (site / "2026-10-14" / "island" / "index.html").exists()
    text = (site / "text" / "2026-10-14-island.txt").read_text(encoding="utf-8")
    assert text.startswith("Topsail Reporter, Island Edition, Wed Oct 14")
    assert "Sunny and warm with a light breeze" in text
    island_index = (site / "island" / "index.html").read_text(encoding="utf-8")
    assert "Thu Oct 15, 2026" in island_index
    assert "href='../2026-10-14/island/'" in island_index and "href='../2026-10-15/'" in island_index
    index = (site / "index.html").read_text(encoding="utf-8")
    assert "href='./2026-10-14/'" in index and "href='./2026-10-15/island/'" in index


# ---- alerts: when, and which edition --------------------------------------

GALE = {"event": "Gale Warning", "headline": "x", "where": "water",
        "onset": "2026-10-17T14:00:00-04:00", "ends": "2026-10-19T06:00:00-04:00"}
RIP = {"event": "Rip Current Statement", "headline": "y", "where": "beach",
       "onset": "2026-10-14T08:00:00-04:00", "ends": "2026-10-14T20:00:00-04:00"}


def test_an_alert_says_when(data):
    data["alerts"] = [GALE, RIP]
    lines = render.numbers_block(data)
    assert lines[:2] == ["\u26a0\ufe0f Gale Warning from Sat 2:00p",
                         "\u26a0\ufe0f Rip Current Statement until 8:00p"]


def test_the_island_edition_leaves_marine_alerts_out(data):
    data["alerts"] = [GALE, RIP]
    lines = render.island_numbers_block(data)
    assert lines[0] == "\u26a0\ufe0f Rip Current Statement until 8:00p"
    assert not any("Gale" in line for line in lines)
    html = render.page(data, None, ["2026-10-14"], "2026-10-14", edition="island")
    assert "Gale Warning" not in html and "Rip Current Statement" in html
    assert "Gale Warning" in render.page(data, None, ["2026-10-14"], "2026-10-14")


def test_computed_sun_times_are_credited_on_the_page(data):
    data["weather_model"] = {"sun": [{"date": "2026-10-14", "sunrise": "7:15 AM",
                                      "sunset": "6:38 PM"}], "wind": [],
                             "sun_source": "computed (NOAA solar equations)"}
    assert "\U0001f305 Sun up 7:15a, down 6:38p" in render.numbers_block(data)
    html = render.page(data, None, ["2026-10-14"], "2026-10-14")
    assert "Sun times computed (NOAA solar equations)" in html


# ---- the page: tiles, tide charts, outlook, switch --------------------------

def test_a_spillover_tide_lands_on_its_own_day(data):
    data["tides"]["sound"]["days"] = [
        {"date": "2026-10-14", "events": [
            {"type": "high", "time": "6:03 PM", "height_ft": 3.9},
            {"type": "low", "time": "12:25 AM", "height_ft": 0.6, "day": "Thu"}]},
        {"date": "2026-10-15", "events": [
            {"type": "low", "time": "12:25 AM", "height_ft": 0.6}]}]
    # Thursday's 12:25 AM is 24 hours plus 25 minutes after Wednesday's midnight,
    # and the two blocks that both carry it give one tide, not two.
    assert render.tide_timeline(data, "sound", "2026-10-14") == [
        (1083, 3.9, "high", "6:03 PM"), (1465, 0.6, "low", "12:25 AM")]


def test_the_tide_curve_passes_through_every_tide(data):
    tl = render.tide_timeline(data, "sound", "2026-10-14")
    for m, h, *_ in tl:
        assert abs(render.tide_height(tl, m) - h) < 1e-9
    (m0, h0, *_), (m1, h1, *_) = tl[:2]
    assert abs(render.tide_height(tl, (m0 + m1) / 2) - (h0 + h1) / 2) < 1e-9
    assert render.tide_height(tl, m0 - 1) is None   # nothing drawn before the first tide


def test_the_outlook_pairs_each_day_with_its_night(data):
    overnight = dict(data["forecast"][1], name="Overnight", is_day=False)
    data["forecast"].insert(0, overnight)
    days = render.outlook_days(data)
    assert [(d["day"]["name"], d["night"]["name"]) for d in days[:2]] == [
        ("This Afternoon", "Tonight"), ("Thursday", "Thursday Night")]
    assert len(days) <= 7


def test_the_page_leads_with_tiles_charts_and_the_edition_switch(data):
    report = render.parse_report(GOOD_REPORT)
    html = render.page(data, report, ["2026-10-14"], "2026-10-14")
    assert "<ul class=tiles>" in html and html.count("<figure class=tidechart") == 2
    assert "<span aria-current=page>🎣 Fishing</span>" in html
    assert "<script>" in html                          # the chart readout
    assert "<h2>Outlook</h2>" in html and "<b class=dn>Today</b>" in html
    island = render.page(data, report, ["2026-10-14"], "2026-10-14", edition="island")
    assert island.count("<figure class=tidechart") == 1   # the beach side only
    assert "<span aria-current=page>🏝️ Island</span>" in island
    assert ">Low tide</span>" in island and ">Moon</span>" not in island


def test_a_page_with_no_tides_draws_no_chart(data):
    data["tides"] = None
    html = render.page(data, None, ["2026-10-14"], "2026-10-14")
    assert "tidechart" not in html.split("<style>")[0] + html.split("</style>")[1]
    assert "<script>" not in html
    assert html.count("<p class=muted>no reading</p>") == 2   # each station says so


# ---- lunch and dinner ---------------------------------------------------------

def _places(*places):
    return {"read": "2026-10-21", "places": list(places)}


def _place(pid, name, hours, **extra):
    return dict({"id": pid, "name": name, "town": "Surf City", "address": "1 Main St",
                 "phone": "910-555-0100", "website": None, "facebook": None,
                 "style": "Seafood", "status": "open", "pick": False, "hours": hours,
                 "hours_note": None, "google": [4.5, 1000], "tripadvisor": None,
                 "reviews": "Fresh fish.", "order": None}, **extra)


def test_lunch_and_dinner_come_from_the_hours():
    p = _place("x", "X", {"Wed": ["11:00-15:00", "17:00-21:00"], "Thu": ["16:00-21:00"],
                          "Fri": ["07:30-13:45"], "Sat": "?"})
    assert render.meals_open(p, "Wed") == {"lunch", "dinner"}
    assert render.meals_open(p, "Thu") == {"dinner"}          # opens at 4: dinner only
    assert render.meals_open(p, "Fri") == {"lunch"}           # a breakfast-and-lunch deli
    assert render.meals_open(p, "Sat") is None                # unknown: call first
    assert render.meals_open(p, "Mon") == set()               # closed
    assert render.meals_open(dict(p, meals=["dinner"]), "Wed") == {"dinner"}
    assert render.hours_today(p, "Wed") == "11 AM–3 PM, 5 PM–9 PM"


def test_every_place_shows_its_week_and_the_days_it_opens():
    p = _place("x", "X", {"Tue": ["11:00-21:00"], "Wed": ["11:00-21:00"], "Thu": ["11:00-21:00"],
                          "Fri": ["11:00-21:00"], "Sat": ["11:00-21:00"], "Sun": ["10:00-15:00"]})
    assert render.week_hours(p) == "Mon closed · Tue–Sat 11 AM–9 PM · Sun 10 AM–3 PM"
    assert render.open_days(p) == "Tue–Sun"
    every = _place("e", "E", {d: ["11:30-21:00"] for d in render.WEEKDAYS})
    assert render.week_hours(every) == "Every day 11:30 AM–9 PM"
    assert render.open_days(every) == "every day"
    wrap = _place("w", "W", {"Fri": ["17:00-21:00"], "Sat": ["17:00-21:00"],
                             "Sun": ["17:00-20:30"], "Mon": ["17:00-21:00"], "Wed": "?"})
    assert render.open_days(wrap) == "Fri–Mon"               # runs past Sunday
    assert render.week_hours(wrap) == ("Mon 5 PM–9 PM · Tue closed · Wed hours not posted · "
                                       "Thu closed · Fri–Sat 5 PM–9 PM · Sun 5 PM–8:30 PM")
    assert render.open_days(_place("t", "T", {"Tue": ["11:00-14:00"], "Thu": ["11:00-14:00"],
                                              "Fri": ["11:00-14:00"]})) == "Tue, Thu–Fri"
    assert render.week_hours(_place("n", "N", {})) == "" and render.open_days(_place("n", "N", {})) == ""


def test_facebook_news_shows_on_the_place_for_three_weeks_and_never_early(data):
    # 2026-10-14 is a Wednesday.
    news = [dict(key="m", id="a", date="2026-10-12", kind="menu", line="Off-season <menu> is out.",
                 url="https://www.facebook.com/m"),
            dict(key="h", id="a", date="2026-10-10", kind="hours", line="Now open Wed-Sun only.",
                 url="https://www.facebook.com/h"),
            dict(key="late", id="a", date="2026-10-15", kind="hours", line="Closing for the season.", url="u"),
            dict(key="old", id="a", date="2026-09-01", kind="hours", line="Summer hours.", url="u"),
            dict(key="once", id="a", date="2026-10-09", kind="hours", line="Closed Saturday, Oct 10.",
                 until="2026-10-10", url="u")]
    eats = render.eats_section(data, _places(
        _place("a", "Alpha Grill", {"Wed": ["11:00-21:00"]}, news=news),
        _place("d", "Delta Diner", {"Wed": ["11:00-15:00"]}, status="call",
               news=[dict(news[1], id="d")])))
    assert ("<p class=news><b>On Facebook, Oct 12:</b> Off-season &lt;menu&gt; is out. "
            "<a href='https://www.facebook.com/m'>Post</a></p>") in eats
    assert "<span class=sp>Oct 10 on Facebook: Now open Wed-Sun only.</span>" in eats   # hours: no tap needed
    assert "Closing for the season" not in eats                # dated after the edition
    assert "Summer hours" not in eats                          # more than 21 days old
    assert "Closed Saturday, Oct 10" not in eats               # that day has passed
    weekly = [dict(key=f"w{d}", id="j", date=f"2026-10-{d:02d}", kind="hours",
                   line=f"Open Friday to Sunday, 7 to 2 (posted the {d}th).", url="u") for d in (5, 12)]
    one = render.eats_section(data, _places(_place("j", "Jolly Grill", {"Wed": ["11:00-21:00"]}, news=weekly)))
    assert "posted the 12th" in one and "posted the 5th" not in one   # a weekly repost shows once
    assert "<br><span class=news><b>On Facebook, Oct 10:</b> Now open Wed-Sun only." in eats  # Call first


def test_a_place_open_only_for_breakfast_is_not_called_closed_all_day(data):
    eats = render.eats_section(data, _places(
        _place("a", "Alpha Grill", {"Wed": ["11:00-21:00"]}),
        _place("b", "Biscuit Hut", {"Wed": ["06:00-10:30"], "Thu": ["06:00-10:30"]})))
    assert "Biscuit Hut (no lunch or dinner)." in eats


def test_the_section_sorts_picks_first_and_names_the_closed_and_the_unsure(data):
    # 2026-10-14 is a Wednesday.
    eats = render.eats_section(data, _places(
        _place("a", "Alpha Grill", {"Wed": ["11:00-21:00"]}, google=[4.9, 50]),
        _place("b", "Bravo Fish", {"Wed": ["11:00-21:00"]}, google=[4.1, 900], pick=True),
        _place("c", "Charlie Pizza", {"Thu": ["11:00-21:00"]}),
        _place("d", "Delta Diner", {"Wed": ["11:00-15:00"]}, status="call",
               hours_note="Closes for the winter."),
        _place("e", "Echo BBQ", {"Wed": ["11:00-20:00"]}, status="closed"),
        _place("f", "Foxtrot Fry", {"Wed": ["11:00-20:00"]}, status="season", pick=True)))
    assert "<b>Closed for the season:</b> ★ Foxtrot Fry.</p>" in eats
    assert eats.count("Foxtrot Fry") == 1                     # not under Call first, no hours
    assert eats.index("Bravo Fish") < eats.index("Our picks") + 400 < eats.index("Alpha Grill")
    assert "<h3>Our picks</h3>" in eats and "<h3>Also worth trying</h3>" in eats
    assert "<b>Closed today:</b> Charlie Pizza (open Thu)." in eats
    assert ("<b>Call first</b><ul><li><b>Delta Diner</b> <a href='tel:9105550100'>910-555-0100</a>"
            "<br>Closes for the winter.<br>Posted hours: <span class=nw>Mon–Tue closed</span> · "
            "<span class=nw>Wed 11 AM–3 PM</span> · <span class=nw>Thu–Sun closed</span></li></ul>") in eats
    assert ("<p><b>Hours:</b> <span class=nw>Mon–Tue closed</span> · <span class=nw>Wed 11 AM–9 PM</span>"
            " · <span class=nw>Thu–Sun closed</span></p>") in eats
    assert "Echo BBQ" not in eats                             # gone for good
    assert "Google 4.1 <small>(900)</small>" in eats


def test_weekly_and_posted_specials_show_and_posts_are_escaped(data):
    places = _places(_place("s", "SurfDog", {"Wed": ["11:00-21:00"]},
                            weekly={"Wed": "Tacos with a side"}),
                     _place("r", "Riverview", {"Wed": ["11:00-20:30"]}))
    specials = {"date": "2026-10-14", "checked_et": ["10:31 AM"],
                "posts": [{"id": "r", "posted_et": "10:05 AM", "text": "Fried <b>flounder</b> plate",
                           "url": "https://www.facebook.com/x"}]}
    eats = render.eats_section(data, places, specials)
    assert "<b>SurfDog</b> Tacos with a side <small>every Wednesday" in eats
    assert "Today: Tacos with a side" in eats                 # on the place's own line too
    assert "Fried &lt;b&gt;flounder&lt;/b&gt; plate" in eats and "<b>flounder" not in eats
    assert "checked at 10:31 AM" in eats
    # Another day's file is never shown as today's.
    assert "flounder" not in render.eats_section(data, places, dict(specials, date="2026-10-13"))


def test_the_real_restaurant_list_loads_and_every_place_is_well_formed():
    places = render.load_restaurants()["places"]
    assert len(places) >= 30
    for p in places:
        assert p["status"] in ("open", "call", "season", "closed"), p["id"]
        for day, spans in p["hours"].items():
            assert day in render.WEEKDAYS, (p["id"], day)
            assert spans == "?" or all(render._hm(a) < render._hm(b)
                                       for a, b in (s.split("-") for s in spans)), p["id"]
        for day in (p.get("weekly") or {}):
            assert p.get("weekly_source") and day in p["hours"], p["id"]
    assert len({p["id"] for p in places}) == len(places)


def test_a_special_read_off_a_photo_says_so(data):
    places = _places(_place("s", "SurfDog", {"Wed": ["11:00-21:00"]}))
    specials = {"date": "2026-10-14", "checked_et": ["11:15 AM"],
                "posts": [{"id": "s", "posted_et": "10:12 AM", "text": "Ribeye plate $21",
                           "url": "https://www.facebook.com/x", "from_photo": True}]}
    eats = render.eats_section(data, places, specials)
    assert "Ribeye plate $21 <small>read from the photo posted 10:12 AM on <a" in eats
