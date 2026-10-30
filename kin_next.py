"""KIN NEXT — independent, session-only Streamlit experience.

Run: streamlit run kin_next.py --server.port 8504
This module never imports kin_store or writes to the original app's database.
"""
from __future__ import annotations

from datetime import datetime, timedelta, time
from pathlib import Path
import html
import json

import streamlit as st

from kin_ai import answer_question, extract_commitment_from_text, provider_status, qa_fallback
from kin_core import (assess_alerts, assess_opportunities, detect_internal_conflicts,
                      parse_dt, sample_commitments, simulated_alert, validate_event_proposal)
from kin_models import MICHIGAN, make_commitment
from kin_sources import CITIES, get_weather, load_events

ROOT = Path(__file__).resolve().parent
LOGO = ROOT / "assets" / "kin-official-logo.webp"
ICON = ROOT / "assets" / "kin-app-icon.webp"
OU_CLOSURES = "https://www.oakland.edu/police/emergency-management/campus-closings/"
PAGES = ["Overview", "My planner", "Weather intelligence", "Campus life", "Ask KIN", "Settings"]

st.set_page_config(page_title="KIN NEXT | Interactive prototype",
                   page_icon=str(ICON) if ICON.exists() else "✦",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');
:root {--gold:#D7A75D;--muted:#A3A8B2;--ink:#0B0D11;--line:#2B2E35;}
html,body,[class*="st-"],button,input,textarea {font-family:'DM Sans',sans-serif;}
.stApp {background:radial-gradient(ellipse 850px 500px at 75% -15%,#312819 0%,transparent 70%),#0B0D11;color:#F4F2ED;}
section[data-testid="stSidebar"] {background:#101216;border-right:1px solid #282A2E;}
.block-container {max-width:1250px;padding-top:1.4rem;padding-bottom:4rem;}
h1,h2,h3 {font-family:'Outfit',sans-serif;letter-spacing:-.03em;}
h1 {font-size:3.1rem!important;line-height:1.1!important;}
h2 {font-size:1.55rem!important;}
div[data-testid="stMetric"] {background:#17191E;border:1px solid #2D3035;border-radius:16px;padding:18px;}
div[data-testid="stMetric"] label {color:#B2B4BA!important;}
div[data-testid="stMetricValue"] {color:#F6D494!important;}
.stButton button[kind="primary"] {background:linear-gradient(110deg,#F7D79B,#C89443)!important;color:#15120C!important;border:0!important;font-weight:800;}
.stButton button {border-radius:12px!important;min-height:44px;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:#323237!important;border-radius:18px!important;}
[data-testid="stAlert"] {border-radius:13px;}
.kin-eyebrow {font-size:.7rem;letter-spacing:.19em;font-weight:800;color:#E2BA74;text-transform:uppercase;}
.kin-hero {padding:34px 35px;background:linear-gradient(115deg,#1D1A17,#17191E 70%);border:1px solid #50402A;border-radius:22px;margin-bottom:20px;}
.kin-hero h1 {margin:10px 0;color:#F7F3EB;}
.kin-hero p {color:#B9B7B2;max-width:650px;}
.kin-chip {display:inline-block;border:1px solid #5B4A32;color:#E8C48A;padding:5px 10px;border-radius:30px;font-size:.74rem;margin-right:8px;}
.kin-event {border-left:3px solid #D4A35C;padding:10px 15px;margin:8px 0;background:#181A1F;border-radius:0 12px 12px 0;}
.kin-event small {color:#B8BBC2;}
@media(max-width:700px){.kin-hero{padding:22px 18px;}h1{font-size:2.25rem!important;}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;}}
</style>
""", unsafe_allow_html=True)


def reset_demo() -> None:
    st.session_state.next_events = [dict(e) for e in sample_commitments()]
    st.session_state.next_pending = None
    st.session_state.next_simulation = False
    st.session_state.next_history = []
    st.session_state.next_weather = None
    st.session_state.next_city = "Oakland University campus (approx.)"


for key, value in {
    "next_events": None, "next_pending": None, "next_simulation": False,
    "next_history": None, "next_weather": None, "next_city": "Oakland University campus (approx.)",
    "next_name": "KIN", "next_page": "Overview", "next_ai_response": None,
    "next_share_ai": False, "next_buffer": 30,
}.items():
    st.session_state.setdefault(key, value)
if st.session_state.next_events is None:
    reset_demo()


def navigate(page: str) -> None:
    st.session_state.next_page = page


def when(value: str) -> str:
    return parse_dt(value).astimezone(MICHIGAN).strftime("%a, %b %d · %I:%M %p").replace(" 0", " ")


def event_card(event: dict) -> None:
    st.markdown(
        '<div class="kin-event"><strong>' + html.escape(event["title"]) + '</strong><br>'
        '<small>' + html.escape(when(event["start"])) + ' – '
        + html.escape(parse_dt(event["end"]).astimezone(MICHIGAN).strftime("%I:%M %p"))
        + ' · ' + html.escape(event.get("event_type", "campus")) + '</small></div>',
        unsafe_allow_html=True)


def add_pending(proposal: dict, source: str = "manual") -> None:
    valid = validate_event_proposal(proposal, strict_michigan=True)
    st.session_state.next_pending = {**valid, "source": source}


def approve() -> None:
    p = st.session_state.next_pending
    if not p:
        return
    c = make_commitment(p["title"], p["start"], p["end"],
                        event_type=p.get("event_type", "personal"),
                        origin="kin-next-approved",
                        requires_travel=p.get("requires_travel", False))
    if any(e["title"] == c["title"] and e["start"] == c["start"] for e in st.session_state.next_events):
        st.session_state.next_history.append("Skipped duplicate: " + c["title"])
    else:
        st.session_state.next_events.append(c)
        st.session_state.next_history.append("Approved: " + c["title"])
    st.session_state.next_pending = None


def pending_panel() -> None:
    p = st.session_state.next_pending
    if not p:
        return
    with st.container(border=True):
        st.markdown("#### Approval required")
        st.write(p["title"])
        st.caption(when(p["start"]) + " → " + when(p["end"]))
        st.caption("No change is made until you approve. This affects only your current browser session.")
        a, b = st.columns(2)
        a.button("Approve and add", key="next_approve", type="primary", on_click=approve, use_container_width=True)
        if b.button("Discard proposal", key="next_discard", use_container_width=True):
            st.session_state.next_pending = None
            st.rerun()


def current_impacts() -> list[dict]:
    alerts = []
    w = st.session_state.next_weather
    if w and w.get("alerts_status") == "retrieved" and w.get("city") == st.session_state.next_city:
        alerts.extend(w.get("alerts", []))
    if st.session_state.next_simulation:
        alerts.append(simulated_alert())
    return assess_alerts(st.session_state.next_events, alerts, st.session_state.next_buffer)


with st.sidebar:
    if ICON.exists():
        st.image(str(ICON), width=88)
    st.markdown("### KIN <span style='color:#D7A75D'>NEXT</span>", unsafe_allow_html=True)
    st.caption("ALTERNATIVE EXPERIENCE · NOT THE LIVE APP")
    st.radio("Explore", PAGES, key="next_page")
    st.divider()
    st.caption("Your companion")
    st.text_input("Assistant nickname", key="next_name", max_chars=35)
    st.caption("Independent prototype. Browser-session data only.")
    if st.button("Reset fictional demo", use_container_width=True):
        reset_demo()
        st.rerun()
    st.divider()
    st.caption("KIN · Kinetic Intelligence Network")
    st.caption("Independent OU-inspired project · Not official university guidance")

page = st.session_state.next_page
events = sorted(st.session_state.next_events, key=lambda e: e["start"])
conflicts = detect_internal_conflicts(events)
impacts = current_impacts()

if page == "Overview":
    st.markdown(
        '<div class="kin-hero"><div class="kin-eyebrow">A smarter way through your day</div>'
        '<h1>Life changes.<br><span style="color:#E4B873">KIN moves with you.</span></h1>'
        '<p>See your commitments, understand disruptions, and discover what fits. '
        'Every important action stays in your hands.</p>'
        '<span class="kin-chip">Michigan-aware</span><span class="kin-chip">Powered by Gemma 4</span>'
        '<span class="kin-chip">You approve changes</span></div>',
        unsafe_allow_html=True)
    st.caption("EXPERIMENTAL DESIGN · Fictional student data · Demo date: October 30, 2026")
    metrics = st.columns(4)
    for col, label, val in zip(metrics,
        ["Commitments", "Time conflicts", "Weather overlaps", "Pending approval"],
        [len(events), len(conflicts), len(impacts), int(st.session_state.next_pending is not None)]):
        col.metric(label, val)
    st.markdown("### Your next move")
    if impacts:
        st.warning("A weather alert overlaps a commitment. Check whether it is a **SIMULATED** warning or an official NWS alert.")
        st.button("Explore weather impact →", type="primary", on_click=navigate, args=("Weather intelligence",))
    elif conflicts:
        st.info("Your fictional timetable contains an overlap.")
        st.button("Review planner →", type="primary", on_click=navigate, args=("My planner",))
    else:
        st.info("Your current example timetable has no detected conflicts. Explore campus opportunities or add a commitment.")
        st.button("Find an OU activity →", type="primary", on_click=navigate, args=("Campus life",))
    st.markdown("### Your KIN journey")
    cols = st.columns(4)
    for col, title, target in zip(cols, ["01 · Plan", "02 · Weather", "03 · Discover", "04 · Ask"], PAGES[1:5]):
        col.button(title, use_container_width=True, key="jump_"+target, on_click=navigate, args=(target,))
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown("### Your timeline")
        for e in events[:7]:
            event_card(e)
    with right:
        st.markdown("### KIN's promise")
        with st.container(border=True):
            st.markdown("**Clarity over noise.**")
            st.write("Weather comes from NWS. Campus events link to official sources. Scheduling rules are deterministic.")
            st.markdown("**Consent by design.**")
            st.write("No calendar writes without approval. This separate prototype keeps sample changes in the current session.")
        pending_panel()

elif page == "My planner":
    st.markdown('<div class="kin-eyebrow">Make a plan</div>', unsafe_allow_html=True)
    st.title("Your time, organized.")
    st.caption("All changes are local to this prototype session. No OU account or personal calendar is connected.")
    tab1, tab2 = st.tabs(["Add a commitment", "View & manage"])
    with tab1:
        with st.form("new_commitment", clear_on_submit=False):
            title = st.text_input("What are you planning?", placeholder="Biology study session")
            col1, col2 = st.columns(2)
            d = col1.date_input("Date", value=datetime(2026, 10, 31).date())
            t = col2.time_input("Start", value=time(14, 0))
            col3, col4 = st.columns(2)
            minutes = col3.selectbox("Duration", [30, 45, 60, 90, 120, 180], index=2)
            category = col4.selectbox("Type", ["study", "class", "exam", "work", "family", "meeting", "personal", "recreation", "gaming"])
            submit = st.form_submit_button("Review before adding", type="primary")
        if submit:
            try:
                if not title.strip():
                    raise ValueError("Enter a commitment title.")
                start = datetime.combine(d, t, tzinfo=MICHIGAN)
                end = start + timedelta(minutes=minutes)
                add_pending({"title": title.strip(), "start": start.isoformat(), "end": end.isoformat(),
                             "event_type": category, "requires_travel": False})
                st.success("Proposal created. Review it below.")
            except (ValueError, TypeError) as exc:
                st.error(str(exc))
        pending_panel()
    with tab2:
        if conflicts:
            for c in conflicts:
                st.warning("Overlap: " + c["a"] + " / " + c["b"])
        for i, e in enumerate(events):
            cols = st.columns([5, 1])
            with cols[0]:
                event_card(e)
            if cols[1].button("Remove", key="remove_"+e["id"]):
                st.session_state.next_events = [x for x in events if x["id"] != e["id"]]
                st.session_state.next_history.append("Removed: " + e["title"])
                st.rerun()
        st.caption("Recent actions")
        for item in reversed(st.session_state.next_history[-6:]):
            st.write("• " + item)

elif page == "Weather intelligence":
    st.markdown('<div class="kin-eyebrow">Source-aware weather</div>', unsafe_allow_html=True)
    st.title("Know what might change.")
    st.caption("Weather and scheduling are separate sources. KIN never infers that OU has canceled classes.")
    city = st.selectbox("Approximate Michigan location", list(CITIES), key="next_city")
    lat, lon = CITIES[city]
    if st.button("Refresh official NWS data", type="primary"):
        with st.spinner("Checking the National Weather Service…"):
            st.session_state.next_weather = get_weather(lat, lon, city)
    w = st.session_state.next_weather
    if w and w.get("city") == city:
        st.caption("Retrieved: " + w.get("retrieved_at", "unknown"))
        if w.get("alerts_status") == "retrieved":
            if w.get("alerts"):
                for a in w["alerts"]:
                    st.warning(a["event"] + " · " + a.get("severity", "Unknown"))
                    if a.get("source_url"):
                        st.link_button("Official alert source", a["source_url"])
            else:
                st.success("No active alerts returned by NWS for this approximate point at the retrieval time.")
        else:
            st.error("NWS alerts unavailable. No conclusion about alert absence can be made.")
        if w.get("forecast_status") == "retrieved":
            with st.expander("Hourly forecast"):
                for p in w.get("forecast", [])[:8]:
                    st.write(str(p.get("startTime", ""))[:16] + " · " + str(p.get("temperature", "?")) +
                             "°" + str(p.get("temperatureUnit", "F")) + " · " + p.get("shortForecast", ""))
        else:
            st.info("Hourly forecast is unavailable.")
    else:
        st.info("Choose a location and refresh to retrieve NWS information.")
    st.divider()
    st.markdown("### Try a fictional weather disruption")
    st.toggle("Enable SIMULATED winter storm", key="next_simulation",
              help="This warning is created for demonstration and is not from the NWS.")
    if st.session_state.next_simulation:
        st.error("SIMULATION ONLY — a fictional winter storm warning for October 31, 2026.")
    if impacts:
        for impact in impacts:
            st.warning(("SIMULATED · " if impact.get("is_simulation") else "NWS · ") +
                       str(impact.get("alert", "Weather")) + " may affect " +
                       str(impact.get("commitment", "a commitment")))
    else:
        st.caption("No matching alert windows found in the current selected data. This is not a travel safety assessment.")
    st.link_button("Check official OU campus closings", OU_CLOSURES)

elif page == "Campus life":
    st.markdown('<div class="kin-eyebrow">More than a timetable</div>', unsafe_allow_html=True)
    st.title("Make room for the good stuff.")
    st.caption("Curated Oakland University event examples with source links. Recheck event status before attending.")
    choices = assess_opportunities(events, load_events(), st.session_state.next_buffer)
    for item in choices:
        with st.container(border=True):
            a, b = st.columns([3, 1])
            a.markdown("#### " + item["title"])
            a.caption(when(item["start"]) + " · " + item.get("venue", "Venue not listed"))
            a.caption("End time is an estimate" if item.get("end_is_estimated") else "End time provided")
            if item["fits"]:
                b.success("Fits your plan")
            else:
                b.warning("Possible conflict")
                b.caption(", ".join(item["conflicts"][:3]))
            st.link_button("Official event source", item["source_url"])
            if st.button("Propose adding to my plan", key="propose_"+item["id"]):
                try:
                    add_pending({"title": item["title"], "start": item["start"], "end": item["end"],
                                 "event_type": "recreation", "requires_travel": True}, source="official_linked")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    pending_panel()

elif page == "Ask KIN":
    st.markdown('<div class="kin-eyebrow">AI with boundaries</div>', unsafe_allow_html=True)
    st.title("Ask. Understand. Decide.")
    status = provider_status()
    st.caption("Configured provider: " + status["provider"] + " · " + status["model"])
    if not status["configured"]:
        st.info("Gemma is not configured on this server. A deterministic, explicitly labeled fallback is available.")
    question = st.selectbox("Start with a question", [
        "What should I check before my fictional exam?",
        "Do I have any timetable conflicts?",
        "What does KIN know about OU closures?",
        "Can I fit a campus sports event into my plan?",
        "Write my own question…",
    ])
    custom = st.text_input("Your question", placeholder="Ask KIN about your selected plan…")
    st.checkbox("Allow selected fictional timetable to be sent to the AI provider",
                key="next_share_ai")
    if st.button("Ask KIN", type="primary"):
        q = custom.strip() or ("" if question.endswith("…") else question)
        if not q:
            st.warning("Enter a question.")
        elif not st.session_state.next_share_ai:
            st.warning("Enable the explicit AI-sharing checkbox to call Gemma. No data has been sent.")
        else:
            context = {"commitments": [
                {"title": e["title"], "start": e["start"], "end": e["end"],
                 "event_type": e.get("event_type")} for e in events[:20]],
                "impacts": impacts, "conflicts": conflicts,
                "ou_closing_url": OU_CLOSURES,
                "note": "Synthetic browser-session demonstration. No verified university closure."}
            with st.spinner("Asking Gemma…"):
                try:
                    response, provider = answer_question(q, context)
                    st.session_state.next_ai_response = (response, provider)
                except Exception as exc:
                    st.session_state.next_ai_response = (qa_fallback(q),
                        "Deterministic fallback — not Gemma (" + type(exc).__name__ + ")")
    if st.session_state.next_ai_response:
        response, provider = st.session_state.next_ai_response
        st.caption("Response source: " + provider)
        st.markdown(response)
    st.divider()
    st.caption("AI proposes and explains. Python validates. Only the user approves calendar changes.")

else:
    st.markdown('<div class="kin-eyebrow">Your experience</div>', unsafe_allow_html=True)
    st.title("Settings & trust")
    st.slider("Planning buffer (minutes, not a travel prediction)", 0, 120, key="next_buffer", step=5)
    st.markdown("### What stays separate")
    st.write("KIN NEXT does not import the original SQLite store or modify the original application.")
    st.write("Calendar additions and removals exist only in this Streamlit browser session.")
    st.write("No university authentication, push notification, road-safety estimates, or multi-user account system.")
    st.write("Weather is fetched only when you click Refresh. AI calls require explicit opt-in.")
    st.link_button("Official OU campus closings", OU_CLOSURES)
    if st.button("Erase this demo session", type="primary"):
        reset_demo()
        st.session_state.next_ai_response = None
        st.rerun()

st.divider()
st.caption("KIN NEXT · Alternative concept for side-by-side comparison · Synthetic data only · "
           "Not an official Oakland University service")
