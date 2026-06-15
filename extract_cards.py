#!/usr/bin/env python3
"""
extract_cards.py -- delineate and extract individual cards from a multi-card
scan or photo into separate, deskewed image files.

Two modes:

  grid   (recommended for phone photos of cards laid out on a table/mat)
         You give the layout as ROWSxCOLS. The script samples the surface
         colour from the image border, finds the gutters between cards,
         splits into cells, then segments + perspective-corrects each card.
         Robust to dark card art and surface tones because the only thing it
         has to recognise is "surface vs not-surface".

  auto   (for flatbed scans / high-contrast solid backgrounds)
         Contour-based detection, no layout needed. Best when cards sit on a
         uniform background clearly different from the cards.

Outputs:
  - One image per card: card-01.jpg, card-02.jpg, ... (grid reading order)
  - A contact sheet (_contact_<name>.jpg) with numbered detections for review

Naming is sequential by design. Card identity cannot be read from pixels, so
renaming to canonical names (lowercase-hyphen, no punctuation, per WORKFLOW.md)
happens after you confirm identities against the contact sheet.

Usage:
  python extract_cards.py INPUT --grid 2x2           # grid mode
  python extract_cards.py INPUT                       # auto mode
  python extract_cards.py ./folder --grid 3x3 -o out  # batch (same layout)

Options:
  -o, --outdir   output directory (default: ./cards_out)
  --grid RxC     grid layout, e.g. 2x2, 3x3, 2x5. Enables grid mode.
  --bg-dist      surface colour tolerance, Lab units (default 28). Raise if
                 cards bleed into the surface, lower if surface leaks in.
  --margin       px trimmed from each crop edge after warp (default 0)
  --min-area     auto mode: min card area frac of frame (default 0.01)
  --max-area     auto mode: max card area frac of frame (default 0.60)
  --ar-lo        auto mode: min aspect short/long (default 0.55)
  --ar-hi        auto mode: max aspect short/long (default 0.85)
  --no-warp      skip perspective correction (axis-aligned bounding crop)
"""

import argparse
import os
import sys
import glob
import cv2
import numpy as np

IMG_EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp")


# ----- geometry helpers -----

def order_points(pts):
    p = pts.reshape(4, 2).astype("float32")
    s = p.sum(1)
    d = np.diff(p, 1).ravel()
    return np.array([p[np.argmin(s)], p[np.argmin(d)],
                     p[np.argmax(s)], p[np.argmax(d)]], "float32")


def warp_card(img, quad, no_warp=False):
    if no_warp:
        x, y, w, h = cv2.boundingRect(quad.astype("int32"))
        crop = img[max(0, y):y + h, max(0, x):x + w]
        if crop.size and crop.shape[0] < crop.shape[1]:
            crop = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)
        return crop if crop.size else None
    tl, tr, br, bl = quad
    W = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    H = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    if W < 5 or H < 5:
        return None
    dst = np.array([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]], "float32")
    out = cv2.warpPerspective(img, cv2.getPerspectiveTransform(quad, dst), (W, H))
    if W > H:
        out = cv2.rotate(out, cv2.ROTATE_90_CLOCKWISE)
    return out


# ----- surface / background model (grid mode) -----

def background_mask(img, bg_dist):
    """Mask of pixels close to the surface colour sampled from the image border."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.int16)
    b = max(8, int(0.012 * min(img.shape[:2])))
    ring = np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
                           lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)])
    bg = np.median(ring, 0)
    dist = np.sqrt(((lab - bg) ** 2).sum(2))
    return (dist < bg_dist).astype(np.uint8), bg


def _content_span(fg_cov, frac=0.55):
    """Range [start, end] of the card band: where foreground coverage is high.
    Excludes outer surface margins, which can be wider than a fixed edge inset."""
    thr = frac * fg_cov.max()
    on = np.where(fg_cov >= thr)[0]
    return (int(on.min()), int(on.max())) if len(on) else (0, len(fg_cov) - 1)


def guided_cuts(fg_cov, n_cells, win_frac=0.08):
    """Return n_cells-1 gutter positions. For each expected gutter at k/n_cells of
    the content span, take the local minimum of foreground coverage within a window.

    This is robust to wide outer surface margins and to cards packed nearly
    edge-to-edge with thin gutters, where the old "deepest background line"
    method would place a phantom cut in the margin and merge two real cards.
    """
    if n_cells < 2:
        return []
    s, e = _content_span(fg_cov)
    span = e - s
    if span <= 0:
        return []
    win = max(1, int(win_frac * span))
    cuts = []
    for i in range(1, n_cells):
        c = s + int(i * span / n_cells)
        lo, hi = max(s, c - win), min(e, c + win)
        cuts.append(lo + int(np.argmin(fg_cov[lo:hi + 1])))
    return sorted(cuts)


def cell_quad_tight(cell, iters=5):
    """Tight card quad via GrabCut: models card vs table/shadow by colour and
    returns a mask hugging the printed border, then the min-area rectangle
    through its four corners (straight edges, corner-to-corner)."""
    h, w = cell.shape[:2]
    if h < 30 or w < 30:
        return None
    mask = np.zeros((h, w), np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    mx, my = int(w * 0.02), int(h * 0.02)
    rect = (mx, my, w - 2 * mx, h - 2 * my)
    try:
        cv2.grabCut(cell, mask, rect, bgd, fgd, iters, cv2.GC_INIT_WITH_RECT)
    except cv2.error:
        return None
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8), 2)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    big = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(big) < 0.25 * h * w:
        return None
    rect = cv2.minAreaRect(big)
    rw, rh = rect[1]
    if min(rw, rh) == 0 or not (0.55 <= min(rw, rh) / max(rw, rh) <= 0.90):
        return None
    return rect


def cell_quad(cell, bg_dist):
    """Find the card quad inside one grid cell as the largest non-surface blob."""
    bgm, _ = background_mask(cell, bg_dist)
    fg = (1 - bgm).astype(np.uint8) * 255
    k = cv2.getStructuringElement
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, k(cv2.MORPH_ELLIPSE, (5, 5)), 1)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, k(cv2.MORPH_ELLIPSE, (41, 41)), 3)
    cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    return cv2.minAreaRect(max(cnts, key=cv2.contourArea))


def extract_grid(img, rows, cols, bg_dist, tight=True):
    H, W = img.shape[:2]
    bgm, _ = background_mask(img, bg_dist)
    fg = (1 - bgm).astype(float)
    ys = [0] + guided_cuts(fg.mean(1), rows) + [H]
    xs = [0] + guided_cuts(fg.mean(0), cols) + [W]
    quads = []
    pad = max(4, int(0.006 * min(H, W)))
    for r in range(len(ys) - 1):
        for c in range(len(xs) - 1):
            y0, y1, x0, x1 = ys[r], ys[r + 1], xs[c], xs[c + 1]
            cy0, cx0 = max(0, y0 - pad), max(0, x0 - pad)
            cell = img[cy0:y1 + pad, cx0:x1 + pad]
            if cell.size == 0:
                continue
            rect = cell_quad_tight(cell) if tight else None
            if rect is None:
                rect = cell_quad(cell, bg_dist)  # fallback
            if rect is None:
                continue
            rw, rh = rect[1]
            if min(rw, rh) < 0.3 * min(cell.shape[:2]):
                continue
            box = cv2.boxPoints(rect)
            box[:, 0] += cx0
            box[:, 1] += cy0
            quads.append(order_points(box))
    return quads


# ----- contour detection (auto mode) -----

def extract_auto(img, min_area, max_area, ar_lo, ar_hi):
    H, W = img.shape[:2]
    area_img = H * W
    gray = cv2.bilateralFilter(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 9, 75, 75)
    quads = []
    for binimg in (
        cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
        cv2.dilate(cv2.Canny(gray, 50, 150), np.ones((5, 5), np.uint8), 1),
    ):
        cnts, _ = cv2.findContours(binimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            a = cv2.contourArea(c)
            if a < min_area * area_img or a > max_area * area_img:
                continue
            rect = cv2.minAreaRect(c)
            rw, rh = rect[1]
            if min(rw, rh) == 0:
                continue
            if ar_lo <= min(rw, rh) / max(rw, rh) <= ar_hi:
                quads.append(order_points(cv2.boxPoints(rect)))
    # containment NMS, keep largest
    quads.sort(key=lambda q: -cv2.contourArea(q.astype("int32")))
    kept = []
    for q in quads:
        cx, cy = q.mean(0)
        if not any(cv2.pointPolygonTest(k.astype("float32"), (float(cx), float(cy)), False) >= 0
                   for k in kept):
            kept.append(q)
    return kept


# ----- ordering + output -----

def sort_grid(quads, row_tol_frac=0.5):
    if not quads:
        return quads
    hs = [np.linalg.norm(q[3] - q[0]) for q in quads]
    tol = np.median(hs) * row_tol_frac
    items = sorted(((q.mean(0), q) for q in quads), key=lambda t: t[0][1])
    rows, cur, cy = [], [], None
    for c, q in items:
        if cy is None or abs(c[1] - cy) <= tol:
            cur.append((c, q))
            cy = np.mean([x[0][1] for x in cur])
        else:
            rows.append(cur)
            cur, cy = [(c, q)], c[1]
    if cur:
        rows.append(cur)
    out = []
    for r in rows:
        out.extend(q for _, q in sorted(r, key=lambda t: t[0][0]))
    return out


def contact_sheet(img, quads, path):
    vis = img.copy()
    for i, q in enumerate(quads, 1):
        cv2.polylines(vis, [q.astype("int32")], True, (0, 0, 255), 4)
        c = q.mean(0).astype(int)
        cv2.putText(vis, str(i), tuple(c), cv2.FONT_HERSHEY_SIMPLEX,
                    2.0, (0, 255, 0), 5, cv2.LINE_AA)
    cv2.imwrite(path, vis)


def process_image(path, args, counter):
    img = cv2.imread(path)
    if img is None:
        print(f"  skip (unreadable): {path}")
        return counter
    if args.grid:
        rows, cols = args.grid
        quads = extract_grid(img, rows, cols, args.bg_dist, tight=not args.no_tight)
    else:
        quads = extract_auto(img, args.min_area, args.max_area, args.ar_lo, args.ar_hi)
    quads = sort_grid(quads)
    base = os.path.splitext(os.path.basename(path))[0]
    contact_sheet(img, quads, os.path.join(args.outdir, f"_contact_{base}.jpg"))
    n_here = 0
    for q in quads:
        crop = warp_card(img, q, args.no_warp)
        if crop is None or crop.size == 0:
            continue
        m = args.margin
        if m > 0 and crop.shape[0] > 2 * m and crop.shape[1] > 2 * m:
            crop = crop[m:-m, m:-m]
        counter += 1
        n_here += 1
        cv2.imwrite(os.path.join(args.outdir, f"card-{counter:02d}.jpg"),
                    crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  {os.path.basename(path)}: {n_here} cards "
          f"(review _contact_{base}.jpg)")
    return counter


def parse_grid(s):
    try:
        r, c = s.lower().split("x")
        return int(r), int(c)
    except Exception:
        raise argparse.ArgumentTypeError("grid must look like ROWSxCOLS, e.g. 2x2")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default="cards_out")
    ap.add_argument("--grid", type=parse_grid, default=None)
    ap.add_argument("--bg-dist", type=float, default=28.0)
    ap.add_argument("--no-tight", action="store_true",
                    help="grid mode: skip GrabCut edge-tightening, use loose blob rect")
    ap.add_argument("--margin", type=int, default=0)
    ap.add_argument("--min-area", type=float, default=0.01)
    ap.add_argument("--max-area", type=float, default=0.60)
    ap.add_argument("--ar-lo", type=float, default=0.55)
    ap.add_argument("--ar-hi", type=float, default=0.85)
    ap.add_argument("--no-warp", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    if os.path.isdir(args.input):
        paths = sorted(p for p in glob.glob(os.path.join(args.input, "*"))
                       if p.lower().endswith(IMG_EXTS))
    else:
        paths = [args.input]
    if not paths:
        print("No input images found.")
        sys.exit(1)

    mode = f"grid {args.grid[0]}x{args.grid[1]}" if args.grid else "auto"
    print(f"Extracting ({mode}) from {len(paths)} image(s) -> {args.outdir}/")
    counter = 0
    for p in paths:
        counter = process_image(p, args, counter)
    print(f"Done. {counter} card crops written to {args.outdir}/")


if __name__ == "__main__":
    main()
