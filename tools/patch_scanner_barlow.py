#!/usr/bin/env python3
"""patch_scanner_barlow.py -- actually load Barlow Condensed, and use it for the deck counts.

The strip bodies and everything on `--card-font` have been asking for Barlow Condensed since
the card-face rebuild, but the font was never added to the Google Fonts request, so every one of
them silently fell back to the system sans. Adding it changes the look of the card text across
the whole scanner: that is the intended card typography, finally arriving.

The deck-group count moves to the same face. It inherited Orbitron at 0.55rem with 0.2em
tracking, where "(8" reads as "18": Orbitron's 1 is a bare stroke and its parentheses are
shallow arcs. Barlow Condensed at 0.72rem with normal tracking is both larger and unambiguous,
and it still sits quietly next to the Orbitron label.

Weights requested: 400 and 500. 500 is what the strips use; 400 covers the counts.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_barlow.py [path/to/cards.html]
"""

import sys

EDITS = [
(
"""<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;400;600&family=Antonio:wght@600&display=swap" rel="stylesheet">""",
"""<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;400;600&family=Antonio:wght@600&family=Barlow+Condensed:wght@400;500;600&display=swap" rel="stylesheet">"""
),
(
""".deck-count{color:var(--muted);font-size:0.55rem;}""",
"""/* Barlow Condensed, not the header's Orbitron: at this size Orbitron's "(8" reads as "18". */
.deck-count{color:var(--muted);font-family:var(--card-font);font-size:0.78rem;letter-spacing:0.01em;
  text-transform:none;font-variant-numeric:tabular-nums;}"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "Barlow+Condensed" in src:
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
