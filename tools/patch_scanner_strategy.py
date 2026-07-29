#!/usr/bin/env python3
"""
patch_scanner_strategy.py -- ST:CC Compendium

Adds the Strategy badge and the guide-passage drawer to card-browser-mockup.html.

Behaviour added:
  - Cards McCue discusses get a teal `Strategy` badge in the Cards view,
    alongside the existing Update / Duplicate badges.
  - The whole pill is the click target on those cards. Cards with no badge
    are not clickable, so a click never returns an empty drawer.
  - The drawer spans the full grid row (grid-column:1/-1), so opening one
    never reflows the cards sideways.
  - data/strategy-cards.json (8 KB) loads at start-up and drives the badge.
    data/strategy-index.json (550 KB) loads only when the first drawer opens.

Idempotent: running it twice is a no-op. Every anchor is asserted, so a
future scanner refactor makes this fail loudly instead of silently skipping.

Usage:
    python tools/patch_scanner_strategy.py [--repo .] [--file card-browser-mockup.html]
    python tools/patch_scanner_strategy.py --check    # exit 1 if not patched
"""

import argparse
import os
import sys

MARK = "/* --- strategy index: badge + drawer --- */"

CSS = MARK + """
.card-badge.strategy{background:rgba(94,200,200,0.14);color:#6fd3d3;border-color:rgba(94,200,200,0.45);}
.card-badge + .card-badge{margin-left:0.3rem;}
.card-entry.has-strategy{cursor:pointer;}
.card-entry.has-strategy:hover{border-color:rgba(94,200,200,0.55);}
.card-entry.drawer-open{border-color:#5ec8c8;box-shadow:0 0 0 1px rgba(94,200,200,0.35);}
.strategy-drawer{grid-column:1/-1;background:rgba(94,200,200,0.05);border:1px solid rgba(94,200,200,0.3);border-radius:4px;padding:1rem 1.1rem;margin:-0.2rem 0 0.4rem;}
.strategy-drawer-head{font-family:'Orbitron',sans-serif;font-size:0.68rem;letter-spacing:0.14em;text-transform:uppercase;color:#6fd3d3;margin-bottom:0.75rem;display:flex;justify-content:space-between;align-items:center;gap:0.6rem;}
.strategy-drawer-close{cursor:pointer;color:#7a8aaa;font-size:1.2rem;line-height:1;padding:0 0.3rem;}
.strategy-drawer-close:hover{color:#6fd3d3;}
.sd-guide{margin-bottom:1rem;}
.sd-guide:last-of-type{margin-bottom:0;}
.sd-guide-title{font-family:'Orbitron',sans-serif;font-size:0.72rem;letter-spacing:0.08em;color:#7ec8f0;text-decoration:none;display:inline-block;margin-bottom:0.15rem;}
.sd-guide-title:hover{color:#a8ddff;}
.sd-section{font-size:0.68rem;color:#7a8aaa;letter-spacing:0.05em;margin-bottom:0.4rem;}
.sd-snippet{font-size:0.85rem;line-height:1.65;color:#ccd6f0;border-left:2px solid rgba(94,200,200,0.35);padding-left:0.8rem;margin-bottom:0.55rem;}
.sd-snippet.truncated::after{content:' \\2026';color:#7a8aaa;}
.sd-more{font-size:0.72rem;color:#7a8aaa;}
.sd-more a{color:#7ec8f0;text-decoration:none;}
.sd-loading{font-size:0.8rem;color:#7a8aaa;}
.sd-attrib{margin-top:0.9rem;padding-top:0.6rem;border-top:1px solid rgba(122,138,170,0.2);font-size:0.66rem;color:#7a8aaa;letter-spacing:0.03em;}
"""

STATE = """
// --- strategy index -------------------------------------------------------
// STRATEGY_COUNTS is card_id -> mention count, from the 8 KB companion file.
// The 550 KB index with the actual passages is fetched only once a drawer is
// opened; loading it up front would be a real cost on mobile.
let STRATEGY_COUNTS = {};
let STRATEGY_INDEX  = null;
let STRATEGY_GUIDES = {};
let openStrategyId  = null;
"""

LOADER = """
// Badge data. A missing file is not fatal: the scanner just shows no badges.
async function loadStrategyCounts(){
  try{
    const r = await fetch('data/strategy-cards.json', {cache:'no-store'});
    if(r.ok){ STRATEGY_COUNTS = (await r.json()).cards || {}; }
  }catch(e){ console.warn('Could not load strategy-cards.json', e); }
}

async function ensureStrategyIndex(){
  if(STRATEGY_INDEX) return true;
  try{
    const r = await fetch('data/strategy-index.json', {cache:'no-store'});
    if(!r.ok) return false;
    const j = await r.json();
    STRATEGY_INDEX = j.cards || {};
    STRATEGY_GUIDES = j.guides || {};
    return true;
  }catch(e){ console.warn('Could not load strategy-index.json', e); return false; }
}

function hasStrategy(c){ return Object.prototype.hasOwnProperty.call(STRATEGY_COUNTS, c.id); }

async function toggleStrategy(id){
  openStrategyId = (openStrategyId === id) ? null : id;
  if(openStrategyId) await ensureStrategyIndex();
  render();
}

function sdEscape(s){
  return String(s).replace(/[&<>"]/g, ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
}

function buildStrategyDrawer(c){
  const el = document.createElement('div');
  el.className = 'strategy-drawer';
  const entries = (STRATEGY_INDEX && STRATEGY_INDEX[c.id]) || null;
  let html = '<div class="strategy-drawer-head"><span>' + sdEscape(c.name)
           + ' in the guides</span><span class="strategy-drawer-close">&times;</span></div>';
  if(!entries){
    html += '<div class="sd-loading">Loading passages\\u2026</div>';
  } else {
    entries.forEach(e=>{
      const meta = STRATEGY_GUIDES[e.guide] || {title:e.guide};
      const anchor = e.hits[0] && e.hits[0].anchor ? '#' + e.hits[0].anchor : '';
      html += '<div class="sd-guide">';
      html += '<a class="sd-guide-title" href="' + e.guide + anchor + '">'
            + sdEscape(meta.title) + ' \\u2192</a>';
      if(e.hits[0] && e.hits[0].heading){
        html += '<div class="sd-section">' + sdEscape(e.hits[0].heading) + '</div>';
      }
      e.hits.forEach(h=>{
        html += '<div class="sd-snippet' + (h.truncated ? ' truncated' : '') + '">'
              + sdEscape(h.snippet) + '</div>';
      });
      const extra = e.count - e.hits.length;
      if(extra > 0){
        html += '<div class="sd-more">and ' + extra + ' more mention' + (extra>1?'s':'')
              + ' in this guide \\u00b7 <a href="' + e.guide + '">open the guide</a></div>';
      }
      html += '</div>';
    });
    html += '<div class="sd-attrib">Content by Matthew McCue (mdmccu2) \\u00b7 quoted verbatim</div>';
  }
  el.innerHTML = html;
  const x = el.querySelector('.strategy-drawer-close');
  if(x) x.onclick = ev=>{ ev.stopPropagation(); openStrategyId = null; render(); };
  return el;
}
"""

EDITS = [
    # 1. CSS, right after the existing badge rules.
    (".card-badge.duplicate{background:rgba(140,150,170,0.12);color:#9aa4b8;border-color:rgba(140,150,170,0.35);}",
     ".card-badge.duplicate{background:rgba(140,150,170,0.12);color:#9aa4b8;border-color:rgba(140,150,170,0.35);}\n"
     + CSS),

    # 2. State, next to the other module-level scanner state.
    ("let viewMode     = \"pill\";",
     "let viewMode     = \"pill\";" + STATE),

    # 3. Fetch the badge file alongside the box JSON.
    ("  buildFullPool();\n}",
     "  await loadStrategyCounts();\n  buildFullPool();\n}\n" + LOADER),

    # 4. Badge + click target on the pill.
    ("""  const badge=badgeInfo(c);
  const badgeHTML = badge ? '<div class="card-badge '+badge.cls+'">'+badge.text+'</div>' : '';
  el.innerHTML='<div class="card-suit-bar">""",
     """  const badge=badgeInfo(c);
  const badgeHTML = badge ? '<div class="card-badge '+badge.cls+'">'+badge.text+'</div>' : '';
  // Strategy badge is additive: a card can be both a Duplicate and discussed.
  const strat = hasStrategy(c);
  if(strat){ el.classList.add('has-strategy'); el.onclick=()=>toggleStrategy(c.id); }
  if(openStrategyId===c.id) el.classList.add('drawer-open');
  const stratHTML = strat ? '<div class="card-badge strategy">Strategy</div>' : '';
  el.innerHTML='<div class="card-suit-bar">"""),

    ("""    +badgeHTML
    +(tagsHTML?'<div class="card-tags">'""",
     """    +badgeHTML+stratHTML
    +(tagsHTML?'<div class="card-tags">'"""),

    # 5. Drawer emitted into the grid, directly after its own pill.
    ("""      grid.appendChild(viewMode==='pill'?buildPillCard(c):buildImgCard(c));""",
     """      grid.appendChild(viewMode==='pill'?buildPillCard(c):buildImgCard(c));
      // Full-width row drawer: grid-column:1/-1 keeps the grid from reflowing.
      if(viewMode==='pill' && openStrategyId===c.id) grid.appendChild(buildStrategyDrawer(c));"""),
]

EDITS_ESC = (
    "document.addEventListener('keydown',e=>{",
    "document.addEventListener('keydown',e=>{\n"
    "  if(e.key==='Escape' && openStrategyId){ openStrategyId=null; render(); return; }",
)


EDITS.append(EDITS_ESC)


def apply(html):
    for old, new in EDITS:
        if new in html:
            continue
        if old not in html:
            raise SystemExit("patch_scanner_strategy: anchor not found:\n  %s..." % old[:90])
        if html.count(old) != 1:
            raise SystemExit("patch_scanner_strategy: anchor not unique:\n  %s..." % old[:90])
        html = html.replace(old, new, 1)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--file", default="cards.html")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    src = os.path.join(args.repo, args.file)
    with open(src, encoding="utf-8") as fh:
        html = fh.read()

    if args.check:
        print("patched" if MARK in html else "NOT patched")
        return 0 if MARK in html else 1

    if MARK in html:
        print("already patched, nothing to do")
        return 0

    patched = apply(html)          # may raise; must happen before any open(..., "w")
    out = args.out or src
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(patched)
    print("patched %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
