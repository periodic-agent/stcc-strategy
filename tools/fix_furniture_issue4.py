#!/usr/bin/env python3
"""One-off fixer for ISSUES.md Issue 4 (furniture gaps, Jul 2026).

- Normalizes the variant top nav (<nav> + "ST:CC Compendium") to the
  documented snippet (<div id="top" class="nav-bar"> + "Back to Compendium")
  on four guides.
- Adds the missing bottom nav bar before <footer> on six guides.
- Closes the unclosed <footer> on tbg-locations.
- Regenerates text/<slug>.txt for every edited guide (the bottom nav text
  sits inside the canonical window).

Run from repo root: python3 tools/fix_furniture_issue4.py
Ships in tools/ per WORKFLOW Rule 7.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_text import canonical_lines

TOP_VARIANT = re.compile(
    r'<nav class="nav-bar">\s*<a href="index\.html">&#8592; ST:CC Compendium</a>\s*</nav>')
TOP_CANON = '<div id="top" class="nav-bar"><a href="index.html">← Back to Compendium</a></div>'
BOTTOM = '<div class="nav-bar"><a href="index.html">← Back to Compendium</a></div>\n\n'

NORMALIZE_TOP = ["sc-market-locations-rewards", "tbg-allies",
                 "tbg-encounters-incidents", "tbg-ships"]
ADD_BOTTOM = ["combining-markets", "promo-pack-2", "sc-market-locations-rewards",
              "tbg-allies", "tbg-encounters-incidents", "tbg-ships"]
CLOSE_FOOTER = ["tbg-locations"]


def edit(slug):
    path = slug + ".html"
    html = open(path, encoding="utf-8").read()
    orig = html
    if slug in NORMALIZE_TOP:
        html, n = TOP_VARIANT.subn(TOP_CANON, html, count=1)
        if n != 1:
            sys.exit("%s: top nav variant not found — aborting, nothing written" % slug)
    if slug in ADD_BOTTOM:
        if html.count("Back to Compendium") >= 2:
            sys.exit("%s: already has two nav bars — aborting" % slug)
        i = html.find("<footer")
        if i < 0:
            sys.exit("%s: no <footer> — aborting" % slug)
        html = html[:i] + BOTTOM + html[i:]
    if slug in CLOSE_FOOTER:
        needle = "Card images &copy; WizKids.\n<script>"
        if needle not in html:
            sys.exit("%s: footer-close anchor not found — aborting" % slug)
        html = html.replace(needle, "Card images &copy; WizKids.\n</footer>\n<script>", 1)
    if html != orig:
        open(path, "w", encoding="utf-8", newline="\n").write(html)
        open(os.path.join("text", slug + ".txt"), "w", encoding="utf-8", newline="\n").write(
            "\n".join(canonical_lines(html)) + "\n")
        print("fixed:", slug)


def main():
    for slug in sorted(set(NORMALIZE_TOP + ADD_BOTTOM + CLOSE_FOOTER)):
        edit(slug)
    print("done — re-run verify_guide.py across all guides")


if __name__ == "__main__":
    main()
