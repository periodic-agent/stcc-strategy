#!/usr/bin/env python3
"""patch_scanner_banner_badge.py -- show a real Strategy badge inside the header banner.

The banner said "Look for the Strategy tag" in plain text. It now says "Look for the
[Strategy] badge", where [Strategy] is an actual `.card-badge.strategy` chip, identical to the
one the cards carry, so the reader recognises the thing they are being sent to look for.

The badge in a card sits above the trait rows and carries `margin-bottom:0.4rem`; inline in a
banner that margin pushes the text off-centre, so one rule zeroes it in that context only.

Exact-string replacements; each must match exactly once. Verify with:
    node tools/test_scanner.mjs .

Usage: python3 tools/patch_scanner_banner_badge.py [path/to/card-browser-mockup.html]
"""

import sys

EDITS = [
(
""".card-badge + .card-badge{margin-left:0.3rem;}""",
""".card-badge + .card-badge{margin-left:0.3rem;}
.new-banner .card-badge{margin-bottom:0;}"""
),
(
"""  <a class="new-banner" onclick="showStrategy(event)" title="Cards discussed in the guides carry a Strategy tag"><span class="new-badge">New</span><span>Card search now links to the guides! Look for the Strategy tag</span><span class="new-arrow">→</span></a>""",
"""  <a class="new-banner" onclick="showStrategy(event)" title="Cards discussed in the guides carry a Strategy badge"><span class="new-badge">New</span><span>Card search now links to the guides! Look for the <span class="card-badge strategy">Strategy</span> badge</span><span class="new-arrow">→</span></a>"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "card-browser-mockup.html"
    src = open(path, encoding="utf-8").read()
    if '.new-banner .card-badge' in src:
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
