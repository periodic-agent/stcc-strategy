#!/usr/bin/env python3
"""rename_scanner_to_cards.py -- rename the Card Scanner page to cards.html.

The scanner shipped as card-browser-mockup.html during development. For public
advertising the page moves to the stable URL cards.html; the old path stays as
a permanent client-side redirect so every link posted before the rename keeps
working (GitHub Pages cannot serve HTTP 301s, so the redirect is a stub page:
canonical tag + meta refresh + location.replace).

What it does, from a pristine repo checkout (run from repo root):
1. cards.html          <- full copy of card-browser-mockup.html with the
                          canonical and og:url meta updated to cards.html
2. card-browser-mockup.html <- replaced by the redirect stub
3. index.html          <- Card Scanner banner href now points at cards.html
4. sitemap.xml         <- loc moved to cards.html
5. tools/strategy_index_config.json <- cards.html added to exclude_files
                          (old name stays excluded: the stub is still *.html)
6. tools/parse.py      <- cards.html added to the exclusion tuple (same reason)
7. Tool defaults that named the old file now default to cards.html:
   patch_scanner_image_fallback.py, patch_scanner_banner_badge.py,
   patch_scanner_strategy_banner.py, patch_scanner_all_boxes.py,
   patch_scanner_strategy.py, test_scanner.mjs, test_scanner_query.mjs,
   build_scanner_data.py (docstring only; tool is retired from the pipeline)

Every replacement is asserted: if an anchor is missing (e.g. the scanner head
changed), the script fails loudly and writes nothing for that file.

Usage: python3 tools/rename_scanner_to_cards.py [repo_root]
Idempotent: a second run finds cards.html already present and exits 0.
"""

import json
import os
import sys

OLD = "card-browser-mockup.html"
NEW = "cards.html"
SITE = "https://periodic-agent.github.io/stcc-strategy/"

REDIRECT_STUB = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ST:CC Card Scanner</title>
<link rel="canonical" href="{site}{new}">
<meta http-equiv="refresh" content="0; url={new}">
<meta name="robots" content="noindex">
<script>location.replace("{new}" + location.search + location.hash);</script>
<style>body{{font-family:sans-serif;background:#0d0d17;color:#c8c8d8;
display:flex;align-items:center;justify-content:center;min-height:90vh}}</style>
</head>
<body>
<p>The Card Scanner has moved to <a href="{new}" style="color:#d4699f">{site}{new}</a></p>
</body>
</html>
""".format(site=SITE, new=NEW)


def sub(path, old, new, count=1, required=True):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    n = text.count(old)
    if n == 0:
        if required:
            sys.exit(f"ANCHOR MISSING in {path}: {old!r} -- nothing written")
        return False
    if count is not None and n != count:
        sys.exit(f"ANCHOR COUNT in {path}: expected {count} of {old!r}, found {n}")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace(old, new))
    return True


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(root)

    if os.path.exists(NEW):
        print(f"{NEW} already exists -- nothing to do (idempotent exit)")
        return

    # 1. cards.html = scanner with its own canonical URL
    with open(OLD, encoding="utf-8") as f:
        scanner = f.read()
    for anchor in (f'rel="canonical" href="{SITE}{OLD}"',
                   f'property="og:url" content="{SITE}{OLD}"'):
        if anchor not in scanner:
            sys.exit(f"ANCHOR MISSING in {OLD}: {anchor!r}")
    scanner = scanner.replace(f"{SITE}{OLD}", f"{SITE}{NEW}")
    with open(NEW, "w", encoding="utf-8", newline="") as f:
        f.write(scanner)

    # 2. old path becomes the redirect stub
    with open(OLD, "w", encoding="utf-8", newline="") as f:
        f.write(REDIRECT_STUB)

    # 3. index banner
    sub("index.html", f'href="{OLD}"', f'href="{NEW}"', count=1)

    # 4. sitemap
    sub("sitemap.xml", f"{SITE}{OLD}", f"{SITE}{NEW}", count=1)

    # 5. strategy index exclude list (JSON-aware: keep both names excluded)
    cfg_path = "tools/strategy_index_config.json"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    if OLD not in cfg["exclude_files"]:
        sys.exit(f"{cfg_path}: {OLD} not in exclude_files")
    if NEW not in cfg["exclude_files"]:
        cfg["exclude_files"].insert(cfg["exclude_files"].index(OLD), NEW)
        with open(cfg_path, "w", encoding="utf-8", newline="") as f:
            json.dump(cfg, f, indent=1, ensure_ascii=False)
            f.write("\n")

    # 6. parse.py exclusion tuple keeps both names
    sub("tools/parse.py", f"'{OLD}'", f"'{OLD}','{NEW}'", count=1)

    # 7. tool defaults now target cards.html (old name may appear in comments
    #    describing history; only the operative default strings are replaced)
    for path, anchor in [
        ("tools/patch_scanner_image_fallback.py", f'else "{OLD}"'),
        ("tools/patch_scanner_banner_badge.py",   f'else "{OLD}"'),
        ("tools/patch_scanner_strategy_banner.py", f'else "{OLD}"'),
        ("tools/patch_scanner_all_boxes.py",      f'else "{OLD}"'),
        ("tools/patch_scanner_strategy.py",       f'default="{OLD}"'),
        ("tools/test_scanner.mjs",                f"/{OLD}'"),
        ("tools/test_scanner_query.mjs",          f'"../{OLD}"'),
    ]:
        sub(path, anchor, anchor.replace(OLD, NEW), count=1)

    print("Rename complete: cards.html live, old path redirects, references updated.")


if __name__ == "__main__":
    main()
