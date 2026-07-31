#!/usr/bin/env python3
"""Extract suit glyphs from the Traits Cyclopedia as TRUE SVG.

The deck-trait and combined-list pages print a small white suit glyph just
LEFT of each card name (which is searchable text). This transcribes those
vector paths into standalone SVGs, one per suit, using known-suit anchor
cards. Same path-transcription approach as tools/extract_focus_svg.py.

Usage: python3 extract_suit_svg.py <cyclopedia.pdf> <outdir>
Requires: pymupdf.
"""
import sys, os
import fitz

# suit -> anchor card names (any page); the glyph sits left of the name text
ANCHORS = {
    'person':    ['BRAD BOIMLER, LT. JG', 'DEANNA TROI-RIKER'],
    'ship':      ['U.S.S. TITAN', 'U.S.S. ZHENG HE'],
    'location':  ['STARBASE 25', 'NEPENTHE', 'HOLODECK'],
    'cargo':     ['CHATEAU PICARD'],
    'incident':  ['RED ALERT', 'HOSTILE CONTACT'],
    'captain':   ['WILLIAM T. RIKER'],
    'ally':      ['ARIN’SEN', "ARIN'SEN", 'THOLIANS', 'BOLIANS'],
    'encounter': ['KOALA', 'BOLTZMANN BRAIN'],
    'directive': ['ANALYZE', 'RECRUIT', 'UTILIZE'],
}

def fmt(v):
    return f'{v:.3f}'.rstrip('0').rstrip('.')

def path_d(items, ox, oy):
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

def glyph_cluster(page, name_rect):
    """All drawings in the small zone left of the name; returns (paths, union)."""
    zone = fitz.Rect(name_rect.x0 - 16, name_rect.y0 - 2.5, name_rect.x0 + 1.5, name_rect.y1 + 2.5)
    sel, union = [], None
    for dr in page.get_drawings():
        rc = dr['rect']
        if zone.contains(rc) and rc.width < 15 and rc.height < 15:
            sel.append(dr)
            union = rc if union is None else union | rc
    return sel, union

def icon_svg(drawings, box, pad=0.3):
    vb = fitz.Rect(box.x0 - pad, box.y0 - pad, box.x1 + pad, box.y1 + pad)
    paths = []
    for dr in drawings:
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
    for suit, names in ANCHORS.items():
        got = False
        for name in names:
            if got:
                break
            for pno in range(15, len(doc)):
                page = doc[pno]
                for hit in page.search_for(name):
                    drs, union = glyph_cluster(page, hit)
                    if not drs:
                        continue
                    svg = icon_svg(drs, union)
                    open(os.path.join(outdir, f'suit-{suit}.svg'), 'w').write(svg)
                    print('ok', suit, name, 'page', pno + 1, len(svg), 'bytes')
                    got = True
                    break
                if got:
                    break
        if not got:
            print('!!', suit)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
