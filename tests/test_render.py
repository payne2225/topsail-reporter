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
    for name in ("The Bite", "Beach &amp; Weather", "Around the Island", "Sources"):
        assert f"<h2>{name}</h2>" in html


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
