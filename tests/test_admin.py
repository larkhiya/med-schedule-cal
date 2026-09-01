"""Tests for the admin editor page (preview.render_admin).

The page is generated at build time and edits the live schedule at runtime, so
these check the build-time contract: it is self-contained, its dropdowns are
baked from the JSON schema (so they can't drift from what CI validates), the
repo slug is injected when known, and the core editor wiring is present.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import preview  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "schedule.schema.json").read_text(encoding="utf-8"))
CONFIG = {
    "calendar_name": "Test Calendar",
    "section": "B",
    "section_chooser": True,
    "include_untimed": True,
    "emit_per_subject_feeds": True,
    "term_start": "2026-08-03",
    "term_end": "2026-10-10",
    "timezone": "Asia/Manila",
    "uid_namespace": "x",
}

TOKEN_RE = re.compile(r"__[A-Z][A-Z_]*__")


def test_render_admin_is_self_contained_with_no_unreplaced_tokens():
    doc = preview.render_admin(CONFIG, SCHEMA, repo_slug="owner/repo")
    assert doc.startswith("<!doctype html>")
    assert not TOKEN_RE.search(doc), "left an unreplaced __TEMPLATE__ token"
    # Fully self-contained: no external scripts or stylesheets. The only network
    # endpoint is the GitHub API, called from inline JS at runtime.
    assert "<script src=" not in doc
    assert "stylesheet" not in doc
    assert "https://api.github.com" in doc


def test_render_admin_bakes_schema_enums_for_dropdowns():
    doc = preview.render_admin(CONFIG, SCHEMA, repo_slug="owner/repo")
    for subject in SCHEMA["$defs"]["event"]["properties"]["subject"]["enum"]:
        assert subject in doc
    for activity in SCHEMA["$defs"]["event"]["properties"]["activity"]["enum"]:
        assert activity in doc


def test_render_admin_bakes_repo_and_editable_settings():
    doc = preview.render_admin(CONFIG, SCHEMA, repo_slug="owner/repo")
    assert "owner/repo" in doc
    for key in preview._ADMIN_CONFIG_KEYS:
        assert key in doc
    # commits the two files the build reads, and names the required token scope
    assert "data/schedule.json" in doc
    assert "data/config.local.json" in doc
    assert "Contents: Read and write" in doc
    # core editor controls are wired up
    for marker in ('id="btnPublish"', 'id="tab-events"', 'id="modalCard"'):
        assert marker in doc


def test_render_admin_empty_repo_keeps_local_repo_field():
    doc = preview.render_admin(CONFIG, SCHEMA, repo_slug="")
    assert '"__REPO__"' not in doc  # token was replaced, just with ""
    assert 'id="repoInput"' in doc  # local build still lets you enter owner/repo


def test_admin_config_keys_exclude_dangerous_knobs():
    # uid_namespace must never be web-editable (would orphan subscriptions).
    assert "uid_namespace" not in preview._ADMIN_CONFIG_KEYS
    assert "timezone" not in preview._ADMIN_CONFIG_KEYS
