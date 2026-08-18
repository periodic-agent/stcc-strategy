#!/usr/bin/env python3
"""patch_scanner_palette_align.py -- one trait palette for chips and card faces.

The filter chips still carried the scan-sampled trio (#e2a04a, #79b3c7, #c85340), which only
read as vivid because a chip at rest is an outline. Filled, on an active chip or on a card, the
same values look washed out. Both now use the site palette, so a family is the same colour
wherever it appears:

    species  #e09050    regular  #4a9fd4    other  #e05a5a

An active chip fills with that colour, so its label switches from white to #14161c for the
three families, matching the card-face pills. Wildcard is unchanged: pale fill, dark label.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_palette_align.py [path/to/cards.html]
"""

import sys

EDITS = [
(
""".cp-species{--cc:#e2a04a;}
.cp-regular{--cc:#79b3c7;}
.cp-other{--cc:#c85340;}""",
"""/* Same palette as the card-face pills; see .vt-species and friends. */
.cp-species{--cc:#e09050;}
.cp-regular{--cc:#4a9fd4;}
.cp-other{--cc:#e05a5a;}
/* Filled, these three are bright enough that near-black beats white. */
.cp-species.active,.cp-regular.active,.cp-other.active{color:#14161c !important;}"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if ".cp-species{--cc:#e09050;}" in src:
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
