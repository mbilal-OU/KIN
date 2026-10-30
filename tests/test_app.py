"""End-to-end interface tests driven by Streamlit's own AppTest harness.

These actually execute app.py, so they catch runtime errors that unit tests on
the modules cannot. No network and no model calls happen: the weather panel is
only fetched on a button press, and the AI buttons are not pressed here.
"""
import importlib
import pathlib

import pytest

import kin_store

APP = str(pathlib.Path(__file__).resolve().parent.parent / "app.py")
AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

SCREENS = ["Today", "Planner", "Michigan Weather", "Discover OU",
           "Approvals & History", "Ask the assistant", "Settings & Trust"]


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """Run the real app against an isolated database with no usable API key.

    The placeholder value is set deliberately: app.py calls load_dotenv(), which
    does not override variables that are already present, so this guarantees the
    suite can never spend quota or reach the network.
    """
    monkeypatch.setenv("KIN_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("KIN_AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "replace_with_your_own_key")
    importlib.reload(kin_store)
    harness = AppTest.from_file(APP, default_timeout=30)
    harness.run()
    return harness


def _goto(harness, screen):
    harness.sidebar.radio[0].set_value(screen).run()
    return harness


# ------------------------------------------------------------- it renders
def test_app_starts_without_exception(app):
    assert not app.exception, f"app raised: {app.exception}"


def test_every_screen_renders_without_exception(app):
    for screen in SCREENS:
        _goto(app, screen)
        assert not app.exception, f"{screen} raised: {app.exception}"


def test_first_run_seeds_the_fictional_timetable(app):
    stored = kin_store.list_commitments()
    assert len(stored) == 2
    titles = {c["title"] for c in stored}
    assert titles == {"Study group (fictional)", "Morning exam (fictional)"}
    assert all("fictional" in c["notes"].lower() or "fictional" in c["title"].lower()
               for c in stored)


# --------------------------------------------------- honest AI status (T17)
def test_missing_api_key_is_shown_as_not_configured(app):
    rendered = " ".join(m.value for m in app.sidebar.markdown)
    assert "not configured" in rendered


def test_trust_screen_declares_blocked_integrations(app):
    _goto(app, "Settings & Trust")
    body = " ".join(m.value for m in app.markdown)
    assert "Blocked by authorization" in body
    assert "MySAIL" in body or "Moodle" in body


def test_trust_screen_disclaims_affiliation_and_compliance(app):
    _goto(app, "Settings & Trust")
    body = " ".join(m.value for m in app.markdown)
    assert "no official OU affiliation" in body
    assert "FERPA" in body


# -------------------------------------------------- guest / naming (T19)
def test_blank_assistant_name_falls_back_to_a_neutral_phrase(app):
    """Clearing the name must mean 'no name', not 'inherit the default'."""
    app.sidebar.text_input[0].set_value("").run()
    assert not app.exception
    body = " ".join(s.value for s in app.subheader) + " ".join(b.label for b in app.button)
    assert "your companion" in body
    assert "Navi" not in body
    assert kin_store.list_workspaces()[0]["assistant_alias"] == ""


def test_custom_assistant_name_is_used_and_persisted(app):
    app.sidebar.text_input[0].set_value("Grizz").run()
    assert not app.exception
    assert any("Grizz" in s.value for s in app.subheader)
    assert kin_store.list_workspaces()[0]["assistant_alias"] == "Grizz"


# ------------------------------------------------------ weather honesty
def test_weather_screen_prompts_before_any_fetch(app):
    _goto(app, "Michigan Weather")
    body = " ".join(m.value for m in app.markdown)
    assert "Get weather" in body
    assert "never your address" in body


def test_weather_screen_offers_a_real_cache_bypass(app):
    _goto(app, "Michigan Weather")
    labels = [b.label for b in app.button]
    assert "Get weather" in labels
    assert "Force new fetch" in labels


def test_weather_screen_links_official_pages(app):
    _goto(app, "Michigan Weather")
    assert not app.exception


# ------------------------------------------------ opportunities (T16, T14)
def test_discover_shows_the_official_event_with_provenance(app):
    _goto(app, "Discover OU")
    body = " ".join(m.value for m in app.markdown)
    assert "Volleyball" in body
    assert "official source" in body
    assert "end time estimated" in body
    assert "Verified as of" in body


def test_proposing_an_event_stores_nothing_until_approved(app):
    _goto(app, "Discover OU")
    propose = [b for b in app.button if b.label.startswith("Propose adding")]
    assert propose, "no propose button rendered"
    before = len(kin_store.list_commitments())
    propose[0].click().run()
    assert not app.exception
    assert len(kin_store.list_commitments()) == before, \
        "a proposal must not write to the timetable"


def test_approving_a_proposal_inserts_once_and_verifies(app):
    _goto(app, "Discover OU")
    [b for b in app.button if b.label.startswith("Propose adding")][0].click().run()
    _goto(app, "Approvals & History")
    before = len(kin_store.list_commitments())
    [b for b in app.button if b.label == "Approve and add"][0].click().run()
    assert not app.exception
    stored = kin_store.list_commitments()
    assert len(stored) == before + 1
    added = max(stored, key=lambda c: c["start"] if "Volleyball" in c["title"] else "")
    assert any("Volleyball" in c["title"] for c in stored)
    assert any(a["verified"] for a in kin_store.list_actions())
    assert any(c.get("end_is_estimated") for c in stored if "Volleyball" in c["title"])


def test_rejecting_a_proposal_leaves_the_timetable_untouched(app):
    _goto(app, "Discover OU")
    [b for b in app.button if b.label.startswith("Propose adding")][0].click().run()
    _goto(app, "Approvals & History")
    before = len(kin_store.list_commitments())
    [b for b in app.button if b.label == "Reject"][0].click().run()
    assert not app.exception
    assert len(kin_store.list_commitments()) == before
    assert kin_store.list_actions()[0]["status"] == "REJECTED"


def test_an_already_added_event_cannot_be_proposed_twice(app):
    _goto(app, "Discover OU")
    [b for b in app.button if b.label.startswith("Propose adding")][0].click().run()
    _goto(app, "Approvals & History")
    [b for b in app.button if b.label == "Approve and add"][0].click().run()
    _goto(app, "Discover OU")
    disabled = [b for b in app.button if b.label == "Already in your timetable"]
    assert disabled, "the duplicate guard should replace the propose button"
    assert disabled[0].disabled


# ------------------------------------------------------- planner actions
def test_manual_event_can_be_added_and_deleted(app):
    _goto(app, "Planner")
    before = len(kin_store.list_commitments())
    submit = [b for b in app.button if b.label == "Add to timetable"]
    assert submit, "the manual entry form did not render"
    submit[0].click().run()
    assert not app.exception
    assert len(kin_store.list_commitments()) == before + 1


def test_planner_exposes_an_ics_download(app):
    _goto(app, "Planner")
    assert not app.exception
    assert any("Download .ics" in b.label for b in app.download_button)


def test_what_if_simulator_changes_nothing_until_applied(app):
    _goto(app, "Planner")
    simulate = [b for b in app.button if b.label == "Simulate"]
    assert simulate
    snapshot = [dict(c) for c in kin_store.list_commitments()]
    simulate[0].click().run()
    assert not app.exception
    assert kin_store.list_commitments() == snapshot


# ------------------------------------------------------------ data rights
def test_user_can_export_everything_kin_stores(app):
    _goto(app, "Settings & Trust")
    assert any("Download everything" in b.label for b in app.download_button)


def test_erase_button_is_disabled_until_confirmed(app):
    _goto(app, "Settings & Trust")
    erase = [b for b in app.button if b.label == "Erase all local KIN data"]
    assert erase
    assert erase[0].disabled, "destructive action must require explicit confirmation"


# ----------------------------------------------------- branding and visuals
def test_masthead_shows_the_full_brand_name(app):
    rendered = " ".join(m.value for m in app.markdown)
    assert "Kinetic Intelligence Network" in rendered
    assert "Keep It Navigable" not in rendered


def test_official_logo_is_rendered_with_accessible_alt_text(app):
    import kin_theme
    if not kin_theme.logo_available():
        pytest.skip("brand assets are not present")
    rendered = " ".join(m.value for m in app.markdown)
    assert "data:image/png;base64," in rendered
    # The brand name must still be announced when the mark is an image.
    assert 'alt="Kinetic Intelligence Network' in rendered


def test_tagline_appears_in_the_brand_lockup(app):
    rendered = " ".join(m.value for m in app.markdown)
    assert "moves with you" in rendered


def test_embedded_logo_is_downscaled_not_shipped_raw():
    """The source artwork is >1 MB; embedding it raw on every rerun is not acceptable."""
    import kin_theme
    if not kin_theme.logo_available():
        pytest.skip("brand assets are not present")
    raw_bytes = kin_theme.LOGO.stat().st_size
    embedded = kin_theme.image_data_uri(str(kin_theme.LOGO), 108)
    assert embedded.startswith("data:image/png;base64,")
    assert len(embedded) < raw_bytes / 4, "logo should be resized before embedding"
    assert len(embedded) < 200_000


def test_brand_helpers_fall_back_cleanly_when_assets_are_missing(tmp_path):
    """A clone without the PNGs must still render a usable masthead."""
    import kin_theme
    missing = str(tmp_path / "nope.png")
    assert kin_theme.image_data_uri(missing, 108) == ""
    original = kin_theme.LOGO
    try:
        kin_theme.LOGO = tmp_path / "nope.png"
        kin_theme.image_data_uri.cache_clear()
        fallback = kin_theme.masthead("subtitle")
        assert "<img" not in fallback
        assert "Kinetic Intelligence Network" in fallback
    finally:
        kin_theme.LOGO = original
        kin_theme.image_data_uri.cache_clear()


def test_sidebar_navigation_covers_every_screen(app):
    options = list(app.sidebar.radio[0].options)
    for screen in SCREENS:
        assert any(screen in option for option in options), f"{screen} missing from nav"


def test_today_renders_a_timeline_with_type_colours(app):
    rendered = " ".join(m.value for m in app.markdown)
    assert "kin-timeline" in rendered
    assert "kin-tl" in rendered
    # The seeded exam should carry its event-type colour on the timeline dot.
    from kin_theme import TYPE_COLORS
    assert TYPE_COLORS["exam"] in rendered


def test_empty_state_is_friendly_in_a_brand_new_workspace(app):
    """A newly created workspace has no commitments, so it must guide the user.

    Deleting every commitment would not test this: the bootstrap deliberately
    reseeds the fictional demo timetable when the whole store is empty.
    """
    from kin_models import make_workspace
    kin_store.add_workspace(make_workspace("Empty Space", "Gaming"))
    app.run()
    app.sidebar.selectbox[0].set_value("Empty Space").run()
    assert not app.exception
    rendered = " ".join(m.value for m in app.markdown)
    assert "kin-empty" in rendered
    assert "Nothing scheduled ahead" in rendered


def test_theme_escapes_user_supplied_text():
    """Titles are rendered as HTML, so they must be escaped."""
    from kin_theme import card, event_row, timeline_item
    nasty = '<img src=x onerror="alert(1)">'
    for rendered in (card(nasty, []), event_row("x", nasty, "m"),
                     timeline_item("9 AM", nasty, "m", "exam")):
        assert "<img" not in rendered
        assert "&lt;img" in rendered


# ------------------------------------- every stored preference is consumed
def test_no_preference_is_stored_without_being_used():
    """Guards against decorative settings: every default must be read somewhere.

    A preference that nothing consumes is a dead feature, which the directive
    forbids. This test fails if someone adds one back.
    """
    import pathlib as _p

    from kin_models import DEFAULT_PREFERENCES
    source = "\n".join(
        (_p.Path(__file__).resolve().parent.parent / name).read_text(encoding="utf-8")
        for name in ("app.py", "kin_ai.py", "kin_core.py", "kin_sources.py"))
    unused = [key for key in DEFAULT_PREFERENCES
              if source.count(f'"{key}"') + source.count(f"'{key}'") < 1]
    assert unused == [], f"stored but never read: {unused}"


def test_preferred_name_appears_in_the_greeting(app):
    kin_store.set_preference("preferred_name", "Jordan")
    app.run()
    assert not app.exception
    assert any("Jordan" in s.value for s in app.subheader)


def test_greeting_omits_the_name_when_blank(app):
    kin_store.set_preference("preferred_name", "")
    app.run()
    heading = " ".join(s.value for s in app.subheader)
    assert "Good day —" in heading


def test_followed_teams_actually_filter_discover(app):
    """Following only a professional team must hide the OU record, not ignore the setting."""
    kin_store.set_preference("favorite_teams", ["Detroit Lions"])
    _goto(app, "Discover OU")
    assert not app.exception
    body = " ".join(m.value for m in app.markdown)
    assert "Volleyball" not in body
    assert "No events match the teams you follow" in body


def test_filter_can_be_overridden_to_show_everything(app):
    kin_store.set_preference("favorite_teams", ["Detroit Lions"])
    _goto(app, "Discover OU")
    app.checkbox[0].set_value(True).run()
    assert not app.exception
    assert "Volleyball" in " ".join(m.value for m in app.markdown)


def test_following_the_grizzlies_shows_the_official_event(app):
    kin_store.set_preference("favorite_teams", ["Oakland Golden Grizzlies"])
    _goto(app, "Discover OU")
    assert "Volleyball" in " ".join(m.value for m in app.markdown)


# ------------------------------------- the full fictional dataset loaded
@pytest.mark.skipif(not __import__("kin_seed").dataset_available(),
                    reason="the fictional dataset file is not present")
class TestWithFullDataset:
    """A whole semester is ~314 commitments. The UI must stay usable."""

    @pytest.fixture()
    def loaded(self, app):
        import kin_seed
        kin_seed.install(kin_store, kin_seed.load_file())
        app.run()
        return app

    def test_every_screen_still_renders(self, loaded):
        for screen in SCREENS:
            _goto(loaded, screen)
            assert not loaded.exception, f"{screen} raised: {loaded.exception}"

    def test_today_limits_the_timeline_to_the_coming_week(self, loaded):
        rendered = " ".join(m.value for m in loaded.markdown)
        assert "Your next seven days" in rendered
        # A term's worth of events must not all be drawn at once.
        assert rendered.count('class="kin-tl ') <= 14

    def test_today_reports_both_a_weekly_and_a_total_count(self, loaded):
        rendered = " ".join(m.value for m in loaded.markdown)
        assert "Next 7 days" in rendered
        assert "Ahead in total" in rendered

    def test_clashes_from_the_dataset_surface_on_today(self, loaded):
        from kin_core import detect_internal_conflicts
        expected = detect_internal_conflicts(kin_store.list_commitments())
        assert expected, "dataset should contain deliberate clashes"
        rendered = " ".join(m.value for m in loaded.markdown)
        assert "Clashes in your timetable" in rendered

    def test_planner_paginates_instead_of_rendering_every_row(self, loaded):
        _goto(loaded, "Planner")
        assert not loaded.exception
        captions = " ".join(c.value for c in loaded.caption)
        assert "commitment(s) in this workspace" in captions
        # At most PAGE rows become editable widgets.
        assert len(loaded.selectbox) < 40

    def test_planner_search_narrows_the_list(self, loaded):
        _goto(loaded, "Planner")
        before = " ".join(c.value for c in loaded.caption)
        loaded.text_input[0].set_value("Midterm").run()
        assert not loaded.exception
        after = " ".join(c.value for c in loaded.caption)
        assert before != after

    def test_profile_name_from_the_dataset_reaches_the_greeting(self, loaded):
        expected = kin_store.get_preferences().get("preferred_name")
        assert expected
        assert any(expected in s.value for s in loaded.subheader)

    def test_dataset_workspaces_are_selectable(self, loaded):
        options = list(loaded.sidebar.selectbox[0].options)
        assert len(options) >= 5


# -------------------------------------------------------- global footer
def test_footer_disclaims_emergency_use_on_every_screen(app):
    for screen in SCREENS:
        _goto(app, screen)
        captions = " ".join(c.value for c in app.caption)
        assert "not an emergency notification system" in captions, screen
