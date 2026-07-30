#!/usr/bin/env python3
"""Extract trait medallion icons from the STCC Traits Cyclopedia PDF.

The cyclopedia is pure vector and its trait-chip labels are NOT text (only card
names are). So extraction anchors on searchable card names, finds the chip pill
rectangles drawn under each name, and maps them 1:1 to that card's traits from
box1.json sorted alphabetically (the chip order used by the cyclopedia).
The medallion is the small emblem cluster inset at each pill's left cap; it is
rendered at high zoom and the surrounding pill/card background is removed by
corner flood-fill, leaving a transparent PNG per trait.

Usage: python3 extract_trait_icons.py <cyclopedia.pdf> <box1.json> <outdir>
Requires: pymupdf, Pillow.
"""
import sys, json, os
import fitz
from PIL import Image

ZOOM = 12  # render scale; medallion ~7pt -> ~84px

# (page_index, searchable card name) -> covers that card's full trait list
ANCHORS = [
    (1, 'ADMIRAL JAROK'),      # Romulan
    (1, 'ADMIRAL NECHEYEV'),   # Human, Starfleet
    (1, 'ADMIRAL PRESSMAN'),   # + Shady
    (1, 'AMBASSADOR KAMARAG'), # Ambassador, Imperial, Klingon
    (1, 'LENARA KAHN'),        # Scientist, Trill
    (1, 'LWAXANA TROI'),       # + Betazoid, Telepath
    (1, 'B-4'),                # Android, Attack, Synthetic
    (1, 'ZEPHRAM COCHRANE', 'Zefram Cochrane'),  # Engineer, Pilot
    (1, 'SAKONNA'),            # Maquis, Vulcan
    (1, 'HORTA'),              # Alien, Creature, Ongoing
    (1, 'FERENGI WINE'),       # Beverage, Ferengi
    (2, 'KOALA'),              # Wildcard
    (2, 'ARIN’SEN'),      # Klingon (fallback)
]

def card_traits(db, name):
    for c in db:
        if c['name'].upper() == name.replace('’', "'").upper():
            return sorted(c['species_traits'] + c['regular_traits'] + c['other_traits'])
    return None

def pills_under(page, name_rect):
    """Chip pill rects in the row under a card name, left-to-right."""
    band = fitz.Rect(name_rect.x0 - 2, name_rect.y1 - 3, name_rect.x0 + 132, name_rect.y1 + 9)
    out = []
    for dr in page.get_drawings():
        rc = dr['rect']
        if not dr.get('fill'):
            continue
        if rc.width >= 18 and 7 <= rc.height <= 10 and band.contains(fitz.Point(rc.x0, (rc.y0 + rc.y1) / 2)):
            out.append(rc)
    out.sort(key=lambda r: r.x0)
    return out

def flood_transparent(img, tol=28):
    """Remove the background by flood fill from the four corners."""
    img = img.convert('RGBA')
    px = img.load()
    w, h = img.size
    from collections import deque
    seen = set()
    for corner in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if corner in seen:
            continue
        base = px[corner][:3]
        q = deque([corner])
        while q:
            x, y = q.popleft()
            if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
                continue
            c = px[x, y]
            if c[3] == 0 or sum(abs(c[i] - base[i]) for i in range(3)) > tol * 3:
                continue
            seen.add((x, y))
            px[x, y] = (0, 0, 0, 0)
            q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return img

def main(pdf_path, box1_path, outdir):
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf_path)
    db = json.load(open(box1_path))
    done = {}
    for anchor in ANCHORS:
        pno, name = anchor[0], anchor[1]
        dbname = anchor[2] if len(anchor) > 2 else name
        traits = card_traits(db, dbname)
        if not traits:
            print(f'!! {name}: not in box1.json'); continue
        page = doc[pno]
        hits = page.search_for(name)
        if not hits:
            print(f'!! {name}: not found on page {pno+1}'); continue
        pills = pills_under(page, hits[0])
        if len(pills) != len(traits):
            print(f'!! {name}: {len(pills)} pills vs {len(traits)} traits {traits} - skipped'); continue
        for pill, trait in zip(pills, traits):
            if trait in done:
                continue
            clip = fitz.Rect(pill.x0 + 0.2, pill.y0 + 0.3, pill.x0 + pill.height + 0.2, pill.y1 - 0.3)
            pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip)
            tmp = os.path.join(outdir, f'{trait.lower().replace(" ", "-")}.png')
            pix.save(tmp)
            flood_transparent(Image.open(tmp)).save(tmp)
            done[trait] = tmp
            print(f'ok {trait}: {tmp}')
    print(f'{len(done)} medallions extracted')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
