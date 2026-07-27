#!/usr/bin/env python3
"""Fill the `filename` field of a box JSON from images already on disk.

Used when a guide import lands a deck's card scans in img/boxN/ ahead of the
community sheet's image column. The sheet stays canonical: once its image
cells are filled, a plain `build_box2_from_sheet.py` regen reproduces exactly
what this script writes, because both key off the same invariant --
`id` == filename stem (WORKFLOW, Card Image Filename Convention).

Only `original` cards are filled by default. Reprints must keep `filename`
empty: the scanner resolves a reprint's art from the earliest printing, so
filling it here would be dead data at best and would flip the art at worst
(WORKFLOW, Session Delta 25 Jul 2026, rule 2).

Idempotent. Reports every change and refuses to overwrite a non-empty cell
unless --overwrite is given.

Usage:
    python3 tools/fill_image_filenames.py box2.json --img-dir img/box2 \
        --source Soval [--variant original] [--overwrite] [--dry-run]
"""

import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("box_json")
    ap.add_argument("--img-dir", required=True,
                    help="folder holding <id>.jpg scans, e.g. img/box2")
    ap.add_argument("--source", action="append", default=[],
                    help="restrict to this deck (repeatable); default: every deck")
    ap.add_argument("--variant", action="append", default=[],
                    help="variants eligible for a filename; default: original")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace a filename cell that is already set")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    variants = set(a.variant) or {"original"}
    cards = json.load(open(a.box_json, encoding="utf-8"))
    on_disk = {f[:-4] for f in os.listdir(a.img_dir) if f.lower().endswith(".jpg")}

    changed, skipped, missing = [], [], []
    for c in cards:
        if a.source and c.get("source") not in a.source:
            continue
        if c.get("variant", "original") not in variants:
            skipped.append((c["id"], "variant=%s" % c.get("variant")))
            continue
        if c["id"] not in on_disk:
            missing.append(c["id"])
            continue
        want = c["id"] + ".jpg"
        have = c.get("filename", "")
        if have == want:
            continue
        if have and not a.overwrite:
            skipped.append((c["id"], "filename already %r" % have))
            continue
        c["filename"] = want
        changed.append(c["id"])

    # Orphan images are only meaningful against the whole box: with --source
    # the folder legitimately holds every other deck's scans too.
    unused = [] if a.source else sorted(on_disk - {c["id"] for c in cards})

    for cid in changed:
        print("  set  %s.jpg" % cid)
    for cid, why in skipped:
        print("  skip %-45s %s" % (cid, why))
    for cid in missing:
        print("  ----  no scan on disk for %s" % cid)
    for f in unused:
        print("  ????  %s.jpg has no card row in this scope" % f)
    print("%d filled, %d skipped, %d without a scan, %d orphan images"
          % (len(changed), len(skipped), len(missing), len(unused)))

    if a.dry_run:
        print("dry run: %s not written" % a.box_json)
        return
    if changed:
        with open(a.box_json, "w", encoding="utf-8") as fh:
            json.dump(cards, fh, indent=2, ensure_ascii=False)
        print("wrote %s" % a.box_json)
    else:
        print("nothing to do; %s untouched" % a.box_json)


if __name__ == "__main__":
    sys.exit(main())
