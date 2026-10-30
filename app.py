"""KIN — Kinetic Intelligence Network. Streamlit interface.

This file is presentation and orchestration only. Every factual claim shown to
the user is computed in kin_core (deterministic rules) or retrieved with
provenance by kin_sources. The language model explains; it never decides.
"""
from __future__ import annotations

import json
from datetime import datetime, time, timedelta

import streamlit as st
from dotenv import load_dotenv

import kin_store as store
import kin_theme as theme
from kin_ai import (
    FALLBACK_TAG, answer_question, briefing_fallback, daily_briefing, explain,
    extract_commitment_from_text, provider_status, qa_fallback, safe_fallback,
)
from kin_calendar import export_ics, parse_ics
from kin_core import (
    assess_alerts, assess_opportunities, detect_internal_conflicts, find_free_windows,
    parse_dt, sample_commitments, simulate_change, simulated_alert, validate_event_proposal,
)
from kin_models import (
    ACTION_APPROVED, ACTION_EXECUTING, ACTION_REJECTED, ACTION_VERIFIED,
    COMMITMENT_STATUSES, EVENT_TYPES, MICHIGAN, event_type_meta, make_action,
    make_commitment, make_notification, make_workspace,
)
from kin_sources import (
    CITIES, INTEGRATION_STATUS, OU_SOURCES, get_weather, load_activity_templates,
    load_campus_resources, load_events, weather_matches_location,
)

load_dotenv()

OU_CLOSING = "https://www.oakland.edu/police/emergency-management/campus-closings/"
NWS_DOCS = "https://www.weather.gov/documentation/services-web-api"
DEMO_TODAY = datetime(2026, 10, 30, tzinfo=MICHIGAN)

st.set_page_config(page_title="KIN | Kinetic Intelligence Network", page_icon="\U0001F9ED",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(theme.CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- bootstrap
def _bootstrap() -> None:
    """Ensure the local database, default workspace and demo seed all exist.

    Deliberately NOT cached: it is three cheap SQLite reads, and caching it
    would mean a freshly erased or newly pointed database never gets seeded.
    """
    workspace = store.ensure_default_workspace()
    if not store.list_commitments():
        for seed in sample_commitments():
            record = make_commitment(
                seed["title"], seed["start"], seed["end"],
                event_type=seed["event_type"], requires_travel=seed["requires_travel"],
                workspace_id=workspace["id"], origin="sample", commitment_id=seed["id"],
                notes="Fictional demonstration record created by KIN at first launch.",
            )
            store.save_commitment(record)


_bootstrap()

for key, default in (("pending_action", None), ("weather", None), ("extracted", None),
                     ("extract_provider", ""), ("ics_preview", None), ("sim_result", None),
                     ("briefing", None), ("qa_history", [])):
    st.session_state.setdefault(key, default)


# ----------------------------------------------------------------- helpers
def fmt(iso: str, with_day: bool = True) -> str:
    try:
        moment = parse_dt(iso).astimezone(MICHIGAN)
    except (ValueError, TypeError):
        return "time unknown"
    pattern = "%a %b %d · %I:%M %p" if with_day else "%I:%M %p"
    return moment.strftime(pattern).replace(" 0", " ").lstrip("0")


def span(start: str, end: str) -> str:
    return f"{fmt(start)} – {fmt(end, with_day=False)}"


def prefs() -> dict:
    return store.get_preferences()


def in_quiet_hours(preferences: dict, now: datetime | None = None) -> bool:
    """Quiet hours only change what the interface emphasises.

    KIN has no push or email delivery, so there is nothing to suppress beyond
    the in-app list. Windows that wrap past midnight are handled.
    """
    hour = (now or datetime.now(MICHIGAN)).hour
    start = int(preferences.get("quiet_hours_start", 22)) % 24
    end = int(preferences.get("quiet_hours_end", 7)) % 24
    if start == end:
        return False
    return start <= hour < end if start < end else hour >= start or hour < end


def active_workspace(workspaces: list[dict]) -> dict:
    chosen = st.session_state.get("workspace_id")
    for w in workspaces:
        if w["id"] == chosen:
            return w
    return workspaces[0]


def assistant_name(workspace: dict, preferences: dict) -> str:
    """The effective assistant name for this workspace.

    A NULL workspace alias inherits the default from preferences; an empty
    string is the user's explicit choice to have no name at all, so it must not
    silently fall back to the default.
    """
    alias = workspace.get("assistant_alias")
    if alias is None:
        alias = preferences.get("assistant_alias") or ""
    return alias.strip()


def display_assistant(workspace: dict, preferences: dict) -> str:
    return assistant_name(workspace, preferences) or "your companion"


@st.cache_data(ttl=600, show_spinner=False)
def cached_weather(city: str, lat: float, lon: float, bust: int = 0) -> dict:
    """Cached per city so one location's data can never appear under another.

    `bust` is part of the cache key on purpose: passing a new value forces a
    genuine network fetch instead of replaying the cached response. It must not
    start with an underscore, because Streamlit excludes such parameters from
    the key.
    """
    return get_weather(lat, lon, city)


def record_action(action: dict) -> None:
    store.save_action(action)


def notify(kind: str, title: str, body: str, importance: str = "info",
           related_id: str | None = None) -> None:
    if store.notification_exists(kind, related_id):
        return
    store.save_notification(make_notification(kind, title, body,
                                              importance=importance, related_id=related_id))


def ai_payload(commitments: list[dict], preferences: dict, **extra) -> dict:
    """Minimised evidence for the model (plan: send as little as possible)."""
    if preferences.get("share_schedule_with_ai", True):
        schedule = [{"title": c["title"], "type": c.get("event_type"),
                     "start": c["start"], "end": c["end"],
                     "status": c.get("status", "planned")} for c in commitments[:25]]
    else:
        schedule = [{"redacted": True, "count": len(commitments),
                     "note": "User disabled schedule sharing with the AI provider."}]
    return {"commitments": schedule,
            "planning_buffer_minutes": preferences.get("planning_buffer"),
            "transport_mode": preferences.get("transport_mode"),
            "transport_note": "The student's usual transport. Do NOT estimate travel time "
                              "or road safety from it; it is context only.",
            "official_ou_closing_info": OU_CLOSING, **extra}


def run_model(fn, fallback_fn, *args, **kwargs) -> tuple[str, str, bool]:
    """Call the model; on any failure return a clearly labelled deterministic text."""
    try:
        text, provider = fn(*args, **kwargs)
        return text, provider, True
    except Exception as exc:                                  # noqa: BLE001 - surfaced to user
        return (fallback_fn(*args[:1]) if args else fallback_fn({}),
                f"{FALLBACK_TAG} ({type(exc).__name__})", False)


# Route requests are made in Streamlit callbacks, before widgets instantiate.
# Assigning a radio widget's session-state key after rendering raises an error.
def navigate_to(destination: str) -> None:
    st.session_state["kin_nav_screen"] = destination


# ------------------------------------------------------------------ sidebar
workspaces = store.list_workspaces()
preferences = prefs()

with st.sidebar:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">'
        '<div class="kin-mark" style="width:34px;height:34px;font-size:15px">KIN</div>'
        '<div style="line-height:1.2"><b style="font-size:15px">Kinetic Intelligence Network</b><br>'
        '<span style="font-size:11.5px;color:var(--kin-muted)">Oakland University companion</span>'
        '</div></div>', unsafe_allow_html=True)

    names = [w["name"] for w in workspaces]
    current = active_workspace(workspaces)
    picked = st.selectbox("Workspace", names, index=names.index(current["name"]),
                          help="Separate areas of life. Each can use its own assistant name.")
    workspace = next(w for w in workspaces if w["name"] == picked)
    st.session_state["workspace_id"] = workspace["id"]

    # Compare against what the box was showing, so clearing it is recorded as an
    # explicit "no name" rather than being read as "unchanged".
    shown_alias = assistant_name(workspace, preferences)
    alias_value = st.text_input(
        "Assistant name", value=shown_alias, max_chars=35,
        placeholder="Leave blank for no name",
        help="Guest mode: this is stored locally on this machine only.")
    if alias_value != shown_alias:
        store.update_workspace(workspace["id"], assistant_alias=alias_value)
        workspace["assistant_alias"] = alias_value

    # A stable navigation key lets dashboard actions route to existing screens.
    st.session_state.setdefault("kin_nav_screen", "Today")
    screen = st.radio("Go to", [
        "Today", "Planner", "Michigan Weather", "Discover OU",
        "Approvals & History", "Ask the assistant", "Settings & Trust",
    ], key="kin_nav_screen", label_visibility="collapsed")

    with st.expander("✨ Show me around", expanded=False):
        st.caption("Four quick steps to demonstrate KIN with fictional data.")
        st.markdown("① **Plan** a fictional event with Gemma 4")
        st.markdown("② **Check** Michigan weather and the labeled simulation")
        st.markdown("③ **Discover** an OU event and propose adding it")
        st.markdown("④ **Approve** the local calendar update")
        st.button("Start the tour", key="kin_tour_start", use_container_width=True,
                  on_click=navigate_to, args=("Today",))


    status = provider_status()
    chip = "live" if status["configured"] else "blocked"
    st.markdown(
        theme.badge("AI " + ("ready" if status["configured"] else "not configured"), chip)
        + f'<div style="font-size:11.5px;color:var(--kin-muted);margin-top:2px">'
          f'{status["provider"]} · {status["model"]}</div>', unsafe_allow_html=True)
    st.caption("Guest mode. No OU login. Fictional data only.")

commitments = store.list_commitments(workspace["id"])
companion = display_assistant(workspace, preferences)
st.markdown(theme.masthead(f"{workspace['name']} workspace · guest mode"), unsafe_allow_html=True)


# ======================================================================
# TODAY
# ======================================================================
if screen == "Today":
    greeting = preferences.get("preferred_name", "").strip()
    st.markdown(
        '<section class="kin-hero">'
        '<div class="kin-eyebrow">KIN CAMPUS EDITION · OAKLAND UNIVERSITY-INSPIRED</div>'
        '<h2>Life changes. <span style="color:#E6B967">KIN moves with you.</span></h2>'
        '<p>One day. Connected commitments, verified context, and campus opportunities.</p>'
        '</section>', unsafe_allow_html=True)
    st.markdown(
        '<div class="kin-journey"><strong>🎯 Try the KIN experience</strong>'
        '<small>Follow a guided, fictional student journey. Check a commitment, '
        'explore a simulated weather change, and approve a campus event.</small>'
        '<div class="kin-steps"><span class="kin-step">1 · Plan</span>'
        '<span class="kin-step">2 · Weather</span>'
        '<span class="kin-step">3 · Discover</span>'
        '<span class="kin-step">4 · Approve</span></div></div>',
        unsafe_allow_html=True)
    tour_cols = st.columns(4)
    for col, (label, destination, token) in zip(tour_cols, [
        ("1 · Plan", "Planner", "plan"),
        ("2 · Weather", "Michigan Weather", "weather"),
        ("3 · Discover", "Discover OU", "discover"),
        ("4 · Approve", "Approvals & History", "approve"),
    ]):
        col.button(label, key=f"kin_tour_{token}", use_container_width=True,
                   on_click=navigate_to, args=(destination,))
    st.caption("DEMO DATE · October 30, 2026 · Fictional academic events; current NWS data is fetched separately.")
    st.subheader(f"Good day{', ' + greeting if greeting else ''} — I'm {companion}")
    horizon = DEMO_TODAY
    upcoming = [c for c in commitments
                if c.get("status") not in ("completed", "canceled")
                and parse_dt(c["start"]) >= horizon - timedelta(hours=12)]
    conflicts = detect_internal_conflicts(commitments)
    weather = st.session_state.get("weather")
    impacts: list[dict] = []
    if weather and weather_matches_location(weather, preferences.get("commute_area", "")):
        alerts = list(weather["alerts"])
        if st.session_state.get("demo_sim"):
            alerts.append(simulated_alert())
        impacts = assess_alerts(commitments, alerts, int(preferences.get("planning_buffer", 45)))

    free = find_free_windows(commitments, horizon)
    st.markdown(theme.stat_tiles([
        ("Upcoming", len(upcoming), "accent"),
        ("Timetable clashes", len(conflicts), "danger" if conflicts else ""),
        ("Weather impacts", len(impacts), "danger" if impacts else ""),
        ("Open windows today", len(free), ""),
    ]), unsafe_allow_html=True)

    # Prioritize a clear next action, not only a dashboard of counters.
    if impacts:
        st.warning("**Needs attention:** A weather time-window overlaps a planned commitment. "
                   "Review the source and the SIMULATED label before making decisions.")
        st.button("Review weather impact →", key="kin_next_weather", type="primary",
                  on_click=navigate_to, args=("Michigan Weather",))
    elif conflicts:
        st.info("**Next action:** Your example timetable has overlapping commitments.")
        st.button("Review my timetable →", key="kin_next_planner",
                  on_click=navigate_to, args=("Planner",))
    else:
        st.info("**You're ready to explore.** Check a source-linked campus event "
                "or ask KIN to help organize a new commitment.")
        actions = st.columns(2)
        actions[0].button("Find campus activities →", key="kin_next_discover",
                          use_container_width=True, on_click=navigate_to,
                          args=("Discover OU",))
        actions[1].button("Ask KIN AI →", key="kin_next_ai",
                          use_container_width=True, on_click=navigate_to,
                          args=("Ask the assistant",))

    for c in conflicts:
        notify("conflict", "Schedule overlap", f"{c['a']} overlaps {c['b']}",
               "high", related_id=f"{c['a_id']}:{c['b_id']}")
    for i in impacts:
        notify("weather", ("SIMULATED " if i["is_simulation"] else "") + i["alert"],
               f"Overlaps {i['commitment']}", "high",
               related_id=f"{i['event_id']}:{i['alert']}")

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown("#### Next up")
        if not upcoming:
            st.markdown(theme.note(
                "Nothing scheduled ahead. Add a commitment in <strong>Planner</strong>, "
                "or browse <strong>Discover OU</strong>."), unsafe_allow_html=True)
        for c in sorted(upcoming, key=lambda e: e["start"])[:8]:
            meta = event_type_meta(c.get("event_type"))
            tags = ""
            if c.get("end_is_estimated"):
                tags += theme.badge("end estimated", "estimate")
            if c.get("origin") == "sample":
                tags += theme.badge("fictional sample", "neutral")
            if any(i["event_id"] == c["id"] for i in impacts):
                tags += theme.badge("weather impact", "danger")
            st.markdown(theme.event_row(meta["icon"], c["title"],
                                        f"{meta['label']} · {span(c['start'], c['end'])}",
                                        badges=tags), unsafe_allow_html=True)

        if conflicts:
            st.markdown("#### Clashes in your timetable")
            for c in conflicts:
                st.markdown(theme.card(
                    f"{c['a']} overlaps {c['b']}",
                    ["Both are in your stored timetable at the same time. "
                     "KIN has not changed anything — open <b>Planner</b> to adjust one of them."],
                    variant="is-warn"), unsafe_allow_html=True)

        st.markdown("#### Grounded briefing")
        st.caption("Built from your stored state. Gemma explains; it never invents events.")
        if st.button(f"Ask {companion} for today's briefing", type="primary"):
            payload = ai_payload(
                commitments, preferences,
                upcoming=[{"title": c["title"], "when": span(c["start"], c["end"])}
                          for c in upcoming[:6]],
                internal_conflicts=conflicts, impacts=impacts,
                free_windows=free,
                weather_status=(weather or {}).get("alerts_status", "not requested"),
                simulation_active=bool(st.session_state.get("demo_sim")))
            with st.spinner("Gemma 4 is reading your structured state..."):
                text, provider, ok = run_model(daily_briefing, briefing_fallback, payload)
            st.session_state["briefing"] = (text, provider, ok)
        if st.session_state.get("briefing"):
            text, provider, ok = st.session_state["briefing"]
            (st.success if ok else st.warning)(
                f"AI-generated using {provider}" if ok
                else "Gemma unavailable — showing the deterministic fallback below.")
            st.markdown(text)
            st.caption(provider)

    with right:
        st.markdown("#### Notifications")
        if in_quiet_hours(preferences):
            st.markdown(theme.badge("quiet hours active", "blocked"), unsafe_allow_html=True)
            st.caption("Low-importance notices are collapsed during your quiet hours.")
        notifications = [n for n in store.list_notifications(20) if n["status"] != "dismissed"]
        if in_quiet_hours(preferences):
            notifications = [n for n in notifications if n["importance"] == "high"]
        if not notifications:
            st.markdown(theme.note("Nothing needs your attention right now."),
                        unsafe_allow_html=True)
        for n in notifications[:6]:
            variant = "is-alert" if n["importance"] == "high" else ""
            st.markdown(theme.card(n["title"], [n["body"],
                                                f'<span class="kin-sub">{fmt(n["created_at"])}</span>'],
                                   variant=variant), unsafe_allow_html=True)
            if st.button("Dismiss", key="dis-" + n["id"]):
                store.dismiss_notification(n["id"])
                st.rerun()
        st.markdown(theme.note(
            "In-app notifications only. KIN has <strong>no</strong> push, SMS or email "
            "delivery, so nothing is sent to your phone."), unsafe_allow_html=True)

        st.markdown("#### Official sources")
        st.link_button("OU campus closings", OU_CLOSING, use_container_width=True)
        st.link_button("National Weather Service", "https://www.weather.gov/dtx/",
                       use_container_width=True)
        st.markdown(theme.note(
            "KIN never states that classes are canceled. Only the official OU page can "
            "confirm that."), unsafe_allow_html=True)


# ======================================================================
# PLANNER
# ======================================================================
elif screen == "Planner":
    st.subheader("Academic & life planner")
    st.caption("Everything here is stored locally on this machine. No university system is connected.")

    tab_list, tab_add, tab_ai, tab_ics, tab_sim = st.tabs(
        ["Timetable", "Add manually", "Extract with Gemma 4", "Import / export .ics", "What-if"])

    # ------------------------------------------------------------- list
    with tab_list:
        if not commitments:
            st.markdown(theme.note("This workspace has no commitments yet."),
                        unsafe_allow_html=True)
        type_filter = st.multiselect("Filter by type", list(EVENT_TYPES),
                                     format_func=lambda k: EVENT_TYPES[k]["label"])
        shown = [c for c in commitments if not type_filter
                 or c.get("event_type") in type_filter]
        for c in shown:
            meta = event_type_meta(c.get("event_type"))
            with st.container(border=True):
                cols = st.columns([5, 2, 1.2])
                with cols[0]:
                    tags = theme.badge(c.get("status", "planned").replace("_", " "),
                                       "live" if c.get("status") == "completed" else "neutral")
                    if c.get("end_is_estimated"):
                        tags += theme.badge("end estimated", "estimate")
                    if c.get("origin") == "ics_import":
                        tags += theme.badge("imported", "neutral")
                    st.markdown(theme.event_row(
                        meta["icon"], c["title"],
                        f"{meta['label']} · {span(c['start'], c['end'])}"
                        + (" · travel buffer applies" if c.get("requires_travel") else ""),
                        variant="done" if c.get("status") == "completed" else
                                "canceled" if c.get("status") == "canceled" else "",
                        badges=tags), unsafe_allow_html=True)
                    if c.get("source_url"):
                        st.link_button("Official source", c["source_url"])
                with cols[1]:
                    new_status = st.selectbox(
                        "Status", COMMITMENT_STATUSES,
                        index=COMMITMENT_STATUSES.index(c.get("status", "planned")),
                        key="st-" + c["id"], label_visibility="collapsed")
                    if new_status != c.get("status"):
                        c["status"] = new_status
                        store.save_commitment(c)
                        record_action(dict(make_action(
                            "UPDATE_LOCAL_EVENT", f"Status → {new_status}: {c['title']}",
                            {"id": c["id"]}, "User changed the commitment status."),
                            status=ACTION_VERIFIED, verified=True,
                            result=f"Stored status is now {new_status}."))
                        st.rerun()
                with cols[2]:
                    if st.button("Delete", key="del-" + c["id"]):
                        store.delete_commitment(c["id"])
                        record_action(dict(make_action(
                            "REMOVE_LOCAL_EVENT", f"Deleted: {c['title']}", {"id": c["id"]},
                            "User deleted the commitment."),
                            status=ACTION_VERIFIED, verified=True,
                            result="Removed from the local store."))
                        st.rerun()

    # ------------------------------------------------------------- add
    with tab_add:
        with st.form("manual_event"):
            c1, c2 = st.columns(2)
            title = c1.text_input("Title", "Work shift")
            etype = c2.selectbox("Type", list(EVENT_TYPES),
                                 format_func=lambda k: f"{EVENT_TYPES[k]['icon']} {EVENT_TYPES[k]['label']}",
                                 index=list(EVENT_TYPES).index("work"))
            c3, c4, c5 = st.columns(3)
            day = c3.date_input("Date", value=DEMO_TODAY.date())
            start_t = c4.time_input("Starts", value=time(17, 0))
            end_t = c5.time_input("Ends", value=time(21, 0))
            travel = st.checkbox("Requires travel (applies your planning buffer)",
                                 value=EVENT_TYPES["work"]["travel"])
            notes = st.text_input("Notes (optional)", "")
            if st.form_submit_button("Add to timetable", type="primary"):
                start = datetime.combine(day, start_t, MICHIGAN)
                end = datetime.combine(day, end_t, MICHIGAN)
                if not title.strip():
                    st.error("Enter a title.")
                elif end <= start:
                    st.error("The end time must be after the start time on the same day.")
                elif store.find_duplicate(title, start.isoformat(), workspace["id"]):
                    st.warning("An identical commitment already exists at that time.")
                else:
                    record = make_commitment(title, start.isoformat(), end.isoformat(),
                                             event_type=etype, requires_travel=travel,
                                             workspace_id=workspace["id"], origin="manual",
                                             notes=notes)
                    store.save_commitment(record)
                    record_action(dict(make_action(
                        "ADD_LOCAL_EVENT", f"Added: {title}", {"id": record["id"]},
                        "User entered the commitment manually."),
                        status=ACTION_VERIFIED, verified=True,
                        result="Confirmed present in the local store."))
                    st.success("Added. It is stored locally on this machine only.")
                    st.rerun()

    # -------------------------------------------------------- extraction
    with tab_ai:
        st.caption("Gemma 4 turns free text into a structured proposal. "
                   "KIN validates it and you must approve before anything is stored. "
                   "Use fictional text only — hosted free-tier inputs may be retained by the provider.")
        raw_text = st.text_area(
            "Paste fictional schedule information",
            value="On Friday October 30, 2026, I have a biology study meeting "
                  "from 5:00 PM until 5:45 PM at Oakland University.", height=95)
        if st.button("Extract schedule with Gemma 4", type="primary"):
            try:
                with st.spinner("Gemma 4 is extracting event details..."):
                    proposed, provider = extract_commitment_from_text(raw_text)
                    proposed = validate_event_proposal(proposed, strict_michigan=True)
                st.session_state["extracted"] = proposed
                st.session_state["extract_provider"] = provider
                st.success("Gemma 4 produced a proposal. Review it before adding.")
            except Exception as exc:                          # noqa: BLE001
                st.session_state["extracted"] = None
                st.error(f"Extraction failed ({type(exc).__name__}): {exc}")
                st.caption("Nothing was added to your timetable.")
        if st.session_state.get("extracted"):
            proposal = st.session_state["extracted"]
            meta = event_type_meta(proposal.get("event_type"))
            st.markdown(theme.card(
                proposal["title"],
                [f"{meta['label']} · {span(proposal['start'], proposal['end'])}",
                 f"<span class='kin-sub'>Travel buffer applies: "
                 f"{'yes' if proposal['requires_travel'] else 'no'}</span>"],
                badges=theme.badge("awaiting your approval", "estimate")),
                unsafe_allow_html=True)
            with st.expander("Exact validated JSON"):
                st.json(proposal)
            st.caption("Model: " + st.session_state.get("extract_provider", "unknown"))
            a, b = st.columns(2)
            if a.button("Approve and add", type="primary"):
                if store.find_duplicate(proposal["title"], proposal["start"], workspace["id"]):
                    st.warning("That commitment is already in your timetable.")
                else:
                    record = make_commitment(
                        proposal["title"], proposal["start"], proposal["end"],
                        event_type=proposal.get("event_type"),
                        requires_travel=proposal["requires_travel"],
                        workspace_id=workspace["id"], origin="gemma_extraction",
                        notes="Extracted by Gemma 4 from fictional text, validated by KIN, "
                              "approved by the user.")
                    store.save_commitment(record)
                    verified = store.commitment_exists(record["id"])
                    record_action(dict(make_action(
                        "ADD_LOCAL_EVENT", f"Approved AI extraction: {record['title']}",
                        {"id": record["id"], "model": st.session_state.get("extract_provider")},
                        "Gemma proposed it; KIN validated the times; the user approved."),
                        status=ACTION_VERIFIED if verified else "FAILED", verified=verified,
                        result="Read back from the local store." if verified
                               else "Could not confirm the write."))
                    st.session_state["extracted"] = None
                    st.success("Approved and stored.")
                    st.rerun()
            if b.button("Discard proposal"):
                record_action(dict(make_action(
                    "ADD_LOCAL_EVENT", f"Discarded AI extraction: {proposal['title']}",
                    {}, "User rejected the model's proposal."),
                    status=ACTION_REJECTED, result="Nothing was stored."))
                st.session_state["extracted"] = None
                st.rerun()

    # --------------------------------------------------------------- ics
    with tab_ics:
        st.markdown("**Export** your current workspace as a standard calendar file.")
        st.download_button(
            "Download .ics", export_ics(commitments, f"KIN — {workspace['name']}"),
            file_name=f"kin-{workspace['name'].lower().replace(' ', '-')}.ics",
            mime="text/calendar")
        st.divider()
        st.markdown("**Import** an .ics file. KIN shows a preview and imports nothing "
                    "until you approve it.")
        uploaded = st.file_uploader("Calendar file", type=["ics"])
        import_type = st.selectbox("Import everything as", list(EVENT_TYPES),
                                   format_func=lambda k: EVENT_TYPES[k]["label"],
                                   index=list(EVENT_TYPES).index("class"))
        if uploaded is not None and st.button("Read file and preview"):
            try:
                parsed = parse_ics(uploaded.getvalue().decode("utf-8", errors="replace"),
                                   workspace_id=workspace["id"], event_type=import_type)
                st.session_state["ics_preview"] = parsed
            except Exception as exc:                          # noqa: BLE001
                st.session_state["ics_preview"] = None
                st.error(f"Could not read that file ({type(exc).__name__}): {exc}")
        preview = st.session_state.get("ics_preview")
        if preview:
            st.write(f"**{len(preview['events'])} event(s) ready to import.**")
            if preview["duplicates_removed"]:
                st.caption(f"{preview['duplicates_removed']} duplicate row(s) removed.")
            if preview["recurring_first_occurrence_only"]:
                st.warning(f"{preview['recurring_first_occurrence_only']} recurring event(s): "
                           "only the first occurrence is imported. KIN does not expand "
                           "repeat rules.")
            for skipped in preview["skipped"]:
                st.caption(f"Skipped — {skipped}")
            for event in preview["events"][:12]:
                st.markdown(theme.event_row("\U0001F4C5", event["title"],
                                            span(event["start"], event["end"])),
                            unsafe_allow_html=True)
            if st.button("Approve import", type="primary"):
                added = skipped_dupes = 0
                for event in preview["events"]:
                    if store.find_duplicate(event["title"], event["start"], workspace["id"]):
                        skipped_dupes += 1
                        continue
                    store.save_commitment(event)
                    added += 1
                record_action(dict(make_action(
                    "IMPORT_CALENDAR", f"Imported {added} event(s) from .ics", {},
                    "User approved a calendar file import."),
                    status=ACTION_VERIFIED, verified=True,
                    result=f"{added} stored, {skipped_dupes} duplicate(s) skipped."))
                st.session_state["ics_preview"] = None
                st.success(f"Imported {added} event(s). Skipped {skipped_dupes} duplicate(s).")
                st.rerun()

    # --------------------------------------------------------------- sim
    with tab_sim:
        st.caption("Try a change without applying it. KIN recalculates conflicts on a copy "
                   "of your timetable and shows the difference.")
        if not commitments:
            st.info("Add a commitment first.")
        else:
            labels = {c["id"]: f"{c['title']} — {span(c['start'], c['end'])}" for c in commitments}
            target = st.selectbox("Move which commitment?", list(labels),
                                  format_func=lambda k: labels[k])
            shift = st.slider("Shift by (minutes)", -240, 240, 60, 15)
            if st.button("Simulate", type="primary"):
                st.session_state["sim_result"] = simulate_change(
                    commitments, move_id=target, shift_minutes=shift)
            result = st.session_state.get("sim_result")
            if result:
                a, b = st.columns(2)
                a.metric("Clashes now", len(result["before_conflicts"]))
                b.metric("Clashes after the change", len(result["after_conflicts"]),
                         delta=result["net_change"], delta_color="inverse")
                for c in result["new_conflicts"]:
                    st.markdown(theme.card(f"New clash: {c['a']} vs {c['b']}", [
                        "This overlap would be created by the change."], variant="is-alert"),
                        unsafe_allow_html=True)
                for c in result["resolved_conflicts"]:
                    st.markdown(theme.card(f"Resolved: {c['a']} vs {c['b']}", [
                        "This overlap would disappear."], variant="is-ok"), unsafe_allow_html=True)
                if not result["new_conflicts"] and not result["resolved_conflicts"]:
                    st.info("No change to your clash list. Other real-world effects are not modelled.")
                if st.button("Apply this change to my timetable"):
                    moved = next(c for c in commitments if c["id"] == target)
                    moved["start"] = (parse_dt(moved["start"]) + timedelta(minutes=shift)).isoformat()
                    moved["end"] = (parse_dt(moved["end"]) + timedelta(minutes=shift)).isoformat()
                    store.save_commitment(moved)
                    record_action(dict(make_action(
                        "UPDATE_LOCAL_EVENT", f"Moved {moved['title']} by {shift} min",
                        {"id": target}, "User applied a simulated change."),
                        status=ACTION_VERIFIED, verified=True, result="Stored new times."))
                    st.session_state["sim_result"] = None
                    st.success("Applied.")
                    st.rerun()


# ======================================================================
# MICHIGAN WEATHER
# ======================================================================
elif screen == "Michigan Weather":
    st.subheader("Michigan weather and schedule impact")

    c1, c2 = st.columns([3, 2])
    city = c1.selectbox("Approximate area", list(CITIES),
                        index=list(CITIES).index(preferences.get(
                            "commute_area", list(CITIES)[0]))
                        if preferences.get("commute_area") in CITIES else 0)
    if city != preferences.get("commute_area"):
        store.set_preference("commute_area", city)
    buffer_minutes = c2.slider("Planning buffer before commitments (minutes)", 0, 120,
                               int(preferences.get("planning_buffer", 45)), 5)
    if buffer_minutes != preferences.get("planning_buffer"):
        store.set_preference("planning_buffer", buffer_minutes)

    lat, lon = CITIES[city]
    b1, b2, b3 = st.columns([2, 2, 3])
    if b1.button("Get weather", type="primary"):
        with st.spinner("Contacting the National Weather Service..."):
            st.session_state["weather"] = cached_weather(city, lat, lon)
    if b2.button("Force new fetch"):
        cached_weather.clear()
        with st.spinner("Bypassing the cache and refetching..."):
            st.session_state["weather"] = cached_weather(
                city, lat, lon, bust=int(datetime.now().timestamp()))
    st.session_state["demo_sim"] = b3.toggle(
        "Include a SIMULATED winter warning", value=bool(st.session_state.get("demo_sim")),
        help="Adds a clearly marked fictional warning so the impact engine can be demonstrated.")

    data = st.session_state.get("weather")
    if data is None:
        st.markdown(theme.note(
            "Press <strong>Get weather</strong> to call the public National Weather Service API. "
            "KIN sends only an approximate coordinate — never your address."),
            unsafe_allow_html=True)
    else:
        if not weather_matches_location(data, city):
            st.warning(f"The data below was retrieved for **{data.get('city') or 'another area'}**, "
                       f"not {city}. Press **Get weather** to load this area.")
        retrieved = fmt(data["retrieved_at"])
        st.markdown(
            theme.badge("NWS live data", "live")
            + theme.badge(f"retrieved {retrieved}", "neutral")
            + (theme.badge(f"office {data['office']}", "neutral") if data.get("office") else ""),
            unsafe_allow_html=True)

        for error in data["errors"]:
            st.error(f"{error} This does **not** mean there are no active warnings — "
                     "KIN simply could not reach the source.")

        if data["alerts_status"] == "retrieved":
            count = len(data["alerts"])
            st.markdown(theme.stat_tiles([
                ("Official alerts returned", count, "danger" if count else "accent"),
                ("Forecast periods", len(data["forecast"]), ""),
                ("Buffer applied", f"{buffer_minutes} min", ""),
            ]), unsafe_allow_html=True)
            if count == 0:
                st.markdown(theme.note(
                    "<strong>0 active alerts were returned for this point at retrieval time.</strong> "
                    "That is a data result, not a safety guarantee, and it covers one coordinate "
                    "rather than your whole route."), unsafe_allow_html=True)
        else:
            st.markdown(theme.badge("alerts unavailable", "danger"), unsafe_allow_html=True)

        if data["alerts_status"] == "retrieved" and data["alerts"]:
            st.markdown("#### Official NWS alerts")
            for alert in data["alerts"]:
                st.markdown(theme.card(
                    f"{alert.get('icon', '')} {alert['event']}",
                    [alert.get("headline") or "No headline supplied.",
                     f"<span class='kin-sub'>Severity {alert['severity']} · "
                     f"{alert.get('onset') or alert.get('effective') or '?'} → "
                     f"{alert.get('ends') or alert.get('expires') or '?'}</span>"],
                    variant="is-alert",
                    badges=theme.badge("official NWS", "live")), unsafe_allow_html=True)
                st.link_button("Open the NWS source", alert["source_url"])

        if data["forecast_status"] == "retrieved":
            with st.expander("Hourly forecast (next twelve periods)"):
                for period in data["forecast"]:
                    st.write(f"**{period.get('startTime', '?')[11:16]}** · "
                             f"{period.get('temperature', '?')}°{period.get('temperatureUnit', 'F')} · "
                             f"{period.get('shortForecast', 'No detail')}")

        alerts = list(data["alerts"])
        if st.session_state.get("demo_sim"):
            sim = simulated_alert()
            alerts.append(sim)
            st.markdown("#### Demonstration section")
            st.markdown(theme.simulation_banner(
                "the warning below was generated by KIN to demonstrate the impact engine. "
                "It did not come from the National Weather Service."), unsafe_allow_html=True)
            st.markdown(theme.card(sim["event"], [
                sim["headline"],
                f"<span class='kin-sub'>{sim['onset']} → {sim['ends']}</span>"],
                variant="is-sim", badges=theme.badge("simulated", "sim")), unsafe_allow_html=True)

        impacts = assess_alerts(commitments, alerts, buffer_minutes)
        st.markdown("#### Ripple Engine — time-window impact")
        st.caption("Deterministic overlap between each alert window and your commitment "
                   "window plus travel buffer. Computed in code, not by the model.")
        if impacts:
            for impact in impacts:
                simulated = impact["is_simulation"]
                st.markdown(theme.card(
                    f"{impact['commitment']} · {impact['alert']}",
                    [impact["reason"],
                     f"<span class='kin-sub'>Buffer applied: "
                     f"{impact['buffer_applied_minutes']} min "
                     f"({preferences.get('transport_mode', 'Car').lower()}) · "
                     f"Severity {impact['severity']}</span>",
                     "<b>Possible impact only. No Oakland University cancellation is confirmed.</b>"],
                    variant="is-sim" if simulated else "is-warn",
                    badges=theme.badge("simulated — not NWS", "sim") if simulated
                           else theme.badge("official NWS", "live")), unsafe_allow_html=True)
                if not simulated:
                    st.link_button("NWS alert source", impact["source_url"])
        elif data["alerts_status"] == "retrieved":
            st.markdown(theme.card(
                "No alert overlaps your timetable",
                ["No active alert window overlapped a commitment window plus buffer. "
                 "This is not a guarantee of safe travel conditions."],
                variant="is-ok"), unsafe_allow_html=True)
        else:
            st.markdown(theme.note(
                "Alert status is unavailable, so KIN cannot assess overlaps. "
                "This is <strong>not</strong> the same as having no alerts."),
                unsafe_allow_html=True)

        s1, s2 = st.columns(2)
        s1.link_button("Official OU closing information", OU_CLOSING, use_container_width=True)
        s2.link_button("NWS API documentation", NWS_DOCS, use_container_width=True)
        st.markdown(theme.note(
            "Class status is <strong>unverified</strong>. KIN does not read an authenticated "
            "closure feed and will never tell you a class is canceled."), unsafe_allow_html=True)

        if st.button(f"Ask {companion} to explain this"):
            payload = ai_payload(
                commitments, preferences, commute_area=city,
                weather_retrieved=data["retrieved_at"],
                weather_status={"forecast": data["forecast_status"],
                                "alerts": data["alerts_status"]},
                official_alerts=[{k: a[k] for k in ("event", "severity", "onset", "ends")}
                                 for a in data["alerts"][:5]],
                simulated_alert_included=bool(st.session_state.get("demo_sim")),
                impacts=impacts)
            with st.spinner("Gemma 4 is writing a source-bounded explanation..."):
                text, provider, ok = run_model(explain, safe_fallback, payload)
            (st.success if ok else st.warning)(
                f"AI-generated using {provider}" if ok
                else "Gemma unavailable — the text below is KIN's deterministic fallback.")
            st.markdown(text)
            st.caption(provider)


# ======================================================================
# DISCOVER OU
# ======================================================================
elif screen == "Discover OU":
    st.subheader("Opportunity Radar")
    st.caption("Make room for living. Officially sourced Oakland University events, "
               "plus activity blocks you schedule yourself.")

    opp_buffer = st.slider("Planning buffer around an event (minutes)", 0, 120,
                           int(preferences.get("opportunity_buffer", 30)), 5)
    if opp_buffer != preferences.get("opportunity_buffer"):
        store.set_preference("opportunity_buffer", opp_buffer)

    tab_official, tab_activities, tab_campus = st.tabs(
        ["Official OU events", "Plan your own activity", "Campus directory"])

    with tab_official:
        events = load_events()
        followed = preferences.get("favorite_teams", [])
        show_all = st.checkbox(
            "Show events from teams I do not follow", value=not followed,
            help="Your followed teams are set in Settings & Trust.")
        if followed and not show_all:
            events = [e for e in events if e.get("organizer") in followed]
            hidden = len(load_events()) - len(events)
            if hidden:
                st.caption(f"{hidden} event(s) hidden because you do not follow that organizer.")
        if not events:
            st.markdown(theme.note(
                "No events match the teams you follow. Tick the box above, or change "
                "your followed teams in <strong>Settings &amp; Trust</strong>."),
                unsafe_allow_html=True)
        assessed = assess_opportunities(commitments, events, buffer_minutes=opp_buffer)
        for item in assessed:
            with st.container(border=True):
                tags = theme.badge("official source", "live")
                if item.get("end_is_estimated"):
                    tags += theme.badge("end time estimated", "estimate")
                st.markdown(theme.card(
                    item["title"],
                    [f"{fmt(item['start'])} – {fmt(item['end'], with_day=False)} · {item['venue']}",
                     f"<span class='kin-sub'>{item['notes']}</span>",
                     f"<span class='kin-sub'>Verified as of {item['verified_as_of']} · "
                     f"status {item['status']}</span>"],
                    badges=tags), unsafe_allow_html=True)
                if item["fits"]:
                    st.success(f"Fits your selected sample calendar with a {opp_buffer}-minute "
                               "buffer. Other commitments KIN does not know about may still clash.")
                else:
                    st.warning("Potential conflict with: " + ", ".join(item["conflicts"]))
                a, b = st.columns(2)
                a.link_button("Official OU Athletics source", item["source_url"],
                              use_container_width=True)
                already = store.find_duplicate(item["title"], item["start"], workspace["id"])
                if already:
                    b.button("Already in your timetable", key="in-" + item["id"],
                             disabled=True, use_container_width=True)
                elif b.button("Propose adding to my timetable", key="prop-" + item["id"],
                              use_container_width=True):
                    st.session_state["pending_action"] = make_action(
                        "ADD_LOCAL_EVENT", item["title"],
                        {"event": item, "workspace_id": workspace["id"]},
                        ("No clash with your stored timetable." if item["fits"]
                         else "Clashes with: " + ", ".join(item["conflicts"])))
                    store.save_action(st.session_state["pending_action"])
                    st.info("Proposal created. Open **Approvals & History** to decide. "
                            "Nothing has been stored yet.")

    with tab_activities:
        st.caption("These are blank templates, not scheduled events. KIN does not hold live "
                   "Detroit Lions, Tigers, Pistons or Red Wings fixtures — check the official "
                   "team sites for real times.")
        templates = load_activity_templates()
        chosen = st.selectbox("Activity", templates, format_func=lambda t: t["title"])
        st.markdown(theme.note(chosen["description"]), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        act_day = c1.date_input("Date", value=DEMO_TODAY.date(), key="tpl-date")
        act_start = c2.time_input("Starts", value=time(19, 0), key="tpl-time")
        if st.button("Propose this activity", type="primary"):
            start = datetime.combine(act_day, act_start, MICHIGAN)
            end = start + timedelta(minutes=chosen["default_duration_minutes"])
            candidate = {"id": chosen["id"], "title": chosen["title"],
                         "start": start.isoformat(), "end": end.isoformat(),
                         "venue": "Your choice", "event_type": chosen["event_type"],
                         "requires_travel": chosen["requires_travel"],
                         "source_url": "", "end_is_estimated": False}
            fit = assess_opportunities(commitments, [candidate], buffer_minutes=opp_buffer)[0]
            st.session_state["pending_action"] = make_action(
                "ADD_LOCAL_EVENT", chosen["title"],
                {"event": candidate, "workspace_id": workspace["id"]},
                ("No clash with your stored timetable." if fit["fits"]
                 else "Clashes with: " + ", ".join(fit["conflicts"])))
            store.save_action(st.session_state["pending_action"])
            if fit["fits"]:
                st.success("No clash found. Approve it in **Approvals & History**.")
            else:
                st.warning("Clashes with: " + ", ".join(fit["conflicts"])
                           + ". You can still approve it in **Approvals & History**.")

    with tab_campus:
        resources = load_campus_resources()
        categories = sorted({r["category"] for r in resources})
        pick = st.multiselect("Category", categories, default=categories)
        for r in [x for x in resources if x["category"] in pick]:
            with st.container(border=True):
                st.markdown(theme.card(r["name"], [
                    r["note"], f"<span class='kin-sub'>{r['category']}</span>"],
                    badges=theme.badge("official link", "live")), unsafe_allow_html=True)
                st.link_button("Open official page", r["url"])
        st.markdown(theme.note(
            "KIN links to official pages. It does not store opening hours or live "
            "availability, because it cannot verify them."), unsafe_allow_html=True)


# ======================================================================
# APPROVALS & HISTORY
# ======================================================================
elif screen == "Approvals & History":
    st.subheader("Approval Center")
    st.caption("Nothing changes your timetable until you approve it here.")

    pending = st.session_state.get("pending_action")
    if pending and pending["status"] == "PROPOSED":
        event = pending["payload"]["event"]
        st.markdown(theme.card(
            pending["summary"],
            [f"{fmt(event['start'])} – {fmt(event['end'], with_day=False)}",
             f"<span class='kin-sub'>Venue: {event.get('venue', 'n/a')}</span>",
             f"<b>Why KIN suggested this:</b> {pending['rationale']}"],
            badges=theme.badge("awaiting approval", "estimate")
                   + (theme.badge("end time estimated", "estimate")
                      if event.get("end_is_estimated") else "")),
            unsafe_allow_html=True)
        if event.get("source_url"):
            st.link_button("Check the official source first", event["source_url"])
        st.markdown(theme.note(
            "Approving stores the event in KIN's <strong>local</strong> database on this "
            "machine. No university calendar is written, no ticket is bought, and no "
            "attendance is registered."), unsafe_allow_html=True)

        a, b = st.columns(2)
        if a.button("Approve and add", type="primary", use_container_width=True):
            pending["status"] = ACTION_APPROVED
            duplicate = store.find_duplicate(event["title"], event["start"],
                                             pending["payload"]["workspace_id"])
            if duplicate:
                pending["status"] = ACTION_VERIFIED
                pending["verified"] = True
                pending["result"] = "Already present; no duplicate was created."
                st.info("That event was already in your timetable. Nothing was duplicated.")
            else:
                pending["status"] = ACTION_EXECUTING
                record = make_commitment(
                    event["title"], event["start"], event["end"],
                    event_type=event.get("event_type", "recreation"),
                    requires_travel=event.get("requires_travel", True),
                    workspace_id=pending["payload"]["workspace_id"],
                    origin="opportunity", source_url=event.get("source_url") or None,
                    end_is_estimated=bool(event.get("end_is_estimated")),
                    notes=event.get("notes", ""))
                store.save_commitment(record)
                verified = store.commitment_exists(record["id"])
                pending["status"] = ACTION_VERIFIED if verified else "FAILED"
                pending["verified"] = verified
                pending["result"] = ("Read back from the local store after writing."
                                     if verified else "The write could not be confirmed.")
                (st.success if verified else st.error)(
                    "Added and verified in your local timetable." if verified
                    else "KIN could not confirm the write. Nothing is claimed as saved.")
            store.save_action(pending)
            st.session_state["pending_action"] = None
            st.rerun()
        if b.button("Reject", use_container_width=True):
            pending["status"] = ACTION_REJECTED
            pending["result"] = "User rejected the proposal. The timetable is unchanged."
            store.save_action(pending)
            st.session_state["pending_action"] = None
            st.info("Rejected. Nothing was stored.")
            st.rerun()
    else:
        st.markdown(theme.note("No action is waiting for your approval."),
                    unsafe_allow_html=True)

    st.markdown("#### Action history")
    history = store.list_actions(60)
    if not history:
        st.caption("Nothing has been approved or rejected yet.")
    for action in history:
        kind = {"VERIFIED": "live", "REJECTED": "blocked",
                "FAILED": "danger"}.get(action["status"], "estimate")
        st.markdown(theme.card(
            action["summary"],
            [f"<span class='kin-sub'>{action['type']} · requested {fmt(action['requested_at'])}</span>",
             action.get("result") or "No result recorded."],
            badges=theme.badge(action["status"], kind)
                   + (theme.badge("verified in store", "live") if action.get("verified") else "")),
            unsafe_allow_html=True)


# ======================================================================
# ASK THE ASSISTANT
# ======================================================================
elif screen == "Ask the assistant":
    st.subheader(f"Ask {companion}")
    st.markdown(theme.note(
        "Answers come from your stored timetable and the weather panel only. "
        "KIN cannot see Moodle, MySAIL, email or any university system."),
        unsafe_allow_html=True)

    st.caption("Explore questions grounded in your selected timetable. A model call only happens after Ask.")
    suggested_question = st.selectbox("Suggested question", [
        "Choose a question or write my own",
        "What is my next important commitment?",
        "What conflicts exist in my current timetable?",
        "What should I check before my exam commute?",
        "What information about OU closures is confirmed?",
    ], key="kin_suggested_question")
    question = st.text_input(
        "Your question",
        value="" if suggested_question == "Choose a question or write my own" else suggested_question,
        placeholder="What is on my timetable before the exam?")
    if st.button("Ask", type="primary") and question.strip():
        weather = st.session_state.get("weather")
        context = ai_payload(
            commitments, preferences,
            internal_conflicts=detect_internal_conflicts(commitments),
            weather_summary={
                "city": (weather or {}).get("city"),
                "alerts_status": (weather or {}).get("alerts_status", "not requested"),
                "official_alert_count": len((weather or {}).get("alerts", [])),
                "simulation_active": bool(st.session_state.get("demo_sim")),
            })
        try:
            with st.spinner("Gemma 4 is reading your stored state..."):
                answer, provider = answer_question(question, context)
            ok = True
        except Exception as exc:                              # noqa: BLE001
            answer, provider, ok = (qa_fallback(question),
                                    f"{FALLBACK_TAG} ({type(exc).__name__})", False)
        st.session_state["qa_history"].insert(0, (question, answer, provider, ok))

    for q, a, provider, ok in st.session_state["qa_history"][:6]:
        with st.container(border=True):
            st.markdown(f"**You:** {q}")
            st.markdown(f"**{companion}:** {a}")
            st.markdown(theme.badge(provider, "live" if ok else "blocked"),
                        unsafe_allow_html=True)


# ======================================================================
# SETTINGS & TRUST
# ======================================================================
else:
    st.subheader("Settings, trust and privacy")
    tab_prefs, tab_ws, tab_trust, tab_data = st.tabs(
        ["Preferences", "Workspaces", "Sources & AI status", "Your data"])

    with tab_prefs:
        with st.form("prefs"):
            c1, c2 = st.columns(2)
            preferred = c1.text_input("What should KIN call you?",
                                      value=preferences.get("preferred_name", ""),
                                      placeholder="Leave blank to stay anonymous")
            alias = c2.text_input("Default assistant name",
                                  value=preferences.get("assistant_alias", ""),
                                  placeholder="Leave blank for no name")
            c3, c4 = st.columns(2)
            buf = c3.slider("Planning buffer (minutes)", 0, 120,
                            int(preferences.get("planning_buffer", 45)), 5)
            obuf = c4.slider("Opportunity buffer (minutes)", 0, 120,
                             int(preferences.get("opportunity_buffer", 30)), 5)
            c5, c6 = st.columns(2)
            transport = c5.selectbox(
                "Usual transport", ["Car", "Bus", "Walk", "Bike", "Rideshare"],
                index=["Car", "Bus", "Walk", "Bike", "Rideshare"].index(
                    preferences.get("transport_mode", "Car")))
            area = c6.selectbox("Approximate commute area", list(CITIES),
                                index=list(CITIES).index(preferences["commute_area"])
                                if preferences.get("commute_area") in CITIES else 0)
            teams = st.multiselect(
                "Teams you follow",
                ["Oakland Golden Grizzlies", "Detroit Lions", "Detroit Tigers",
                 "Detroit Pistons", "Detroit Red Wings"],
                default=preferences.get("favorite_teams", []))
            st.caption("Following a team filters the Discover OU list to that organizer. "
                       "KIN holds curated Oakland University records only — it has no live "
                       "fixture feed for professional teams, so following one of those "
                       "currently hides every official event until you untick the filter "
                       "on that screen.")
            c7, c8 = st.columns(2)
            qs = c7.number_input("Quiet hours start", 0, 23,
                                 int(preferences.get("quiet_hours_start", 22)))
            qe = c8.number_input("Quiet hours end", 0, 23,
                                 int(preferences.get("quiet_hours_end", 7)))
            share = st.checkbox(
                "Allow KIN to send my timetable titles to the AI provider",
                value=bool(preferences.get("share_schedule_with_ai", True)),
                help="Turn this off to send only counts. The briefing becomes less specific.")
            if st.form_submit_button("Save preferences", type="primary"):
                store.set_preferences({
                    "preferred_name": preferred, "assistant_alias": alias,
                    "planning_buffer": buf, "opportunity_buffer": obuf,
                    "transport_mode": transport, "commute_area": area,
                    "favorite_teams": teams, "quiet_hours_start": int(qs),
                    "quiet_hours_end": int(qe), "share_schedule_with_ai": share})
                st.success("Saved locally.")
                st.rerun()
        if st.button("Restore default preferences"):
            store.reset_preferences()
            st.success("Preferences reset.")
            st.rerun()

    with tab_ws:
        st.caption("Workspaces keep different parts of life separate. Commitments belong to "
                   "exactly one workspace and are not shared between them.")
        for w in store.list_workspaces():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1.3])
                name = c1.text_input("Name", value=w["name"], key="wn-" + w["id"],
                                     label_visibility="collapsed")
                stored_alias = w.get("assistant_alias")
                al = c2.text_input(
                    "Assistant alias", value=stored_alias or "",
                    key="wa-" + w["id"], label_visibility="collapsed",
                    placeholder=f"Default: {preferences.get('assistant_alias') or 'no name'}")
                if name != w["name"] or al != (stored_alias or ""):
                    store.update_workspace(w["id"], name=name, assistant_alias=al)
                    st.rerun()
                count = len(store.list_commitments(w["id"]))
                c3.caption(f"{count} item(s)")
                if len(store.list_workspaces()) > 1:
                    if c3.button("Delete", key="wd-" + w["id"]):
                        store.delete_workspace(w["id"])
                        st.session_state["workspace_id"] = None
                        st.rerun()
        with st.form("new_ws"):
            c1, c2 = st.columns([3, 2])
            new_name = c1.text_input("New workspace name", placeholder="e.g. BIO 6000")
            new_kind = c2.selectbox("Type", ["Personal", "University", "Course", "Research",
                                             "Employment", "Family", "Sports", "Gaming", "Other"])
            if st.form_submit_button("Create workspace") and new_name.strip():
                store.add_workspace(make_workspace(new_name, new_kind))
                st.success(f"Created “{new_name}”.")
                st.rerun()

    with tab_trust:
        st.markdown("#### Integration status")
        st.caption("An honest list of what is connected and what is not.")
        for integration in INTEGRATION_STATUS:
            kind = {"Live and verified": "live", "Local and functional": "neutral",
                    "Blocked by authorization": "blocked"}.get(integration["status"], "estimate")
            st.markdown(theme.card(integration["name"], [integration["detail"]],
                                   badges=theme.badge(integration["status"], kind)),
                        unsafe_allow_html=True)

        st.markdown("#### AI provider")
        status = provider_status()
        st.markdown(theme.card(
            f"{status['provider']} · {status['model']}",
            [status["detail"],
             "Your API key is read from a local .env file. KIN never displays it, logs it, "
             "or puts it in a prompt."],
            badges=theme.badge("configured" if status["configured"] else "not configured",
                               "live" if status["configured"] else "blocked")),
            unsafe_allow_html=True)

        st.markdown("#### What KIN does not do")
        st.markdown(theme.note(
            "No Oakland University login, Moodle or MySAIL access. No push, SMS or email "
            "delivery. No ticket purchases. No road-safety or travel-time prediction. "
            "No claim of FERPA, SOC 2 or HIPAA compliance, and no official OU affiliation. "
            "Guest mode means no account — not guaranteed anonymity, because a hosted "
            "deployment still processes data server-side."), unsafe_allow_html=True)

        st.markdown("#### Official sources KIN links to")
        for s in OU_SOURCES[:4]:
            st.link_button(s["name"], s["url"])

    with tab_data:
        snapshot = store.export_all()
        c1, c2, c3 = st.columns(3)
        c1.metric("Commitments", len(snapshot["commitments"]))
        c2.metric("Actions logged", len(snapshot["actions"]))
        c3.metric("Workspaces", len(snapshot["workspaces"]))
        st.download_button("Download everything KIN stores (JSON)",
                           json.dumps(snapshot, indent=2),
                           file_name="kin-local-data.json", mime="application/json")
        with st.expander("Inspect the stored record"):
            st.json(snapshot)
        st.divider()
        st.markdown("**Erase local data.** This deletes every commitment, preference, "
                    "workspace, action and notification stored on this machine.")
        confirm = st.checkbox("I understand this cannot be undone")
        if st.button("Erase all local KIN data", disabled=not confirm):
            store.erase_all()
            st.cache_data.clear()
            for key in ("pending_action", "weather", "extracted", "briefing", "qa_history"):
                st.session_state[key] = None if key != "qa_history" else []
            st.success("Erased. KIN will reseed the fictional demo timetable on the next run.")
            st.rerun()


st.divider()
st.caption("KIN · Hacktoberfest proof of concept · guest-only local data · not an official "
           "Oakland University service · not an emergency notification system. "
           "Weather from the National Weather Service. Class status is never inferred from weather.")
