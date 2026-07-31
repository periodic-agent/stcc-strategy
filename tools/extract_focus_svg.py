#!/usr/bin/env python3
"""Extract focus icons from the Traits Cyclopedia as TRUE SVG.

The cyclopedia is pure vector; each focus icon is a handful of filled paths
(dark shadow wedge, colored stripe, glyph). This transcribes the PDF path
data (lines + cubic beziers) inside the icon's bounding box directly into an
SVG document: zero approximation, crisp at any size. Anchoring is the same
card-name trick as the other extractors.

Usage: python3 extract_focus_svg.py <cyclopedia.pdf> <outdir>
Requires: pymupdf.
"""
import sys, os
import fitz

ANCHORS = {
    'focus-research':  'LENARA KAHN',
    'focus-influence': 'ADMIRAL NECHEYEV',
    'focus-military':  'LURSA',
    'focus-any':       'NEW FEDERATION APPLICANTS',
}

def row_icon_cluster(page, name_rect, xlo=95, xhi=140):
    cands = []
    for dr in page.get_drawings():
        rc = dr['rect']
        cy = (rc.y0 + rc.y1) / 2
        if 2.5 <= rc.width <= 14 and 2.5 <= rc.height <= 14 \
           and name_rect.y0 - 3 <= cy <= name_rect.y1 + 3 \
           and name_rect.x0 + xlo <= rc.x0 <= name_rect.x0 + xhi:
            cands.append(rc)
    if not cands:
        return None
    cands.sort(key=lambda rc: rc.x0)
    u = cands[0]
    for rc in cands:
        if rc.x0 - u.x1 < 2.5:
            u = u | rc
    return u

def fmt(v):
    return f'{v:.3f}'.rstrip('0').rstrip('.')

def path_d(items, ox, oy):
    """Build an SVG path 'd' from pymupdf drawing items, offset to the viewBox."""
    d = []
    cur = None
    for it in items:
        kind = it[0]
        if kind == 'l':
            p0, p1 = it[1], it[2]
            if cur is None or abs(p0.x - cur.x) > 1e-4 or abs(p0.y - cur.y) > 1e-4:
                d.append(f'M{fmt(p0.x - ox)} {fmt(p0.y - oy)}')
            d.append(f'L{fmt(p1.x - ox)} {fmt(p1.y - oy)}')
            cur = p1
        elif kind == 'c':
            p0, p1, p2, p3 = it[1], it[2], it[3], it[4]
            if cur is None or abs(p0.x - cur.x) > 1e-4 or abs(p0.y - cur.y) > 1e-4:
                d.append(f'M{fmt(p0.x - ox)} {fmt(p0.y - oy)}')
            d.append(f'C{fmt(p1.x - ox)} {fmt(p1.y - oy)} {fmt(p2.x - ox)} {fmt(p2.y - oy)} {fmt(p3.x - ox)} {fmt(p3.y - oy)}')
            cur = p3
        elif kind == 're':
            rc = it[1]
            d.append(f'M{fmt(rc.x0 - ox)} {fmt(rc.y0 - oy)}H{fmt(rc.x1 - ox)}V{fmt(rc.y1 - oy)}H{fmt(rc.x0 - ox)}Z')
            cur = None
        elif kind == 'qu':
            q = it[1]
            pts = [q.ul, q.ur, q.lr, q.ll]
            d.append('M' + 'L'.join(f'{fmt(p.x - ox)} {fmt(p.y - oy)}' for p in pts) + 'Z')
            cur = None
    d.append('Z')
    return ''.join(d)

def rgb(c):
    return f'rgb({round(c[0]*255)},{round(c[1]*255)},{round(c[2]*255)})'

def icon_svg(page, box, pad=0.3):
    vb = fitz.Rect(box.x0 - pad, box.y0 - pad, box.x1 + pad, box.y1 + pad)
    paths = []
    for dr in page.get_drawings():
        rc = dr['rect']
        if not (vb.contains(rc)):
            continue
        if dr.get('fill') is None and dr.get('color') is None:
            continue
        attrs = []
        if dr.get('fill') is not None:
            attrs.append(f'fill="{rgb(dr["fill"])}"')
            if dr.get('even_odd'):
                attrs.append('fill-rule="evenodd"')
        else:
            attrs.append('fill="none"')
        if dr.get('color') is not None and dr.get('width'):
            attrs.append(f'stroke="{rgb(dr["color"])}" stroke-width="{fmt(dr["width"])}"')
        paths.append(f'<path d="{path_d(dr["items"], vb.x0, vb.y0)}" {" ".join(attrs)}/>')
    w, h = fmt(vb.width), fmt(vb.height)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}">' + ''.join(paths) + '</svg>')

def main(pdf_path, outdir):
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf_path)
    for key, name in ANCHORS.items():
        got = False
        for pno in range(1, 32):
            page = doc[pno]
            hits = page.search_for(name)
            if not hits:
                continue
            box = row_icon_cluster(page, hits[0])
            if not box:
                continue
            svg = icon_svg(page, box)
            path = os.path.join(outdir, key + '.svg')
            open(path, 'w').write(svg)
            print('ok', key, name, 'page', pno + 1, len(svg), 'bytes')
            got = True
            break
        if not got:
            print('!!', key)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
