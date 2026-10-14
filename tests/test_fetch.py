from __future__ import annotations

import datetime as dt
import json
import os
import shutil

import pytest

import config
import fetch
from conftest import FIXTURE_NOW, FIXTURES


def test_a_replayed_morning_has_every_feed_and_no_errors(data):
    for key in ("tides", "weather_model", "forecast", "marine", "surf_zone",
                "buoy", "sound_temp", "waves"):
        assert data[key], key
    assert data["errors"] == []
    assert data["kind"] == "sample"
    assert data["generated_et"] == "2:30 PM ET"


def test_the_sound_station_carries_the_full_cycle(data):
    day = data["tides"]["sound"]["days"][0]
    assert day["date"] == "2026-10-14"
    assert [(e["type"], e["time"]) for e in day["events"]] == [
        ("low", "5:11 AM"), ("high", "11:28 AM"), ("low", "5:58 PM"), ("high", "11:44 PM")]


def test_a_spillover_tide_carries_its_weekday(data):
    day = data["tides"]["sound"]["days"][1]
    assert day["date"] == "2026-10-15"
    assert day["events"][0] == {"type": "high", "time": "11:44 PM", "height_ft": 3.3, "day": "Wed"}
    assert all("day" not in e for e in day["events"][1:])


def test_the_ocean_station_runs_ahead_of_the_sound(data):
    ocean = data["tides"]["ocean"]["days"][0]["events"]
    assert ("high", "10:22 AM") in [(e["type"], e["time"]) for e in ocean]


def test_surf_zone_reads_the_coastal_pender_block():
    with open(os.path.join(FIXTURES, "srf.json"), encoding="utf-8") as f:
        surf = fetch.parse_surf_zone(json.load(f)["productText"])
    first = surf["periods"][0]
    assert first["name"] == "Rest Of Today" and first["date"] == "2026-10-14"
    assert first["fields"]["rip_current_risk"] == "Low"
    assert first["fields"]["surf_height"] == "1 to 2 feet"
    assert first["fields"]["water_temp"] == "In the mid 70s"
    assert first["fields"]["tides"] == "Topsail Inlet: High at 10:22 AM EDT. Low at 04:51 PM EDT"
    names = [(p["name"], p["date"]) for p in surf["periods"]]
    assert names == [("Rest Of Today", "2026-10-14"), ("Thursday", "2026-10-15"),
                     ("Friday", "2026-10-16"), ("Saturday", "2026-10-17"),
                     ("Sunday", "2026-10-18")]
    sunday = surf["periods"][-1]["fields"]
    # The extended days wrap onto unindented lines and carry no field rows.
    assert sunday["rip_current_risk"] == "Moderate"
    assert sunday["surf_height"] == "2 to 3 feet"
    assert sunday["summary"].endswith("Northeast winds around 15 mph")
    # The rip-risk definitions after "&&" are not a period's text.
    assert "life-threatening" not in json.dumps(surf).lower()


def test_surf_for_returns_only_a_daytime_period():
    surf = {"periods": [{"date": "2026-10-14", "is_day": False, "fields": {}},
                        {"date": "2026-10-15", "is_day": True, "fields": {"x": 1}}]}
    assert fetch.surf_for(surf, "2026-10-14") is None
    assert fetch.surf_for(surf, "2026-10-15")["fields"] == {"x": 1}


def test_a_surf_zone_period_named_for_a_weekday_lands_on_the_next_one():
    issued = dt.date(2026, 10, 31)  # a Saturday
    assert fetch._srf_period_date("SUNDAY", issued) == (dt.date(2026, 11, 1), True)
    assert fetch._srf_period_date("SATURDAY NIGHT", issued) == (dt.date(2026, 10, 31), False)
    assert fetch._srf_period_date("TONIGHT", issued) == (issued, False)


def test_a_missing_zone_is_an_error_not_a_guess():
    with pytest.raises(RuntimeError, match="no NCZ106 block"):
        fetch.parse_surf_zone("NCZ108-\nSomewhere else\n$$\n")


def test_the_buoy_reads_feet_and_fahrenheit(data):
    b = data["buoy"]
    assert (b["wave_ft"], b["period_s"], b["wave_from"], b["water_temp_f"]) == (1.6, 7.0, "SE", 77)
    assert b["observed_et"] == "2:00 PM"


def test_the_buoy_skips_rows_with_nothing_we_use():
    text = ("#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP\n"
            "#yr  mo dy hr mn degT m/s  m/s     m   sec   sec degT   hPa  degC  degC\n"
            "2026 11 02 12 00  MM   MM   MM    MM    MM    MM  MM     MM    MM    MM\n"
            "2026 11 02 11 30  MM   MM   MM   1.0     8   4.0  90     MM    MM  18.5\n")
    b = fetch.parse_ndbc(text)
    assert b["observed_utc"] == "2026-11-02T11:30Z"
    assert b["observed_et"] == "6:30 AM"  # EST by then
    assert (b["wave_ft"], b["water_temp_f"], b["wave_from"]) == (3.3, 65, "E")


def test_the_marine_headline_drops_the_wave_detail():
    assert fetch.marine_headline("SW winds 10 kt. Seas 2 ft. Wave Detail: E 2 ft at 7 seconds.") \
        == "SW winds 10 kt. Seas 2 ft."


def test_noaa_error_bodies_raise():
    with pytest.raises(RuntimeError, match="NOAA"):
        fetch.parse_tides({"error": {"message": "No data was found"}}, dt.date(2026, 10, 14), 2)
    with pytest.raises(RuntimeError, match="NOAA"):
        fetch.parse_coops_temp({"error": {"message": "x"}})


def test_one_dead_feed_nulls_only_itself(tmp_path):
    replay = tmp_path / "replay"
    shutil.copytree(FIXTURES, replay)
    os.remove(replay / "buoy.txt")
    data = fetch.build("2026-10-14", now_utc=FIXTURE_NOW, replay_dir=str(replay))
    assert data["buoy"] is None
    assert data["tides"] and data["surf_zone"] and data["marine"]
    assert len(data["errors"]) == 1 and data["errors"][0].startswith("ndbc:")


def test_a_stale_surf_zone_forecast_is_refused():
    later = FIXTURE_NOW + dt.timedelta(hours=40)
    data = fetch.build("2026-10-14", now_utc=later, replay_dir=FIXTURES)
    assert data["surf_zone"] is None
    assert any("surf-zone" in e and "old" in e for e in data["errors"])


def test_moon_marks_spring_tides_near_full_and_new():
    full = fetch.moon_phase(dt.datetime(2026, 10, 26, 4, 0, tzinfo=dt.timezone.utc))
    assert full["phase"] == "full moon" and full["tides"].startswith("spring")
    quarter = fetch.moon_phase(dt.datetime(2026, 11, 1, 20, 0, tzinfo=dt.timezone.utc))
    assert quarter["tides"].startswith("neap")


@pytest.mark.parametrize("utc, offset", [
    (dt.datetime(2026, 11, 1, 5, 59, tzinfo=dt.timezone.utc), -4),
    (dt.datetime(2026, 11, 1, 6, 0, tzinfo=dt.timezone.utc), -5),
    (dt.datetime(2026, 3, 8, 6, 59, tzinfo=dt.timezone.utc), -5),
    (dt.datetime(2026, 3, 8, 7, 0, tzinfo=dt.timezone.utc), -4),
])
def test_eastern_time_follows_the_us_rule(utc, offset):
    assert config.et_offset_hours(utc) == offset


@pytest.mark.parametrize("date, kind", [
    ("2026-10-28", None), ("2026-10-29", "preview"), ("2026-10-30", "preview"),
    ("2026-10-31", "arrival"), ("2026-11-01", "daily"), ("2026-11-06", "daily"),
    ("2026-11-07", "departure"), ("2026-11-08", None), ("2026-10-14", "sample"),
])
def test_every_day_of_the_run_has_its_kind(date, kind):
    assert config.kind_for(date) == kind
