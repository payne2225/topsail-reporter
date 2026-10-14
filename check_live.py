"""Wait until the live site serves this morning's text exactly as rendered.

    python check_live.py --date 2026-10-29

Polls the published text every 20 seconds (with a cache-buster) and
compares it with site/text/<date>.txt in this checkout. One call waits at
most 540 seconds so it fits in a single tool call.

    LIVE        0   the phone will get exactly this text
    NOT YET    12   still the old text or no text: run it again
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error
import urllib.request

import config

HERE = os.path.dirname(os.path.abspath(__file__))


def live_text(date_iso: str) -> str | None:
    url = f"{config.SITE_BASE}/text/{date_iso}.txt?t={int(time.time())}"
    req = urllib.request.Request(url, headers={"User-Agent": "TopsailReporter/1.0",
                                               "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", required=True)
    parser.add_argument("--wait", type=int, default=540)
    args = parser.parse_args(argv)
    with open(os.path.join(HERE, "site", "text", f"{args.date}.txt"), encoding="utf-8") as f:
        want = f.read()
    deadline = time.monotonic() + min(args.wait, 540)
    got = None
    while True:
        got = live_text(args.date)
        if got == want:
            print(f"LIVE: {config.SITE_BASE}/text/{args.date}.txt serves this morning's text "
                  f"({len(want)} characters)")
            return 0
        if time.monotonic() + 20 > deadline:
            break
        time.sleep(20)
    state = "no text there yet" if got is None else "an older text"
    print(f"NOT YET: the live site still serves {state}. Run this again.")
    return 12


if __name__ == "__main__":
    sys.exit(main())
