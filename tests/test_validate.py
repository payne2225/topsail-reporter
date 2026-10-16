from __future__ import annotations

import render
import validate
from conftest import GOOD_REPORT


def problems(data, text):
    return validate.check("2026-10-14", data, render.parse_report(text))


def test_a_good_report_passes(data):
    assert problems(data, GOOD_REPORT) == []


def test_an_invented_tide_time_is_caught(data):
    out = problems(data, GOOD_REPORT.replace("after the 11:28 AM high", "after the 11:45 AM high"))
    assert len(out) == 1 and "'11:45 AM' in '## The Bite'" in out[0]


def test_a_bare_time_must_still_be_a_real_one(data):
    assert problems(data, GOOD_REPORT.replace("at 6:37.", "at 6:40.")) != []


def test_the_inlet_tide_from_the_surf_forecast_counts(data):
    assert problems(data, GOOD_REPORT.replace("Low rip risk.", "Low rip risk. Inlet high 10:22 AM.")) == []


def test_event_times_are_free_in_around_the_island(data):
    assert problems(data, GOOD_REPORT.replace("at 5:30 PM", "at 7:45 PM")) == []


def test_the_text_rules(data):
    long = GOOD_REPORT.replace("Bring a jacket", "Bring a jacket " + "really " * 80)
    assert any("Text is" in p for p in problems(data, long))
    link = GOOD_REPORT.replace("The surf is small", "See https://x.example. The surf is small")
    assert any("link" in p for p in problems(data, link))
    dash = GOOD_REPORT.replace("The surf is small and friendly.", "The surf is small — friendly.")
    assert any("em dash" in p for p in problems(data, dash))
    md = GOOD_REPORT.replace("The surf is small", "The **surf** is small")
    assert any("markdown" in p for p in problems(data, md))
    marker = GOOD_REPORT.replace("Sound is the play", "Topsail Reporter: Sound is the play")
    assert any("render.py writes that line" in p for p in problems(data, marker))


def test_structure_rules(data):
    no_bite = GOOD_REPORT.replace("## The Bite\nRed drum", "## The Bight\nRed drum")
    out = problems(data, no_bite)
    assert any("'## The Bite' is missing" in p for p in out)
    assert any("unknown section '## The Bight'" in p for p in out)
    assert any("kind is 'daily'" in p for p in problems(data, GOOD_REPORT.replace("kind: sample", "kind: daily")))
    assert any("date is" in p for p in problems(data, GOOD_REPORT.replace("date: 2026-10-14", "date: 2026-10-15")))
    one_source = GOOD_REPORT.replace("- [Town of Topsail Beach](https://topsailbeachnc.gov/)\n", "")
    assert any("Sources has 1 link" in p for p in problems(data, one_source))
    assert any("placeholder" in p for p in problems(data, GOOD_REPORT.replace("Sunny and warm.", "TODO weather.")))
    long_head = GOOD_REPORT.replace("headline: Flat water", "headline: " + "x" * 90 + " Flat water")
    assert any("headline is" in p for p in problems(data, long_head))


def test_no_report_is_a_problem(data):
    assert validate.check("2026-10-14", data, None) == ["reports/2026-10-14.md does not exist"]


# ---- the Island Edition ----------------------------------------------------

def test_the_island_sections_and_headline_are_required(data):
    out = problems(data, GOOD_REPORT.replace(
        "island_headline: Warm sun, small surf, and a museum worth the walk\n", ""))
    assert out == ["front matter has no island_headline"]
    no_things = GOOD_REPORT.replace("## Things To Do\n", "## Things to see\n")
    out = problems(data, no_things)
    assert any("'## Things To Do' is missing" in p for p in out)


def test_the_island_text_follows_the_text_rules(data):
    dash = GOOD_REPORT.replace("an easy beach day.", "an easy \u2014 beach day.")
    assert any("Island Text has an em dash" in p for p in problems(data, dash))
    long = GOOD_REPORT.replace("an easy beach day.", "an easy beach day " + "really " * 80 + ".")
    assert any("Island Text is" in p for p in problems(data, long))


def test_an_island_time_may_come_from_things_to_do(data):
    # 11:00 AM is no tide or sun time; it is fine because Things To Do sources it.
    assert problems(data, GOOD_REPORT) == []
    unsourced = GOOD_REPORT.replace("opens at 11:00 AM, per its site.", "opens late morning.")
    out = problems(data, unsourced)
    assert len(out) == 1 and "'11:00 AM' in '## Island Text'" in out[0]


def test_an_invented_beach_tide_in_the_island_text_is_caught(data):
    out = problems(data, GOOD_REPORT.replace("the 4:51 PM low tide", "the 4:15 PM low tide"))
    assert len(out) == 1 and "'4:15 PM' in '## Island Text'" in out[0]


def test_a_things_to_do_time_does_not_excuse_the_fishing_text(data):
    out = problems(data, GOOD_REPORT.replace("around the 11:28 AM high", "around the 11:00 AM high"))
    assert len(out) == 1 and "'11:00 AM' in '## Text'" in out[0]
