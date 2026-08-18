#!/usr/bin/env python3
"""patch_scanner_trait_pill_colors.py -- trait pills on the card face use the site palette.

The vertical trait pills took their colours from the card scans and were then dimmed a step so
white uppercase text would sit on them: species #e2a04a, regular #79b3c7, other #c85340. The
scans are heavily muted, so the pills read as washed out next to the filter chips that name the
same three families.

They now use the palette the filter chips use (species #e09050, regular #4a9fd4, other #e05a5a)
with dark ink instead of white. Contrast against #14161c is 7.1, 6.2 and 5.0, all better than
the white-on-muted they replace, and it matches how an active filter chip already renders: the
family colour filled, near-black label.

Wildcard keeps its pale salmon, which was never sampled from a scan.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_trait_pill_colors.py [path/to/cards.html]
"""

import sys

EDITS = [
(
""".vt-species{background:#e2a04a;}
.vt-regular{background:#79b3c7;}
.vt-other{background:#c85340;}""",
"""/* Site palette, not the scans: the printed cards are far too muted to sample.
   Dark ink because these fills are bright enough that white would be the weaker pair. */
.vt-species{background:#e09050;color:#14161c;}
.vt-regular{background:#4a9fd4;color:#14161c;}
.vt-other{background:#e05a5a;color:#14161c;}"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if ".vt-species{background:#e09050" in src:
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
    print(f"patched {path}: {len(EDITS)} exact-string replacement(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
