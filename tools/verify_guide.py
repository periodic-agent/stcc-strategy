#!/usr/bin/env python3
"""ST:CC Compendium guide verifier.

Machine-checks a built guide against the verbatim source text. Any model
(or human) edit that drops or alters McCue's prose fails here.

Usage:
    python3 verify_guide.py <guide.html> <marked_text.txt> [--config cfg.json] [--img-root DIR]

Checks:
  1. Verbatim fidelity: every source line (minus configured cuts) appears
     unaltered in the guide text.
  2. Every img src resolves to a file under --img-root (default: guide's dir).
  3. Every TOC/back-top anchor resolves to an id.
  4. Tag balance (well-formed HTML).
  5. Required furniture: WizKids credit, McCue attribution, lightbox,
     GoatCounter, top+bottom nav bars.

Exit 0 = pass, 1 = fail. Stdlib only.
"""

import html as htmllib
import json
import os
import re
import sys
from html.parser import HTMLParser

VOID = {"img", "br", "meta", "link", "input", "hr", "source"}


def norm(t):
    t = re.sub(r"\[\[A:[^\]]+\]\]", " ", t)
    t = re.sub(r"\[\[/?(B|I|H2|H3|A)\]\]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def plain(t):
    return t.replace("’", "'").replace("“", '"').replace("”", '"')


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
    cfg, img_root = {}, None
    i = 0
    while i < len(argv):
        if argv[i] == "--config":
            cfg = json.load(open(argv[i + 1], encoding="utf-8"))
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
    cuts = cfg.get("cut", [])

    guide = open(guide_path, encoding="utf-8").read()
    failures, warnings = [], []

    # 1. verbatim fidelity
    main_html = guide.split('<main class="content">', 1)[-1].split("<footer", 1)[0]
    flat = htmllib.unescape(re.sub(r"<[^>]+>", " ", main_html))
    flat = re.sub(r"\s+", " ", flat)
    for i, line in enumerate(open(text_path, encoding="utf-8").read().split("\n"), 1):
        line = line.strip()
        if not line or line.startswith("[[IMG"):
            continue
        if any(plain(norm(line)).startswith(plain(norm(c))) for c in cuts if c.strip()):
            continue
        for a, to in cfg.get("replace", []):
            line = line.replace(a, to)
        t = norm(line)
        if t and t not in flat:
            failures.append("VERBATIM line %d missing/altered: %s..." % (i, t[:80]))

    # 2. image refs
    for src in re.findall(r'src="(img/[^"]+)"', guide):
        if not os.path.exists(os.path.join(img_root, src)):
            failures.append("IMAGE missing: %s (root %s)" % (src, img_root))

    # 3. anchors
    ids = set(re.findall(r'id="([\w-]+)"', guide))
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
        "WizKids credit": "Card images &copy; WizKids.",
        "McCue attribution": "Matthew McCue (mdmccu2)",
        "lightbox": 'id="lightbox"',
        "GoatCounter": "stcc-compendium.goatcounter.com",
        "stylesheet": "css/stcc.css",
    }
    for name, needle in furniture.items():
        if needle not in guide:
            failures.append("FURNITURE missing: %s" % name)
    if guide.count("Back to Compendium") < 2:
        failures.append("FURNITURE: need Back to Compendium top and bottom")

    for w in warnings:
        print("WARN:", w)
    if failures:
        print("FAIL (%d):" % len(failures))
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("PASS: verbatim text intact, %d image refs OK, anchors OK, HTML balanced, furniture OK"
          % len(re.findall(r'src="img/', guide)))


if __name__ == "__main__":
    main()
