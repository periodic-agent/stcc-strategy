#!/usr/bin/env python3
"""Extract skill/focus specialty icons from the STCC Traits Cyclopedia PDF.

Companion to extract_trait_icons.py (same anchoring idea: card names are the
only searchable text). Each card row in the common-cards lists carries its
skill/focus icons at the right edge of the column (x ~ name.x0+95..134).
Icon shapes observed: circle = skill, corner-stripe "D" = focus, tricolor
stripe = Any, black "?" = Variable. Anchors are single-icon cards so the
crop-to-name mapping is unambiguous; multi-icon rows (e.g. Bruce Maddox,
Research Skill + Research Focus) are split by x-gap clustering and labeled
after visual confirmation.

Known gaps / findings (July 2026):
- No Military-Skill single-icon anchor matched on searchable pages yet.
- Delta Vega and Boreth show stripe (focus-style) icons in the cyclopedia but
  box1.json records their icons as Skills; data cross-check pending.

Usage: python3 extract_skillfocus_icons.py <cyclopedia.pdf> <outdir>
Requires: pymupdf, Pillow.
"""
import sys, os
import fitz
from PIL import Image
from collections import deque

ZOOM = 12

# key -> (anchor card names to try, cluster pick: index or 'all')
ANCHORS = {
    'skill-influence':  (['RISA'], 0),                    # Influence Skill (box1)
    'skill-variable':   (['MALIK'], 0),                   # leftmost "?" of three
    'any':              (['BORETH'], 0),                  # Any Skill (Koloth deck page)
    'focus-influence':  (['ADMIRAL NECHEYEV'], 0),        # Influence Focus
    'focus-research':   (['LENARA KAHN'], 0),             # Research Focus
    'focus-military':   (['LURSA'], 0),                   # Military Focus
    'focus-any':        (['NEW FEDERATION APPLICANTS'], 0),
    # skill-research / maddox focus-research: split BRUCE MADDOX pair manually,
    # see main() below.
}

def flood_transparent(img, tol=28):
    img = img.convert('RGBA'); px = img.load(); w, h = img.size; seen = set()
    for corner in [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]:
        base = px[corner][:3]; q = deque([corner])
        while q:
            x, y = q.popleft()
            if (x, y) in seen or not (0 <= x < w and 0 <= y < h): continue
            c = px[x, y]
            if c[3] == 0 or sum(abs(c[i]-base[i]) for i in range(3)) > tol*3: continue
            seen.add((x, y)); px[x, y] = (0, 0, 0, 0)
            q.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    return img

def row_icon_clusters(page, name_rect, xlo=95, xhi=140):
    cands = []
    for dr in page.get_drawings():
        rc = dr['rect']
        cy = (rc.y0 + rc.y1) / 2
        if 2.5 <= rc.width <= 14 and 2.5 <= rc.height <= 14 \
           and name_rect.y0 - 3 <= cy <= name_rect.y1 + 3 \
           and name_rect.x0 + xlo <= rc.x0 <= name_rect.x0 + xhi:
            cands.append(rc)
    cands.sort(key=lambda rc: rc.x0)
    clusters = []
    for rc in cands:
        if clusters and rc.x0 - clusters[-1].x1 < 2.5:
            clusters[-1] = clusters[-1] | rc
        else:
            clusters.append(fitz.Rect(rc))
    return clusters

def save_clip(page, rect, path):
    clip = fitz.Rect(rect.x0-0.4, rect.y0-0.4, rect.x1+0.4, rect.y1+0.4)
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip)
    pix.save(path)
    flood_transparent(Image.open(path)).save(path)

def main(pdf_path, outdir):
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf_path)
    for key, (names, pick) in ANCHORS.items():
        got = False
        for name in names:
            for pno in range(1, 32):
                page = doc[pno]
                hits = page.search_for(name) or page.search_for(name.replace("'", '’'))
                if not hits: continue
                cl = row_icon_clusters(page, hits[0])
                if not cl: continue
                save_clip(page, cl[min(pick, len(cl)-1)], os.path.join(outdir, key + '.png'))
                print('ok', key, name, 'page', pno + 1); got = True; break
            if got: break
        if not got: print('!!', key)
    # Bruce Maddox pair: circle (skill) at x 134.2-143.9, stripe (focus) at 144.9-156.3
    page = doc[1]
    r = page.search_for('BRUCE MADDOX')
    if r:
        save_clip(page, fitz.Rect(134.2, 194.5, 143.9, 204.3), os.path.join(outdir, 'skill-research.png'))
        save_clip(page, fitz.Rect(144.9, 194.5, 156.3, 204.3), os.path.join(outdir, 'focus-research.png'))
        print('ok skill-research / focus-research (Maddox pair)')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
