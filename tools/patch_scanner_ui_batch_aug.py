#!/usr/bin/env python3
"""patch_scanner_ui_batch_aug.py -- small UI batch on cards.html.

1. Deck filter label reads "Market and Crew decks".
2. Hero header shrinks: the "ST:CC Strategy Compendium" label line is dropped, the meta line
   describes what the tools actually do now, and the block's padding tightens to suit the
   smaller content.
3. The orphaned New-banner rules go: the markup was removed deliberately in the card-face pass
   and only its CSS was left behind.

Content is built in memory and written once, so a failed patch cannot truncate the scanner.
Exact-string replacements; each must match exactly once.

Usage: python3 tools/patch_scanner_ui_batch_aug.py [path/to/cards.html]
"""

import sys

EDITS = [
# 1 -- deck label
(
"""    <div class="filter-label">Deck</div>""",
"""    <div class="filter-label">Market and Crew decks</div>"""
),
# 2 -- hero header markup
(
"""<header class="chapter-header">
  <div class="chapter-label">ST:CC Strategy Compendium</div>
  <h1 class="chapter-title"><span>Card</span> Scanner</h1>
  <div class="chapter-meta">Select boxes, filter by trait or skill, search by name. Show details or images.</div>
  
</header>""",
"""<header class="chapter-header">
  <h1 class="chapter-title"><span>Card</span> Scanner</h1>
  <div class="chapter-meta">Select boxes, filter by suit, trait, or skill, search by name, starting position.</div>
</header>"""
),
# 2b -- header padding, now that a line is gone
(
""".chapter-header{background:linear-gradient(135deg,#160820 0%,#2a1035 50%,#160820 100%);border-bottom:2px solid var(--scanner);padding:2.5rem 2rem 2rem;text-align:center;position:relative;overflow:hidden;}""",
""".chapter-header{background:linear-gradient(135deg,#160820 0%,#2a1035 50%,#160820 100%);border-bottom:2px solid var(--scanner);padding:1.2rem 2rem 1rem;text-align:center;position:relative;overflow:hidden;}"""
),
(
""".chapter-meta{margin-top:0.6rem;font-size:0.78rem;color:var(--muted);}""",
""".chapter-meta{margin-top:0.4rem;font-size:0.78rem;color:var(--muted);}"""
),
# 3 -- orphaned banner CSS
(
""".new-banner{display:inline-flex;align-items:center;gap:0.55rem;margin-top:1rem;padding:0.28rem 0.75rem 0.28rem 0.32rem;background:rgba(94,200,200,0.07);border:1px solid rgba(94,200,200,0.35);border-radius:999px;font-family:'Exo 2',sans-serif;font-size:0.8rem;color:var(--text);text-decoration:none;cursor:pointer;transition:border-color .2s,background .2s,transform .2s;}
.new-banner:hover{border-color:rgba(111,211,211,0.75);background:rgba(94,200,200,0.14);transform:translateY(-1px);}
.new-badge{font-family:'Orbitron',sans-serif;font-size:0.58rem;font-weight:700;letter-spacing:0.14em;color:#fff;text-transform:uppercase;padding:0.22rem 0.5rem;border-radius:999px;background:linear-gradient(135deg,#f0902e,#d44a4a);box-shadow:0 0 12px rgba(240,144,46,0.45);}
.new-banner .new-arrow{color:var(--muted);font-size:0.85rem;transition:transform .2s;}
.new-banner:hover .new-arrow{transform:translateX(3px);}
""",
""""""
),
(
""".new-banner .card-badge{margin-bottom:0;}
""",
""""""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "Market and Crew decks" in src:
        print("already patched; nothing to do")
        return 0
    out = src
    for old, new in EDITS:
        n = out.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for {old.splitlines()[0][:60]!r}", file=sys.stderr)
            return 1
        out = out.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(out)
    print(f"patched {path}: {len(EDITS)} exact-string replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
