#!/usr/bin/env python3
"""Canonical text extractor for ST:CC Compendium guides.

Extracts the normalized text content of a guide's <main> block. The output
is the guide's CANONICAL TEXT: the approved wording of everything the page
says. One line per block-level element, whitespace-collapsed, curly quotes
straightened.

This module is the single source of truth for extraction. Both the build
pipeline (writing text/<slug>.txt) and verify_guide.py (comparing the built
page against it) import canonical_lines() from here, so the comparison can
never drift from the generation.

Usage:
    python3 extract_text.py <guide.html> [-o out.txt]

Stdlib only.
"""

import html as htmllib
import re
import sys

BLOCK_SPLIT = re.compile(
    r"</(?:p|h1|h2|h3|h4|li|div|figcaption|caption|td|th|blockquote)>|<br\s*/?>",
    re.I)


def _plain(t):
    return (t.replace("’", "'").replace("‘", "'")
             .replace("“", '"').replace("”", '"'))


def canonical_lines(page_html):
    """Return the canonical text of a guide page as a list of lines."""
    main = page_html.split('<main class="content">', 1)[-1].split("<footer", 1)[0]
    lines = []
    for block in BLOCK_SPLIT.split(main):
        text = htmllib.unescape(re.sub(r"<[^>]+>", " ", block))
        text = _plain(re.sub(r"\s+", " ", text).strip())
        if text:
            lines.append(text)
    return lines


def main():
    args = sys.argv[1:]
    out = None
    if "-o" in args:
        i = args.index("-o")
        out = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1:
        sys.exit(__doc__)
    lines = canonical_lines(open(args[0], encoding="utf-8").read())
    payload = "\n".join(lines) + "\n"
    if out:
        open(out, "w", encoding="utf-8", newline="\n").write(payload)
        print("%s: %d lines" % (out, len(lines)))
    else:
        sys.stdout.write(payload)


if __name__ == "__main__":
    main()
