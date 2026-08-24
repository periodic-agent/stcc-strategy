#!/usr/bin/env python3
"""patch_scanner_toolbar_order.py -- controls left, count right.

Row 2 read: count, then Images / Text / Reset pushed to the right. The controls now lead the
row, sitting directly under the search box they belong to, and the count trails on the right
where it reads as output rather than a label.

Order is set in the markup, and the auto margin moves from the toggle to the count. Under 560px
the row still wraps, and the count is the piece that drops to a second line.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_toolbar_order.py [path/to/cards.html]
"""

import sys

EDITS = [
(
"""  <div class="search-count-row">
    <span class="search-count" id="searchCount"></span>
    <div class="view-toggle">
      <button class="vtoggle" id="btnPill" onclick="setView('pill')">Text</button>
      <button class="vtoggle active" id="btnImg" onclick="setView('image')">Images</button>
    </div>
    <button class="clear-btn" onclick="clearAll()">Reset</button>
  </div>""",
"""  <div class="search-count-row">
    <div class="view-toggle">
      <button class="vtoggle active" id="btnImg" onclick="setView('image')">Images</button>
      <button class="vtoggle" id="btnPill" onclick="setView('pill')">Text</button>
    </div>
    <button class="clear-btn" onclick="clearAll()">Reset</button>
    <span class="search-count" id="searchCount"></span>
  </div>"""
),
(
""".search-count-row .view-toggle{margin-left:auto;}""",
""".search-count-row .search-count{margin-left:auto;}"""
),
(
"""  .search-count-row .view-toggle{margin-left:0;}""",
"""  .search-count-row .search-count{margin-left:0;}"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if ".search-count-row .search-count{margin-left:auto;}" in src:
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
