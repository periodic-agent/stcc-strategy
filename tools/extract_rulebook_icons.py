#!/usr/bin/env python3
"""Extract the icon-reference glyphs from the To Boldly Go rulebook as TRUE SVG.

The back cover ("OTHER ICONS" / "ICON REFERENCE") prints every token and suit
glyph as vector art with its name set directly beneath it, which gives a clean
text anchor per icon. Same path-transcription approach as the cyclopedia
extractors: PDF drawing items (lines, cubics, rects, quads) are written out as
SVG path data, so the result is crisp at any size rather than a resampled crop.

Usage: python3 extract_rulebook_icons.py <rulebook.pdf> <outdir> [page]
Requires: pymupdf.
"""
import sys, os
import fitz

# label -> output key. The label sits centred beneath its icon.
WANTED = {
    'ACTION TOKEN': 'action', 'AWAY TEAM': 'away-team', 'VICTORY POINTS': 'vp',
    'DILITHIUM': 'dilithium', 'LATINUM': 'latinum', 'GLORY': 'glory-token',
    'ANY SKILL': 'skill-any', 'BEST FOCUS': 'focus-best',
    'BORG COLLECTIVE': 'borg-collective', 'BORG DRONE': 'borg-drone',
    'TREACHERY': 'treachery',
}

# Suit marks are NOT drawn paths here: the icon-reference list sets them with an
# embedded symbol font, so nothing is found beside those labels. They come from
# tools/extract_suit_font.py instead.
SUITS = {}


def fmt(v):
    return f'{v:.3f}'.rstrip('0').rstrip('.')


def path_d(items, ox, oy):
    d, cur = [], None
    for it in items:
        k = it[0]
        if k == 'l':
            p0, p1 = it[1], it[2]
            if cur is None or abs(p0.x - cur.x) > 1e-4 or abs(p0.y - cur.y) > 1e-4:
                d.append(f'M{fmt(p0.x - ox)} {fmt(p0.y - oy)}')
            d.append(f'L{fmt(p1.x - ox)} {fmt(p1.y - oy)}')
            cur = p1
        elif k == 'c':
            p0, p1, p2, p3 = it[1], it[2], it[3], it[4]
            if cur is None or abs(p0.x - cur.x) > 1e-4 or abs(p0.y - cur.y) > 1e-4:
                d.append(f'M{fmt(p0.x - ox)} {fmt(p0.y - oy)}')
            d.append('C' + ' '.join(f'{fmt(p.x - ox)} {fmt(p.y - oy)}' for p in (p1, p2, p3)))
            cur = p3
        elif k == 're':
            rc = it[1]
            d.append(f'M{fmt(rc.x0 - ox)} {fmt(rc.y0 - oy)}H{fmt(rc.x1 - ox)}'
                     f'V{fmt(rc.y1 - oy)}H{fmt(rc.x0 - ox)}Z')
            cur = None
        elif k == 'qu':
            q = it[1]
            d.append('M' + 'L'.join(f'{fmt(p.x - ox)} {fmt(p.y - oy)}'
                                    for p in (q.ul, q.ur, q.lr, q.ll)) + 'Z')
            cur = None
    d.append('Z')
    return ''.join(d)


def rgb(c):
    return 'rgb(%d,%d,%d)' % tuple(round(v * 255) for v in c)


def cluster_above(page, label_rect, up=46, half=26):
    """Drawings in the box directly above a centred label."""
    cx = (label_rect.x0 + label_rect.x1) / 2
    zone = fitz.Rect(cx - half, label_rect.y0 - up, cx + half, label_rect.y0 - 2.5)
    sel, union = [], None
    for dr in page.get_drawings():
        rc = dr['rect']
        if zone.contains(rc) and rc.width > 0.4 and rc.height > 0.4:
            sel.append(dr)
            union = rc if union is None else union | rc
    return sel, union


def cluster_left(page, label_rect, back=17, pad_y=3.0):
    """Drawings in the small zone left of an inline label."""
    zone = fitz.Rect(label_rect.x0 - back, label_rect.y0 - pad_y,
                     label_rect.x0 + 1.0, label_rect.y1 + pad_y)
    sel, union = [], None
    for dr in page.get_drawings():
        rc = dr['rect']
        if zone.contains(rc) and rc.width < 16 and rc.height < 16:
            sel.append(dr)
            union = rc if union is None else union | rc
    return sel, union


def to_svg(drawings, box, pad=0.4):
    vb = fitz.Rect(box.x0 - pad, box.y0 - pad, box.x1 + pad, box.y1 + pad)
    paths = []
    for dr in drawings:
        a = []
        if dr.get('fill') is not None:
            a.append(f'fill="{rgb(dr["fill"])}"')
            if dr.get('even_odd'):
                a.append('fill-rule="evenodd"')
        else:
            a.append('fill="none"')
        if dr.get('color') is not None and dr.get('width'):
            a.append(f'stroke="{rgb(dr["color"])}" stroke-width="{fmt(dr["width"])}"')
        paths.append(f'<path d="{path_d(dr["items"], vb.x0, vb.y0)}" {" ".join(a)}/>')
    w, h = fmt(vb.width), fmt(vb.height)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}">' + ''.join(paths) + '</svg>')


def main(pdf, outdir, page_no='36'):
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf)
    page = doc[int(page_no) - 1]
    done = {}
    for label, key in WANTED.items():
        best = None
        for r in page.search_for(label):
            drs, box = cluster_above(page, r)
            if drs and (best is None or len(drs) > len(best[0])):
                best = (drs, box, r)
        if not best:
            print(f'!! {label}')
            continue
        drs, box, r = best
        svg = to_svg(drs, box)
        open(os.path.join(outdir, key + '.svg'), 'w').write(svg)
        done[key] = len(svg)
        print(f'ok {label:16} -> {key + ".svg":22} {len(drs):3d} paths, '
              f'{box.width:.1f}x{box.height:.1f}pt, {len(svg)} bytes')
    for label, key in SUITS.items():
        best = None
        for r in page.search_for(label):
            drs, box = cluster_left(page, r)
            if drs and (best is None or len(drs) > len(best[0])):
                best = (drs, box)
        if not best:
            print(f'!! {label} (suit)')
            continue
        drs, box = best
        svg = to_svg(drs, box)
        open(os.path.join(outdir, key + '.svg'), 'w').write(svg)
        done[key] = len(svg)
        print(f'ok {label:16} -> {key + ".svg":22} {len(drs):3d} paths, '
              f'{box.width:.1f}x{box.height:.1f}pt, {len(svg)} bytes  (suit, glyph left of name)')
    print(f'\n{len(done)} of {len(WANTED) + len(SUITS)} extracted')


if __name__ == '__main__':
    main(*sys.argv[1:])
