"""Presentation layer: Oakland University visual identity for KIN.

KIN — Kinetic Intelligence Network.

Design intent (plan Module S): modern, readable and calm enough for daily use,
warm enough that a student actually wants to open it. Black and gold reference
Oakland University's Golden Grizzlies identity without claiming affiliation.
Motion is limited to short, non-essential transitions; nothing animates to
attract attention. Contrast targets WCAG 2.2 AA, and the layout works at phone
width with a 16px gutter.
"""
from __future__ import annotations

import base64
import html
import io
from functools import lru_cache
from pathlib import Path
from typing import Any

BRAND = "KIN"
BRAND_LONG = "Kinetic Intelligence Network"
TAGLINE = "Life changes. KIN moves with you."

ASSETS = Path(__file__).parent / "assets"
LOGO = ASSETS / "kin-logo.png"
ICON = ASSETS / "kin-icon.png"


@lru_cache(maxsize=8)
def image_data_uri(path: str, max_height: int) -> str:
    """Return a downscaled PNG as a data URI, or '' when unavailable.

    The source artwork is large (the wordmark is ~1.2 MB at 2048px). Embedding
    it raw would ship well over a megabyte of HTML on every rerun, so it is
    resized once per process and cached. Returning '' lets the caller fall back
    to text, which keeps the app working if the assets are missing.
    """
    source = Path(path)
    if not source.exists():
        return ""
    try:
        from PIL import Image
    except ImportError:
        return ""
    try:
        with Image.open(source) as image:
            image = image.convert("RGBA")
            if image.height > max_height:
                ratio = max_height / image.height
                image = image.resize(
                    (max(1, round(image.width * ratio)), max_height),
                    Image.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)
    except (OSError, ValueError):
        return ""
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def logo_available() -> bool:
    return LOGO.exists()


def icon_image():
    """The app icon as a PIL Image for st.set_page_config, or None."""
    if not ICON.exists():
        return None
    try:
        from PIL import Image
        return Image.open(ICON)
    except (ImportError, OSError):
        return None

GOLD = "#F6B61C"
GOLD_DEEP = "#8A6200"
INK = "#0B0B0C"

# Per-event-type accent colours, used for the timeline dots and type chips.
TYPE_COLORS: dict[str, str] = {
    "class": "#2F6FD0", "exam": "#C0392B", "quiz": "#D35400",
    "assignment": "#8E44AD", "lab": "#16A085", "meeting": "#2C7A7B",
    "study": "#2D7D46", "work": "#5B6370", "family": "#C2185B",
    "recreation": "#F6B61C", "gaming": "#6C4DD3", "personal": "#7A8290",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --kin-gold: #F6B61C;
  --kin-gold-soft: #FDF4DD;
  --kin-gold-deep: #8A6200;
  --kin-ink: #0B0B0C;
  --kin-text: #15171C;
  --kin-muted: #5B616D;
  --kin-faint: #878D99;
  --kin-surface: #FFFFFF;
  --kin-surface-2: #F6F7F9;
  --kin-surface-3: #EEF0F4;
  --kin-border: #E2E5EB;
  --kin-danger: #B3261E;
  --kin-danger-soft: #FDECEA;
  --kin-warn: #8A5A00;
  --kin-warn-soft: #FFF7E6;
  --kin-ok: #176B3A;
  --kin-ok-soft: #EAF7EF;
  --kin-sim: #5B3A9E;
  --kin-sim-soft: #F1ECFB;
  --kin-info-soft: #EDF2FB;
  --kin-r: 14px;
  --kin-r-sm: 10px;
  --kin-shadow: 0 1px 2px rgba(16,18,22,.04), 0 4px 16px rgba(16,18,22,.05);
}
@media (prefers-color-scheme: dark) {
  :root {
    --kin-gold: #FFC83D;
    --kin-gold-soft: #2B2516;
    --kin-gold-deep: #FFDA86;
    --kin-ink: #F4F5F7;
    --kin-text: #E9EBEF;
    --kin-muted: #A6ADBA;
    --kin-faint: #878E9C;
    --kin-surface: #15171C;
    --kin-surface-2: #1C1F26;
    --kin-surface-3: #23272F;
    --kin-border: #2E333D;
    --kin-danger: #F3B7B3;
    --kin-danger-soft: #3A211F;
    --kin-warn: #FFD392;
    --kin-warn-soft: #332814;
    --kin-ok: #9DE4B6;
    --kin-ok-soft: #14301F;
    --kin-sim: #C8B4F7;
    --kin-sim-soft: #241D38;
    --kin-info-soft: #1A2131;
    --kin-shadow: 0 1px 2px rgba(0,0,0,.3), 0 4px 18px rgba(0,0,0,.25);
  }
}

html, body, [class*="st-"], .stMarkdown, button, input, select, textarea {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1220px; }
@media (max-width: 640px) { .block-container { padding-left: 16px; padding-right: 16px; } }

/* ============================================================= masthead */
.kin-masthead {
  position: relative; overflow: hidden;
  display: flex; align-items: center; gap: 16px;
  padding: 20px 24px; margin-bottom: 18px;
  background:
    radial-gradient(900px 200px at 88% -40%, rgba(246,182,28,.22), transparent 70%),
    linear-gradient(104deg, #0B0B0C 0%, #1C1D22 52%, #332806 100%);
  border-radius: var(--kin-r);
  border: 1px solid rgba(246,182,28,.28);
}
.kin-masthead::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(90deg, var(--kin-gold), transparent 42%);
  height: 3px; top: 0;
}
.kin-mark {
  width: 46px; height: 46px; flex: 0 0 46px;
  display: grid; place-items: center; border-radius: 12px;
  background: linear-gradient(145deg, #FFD25F, var(--kin-gold));
  color: #0B0B0C; font-weight: 800; font-size: 17px; letter-spacing: -.3px;
  box-shadow: 0 2px 10px rgba(246,182,28,.3);
}
.kin-wordmark { display: flex; flex-direction: column; min-width: 0; line-height: 1.3; }
.kin-wordmark b {
  color: #FFF; font-size: 17px; font-weight: 700; letter-spacing: .18em;
  text-transform: uppercase;
}
.kin-wordmark span { color: #C9CCD3; font-size: 12.5px; font-weight: 450; }
/* Official wordmark. The artwork is already gold-on-black, so it sits
   directly on the masthead with no plate behind it. */
.kin-logo {
  height: 54px; width: auto; max-width: min(58vw, 420px);
  object-fit: contain; display: block;
}
.kin-masthead-meta {
  color: #C9CCD3; font-size: 12.5px; font-weight: 450;
  padding-left: 16px; margin-left: 4px;
  border-left: 1px solid rgba(255,255,255,.17);
  align-self: center; max-width: 230px;
}
.kin-masthead-tag {
  margin-left: auto; flex: 0 0 auto; color: #0B0B0C; background: var(--kin-gold);
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em;
  border-radius: 999px; padding: 6px 13px;
}
@media (max-width: 860px) {
  .kin-masthead-meta { border-left: 0; padding-left: 0; margin-left: 0; }
}
@media (max-width: 680px) {
  .kin-masthead { flex-wrap: wrap; gap: 12px; padding: 16px; }
  .kin-masthead-tag { margin-left: 0; }
  .kin-wordmark b { font-size: 15px; }
  .kin-logo { height: 42px; max-width: 72vw; }
  .kin-masthead-meta { flex-basis: 100%; max-width: none; }
}

/* Sidebar brand lockup */
.kin-sb-brand {
  display: flex; align-items: center; gap: 11px; margin-bottom: 16px;
}
.kin-sb-mark {
  width: 38px; height: 38px; flex: 0 0 38px; border-radius: 10px;
  object-fit: contain; background: #0B0B0C; padding: 3px;
  border: 1px solid rgba(246,182,28,.35);
}
.kin-sb-text { line-height: 1.3; min-width: 0; }
.kin-sb-text b {
  display: block; font-size: 11.5px; font-weight: 700;
  letter-spacing: .1em; text-transform: uppercase; color: var(--kin-text);
}
.kin-sb-text span { font-size: 11px; color: var(--kin-muted); }

/* ================================================================= hero */
.kin-hero { margin: 0 0 6px; }
.kin-hero h2 {
  margin: 0; font-size: 25px; font-weight: 750; color: var(--kin-text);
  letter-spacing: -.3px;
}
.kin-hero .kin-date {
  color: var(--kin-muted); font-size: 13px; font-weight: 500;
  text-transform: uppercase; letter-spacing: .07em; margin-bottom: 3px;
}
.kin-hero p { color: var(--kin-muted); font-size: 14px; margin: 5px 0 0; }

/* =========================================================== stat tiles */
.kin-stats { display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0 20px; }
.kin-stat {
  flex: 1 1 140px; min-width: 130px; position: relative;
  background: var(--kin-surface); border: 1px solid var(--kin-border);
  border-radius: var(--kin-r); padding: 14px 16px; box-shadow: var(--kin-shadow);
}
.kin-stat .ic { font-size: 15px; opacity: .85; margin-bottom: 7px; }
.kin-stat .v {
  font-size: 27px; font-weight: 750; color: var(--kin-text);
  line-height: 1; letter-spacing: -.6px;
}
.kin-stat .k {
  font-size: 11px; color: var(--kin-muted); text-transform: uppercase;
  letter-spacing: .08em; margin-top: 6px; font-weight: 600;
}
.kin-stat.accent { border-top: 3px solid var(--kin-gold); }
.kin-stat.danger { border-top: 3px solid var(--kin-danger); }
.kin-stat.danger .v { color: var(--kin-danger); }
.kin-stat.ok     { border-top: 3px solid var(--kin-ok); }

/* ================================================================ cards */
.kin-card {
  background: var(--kin-surface); border: 1px solid var(--kin-border);
  border-left: 4px solid var(--kin-gold);
  border-radius: var(--kin-r); padding: 15px 17px; margin-bottom: 11px;
  box-shadow: var(--kin-shadow);
}
.kin-card.is-alert { border-left-color: var(--kin-danger); background: var(--kin-danger-soft); }
.kin-card.is-warn  { border-left-color: var(--kin-warn);   background: var(--kin-warn-soft); }
.kin-card.is-ok    { border-left-color: var(--kin-ok);     background: var(--kin-ok-soft); }
.kin-card.is-sim {
  border: 1px dashed var(--kin-sim); border-left: 4px dashed var(--kin-sim);
  background: var(--kin-sim-soft);
}
.kin-card h4 {
  margin: 0 0 6px; font-size: 15.5px; font-weight: 680; color: var(--kin-text);
  letter-spacing: -.1px;
}
.kin-card p { margin: 3px 0; font-size: 13.6px; color: var(--kin-text); line-height: 1.55; }
.kin-card .kin-sub { color: var(--kin-muted); font-size: 12.4px; }

/* =============================================================== badges */
.kin-badge {
  display: inline-block; font-size: 10.5px; font-weight: 700;
  letter-spacing: .05em; text-transform: uppercase;
  padding: 4px 9px; border-radius: 6px; margin: 3px 6px 3px 0;
  border: 1px solid transparent; white-space: nowrap;
}
.kin-badge.live     { background: var(--kin-ok-soft);     color: var(--kin-ok);      border-color: currentColor; }
.kin-badge.sim      { background: var(--kin-sim-soft);    color: var(--kin-sim);     border-color: currentColor; }
.kin-badge.estimate { background: var(--kin-warn-soft);   color: var(--kin-warn);    border-color: currentColor; }
.kin-badge.blocked  { background: var(--kin-surface-3);   color: var(--kin-muted);   border-color: var(--kin-border); }
.kin-badge.neutral  { background: var(--kin-gold-soft);   color: var(--kin-gold-deep); border-color: currentColor; }
.kin-badge.danger   { background: var(--kin-danger-soft); color: var(--kin-danger);  border-color: currentColor; }

/* ============================================================= timeline */
.kin-timeline { margin: 4px 0 8px; }
.kin-tl {
  display: flex; gap: 14px; align-items: stretch;
  padding: 0; margin: 0; position: relative;
}
.kin-tl + .kin-tl { margin-top: 2px; }
.kin-tl .when {
  flex: 0 0 76px; text-align: right; padding-top: 13px;
  font-size: 12.5px; font-weight: 650; color: var(--kin-muted);
  font-variant-numeric: tabular-nums;
}
.kin-tl .rail { flex: 0 0 14px; position: relative; }
.kin-tl .rail::before {
  content: ""; position: absolute; left: 6px; top: 0; bottom: 0;
  width: 2px; background: var(--kin-border);
}
.kin-tl:first-child .rail::before { top: 16px; }
.kin-tl:last-child  .rail::before { bottom: calc(100% - 16px); }
.kin-tl .dot {
  position: absolute; left: 1px; top: 15px;
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--kin-gold); border: 2px solid var(--kin-surface);
  box-shadow: 0 0 0 1px var(--kin-border);
}
.kin-tl .item {
  flex: 1; min-width: 0; margin-bottom: 9px;
  background: var(--kin-surface); border: 1px solid var(--kin-border);
  border-radius: var(--kin-r-sm); padding: 11px 14px;
  transition: border-color .15s ease, transform .15s ease;
}
.kin-tl .item:hover { border-color: var(--kin-gold); transform: translateX(2px); }
.kin-tl .item .ttl {
  font-size: 14.5px; font-weight: 640; color: var(--kin-text);
  display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
}
.kin-tl .item .meta { font-size: 12.3px; color: var(--kin-muted); margin-top: 3px; }
.kin-tl.done .item   { opacity: .6; }
.kin-tl.done .ttl    { text-decoration: line-through; }
.kin-tl.flagged .item { border-color: var(--kin-danger); background: var(--kin-danger-soft); }
.kin-tl.flagged .dot  { background: var(--kin-danger); }
@media (max-width: 560px) {
  .kin-tl .when { flex-basis: 58px; font-size: 11.5px; }
}

/* ============================================================ type chip */
.kin-type {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight: 650; color: var(--kin-muted);
  text-transform: uppercase; letter-spacing: .04em;
}
.kin-type i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

/* ================================================================ rows */
.kin-row {
  display: flex; gap: 13px; align-items: flex-start;
  padding: 12px 14px; border: 1px solid var(--kin-border);
  border-radius: var(--kin-r-sm); background: var(--kin-surface);
  margin-bottom: 8px; box-shadow: var(--kin-shadow);
  transition: border-color .15s ease;
}
.kin-row:hover { border-color: var(--kin-gold); }
.kin-row .ico { font-size: 18px; flex: 0 0 26px; text-align: center; line-height: 1.45; }
.kin-row .body { min-width: 0; flex: 1; }
.kin-row .ttl { font-weight: 640; font-size: 14.5px; color: var(--kin-text); }
.kin-row .meta { font-size: 12.4px; color: var(--kin-muted); margin-top: 2px; }
.kin-row.done .ttl { text-decoration: line-through; opacity: .6; }
.kin-row.canceled { opacity: .55; }

/* ============================================================== notice */
.kin-note {
  border: 1px solid var(--kin-border); border-left: 3px solid var(--kin-faint);
  border-radius: var(--kin-r-sm); background: var(--kin-surface-2);
  padding: 12px 15px; font-size: 12.9px; color: var(--kin-muted);
  margin: 8px 0 14px; line-height: 1.6;
}
.kin-note strong { color: var(--kin-text); }
.kin-sim-banner {
  border: 1px dashed var(--kin-sim); background: var(--kin-sim-soft);
  color: var(--kin-text); border-radius: var(--kin-r-sm);
  padding: 13px 16px; margin: 10px 0; font-size: 13.4px; line-height: 1.6;
}
.kin-sim-banner b { color: var(--kin-sim); letter-spacing: .04em; }

/* ============================================================== empty */
.kin-empty {
  text-align: center; padding: 34px 20px;
  border: 1px dashed var(--kin-border); border-radius: var(--kin-r);
  background: var(--kin-surface-2); margin: 8px 0 14px;
}
.kin-empty .ic { font-size: 30px; opacity: .55; }
.kin-empty h5 {
  margin: 11px 0 5px; font-size: 15px; font-weight: 650; color: var(--kin-text);
}
.kin-empty p { margin: 0; font-size: 13.2px; color: var(--kin-muted); }

/* ============================================ section heading + sidebar */
.kin-sec {
  display: flex; align-items: center; gap: 9px;
  margin: 22px 0 10px; padding-bottom: 8px;
  border-bottom: 1px solid var(--kin-border);
}
.kin-sec .ic { font-size: 15px; }
.kin-sec h3 {
  margin: 0; font-size: 13px; font-weight: 700; color: var(--kin-text);
  text-transform: uppercase; letter-spacing: .09em;
}
.kin-sec .hint { margin-left: auto; font-size: 12px; color: var(--kin-faint); }

section[data-testid="stSidebar"] { border-right: 1px solid var(--kin-border); }
section[data-testid="stSidebar"] .stRadio > label { display: none; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 2px; }
section[data-testid="stSidebar"] .stRadio label {
  padding: 9px 12px; border-radius: var(--kin-r-sm);
  transition: background .14s ease; font-size: 14px; width: 100%;
}
section[data-testid="stSidebar"] .stRadio label:hover { background: var(--kin-surface-3); }

/* ============================================================== buttons */
.stButton > button {
  border-radius: var(--kin-r-sm); font-weight: 600; min-height: 42px;
  font-size: 13.8px; transition: transform .12s ease, box-shadow .12s ease;
}
.stButton > button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: var(--kin-shadow); }
.stButton > button[kind="primary"] {
  background: var(--kin-gold-deep); border-color: var(--kin-gold-deep); color: #FFF;
}
.stDownloadButton > button { border-radius: var(--kin-r-sm); font-weight: 600; min-height: 42px; }
.stLinkButton > a { border-radius: var(--kin-r-sm); font-weight: 580; min-height: 40px; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 3px; border-bottom: 1px solid var(--kin-border); }
.stTabs [data-baseweb="tab"] { font-size: 13.8px; font-weight: 600; border-radius: 9px 9px 0 0; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; animation: none !important; }
}
</style>
"""


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def masthead(subtitle: str, tag: str = "Hacktoberfest 2026") -> str:
    """The brand bar. Uses the official wordmark when present, text otherwise.

    The alt text carries the full brand name so the heading is still announced
    to a screen reader and still searchable when the image is used.
    """
    wordmark = image_data_uri(str(LOGO), 108)
    if wordmark:
        brand = (
            f'<img class="kin-logo" src="{wordmark}" '
            f'alt="{_esc(BRAND_LONG)} — {_esc(TAGLINE)}">'
        )
    else:
        brand = (f'<div class="kin-mark">{BRAND}</div>'
                 f'<div class="kin-wordmark"><b>{_esc(BRAND_LONG)}</b>'
                 f'<span>{_esc(TAGLINE)}</span></div>')
    return (
        '<div class="kin-masthead">'
        f'{brand}'
        f'<div class="kin-masthead-meta">{_esc(subtitle)}</div>'
        f'<div class="kin-masthead-tag">{_esc(tag)}</div>'
        '</div>'
    )


def sidebar_brand() -> str:
    """Compact mark plus wordmark for the sidebar."""
    mark = image_data_uri(str(ICON), 76)
    glyph = (f'<img src="{mark}" alt="" class="kin-sb-mark">' if mark
             else f'<div class="kin-mark" style="width:36px;height:36px;'
                  f'font-size:14px">{BRAND}</div>')
    return (
        '<div class="kin-sb-brand">'
        f'{glyph}'
        '<div class="kin-sb-text">'
        f'<b>{_esc(BRAND_LONG)}</b>'
        f'<span>{_esc(TAGLINE)}</span>'
        '</div></div>'
    )


def hero(date_line: str, heading: str, sub: str = "") -> str:
    return (
        '<div class="kin-hero">'
        f'<div class="kin-date">{_esc(date_line)}</div>'
        f'<h2>{_esc(heading)}</h2>'
        + (f'<p>{_esc(sub)}</p>' if sub else '')
        + '</div>'
    )


def section(icon: str, title: str, hint: str = "") -> str:
    return (
        f'<div class="kin-sec"><span class="ic">{_esc(icon)}</span><h3>{_esc(title)}</h3>'
        + (f'<span class="hint">{_esc(hint)}</span>' if hint else '')
        + '</div>'
    )


def badge(text: str, kind: str = "neutral") -> str:
    return f'<span class="kin-badge {_esc(kind)}">{_esc(text)}</span>'


def type_chip(event_type: str, label: str) -> str:
    colour = TYPE_COLORS.get(event_type, TYPE_COLORS["personal"])
    return (f'<span class="kin-type"><i style="background:{colour}"></i>'
            f'{_esc(label)}</span>')


def stat_tiles(items: list[tuple[str, Any, str]] | list[tuple[str, Any, str, str]]) -> str:
    """Accepts (label, value, variant) or (label, value, variant, icon)."""
    cells = []
    for item in items:
        label, value, variant = item[0], item[1], item[2]
        icon = item[3] if len(item) > 3 else ""
        cells.append(
            f'<div class="kin-stat {_esc(variant)}">'
            + (f'<div class="ic">{_esc(icon)}</div>' if icon else '')
            + f'<div class="v">{_esc(value)}</div>'
              f'<div class="k">{_esc(label)}</div></div>'
        )
    return f'<div class="kin-stats">{"".join(cells)}</div>'


def card(title: str, lines: list[str], *, variant: str = "", badges: str = "") -> str:
    body = "".join(f'<p>{line}</p>' for line in lines)
    return f'<div class="kin-card {_esc(variant)}"><h4>{_esc(title)}</h4>{badges}{body}</div>'


def event_row(icon: str, title: str, meta: str, *, variant: str = "", badges: str = "") -> str:
    return (
        f'<div class="kin-row {_esc(variant)}">'
        f'<div class="ico">{_esc(icon)}</div>'
        f'<div class="body"><div class="ttl">{_esc(title)}</div>'
        f'<div class="meta">{_esc(meta)}</div>{badges}</div></div>'
    )


def timeline_item(time_label: str, title: str, meta: str, event_type: str,
                  *, variant: str = "", badges: str = "") -> str:
    """One entry on the Today timeline."""
    colour = TYPE_COLORS.get(event_type, TYPE_COLORS["personal"])
    return (
        f'<div class="kin-tl {_esc(variant)}">'
        f'<div class="when">{_esc(time_label)}</div>'
        f'<div class="rail"><span class="dot" style="background:{colour}"></span></div>'
        f'<div class="item"><div class="ttl">{_esc(title)}{badges}</div>'
        f'<div class="meta">{_esc(meta)}</div></div></div>'
    )


def timeline(items: list[str]) -> str:
    return f'<div class="kin-timeline">{"".join(items)}</div>'


def note(text_html: str) -> str:
    return f'<div class="kin-note">{text_html}</div>'


def empty(icon: str, heading: str, body: str) -> str:
    return (f'<div class="kin-empty"><div class="ic">{_esc(icon)}</div>'
            f'<h5>{_esc(heading)}</h5><p>{_esc(body)}</p></div>')


def simulation_banner(text: str) -> str:
    return f'<div class="kin-sim-banner"><b>SIMULATION ACTIVE</b> — {_esc(text)}</div>'
