"""The Facebook browser profile the specials check signs in with.

It lives outside the repo (%LOCALAPPDATA%\\topsail-reporter\\fb-profile on
Windows) and only on the home PC. Nothing here prints, copies or commits a
cookie: the profile directory is the only place the session exists.
"""
from __future__ import annotations

import os

STATE = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.local/share"),
                     "topsail-reporter")
PROFILE = os.path.join(STATE, "fb-profile")


def open_context(pw, headless: bool = True):
    """Chromium on the saved profile. The same build signs in (headed) and
    checks (headless), so the saved session opens in both."""
    os.makedirs(PROFILE, exist_ok=True)
    ctx = pw.chromium.launch_persistent_context(
        PROFILE, channel="chromium", headless=headless, locale="en-US",
        timezone_id="America/New_York", viewport={"width": 1280, "height": 1000})
    if headless:
        # Headless Chromium says so in its user agent; read pages as the
        # same browser the profile signed in with.
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        ua = page.evaluate("navigator.userAgent").replace("HeadlessChrome", "Chrome")
        ctx.set_extra_http_headers({"User-Agent": ua})
        ctx.add_init_script("Object.defineProperty(navigator,'userAgent',{get:()=>%r})" % ua)
    return ctx


def signed_in(ctx) -> bool:
    """True when the profile holds a Facebook session (checks only that the
    session cookie exists; never reads its value out)."""
    return any(c["name"] == "c_user" and c["domain"].endswith("facebook.com")
               for c in ctx.cookies("https://www.facebook.com"))
