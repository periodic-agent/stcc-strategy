#!/usr/bin/env python3
"""Extract ALL trait medallion icons from the STCC Traits Cyclopedia PDF.

The cyclopedia is pure vector; card names are searchable text but trait-chip
labels are not. Three passes recover every medallion (62 traits, boxes 1-3):

1. Commons sweep (pages 2-7, one box per page pair): for every card of that
   box, find its name, take the chip pills drawn beneath (single row), and map
   them 1:1 to the card's alphabetically sorted traits. The medallion is the
   square at each pill's left cap.
2. Two-row sweep: same, but allowing chip rows that wrapped to two lines
   (pills sorted row-major), which rescues cards with many/long traits.
3. Deck-header sweep (pages 31-45): deck-only traits (e.g. Reman, Mind
   Control, Path of Surak) never appear as chips, only as section headers in
   the per-captain trait pages. Headers are alphabetical down the columns, so
   they map 1:1 to the deck's sorted trait union from the box JSONs (plus one
   trailing WITHOUT TRAITS header, dropped).

White fills are excluded when detecting pills (a pill's own label paths can
be pill-sized). Backgrounds are removed by corner flood fill.

Usage: python3 extract_trait_icons.py <cyclopedia.pdf> <box_json_dir> <outdir>
       (box_json_dir must contain box1.json, box2.json, box3.json)
Requires: pymupdf, Pillow.
"""
import sys, json, os
import fitz
from PIL import Image
from collections import deque

ZOOM = 12
PAGE_BOX = {1: 'box1.json', 2: 'box1.json', 3: 'box2.json',
            4: 'box2.json', 5: 'box3.json', 6: 'box3.json'}


def key_of(t):
    return t.lower().replace(' ', '-').replace("'", '')


def card_traits(c):
    return sorted(c['species_traits'] + c['regular_traits'] + c['other_traits'])


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


def save_medallion(page, pill, path):
    h = pill.y1 - pill.y0
    clip = fitz.Rect(pill.x0 + 0.2, pill.y0 + 0.3, pill.x0 + h + 0.2, pill.y1 - 0.3)
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip)
    pix.save(path)
    flood_transparent(Image.open(path)).save(path)


def pills_under(page, r, rows=1):
    band = fitz.Rect(r.x0 - 2, r.y1 - 3, r.x0 + 132, r.y1 + (9 if rows == 1 else 21))
    out = []
    for dr in page.get_drawings():
        rc = dr['rect']
        f = dr.get('fill')
        if f and f != (1.0, 1.0, 1.0) and rc.width >= 18 and 7 <= rc.height <= 10 \
           and band.contains(fitz.Point(rc.x0, (rc.y0 + rc.y1) / 2)):
            out.append(rc)
    out.sort(key=lambda x: (round(x.y0), x.x0))
    return out


def commons_sweep(doc, dbs, done, outdir, rows):
    n = 0
    for pno, dbf in PAGE_BOX.items():
        page = doc[pno]
        for c in dbs[dbf]:
            traits = card_traits(c)
            if not traits: continue
            keys = [key_of(t) for t in traits]
            if all(k in done for k in keys): continue
            hits = page.search_for(c['name'].upper())
            if not hits: continue
            pills = pills_under(page, hits[0], rows)
            if len(pills) != len(traits): continue
            for pill, t, k in zip(pills, traits, keys):
                if k in done: continue
                save_medallion(page, pill, os.path.join(outdir, k + '.png'))
                done.add(k); n += 1
                print(f'ok {t} (via {c["name"]}, p{pno+1})')
    return n


def deck_header_sweep(doc, dbs, done, outdir):
    all_cards = [c for db in dbs.values() for c in db]
    captains = {c['source'] for c in all_cards if c['source'] not in ('Common', 'Promo')}
    n = 0
    for pno in range(30, min(45, len(doc))):
        page = doc[pno]
        cap = next((name for name in captains
                    if (h := page.search_for(name.upper()) or page.search_for('CPT. ' + name.upper()))
                    and h[0].y1 < 40), None)
        if not cap: continue
        traits = sorted({t for c in all_cards if c['source'] == cap for t in card_traits(c)})
        keys = [key_of(t) for t in traits]
        if all(k in done for k in keys): continue
        chips = []
        for dr in page.get_drawings():
            rc = dr['rect']
            f = dr.get('fill')
            if f and f != (1.0, 1.0, 1.0) and 26 <= rc.width <= 120 and 10 <= rc.height <= 12.4 and rc.y0 > 42:
                chips.append(fitz.Rect(rc))
        merged = []
        for rc in sorted(chips, key=lambda r: (r.x0 // 140, r.y0)):
            if merged and merged[-1].intersects(rc): merged[-1] = merged[-1] | rc
            else: merged.append(rc)
        if len(merged) == len(traits) + 1:  # trailing WITHOUT TRAITS header
            merged = merged[:-1]
        if len(merged) != len(traits): continue
        for rc, t, k in zip(merged, traits, keys):
            if k in done: continue
            save_medallion(page, rc, os.path.join(outdir, k + '.png'))
            done.add(k); n += 1
            print(f'ok {t} (header, {cap}, p{pno+1})')
    return n


def main(pdf_path, json_dir, outdir):
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf_path)
    dbs = {f: json.load(open(os.path.join(json_dir, f)))
           for f in ('box1.json', 'box2.json', 'box3.json')}
    done = {f[:-4] for f in os.listdir(outdir) if f.endswith('.png')}
    n = commons_sweep(doc, dbs, done, outdir, rows=1)
    n += commons_sweep(doc, dbs, done, outdir, rows=2)
    n += deck_header_sweep(doc, dbs, done, outdir)
    every = {key_of(t) for db in dbs.values() for c in db for t in card_traits(c)}
    missing = sorted(every - done)
    print(f'{n} new, {len(done)} total; missing: {missing or "none"}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
