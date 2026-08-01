#!/usr/bin/env python3
"""
shrink_card_images.py -- resize repo card images to the display standard.

Decision (Jul 2026, Periodic_agent): the repo carries DISPLAY copies only;
high-resolution originals stay on local disk, off git. Standard:

    max width 1170 px (native iPhone screen width; lightbox renders 1:1),
    JPEG quality 80, progressive, ICC profile carried, ~500-600 KB per card.

This both shrinks the existing library and is the filter step for every
future image import: run it over img/ (or a staging folder) after adding
new scans, before pushing.

Rules: a file is processed only if it is wider than MAX_W or larger than
SIZE_SKIP bytes; everything already small passes untouched. Resizing
preserves aspect ratio. Never upscales.

Usage
  python3 tools/shrink_card_images.py img/box3 img/box1 [--dry-run]
  python3 tools/shrink_card_images.py img --dry-run     (whole tree)
"""
import argparse
import glob
import os
import sys

from PIL import Image

MAX_W = 1170        # native iPhone width; pristine in the lightbox
QUALITY = 80


def shrink(path, apply):
    """Resize only images WIDER than the standard.

    The gate is width alone, deliberately. An earlier version also re-encoded any
    file over 400 KB, which meant every already-standard card (they run ~600 KB at
    1170 px q80) was re-compressed on each run: the filter was not idempotent and
    quietly stacked JPEG generation loss. Width is the definition of the standard,
    so a file already at or under MAX_W is done and must be left untouched.
    """
    before = os.path.getsize(path)
    im = Image.open(path)
    w, h = im.size
    if w <= MAX_W:
        return None
    icc = im.info.get("icc_profile")
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if w > MAX_W:
        im = im.resize((MAX_W, round(h * MAX_W / w)), Image.LANCZOS)
    if apply:
        im.save(path, "JPEG", quality=QUALITY, optimize=True, progressive=True,
                **({"icc_profile": icc} if icc else {}))
        after = os.path.getsize(path)
    else:
        import io
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True,
                **({"icc_profile": icc} if icc else {}))
        after = buf.tell()
    return before, after, (w, h), im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+", help="image folders (searched recursively)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = []
    for d in args.dirs:
        files += glob.glob(os.path.join(d, "**", "*.jpg"), recursive=True)
    files = sorted(set(files))
    if not files:
        sys.exit("no .jpg files found")

    done, skipped, b_tot, a_tot = 0, 0, 0, 0
    for p in files:
        r = shrink(p, apply=not args.dry_run)
        if r is None:
            skipped += 1
            continue
        before, after, dim0, dim1 = r
        done += 1
        b_tot += before
        a_tot += after
        if done <= 8:
            print(f"  {p}: {dim0[0]}x{dim0[1]} {before/1e3:.0f}KB -> "
                  f"{dim1[0]}x{dim1[1]} {after/1e3:.0f}KB")
    if done > 8:
        print(f"  ... {done - 8} more")
    print(f"\nprocessed {done}, skipped {skipped} (already small)")
    if done:
        print(f"total {b_tot/1e6:.0f} MB -> {a_tot/1e6:.0f} MB "
              f"(mean {a_tot/done/1e3:.0f} KB/file)")
    if args.dry_run:
        print("dry run -- nothing written.")


if __name__ == "__main__":
    main()
