"""Presentation helpers: Oakland University visual identity for the Streamlit UI.

Design intent (plan Module S): calm, modern, readable and discreet. Black and
gold reference Oakland University's Golden Grizzlies identity without claiming
any official affiliation. No animation, no decorative dashboards, AA-oriented
contrast, and a layout that still works at phone width.
"""
from __future__ import annotations

import html
from typing import Any

GOLD = "#F6B61C"
GOLD_DEEP = "#B8820A"
INK = "#0B0B0C"

CSS = """
<style>
:root {
  --kin-gold: #F6B61C;
  --kin-gold-soft: #FDF3DA;
  --kin-gold-deep: #8A6200;
  --kin-ink: #0B0B0C;
  --kin-text: #16181D;
  --kin-muted: #5C626E;
  --kin-surface: #FFFFFF;
  --kin-surface-2: #F6F7F9;
  --kin-border: #E1E4EA;
  --kin-danger: #B3261E;
  --kin-danger-soft: #FCEDEC;
  --kin-warn: #8A5A00;
  --kin-warn-soft: #FFF6E3;
  --kin-ok: #1B6B3A;
  --kin-ok-soft: #EAF6EE;
  --kin-info-soft: #EDF2FB;
  --kin-radius: 12px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --kin-gold: #FFC83D;
    --kin-gold-soft: #2A2415;
    --kin-gold-deep: #FFD977;
    --kin-ink: #F3F4F6;
    --kin-text: #E8EAED;
    --kin-muted: #A2A9B6;
    --kin-surface: #16181D;
    --kin-surface-2: #1D2026;
    --kin-border: #2E323B;
    --kin-danger: #F2B8B5;
    --kin-danger-soft: #3B2220;
    --kin-warn: #FFD08A;
    --kin-warn-soft: #332814;
    --kin-ok: #9BE3B4;
    --kin-ok-soft: #16301F;
    --kin-info-soft: #1B2231;
  }
}

/* ---------------------------------------------------------- masthead */
.kin-masthead {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 20px; margin-bottom: 4px;
  background: linear-gradient(100deg, var(--kin-ink) 0%, #1F2024 55%, #2A2206 100%);
  border-radius: var(--kin-radius);
  border: 1px solid rgba(246,182,28,.35);
}
.kin-mark {
  width: 40px; height: 40px; flex: 0 0 40px;
  display: grid; place-items: center;
  border-radius: 10px; background: var(--kin-gold);
  color: #0B0B0C; font-weight: 800; font-size: 19px; letter-spacing: -.5px;
}
.kin-wordmark { display: flex; flex-direction: column; line-height: 1.25; min-width: 0; }
.kin-wordmark b { color: #FFFFFF; font-size: 20px; letter-spacing: .2px; }
.kin-wordmark span { color: #D7D9DE; font-size: 12.5px; }
.kin-masthead-tag {
  margin-left: auto; flex: 0 0 auto;
  color: var(--kin-gold); font-size: 11.5px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .09em;
  border: 1px solid rgba(246,182,28,.45); border-radius: 999px; padding: 5px 11px;
}
@media (max-width: 640px) {
  .kin-masthead { flex-wrap: wrap; }
  .kin-masthead-tag { margin-left: 0; }
}

/* ------------------------------------------------------------- cards */
.kin-card {
  background: var(--kin-surface); border: 1px solid var(--kin-border);
  border-left: 3px solid var(--kin-gold);
  border-radius: var(--kin-radius); padding: 14px 16px; margin-bottom: 10px;
}
.kin-card.is-alert   { border-left-color: var(--kin-danger); background: var(--kin-danger-soft); }
.kin-card.is-warn    { border-left-color: var(--kin-warn);   background: var(--kin-warn-soft); }
.kin-card.is-ok      { border-left-color: var(--kin-ok);     background: var(--kin-ok-soft); }
.kin-card.is-sim     { border-left-color: #7A4FBF;           background: var(--kin-info-soft);
                       border-style: dashed; }
.kin-card h4 { margin: 0 0 4px; font-size: 15.5px; color: var(--kin-text); font-weight: 650; }
.kin-card p  { margin: 2px 0; font-size: 13.5px; color: var(--kin-text); }
.kin-card .kin-sub { color: var(--kin-muted); font-size: 12.5px; }

/* ------------------------------------------------------------ badges */
.kin-badge {
  display: inline-block; font-size: 11px; font-weight: 650;
  letter-spacing: .04em; text-transform: uppercase;
  padding: 3px 9px; border-radius: 999px; margin: 2px 5px 2px 0;
  border: 1px solid transparent; white-space: nowrap;
}
.kin-badge.live      { background: var(--kin-ok-soft);     color: var(--kin-ok);     border-color: currentColor; }
.kin-badge.sim       { background: #EDE7F8;                color: #5B3A9E;           border-color: currentColor; }
.kin-badge.estimate  { background: var(--kin-warn-soft);   color: var(--kin-warn);   border-color: currentColor; }
.kin-badge.blocked   { background: var(--kin-surface-2);   color: var(--kin-muted);  border-color: var(--kin-border); }
.kin-badge.neutral   { background: var(--kin-gold-soft);   color: var(--kin-gold-deep); border-color: currentColor; }
.kin-badge.danger    { background: var(--kin-danger-soft); color: var(--kin-danger); border-color: currentColor; }
@media (prefers-color-scheme: dark) {
  .kin-badge.sim { background: #2A2340; color: #C9B6F5; }
}

/* ------------------------------------------------------- stat tiles */
.kin-stats { display: flex; gap: 10px; flex-wrap: wrap; margin: 2px 0 14px; }
.kin-stat {
  flex: 1 1 130px; min-width: 120px;
  background: var(--kin-surface-2); border: 1px solid var(--kin-border);
  border-radius: var(--kin-radius); padding: 11px 13px;
}
.kin-stat .v { font-size: 23px; font-weight: 700; color: var(--kin-text); line-height: 1.1; }
.kin-stat .k {
  font-size: 11px; color: var(--kin-muted); text-transform: uppercase;
  letter-spacing: .07em; margin-top: 3px;
}
.kin-stat.accent { border-left: 3px solid var(--kin-gold); }
.kin-stat.danger { border-left: 3px solid var(--kin-danger); }

/* -------------------------------------------------------- timetable */
.kin-row {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 10px 12px; border: 1px solid var(--kin-border);
  border-radius: 10px; background: var(--kin-surface); margin-bottom: 7px;
}
.kin-row .ico { font-size: 17px; flex: 0 0 24px; text-align: center; line-height: 1.5; }
.kin-row .body { min-width: 0; flex: 1; }
.kin-row .ttl { font-weight: 620; font-size: 14.5px; color: var(--kin-text); }
.kin-row .meta { font-size: 12.5px; color: var(--kin-muted); margin-top: 1px; }
.kin-row.done .ttl { text-decoration: line-through; opacity: .62; }
.kin-row.canceled { opacity: .55; }

/* ----------------------------------------------------------- notice */
.kin-note {
  border: 1px solid var(--kin-border); border-radius: 10px;
  background: var(--kin-surface-2); padding: 10px 13px;
  font-size: 12.8px; color: var(--kin-muted); margin: 6px 0 12px;
}
.kin-note strong { color: var(--kin-text); }
.kin-sim-banner {
  border: 1px dashed #7A4FBF; background: var(--kin-info-soft);
  color: var(--kin-text); border-radius: 10px;
  padding: 11px 14px; margin: 8px 0; font-size: 13.5px;
}

/* Tighten Streamlit chrome a little without fighting the framework. */
.block-container { padding-top: 2.2rem; max-width: 1180px; }
section[data-testid="stSidebar"] { border-right: 1px solid var(--kin-border); }
div[data-testid="stSidebarUserContent"] h2 { font-size: 15px; letter-spacing: .02em; }
.stButton > button { border-radius: 9px; font-weight: 580; min-height: 40px; }

/* 2026 campus experience refresh — pure visual styling, no backend dependency */
.kin-masthead{
  background:linear-gradient(114deg,#101014 5%,#231c12 72%,#382915 100%);
  border:1px solid rgba(235,186,100,.42);
  box-shadow:0 12px 26px rgba(17,17,19,.13);
  min-height:86px;
}
.kin-mark{
  width:56px!important;height:56px!important;flex:0 0 56px!important;
  border-radius:16px!important;background:linear-gradient(140deg,#fff0c2 0%,#e8ba63 40%,#bc8c3c 100%)!important;
  color:#131313!important;font-size:22px!important;font-weight:900;letter-spacing:-2px;
  box-shadow:inset 0 1px 2px #fff8,0 5px 15px #0004;
}
.kin-dot{position:relative;display:inline-block}
.kin-dot:before{
  content:"";position:absolute;top:-4px;left:50%;transform:translateX(-50%);
  width:5px;height:5px;background:#111;border-radius:50%;
}
.kin-wordmark b{font-size:22px;letter-spacing:-.6px}
.kin-wordmark span{font-size:13px}
.kin-card,.kin-row,.kin-stat{transition:box-shadow .18s ease,transform .18s ease}
@media(hover:hover) and (prefers-reduced-motion:no-preference){
  .kin-card:hover,.kin-row:hover{box-shadow:0 8px 22px rgba(33,28,16,.09);transform:translateY(-1px)}
}
.stButton > button[kind="primary"]{
  background:linear-gradient(110deg,#e3ad50,#b9832e)!important;
  color:#111!important;border-color:#a77932!important;font-weight:740!important;
}
.stButton > button:hover{border-color:#b9832e!important}
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,rgba(255,248,229,.66),transparent 270px);
}
[data-testid="stRadio"] label[data-baseweb="radio"]{padding:5px 6px;border-radius:9px}
[data-testid="stRadio"] label[data-baseweb="radio"]:hover{background:rgba(188,148,91,.12)}
.kin-hero{
  border-radius:16px;padding:22px 24px;margin:8px 0 18px;
  background:linear-gradient(115deg,#111115 0%,#22201b 68%,#4a3418 100%);
  color:#fff;box-shadow:0 14px 26px #15100a1c;
}
.kin-eyebrow{color:#f2c36f;font-weight:750;font-size:11px;letter-spacing:.13em;text-transform:uppercase;margin-bottom:8px}
.kin-hero h2{font-size:clamp(23px,3vw,34px);line-height:1.2;letter-spacing:-.75px;margin:0 0 8px;color:#fff}
.kin-hero p{margin:0;color:#e3dfd8;font-size:14px;line-height:1.5}
.kin-journey{border:1px solid #dfc49a;border-radius:14px;padding:14px;margin-bottom:14px;background:linear-gradient(135deg,#fffaf0,#f8f3e9)}
.kin-journey strong{font-size:15px;color:#2b2318}
.kin-journey small{display:block;color:#5d5142;margin-top:4px;font-size:12px}
.kin-steps{display:flex;gap:10px;flex-wrap:wrap;padding-top:12px}
.kin-step{padding:6px 10px;border-radius:7px;border:1px solid #e1ccb0;color:#57432a;font-size:11px;font-weight:750}
@media(max-width:640px){
  .kin-masthead{padding:14px!important}
  .kin-hero{padding:18px 17px}
  .kin-journey{padding:12px}
}
@media(prefers-reduced-motion:reduce){.kin-card,.kin-row,.kin-stat{transition:none!important}}

</style>
"""


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def masthead(subtitle: str, tag: str = "Hacktoberfest proof of concept") -> str:
    return (
        '<div class="kin-masthead">'
        '<div class="kin-mark">K<span class="kin-dot">I</span>N</div>'
        f'<div class="kin-wordmark"><b>Kinetic Intelligence Network</b><span>{_esc(subtitle)}</span></div>'
        f'<div class="kin-masthead-tag">{_esc(tag)}</div>'
        '</div>'
    )


def badge(text: str, kind: str = "neutral") -> str:
    return f'<span class="kin-badge {_esc(kind)}">{_esc(text)}</span>'


def stat_tiles(items: list[tuple[str, Any, str]]) -> str:
    """items: list of (label, value, variant) where variant is '', 'accent' or 'danger'."""
    cells = "".join(
        f'<div class="kin-stat {_esc(variant)}"><div class="v">{_esc(value)}</div>'
        f'<div class="k">{_esc(label)}</div></div>'
        for label, value, variant in items
    )
    return f'<div class="kin-stats">{cells}</div>'


def card(title: str, lines: list[str], *, variant: str = "", badges: str = "") -> str:
    body = "".join(f'<p>{line}</p>' for line in lines)
    return (
        f'<div class="kin-card {_esc(variant)}">'
        f'<h4>{_esc(title)}</h4>{badges}{body}</div>'
    )


def event_row(icon: str, title: str, meta: str, *, variant: str = "", badges: str = "") -> str:
    return (
        f'<div class="kin-row {_esc(variant)}">'
        f'<div class="ico">{_esc(icon)}</div>'
        f'<div class="body"><div class="ttl">{_esc(title)}</div>'
        f'<div class="meta">{_esc(meta)}</div>{badges}</div></div>'
    )


def note(text_html: str) -> str:
    return f'<div class="kin-note">{text_html}</div>'


def simulation_banner(text: str) -> str:
    return f'<div class="kin-sim-banner"><b>SIMULATION ACTIVE</b> — {_esc(text)}</div>'
