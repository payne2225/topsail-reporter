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
    ("2026-11-04", None), ("2026-11-05", "preview"), ("2026-11-06", "preview"),
    ("2026-11-07", "arrival"), ("2026-11-08", "daily"), ("2026-11-13", "daily"),
    ("2026-11-14", "departure"), ("2026-11-15", None), ("2026-10-14", "sample"),
    ("2026-10-29", None), ("2026-10-31", None),       # the old run, moved a week on 2026-10-23
])
def test_every_day_of_the_run_has_its_kind(date, kind):
    assert config.kind_for(date) == kind


# ---- a busy Open-Meteo (the 2026-10-16 rehearsal got 429 twice) ----------

import shutil
import urllib.error

from conftest import FIXTURE_NOW, FIXTURES


def test_the_sun_math_matches_the_almanac_for_the_run():
    # USNO for Topsail Beach, reference/sources.md: every morning of the run.
    almanac = {"2026-10-29": ("7:28 AM", "6:20 PM"), "2026-10-30": ("7:29 AM", "6:19 PM"),
               "2026-10-31": ("7:30 AM", "6:18 PM"), "2026-11-01": ("6:31 AM", "5:17 PM"),
               "2026-11-02": ("6:32 AM", "5:16 PM"), "2026-11-03": ("6:33 AM", "5:15 PM"),
               "2026-11-04": ("6:33 AM", "5:14 PM"), "2026-11-05": ("6:34 AM", "5:13 PM"),
               "2026-11-06": ("6:35 AM", "5:13 PM"), "2026-11-07": ("6:36 AM", "5:12 PM")}
    def minutes(clock: str) -> int:
        t = dt.datetime.strptime(clock, "%I:%M %p")
        return t.hour * 60 + t.minute
    for day, (rise, sset) in almanac.items():
        got = fetch.sun_times(dt.date.fromisoformat(day))
        # Within a minute: USNO and NOAA's equations round a few seconds apart.
        assert abs(minutes(got["sunrise"]) - minutes(rise)) <= 1, day
        assert abs(minutes(got["sunset"]) - minutes(sset)) <= 1, day


def test_a_dead_open_meteo_still_leaves_the_sun(tmp_path):
    replay = tmp_path / "replay"
    shutil.copytree(FIXTURES, replay)
    (replay / "openmeteo.json").unlink()
    data = fetch.build("2026-10-14", now_utc=FIXTURE_NOW, replay_dir=str(replay))
    model = data["weather_model"]
    assert model["sun"][0] == {"date": "2026-10-14", "sunrise": "7:15 AM", "sunset": "6:38 PM"}
    assert model["wind"] == [] and model["sun_source"].startswith("computed")
    assert any(e.startswith("open-meteo:") for e in data["errors"])


def _busy(code, headers=None):
    return urllib.error.HTTPError("https://x.example", code, "busy", headers or {}, None)


def test_a_429_is_retried_then_answered(monkeypatch):
    calls, waits = [], []

    def fake_get(url, params=None, accept=None):
        calls.append(url)
        if len(calls) < 3:
            raise _busy(429, {"Retry-After": "7"} if len(calls) == 1 else {})
        return "ok"
    monkeypatch.setattr(fetch, "_get", fake_get)
    assert fetch._get_patiently("https://x.example", sleep=waits.append) == "ok"
    assert waits == [7, 45]


def test_retries_give_up_and_other_errors_do_not_wait(monkeypatch):
    waits = []
    monkeypatch.setattr(fetch, "_get", lambda *a, **k: (_ for _ in ()).throw(_busy(503)))
    with pytest.raises(urllib.error.HTTPError):
        fetch._get_patiently("https://x.example", sleep=waits.append)
    assert waits == [15, 45]
    waits.clear()
    monkeypatch.setattr(fetch, "_get", lambda *a, **k: (_ for _ in ()).throw(_busy(404)))
    with pytest.raises(urllib.error.HTTPError):
        fetch._get_patiently("https://x.example", sleep=waits.append)
    assert waits == []
