#!/usr/bin/env python3
"""patch_scanner_mobile_toolbar.py -- make the scanner toolbar survive a phone screen.

The search row was a single no-wrap flex line holding the input, the ? button, the Cards/Images
toggle and Clear all, and the file carried no media queries at all. On a narrow screen the input
collapsed and the buttons ran off the edge.

Now:
- Row 1: search input (with min-width:0 so it can actually shrink) and the ? button.
- Row 2: the result count on the left, Cards/Images and Reset on the right.
- Both rows wrap, so nothing can overflow the viewport again.
- "Clear all" reads "Reset".
- The lower results-bar is removed: it repeated the same count a third time. Its
  distinctDisplay/copiesExtra nodes move into the row 2 count, hidden, so render() keeps working
  without a JS change.
- One media query under 560px tightens button padding.

Exact-string replacements; each must match exactly once. Verify with:
    node tools/test_scanner.mjs .

Usage: python3 tools/patch_scanner_mobile_toolbar.py [path/to/cards.html]
"""

import sys

EDITS = [
(
""".search-row{display:flex;gap:0.75rem;align-items:center;margin-bottom:1.25rem;}""",
""".search-row{display:flex;flex-wrap:wrap;gap:0.75rem;align-items:center;margin-bottom:0.6rem;}"""
),
(
""".search-box{flex:1;background:var(--bg2);""",
""".search-box{flex:1 1 12rem;min-width:0;background:var(--bg2);"""
),
(
""".search-count-row{margin:-0.85rem 0 1.1rem;padding:0 0.2rem;}""",
""".search-count-row{display:flex;flex-wrap:wrap;align-items:center;gap:0.6rem;margin:0 0 1.1rem;padding:0 0.2rem;}
.search-count-row .view-toggle{margin-left:auto;}
@media (max-width:560px){
  .vtoggle,.clear-btn{padding:0.3rem 0.5rem;letter-spacing:0.06em;}
  .search-count-row{gap:0.4rem;}
  .search-count-row .view-toggle{margin-left:0;}
}"""
),
(
"""    <div class="view-toggle">
      <button class="vtoggle active" id="btnPill" onclick="setView('pill')">Cards</button>
      <button class="vtoggle" id="btnImg" onclick="setView('image')">Images</button>
    </div>
    <button class="clear-btn" onclick="clearAll()">Clear all</button>
  </div>

  <div class="search-count-row"><span class="search-count" id="searchCount"></span></div>""",
"""  </div>

  <div class="search-count-row">
    <span class="search-count" id="searchCount"></span>
    <div class="view-toggle">
      <button class="vtoggle active" id="btnPill" onclick="setView('pill')">Cards</button>
      <button class="vtoggle" id="btnImg" onclick="setView('image')">Images</button>
    </div>
    <button class="clear-btn" onclick="clearAll()">Reset</button>
  </div>"""
),
(
"""<div class="results-bar">
  <div class="result-count"><span id="distinctDisplay">0</span> distinct cards<span id="copiesExtra"></span></div>
</div>""",
"""<div class="results-bar" hidden>
  <div class="result-count"><span id="distinctDisplay">0</span> distinct cards<span id="copiesExtra"></span></div>
</div>"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "flex:1 1 12rem" in src:
        print("already patched; nothing to do")
        return 0
    for old, new in EDITS:
        n = src.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for block starting {old.splitlines()[0][:60]!r}",
                  file=sys.stderr)
            return 1
        src = src.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(src)
    print(f"patched {path}: {len(EDITS)} exact-string replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
