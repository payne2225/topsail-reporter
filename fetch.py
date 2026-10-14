"""Every hard number the Topsail Reporter prints, fetched once a morning.

    python fetch.py --date 2026-10-29          # -> data/2026-10-29.json
    python fetch.py --date 2026-10-29 --raw tests/fixtures   # also keep raw payloads

Sources, all free and keyless:
  - NOAA CO-OPS tide predictions: Hampstead (sound, leads) and Ocean City
    Beach pier (ocean), plus Beaufort water temperature as the sound proxy.
  - NWS Wilmington: the Topsail Beach point forecast, the AMZ250 coastal
    waters forecast, the surf zone forecast's Coastal Pender block (rip
    current risk, surf height, water temperature), and active alerts for the
    beach and the marine zone.
  - NDBC 41110, the Masonboro Inlet buoy: measured waves and water temp.
  - Open-Meteo: sunrise/sunset and hourly wind, and its marine model's wave
    outlook (modelled, and labelled that way on the page).

Every source is guarded on its own: one dead feed nulls that one reading and
records why in `errors`. Nothing here ever substitutes a plausible number
for a missing one; the renderer prints "no reading" instead.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request

import config

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "TopsailReporter/1.0 (+https://github.com/payne2225/topsail-reporter)"
TIMEOUT = 25

COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def compass(deg: float | None) -> str | None:
    if deg is None:
        return None
    return COMPASS[int((float(deg) % 360) / 22.5 + 0.5) % 16]


def _get(url: str, params: dict | None = None, accept: str = "application/json") -> str:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", "replace")


class Fetcher:
    """Network calls, optionally saving each raw payload for test fixtures.

    With `replay_dir` nothing touches the network: each call reads the file
    a `raw_dir` run saved under the same name. That is how the tests run a
    whole morning offline.
    """

    def __init__(self, raw_dir: str | None = None, replay_dir: str | None = None,
                 now_utc: dt.datetime | None = None):
        self.raw_dir = raw_dir
        self.replay_dir = replay_dir
        self.now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
        self.errors: list[str] = []

    def text(self, name: str, url: str, params: dict | None = None,
             accept: str = "application/json") -> str:
        if self.replay_dir:
            with open(os.path.join(self.replay_dir, name), encoding="utf-8") as f:
                return f.read()
        body = _get(url, params, accept)
        if self.raw_dir:
            os.makedirs(self.raw_dir, exist_ok=True)
            with open(os.path.join(self.raw_dir, name), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write(body)
        return body

    def json(self, name: str, url: str, params: dict | None = None,
             accept: str = "application/json") -> dict:
        return json.loads(self.text(name, url, params, accept))

    def safe(self, label: str, fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - one dead feed must not end the run
            self.errors.append(f"{label}: {type(exc).__name__}: {str(exc)[:200]}")
            return None


# ------------------------------------------------------------------ tides

def pick_tide_cycle(events: list[dict], day: dt.date) -> list[dict]:
    """The full two-high, two-low cycle centred on `day`, spillover included.

    A lunar day is about 24h50m, so many calendar days hold only three
    events and the missing one is the one a plan needs. Take the four
    consecutive events whose centre sits closest to the day's noon; any
    event outside the day carries its weekday so it cannot be misread.
    """
    if len(events) < 4:
        return [dict(e) for e in events]
    noon = dt.datetime.combine(day, dt.time(12, 0))
    best, best_gap = events[:4], None
    for i in range(len(events) - 3):
        window = events[i:i + 4]
        centre = window[0]["when"] + (window[3]["when"] - window[0]["when"]) / 2
        gap = abs((centre - noon).total_seconds())
        if best_gap is None or gap < best_gap:
            best, best_gap = window, gap
    out = []
    for e in best:
        item = {"type": e["type"], "time": config.clock(e["when"]),
                "height_ft": e["height_ft"]}
        if e["when"].date() != day:
            item["day"] = e["when"].strftime("%a")
        out.append(item)
    return out


def parse_tides(payload: dict, first: dt.date, days: int) -> list[dict]:
    if "error" in payload:
        # CO-OPS answers 200 with an error body: this key is the only guard.
        raise RuntimeError(f"NOAA: {payload['error'].get('message', '').strip()}")
    events = []
    for p in payload.get("predictions", []):
        when = dt.datetime.strptime(p["t"], "%Y-%m-%d %H:%M")
        events.append({"type": "high" if p["type"] == "H" else "low",
                       "when": when, "height_ft": round(float(p["v"]), 1)})
    if not events:
        raise RuntimeError("NOAA: no predictions returned")
    return [{"date": (first + dt.timedelta(days=i)).isoformat(),
             "events": pick_tide_cycle(events, first + dt.timedelta(days=i))}
            for i in range(days)]


def fetch_tides(f: Fetcher, date: dt.date) -> dict:
    begin = (date - dt.timedelta(days=1)).strftime("%Y%m%d")
    end = (date + dt.timedelta(days=config.TIDE_DAYS)).strftime("%Y%m%d")
    out = {}
    for st in config.TIDE_STATIONS:
        def one(st=st):
            payload = f.json(
                f"tides_{st['key']}.json",
                "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
                # datum and interval=hilo are both mandatory: without hilo the
                # API 400s and blames the datum.
                {"product": "predictions", "application": "topsail-reporter",
                 "begin_date": begin, "end_date": end, "datum": "MLLW",
                 "station": st["id"], "time_zone": "lst_ldt", "units": "english",
                 "interval": "hilo", "format": "json"})
            return {"station": st["name"], "id": st["id"], "label": st["label"],
                    "note": st["note"],
                    "days": parse_tides(payload, date, config.TIDE_DAYS)}
        res = f.safe(f"tides:{st['id']}", one)
        if res:
            out[st["key"]] = res
    return out


def parse_coops_temp(payload: dict) -> dict:
    if "error" in payload or not payload.get("data"):
        raise RuntimeError("NOAA: no water temperature returned")
    latest = payload["data"][-1]
    return {"water_temp_f": round(float(latest["v"]), 1), "observed": latest["t"]}


def fetch_sound_temp(f: Fetcher) -> dict | None:
    st = config.SOUND_TEMP_STATION

    def one():
        payload = f.json("sound_temp.json",
                         "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
                         {"product": "water_temperature", "application": "topsail-reporter",
                          "date": "latest", "station": st["id"], "units": "english",
                          "time_zone": "lst_ldt", "format": "json"})
        return {**parse_coops_temp(payload), "station": st["name"],
                "miles": st["miles"], "bearing": st["bearing"]}
    return f.safe("coops-temp", one)


# ------------------------------------------------------------------ moon

def moon_phase(now_utc: dt.datetime) -> dict:
    """Phase and illumination, good to about a day.

    A fishing fact, not decoration: new and full moons bring spring tides
    (bigger swings, harder inlet current); the quarters bring neap tides.
    """
    ref = dt.datetime(2000, 1, 6, 18, 14, tzinfo=dt.timezone.utc)
    synodic = 29.53058867
    age = ((now_utc - ref).total_seconds() / 86400.0) % synodic
    frac = age / synodic
    illum = round((1 - math.cos(2 * math.pi * frac)) / 2 * 100)
    names = [(0.22, "waxing crescent"), (0.28, "first quarter"),
             (0.47, "waxing gibbous"), (0.53, "full moon"),
             (0.72, "waning gibbous"), (0.78, "last quarter"),
             (0.97, "waning crescent"), (1.01, "new moon")]
    name = "new moon" if frac < 0.03 else next(n for cut, n in names if frac <= cut)
    near_new = min(age, synodic - age)
    near_full = abs(age - synodic / 2)
    tides = ("spring tides (bigger swings, stronger inlet current)"
             if min(near_new, near_full) <= 2.5 else
             "neap tides (smaller swings, gentler current)"
             if min(abs(age - synodic / 4), abs(age - 3 * synodic / 4)) <= 2.5 else
             "mid-range tides")
    return {"phase": name, "illumination_pct": illum, "age_days": round(age, 1),
            "tides": tides}


# ------------------------------------------------------------------ NWS

def parse_forecast(payload: dict, limit: int = 14) -> list[dict]:
    out = []
    for p in payload["properties"]["periods"][:limit]:
        out.append({
            "name": p["name"],
            "start": p.get("startTime", "")[:10],
            "is_day": bool(p.get("isDaytime")),
            "temp_f": p.get("temperature"),
            "pop_pct": (p.get("probabilityOfPrecipitation") or {}).get("value"),
            "wind": f"{p.get('windDirection', '')} {p.get('windSpeed', '')}".strip(),
            "short": p.get("shortForecast"),
            "detailed": p.get("detailedForecast"),
        })
    return out


def fetch_forecast(f: Fetcher) -> list[dict] | None:
    office, x, y = config.NWS_GRID
    return f.safe("nws:forecast", lambda: parse_forecast(f.json(
        "forecast.json", f"https://api.weather.gov/gridpoints/{office}/{x},{y}/forecast",
        accept="application/geo+json")))


def marine_headline(text: str) -> str:
    """'SW winds 10 kt. Seas 2 ft.' - the part before the wave detail."""
    head = re.split(r"\s*Wave Detail:", text or "", maxsplit=1)[0].strip()
    return head


def parse_marine(payload: dict, limit: int = 6) -> dict:
    props = payload["properties"]
    periods = [{"name": p["name"], "text": p["detailedForecast"],
                "headline": marine_headline(p["detailedForecast"])}
               for p in props.get("periods", [])[:limit]]
    if not periods:
        raise RuntimeError("NWS: marine forecast has no periods")
    return {"zone": config.MARINE_ZONE, "zone_name": config.MARINE_ZONE_NAME,
            "updated": props.get("updated"), "periods": periods}


def fetch_marine(f: Fetcher) -> dict | None:
    return f.safe("nws:marine", lambda: parse_marine(f.json(
        "marine.json", f"https://api.weather.gov/zones/marine/{config.MARINE_ZONE}/forecast",
        accept="application/geo+json")))


SRF_FIELDS = {
    "rip current risk": "rip_current_risk",
    "surf height": "surf_height",
    "water temperature": "water_temp",
    "uv index": "uv_index",
    "weather": "weather",
    "high temperature": "high",
    "low temperature": "low",
    "winds": "winds",
    "thunderstorm potential": "thunderstorms",
    "waterspout risk": "waterspouts",
    "tides": "tides",
}
WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]


def _srf_issued(text: str) -> dt.date | None:
    m = re.search(r"^\d{3,4} [AP]M E[DS]T \w{3} (\w{3}) (\d{1,2}) (\d{4})$", text, re.M)
    if not m:
        return None
    return dt.datetime.strptime(" ".join(m.groups()), "%b %d %Y").date()


def _srf_period_date(name: str, issued: dt.date) -> tuple[dt.date | None, bool]:
    """(date, is_daytime) for a surf zone period heading."""
    name = name.upper().strip()
    if name in ("TODAY", "REST OF TODAY", "THIS AFTERNOON", "THIS MORNING"):
        return issued, True
    if name in ("TONIGHT", "REST OF TONIGHT", "THIS EVENING", "OVERNIGHT"):
        return issued, False
    night = name.endswith(" NIGHT")
    base = name[:-6] if night else name
    if base in WEEKDAYS:
        delta = (WEEKDAYS.index(base) - issued.weekday()) % 7
        return issued + dt.timedelta(days=delta), not night
    return None, True


def parse_surf_zone(text: str, zone: str = config.LAND_ZONE) -> dict:
    """The zone's block of an NWS surf zone forecast, field by field."""
    start = re.search(rf"^{zone}-", text, re.M)
    if not start:
        raise RuntimeError(f"surf zone forecast has no {zone} block")
    block = text[start.start():]
    # "&&" opens the rip-risk definitions; "$$" ends the zone.
    block = re.split(r"^(?:&&|\$\$)\s*$", block, maxsplit=1, flags=re.M)[0]
    issued = _srf_issued(block) or _srf_issued(text)
    issued_line = re.search(r"^\d{3,4} [AP]M E[DS]T .+$", block, re.M)
    periods, current, last_key = [], None, None
    for raw in block.splitlines():
        line = raw.rstrip()
        head = re.match(r"^\.([A-Z][A-Z ]+?)\.\.\.(.*)$", line)
        if head:
            name = head.group(1).strip()
            if name == "EXTENDED":
                current, last_key = None, None
                continue
            day, is_day = _srf_period_date(name, issued) if issued else (None, True)
            current = {"name": name.title(), "date": day.isoformat() if day else None,
                       "is_day": is_day, "fields": {}}
            periods.append(current)
            rest = head.group(2).strip()
            if rest:
                current["fields"]["summary"] = rest
            last_key = "summary"
            continue
        if current is None or not line.strip():
            continue
        field = re.match(r"^([A-Za-z][A-Za-z /]*?)\**\.{2,}(.*)$", line)
        if field:
            key = SRF_FIELDS.get(field.group(1).strip().lower())
            last_key = key
            if key:
                current["fields"][key] = field.group(2).strip()
        elif last_key and last_key in current["fields"]:
            # Wrapped text: indented (the tide lines) or not (extended days).
            current["fields"][last_key] += " " + line.strip()
    for p in periods:
        fields = p["fields"]
        for k, v in fields.items():
            v = re.sub(r"\.{3,}", ": ", v)
            fields[k] = re.sub(r"\s+", " ", v).strip().rstrip(".")
        # The extended days come as one sentence run; lift the two numbers
        # the report leans on out of it so every period reads the same way.
        summary = fields.get("summary", "")
        rip = re.search(r"\b(Low|Moderate|High) rip current risk", summary, re.I)
        surf = re.search(r"Surf height ([^.]+)", summary, re.I)
        if rip and "rip_current_risk" not in fields:
            fields["rip_current_risk"] = rip.group(1).title()
        if surf and "surf_height" not in fields:
            fields["surf_height"] = surf.group(1).strip()
    if not periods:
        raise RuntimeError(f"surf zone forecast {zone} block has no periods")
    return {"zone": zone, "issued": issued_line.group(0) if issued_line else None,
            "issued_date": issued.isoformat() if issued else None, "periods": periods}


def surf_for(surf: dict | None, date_iso: str) -> dict | None:
    """The daytime surf zone period for `date_iso`, or None."""
    if not surf:
        return None
    for p in surf.get("periods", []):
        if p.get("date") == date_iso and p.get("is_day"):
            return p
    return None


def fetch_surf_zone(f: Fetcher) -> dict | None:
    def one():
        listing = f.json("srf_list.json",
                         f"https://api.weather.gov/products/types/SRF/locations/{config.SURF_OFFICE}",
                         accept="application/ld+json")
        items = listing.get("@graph") or []
        if not items:
            raise RuntimeError("no surf zone forecasts listed (out of season?)")
        latest = items[0]
        issued = dt.datetime.fromisoformat(latest["issuanceTime"].replace("Z", "+00:00"))
        age_h = (f.now_utc - issued).total_seconds() / 3600
        if age_h > 36:
            raise RuntimeError(f"newest surf zone forecast is {age_h:.0f} h old (out of season?)")
        product = f.json("srf.json", latest["@id"], accept="application/ld+json")
        return parse_surf_zone(product["productText"])
    return f.safe("nws:surf-zone", one)


def parse_alerts(payload: dict, where: str) -> list[dict]:
    return [{"event": a["properties"]["event"],
             "headline": a["properties"].get("headline"),
             "ends": a["properties"].get("ends") or a["properties"].get("expires"),
             "where": where}
            for a in payload.get("features", [])]


def fetch_alerts(f: Fetcher) -> list[dict] | None:
    def one():
        land = f.json("alerts_land.json", "https://api.weather.gov/alerts/active",
                      {"point": f"{config.LAT},{config.LON}"}, accept="application/geo+json")
        sea = f.json("alerts_marine.json", "https://api.weather.gov/alerts/active",
                     {"zone": config.MARINE_ZONE}, accept="application/geo+json")
        seen, out = set(), []
        for a in parse_alerts(land, "beach") + parse_alerts(sea, "water"):
            if a["event"] not in seen:
                seen.add(a["event"])
                out.append(a)
        return out
    return f.safe("nws:alerts", one)


# ------------------------------------------------------------------ buoy

def parse_ndbc(text: str) -> dict:
    """Newest row of an NDBC realtime2 file with any reading we use."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 3:
        raise RuntimeError("NDBC: empty file")
    cols = lines[0].lstrip("#").split()
    for row in lines[2:]:
        vals = dict(zip(cols, row.split()))

        def num(key):
            v = vals.get(key)
            return None if v in (None, "MM") else float(v)
        wvht, wtmp = num("WVHT"), num("WTMP")
        if wvht is None and wtmp is None:
            continue
        observed = dt.datetime(int(vals["YY"]), int(vals["MM"]), int(vals["DD"]),
                               int(vals["hh"]), int(vals["mm"]), tzinfo=dt.timezone.utc)
        return {"observed_utc": observed.strftime("%Y-%m-%dT%H:%MZ"),
                "observed_et": config.clock(config.eastern(observed)),
                "wave_ft": round(wvht * 3.28084, 1) if wvht is not None else None,
                "period_s": num("DPD"),
                "wave_from": compass(num("MWD")),
                "water_temp_f": round(wtmp * 9 / 5 + 32) if wtmp is not None else None}
    raise RuntimeError("NDBC: no recent row with waves or water temperature")


def fetch_buoy(f: Fetcher) -> dict | None:
    b = config.BUOY

    def one():
        text = f.text("buoy.txt", f"https://www.ndbc.noaa.gov/data/realtime2/{b['id']}.txt",
                      accept="text/plain")
        return {**parse_ndbc(text), "station": b["name"], "id": b["id"],
                "miles": b["miles"], "bearing": b["bearing"]}
    return f.safe("ndbc", one)


# ------------------------------------------------------------------ Open-Meteo

def parse_weather_model(payload: dict, date_iso: str) -> dict:
    daily = payload["daily"]
    sun = []
    for i, day in enumerate(daily["time"]):
        rise = dt.datetime.fromisoformat(daily["sunrise"][i])
        sset = dt.datetime.fromisoformat(daily["sunset"][i])
        sun.append({"date": day, "sunrise": config.clock(rise), "sunset": config.clock(sset)})
    hourly = payload.get("hourly") or {}
    wind = []
    for i, stamp in enumerate(hourly.get("time", [])):
        if not stamp.startswith(date_iso):
            continue
        hour = int(stamp[11:13])
        if hour < 6 or hour > 21 or hour % 3:
            continue
        wind.append({"time": config.clock(dt.time(hour, 0)),
                     "speed_mph": round(hourly["wind_speed_10m"][i]),
                     "gust_mph": round(hourly["wind_gusts_10m"][i]),
                     "from": compass(hourly["wind_direction_10m"][i]),
                     "temp_f": round(hourly["temperature_2m"][i])})
    return {"sun": sun, "wind": wind}


def fetch_weather_model(f: Fetcher, date: dt.date) -> dict | None:
    def one():
        payload = f.json("openmeteo.json", "https://api.open-meteo.com/v1/forecast", {
            "latitude": config.LAT, "longitude": config.LON,
            "daily": "sunrise,sunset",
            "hourly": "temperature_2m,wind_speed_10m,wind_gusts_10m,wind_direction_10m",
            "temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
            "timezone": "America/New_York",
            "start_date": date.isoformat(),
            "end_date": (date + dt.timedelta(days=config.TIDE_DAYS - 1)).isoformat()})
        return parse_weather_model(payload, date.isoformat())
    return f.safe("open-meteo", one)


def parse_wave_model(payload: dict) -> list[dict]:
    d = payload["daily"]
    return [{"date": day,
             "max_ft": round(d["wave_height_max"][i], 1) if d["wave_height_max"][i] is not None else None,
             "period_s": round(d["wave_period_max"][i]) if d["wave_period_max"][i] is not None else None,
             "from": compass(d["wave_direction_dominant"][i])}
            for i, day in enumerate(d["time"])]


def fetch_wave_model(f: Fetcher, date: dt.date) -> list[dict] | None:
    lat, lon = config.MARINE_MODEL_POINT
    return f.safe("open-meteo-marine", lambda: parse_wave_model(f.json(
        "waves.json", "https://marine-api.open-meteo.com/v1/marine", {
            "latitude": lat, "longitude": lon,
            "daily": "wave_height_max,wave_direction_dominant,wave_period_max",
            "length_unit": "imperial", "timezone": "America/New_York",
            "start_date": date.isoformat(),
            "end_date": (date + dt.timedelta(days=config.TIDE_DAYS - 1)).isoformat()})))


# ------------------------------------------------------------------ main

def build(date_iso: str, raw_dir: str | None = None, now_utc: dt.datetime | None = None,
          replay_dir: str | None = None) -> dict:
    now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
    date = dt.date.fromisoformat(date_iso)
    f = Fetcher(raw_dir, replay_dir, now_utc)
    data = {
        "date": date_iso,
        "kind": config.kind_for(date_iso),
        "generated_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_et": f"{config.clock(config.eastern(now_utc))} ET",
        "tides": fetch_tides(f, date),
        "moon": moon_phase(dt.datetime.combine(date, dt.time(16, 0), dt.timezone.utc)),
        "weather_model": fetch_weather_model(f, date),
        "forecast": fetch_forecast(f),
        "marine": fetch_marine(f),
        "surf_zone": fetch_surf_zone(f),
        "buoy": fetch_buoy(f),
        "sound_temp": fetch_sound_temp(f),
        "waves": fetch_wave_model(f, date),
        "alerts": fetch_alerts(f),
    }
    data["errors"] = f.errors
    return data


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", default=config.eastern().strftime("%Y-%m-%d"))
    parser.add_argument("--out", help="default data/<date>.json")
    parser.add_argument("--raw", help="also save every raw payload into this folder")
    args = parser.parse_args(argv)

    data = build(args.date, args.raw)
    out = args.out or os.path.join(HERE, "data", f"{args.date}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    have = [k for k in ("tides", "weather_model", "forecast", "marine", "surf_zone",
                        "buoy", "sound_temp", "waves") if data.get(k)]
    print(f"OK: wrote {os.path.relpath(out, HERE)} ({len(have)}/8 feeds: "
          f"{', '.join(have)}; {len(data['errors'])} errors)")
    for e in data["errors"]:
        print(f"  ! {e}")
    # No tides at all is the one failure worth a non-zero exit: a fishing
    # report without the tide table is not worth texting.
    return 0 if data["tides"] else 1


if __name__ == "__main__":
    sys.exit(main())
