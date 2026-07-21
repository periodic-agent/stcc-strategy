#!/usr/bin/env python3
"""ST:CC Compendium guide verifier (v2 — canonical text scheme).

Machine-checks a built guide against its canonical text file. The canonical
file (text/<slug>.txt) is the APPROVED wording of the page: the verbatim
import plus every correction Periodic_agent has explicitly approved. Any
model (or human) edit that alters, adds, or removes page text without a
matching approved update to the canonical file fails here.

Usage:
    python3 verify_guide.py <guide.html> <canonical.txt> [--img-root DIR]

(--config is accepted and ignored, for compatibility with old invocations.)

Checks:
  1. Canonical fidelity: the guide's extracted text (via extract_text.py,
     the same extractor that generated the canonical file) matches the
     canonical file EXACTLY — line for line, in order. Alterations,
     insertions, deletions, and reorderings all fail.
  2. Every img src resolves to a file under --img-root (default: guide's dir).
  3. Every TOC/back-top anchor resolves to an id.
  4. Tag balance (well-formed HTML).
  5. Required furniture: WizKids credit, McCue attribution, lightbox,
     GoatCounter, stylesheet, top+bottom nav bars.

Exit 0 = pass, 1 = fail. Stdlib only.
"""

import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_text import canonical_lines, _plain  # noqa: E402

VOID = {"img", "br", "meta", "link", "input", "hr", "source"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errs = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errs.append("mismatched </%s> near %s" % (tag, self.stack[-3:]))


def main():
    argv, args = sys.argv[1:], []
    img_root = None
    i = 0
    while i < len(argv):
        if argv[i] == "--config":          # legacy, ignored
            i += 2
        elif argv[i] == "--img-root":
            img_root = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 2:
        sys.exit(__doc__)
    guide_path, text_path = args
    if img_root is None:
        img_root = os.path.dirname(os.path.abspath(guide_path))

    guide = open(guide_path, encoding="utf-8").read()
    failures = []

    # 1. canonical fidelity — exact, ordered, both directions
    got = canonical_lines(guide)
    want = [_plain(l.strip()) for l in
            open(text_path, encoding="utf-8").read().split("\n") if l.strip()]
    if got != want:
        n = min(len(got), len(want))
        diff_at = next((j for j in range(n) if got[j] != want[j]), n)
        failures.append("CANONICAL mismatch at line %d:" % (diff_at + 1))
        failures.append("  canonical: %s" %
                        (want[diff_at][:100] if diff_at < len(want) else "<end of file>"))
        failures.append("  guide:     %s" %
                        (got[diff_at][:100] if diff_at < len(got) else "<end of page>"))
        if len(got) != len(want):
            failures.append("  line count: canonical %d vs guide %d" % (len(want), len(got)))

    # 2. image refs
    for src in re.findall(r'src="(img/[^"]+)"', guide):
        if not os.path.exists(os.path.join(img_root, src)):
            failures.append("IMAGE missing: %s (root %s)" % (src, img_root))

    # 3. anchors
    ids = set(re.findall(r'id="([\w-]+)"', guide))
    ids.add("top")  # browsers scroll #top natively, no id required
    for href in set(re.findall(r'href="#([\w-]+)"', guide)):
        if href not in ids:
            failures.append("ANCHOR #%s has no matching id" % href)

    # 4. balance
    p = Balance()
    p.feed(guide)
    for e in p.errs[:5]:
        failures.append("HTML " + e)
    if p.stack:
        failures.append("HTML unclosed tags: %s" % p.stack)

    # 5. furniture
    furniture = {
        "McCue attribution": "Matthew McCue (mdmccu2)",
        "lightbox": 'id="lightbox"',
        "GoatCounter": "stcc-compendium.goatcounter.com",
        "stylesheet": "css/stcc.css",
    }
    for name, needle in furniture.items():
        if needle not in guide:
            failures.append("FURNITURE missing: %s" % name)
    if not re.search(r"Card images (&copy;|©) WizKids", guide):
        failures.append("FURNITURE missing: WizKids credit")
    if guide.count("Back to Compendium") < 2:
        failures.append("FURNITURE: need Back to Compendium top and bottom")

    if failures:
        print("FAIL (%d):" % len(failures))
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("PASS: canonical text intact (%d lines), %d image refs OK, anchors OK, "
          "HTML balanced, furniture OK"
          % (len(want), len(re.findall(r'src="img/', guide))))


if __name__ == "__main__":
    main()
