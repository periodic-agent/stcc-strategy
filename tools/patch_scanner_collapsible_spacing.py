#!/usr/bin/env python3
"""patch_scanner_collapsible_spacing.py -- close the gap under collapsible filter labels.

Box, Deck and Suit put their pills 0.5rem under the label (the .filter-label bottom margin).
The collapsible sections (Species / Regular / Other traits, Skills, Focus) stacked three gaps
instead: the same label margin, the header's own bottom padding, and the body's top padding,
about 1.2rem in total. They now match the non-collapsible rows exactly.

Exact-string replacements; each must match exactly once.

Usage: python3 tools/patch_scanner_collapsible_spacing.py [path/to/cards.html]
"""

import sys

EDITS = [
(
""".collapsible-header{display:flex;align-items:center;justify-content:space-between;cursor:pointer;padding:0.3rem 0;user-select:none;}""",
""".collapsible-header{display:flex;align-items:center;justify-content:space-between;cursor:pointer;padding:0.3rem 0 0;user-select:none;}
.collapsible-header .filter-label{margin-bottom:0;}"""
),
(
""".collapsible-body{display:none;padding-top:0.4rem;}""",
""".collapsible-body{display:none;padding-top:0.5rem;}"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if ".collapsible-header .filter-label" in src:
        print("already patched; nothing to do")
        return 0
    out = src
    for old, new in EDITS:
        n = out.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for {old[:50]!r}", file=sys.stderr)
            return 1
        out = out.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(out)
    print(f"patched {path}: {len(EDITS)} exact-string replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
