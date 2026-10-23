"""Wait until the live site serves this morning's texts exactly as rendered.

    python check_live.py --date 2026-11-05

Polls both published texts (the fishing one and the Island Edition) every
20 seconds, with a cache-buster, and compares each with its copy under
site/text/ in this checkout. One call waits at most 540 seconds so it fits
in a single tool call.

    LIVE        0   both phones' Shortcuts will get exactly these texts
    NOT YET    12   a text is still old or missing: run it again
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


def live_text(name: str) -> str | None:
    url = f"{config.SITE_BASE}/text/{name}?t={int(time.time())}"
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
    want = {}
    for edition in config.EDITIONS:
        name = config.text_file(args.date, edition)
        with open(os.path.join(HERE, "site", "text", name), encoding="utf-8") as f:
            want[name] = f.read()
    deadline = time.monotonic() + min(args.wait, 540)
    waiting = dict(want)
    got = {}
    while True:
        for name in list(waiting):
            got[name] = live_text(name)
            if got[name] == want[name]:
                del waiting[name]
        if not waiting:
            sizes = ", ".join(f"{n} {len(t)} characters" for n, t in want.items())
            print(f"LIVE: {config.SITE_BASE}/text/ serves this morning's texts ({sizes})")
            return 0
        if time.monotonic() + 20 > deadline:
            break
        time.sleep(20)
    for name in waiting:
        state = "no text there yet" if got.get(name) is None else "an older text"
        print(f"NOT YET: {name}: the live site still serves {state}. Run this again.")
    return 12


if __name__ == "__main__":
    sys.exit(main())
