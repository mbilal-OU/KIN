"""UI contract tests for the KIN campus branding helpers.

These do not test the real browser or authenticate a public deployment.
"""
from kin_theme import CSS, masthead, badge


def test_brand_identity_is_finalized():
    html = masthead("My Life workspace")
    assert "Kinetic Intelligence Network" in html
    assert "Keep It Navigable" not in html


def test_masthead_escapes_untrusted_workspace_text():
    html = masthead("<script>alert('x')</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_campus_experience_styles_present():
    assert ".kin-hero" in CSS
    assert ".kin-journey" in CSS
    assert "prefers-reduced-motion" in CSS


def test_simulation_badge_is_distinct():
    assert "SIMULATED" in badge("SIMULATED", "sim")
