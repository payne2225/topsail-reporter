from __future__ import annotations

import os

import check_live
import config


def _site(tmp_path, monkeypatch):
    texts = tmp_path / "site" / "text"
    texts.mkdir(parents=True)
    for edition in config.EDITIONS:
        (texts / config.text_file("2026-10-29", edition)).write_text(
            f"Topsail Reporter {edition}\n", encoding="utf-8")
    monkeypatch.setattr(check_live, "HERE", str(tmp_path))
    monkeypatch.setattr(check_live.time, "sleep", lambda s: None)


def test_live_needs_both_texts(tmp_path, monkeypatch, capsys):
    _site(tmp_path, monkeypatch)
    served = {"2026-10-29.txt": "Topsail Reporter fishing\n",
              "2026-10-29-island.txt": "Topsail Reporter island\n"}
    monkeypatch.setattr(check_live, "live_text", served.get)
    assert check_live.main(["--date", "2026-10-29", "--wait", "0"]) == 0
    assert "LIVE" in capsys.readouterr().out


def test_an_old_island_text_is_not_yet(tmp_path, monkeypatch, capsys):
    _site(tmp_path, monkeypatch)
    served = {"2026-10-29.txt": "Topsail Reporter fishing\n"}
    monkeypatch.setattr(check_live, "live_text", served.get)
    assert check_live.main(["--date", "2026-10-29", "--wait", "0"]) == 12
    out = capsys.readouterr().out
    assert "NOT YET: 2026-10-29-island.txt" in out and "2026-10-29.txt:" not in out
