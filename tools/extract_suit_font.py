#!/usr/bin/env python3
"""Extract the game's suit glyphs as TRUE SVG from the rulebook's icon font.

The rulebook sets suit marks with an embedded symbol font (STCC...Regular)
rather than as drawn paths, so the path-transcription used for the other icons
finds nothing next to those labels. The outlines are still vector: pull the
embedded CFF, walk its charstrings, and write each glyph out as SVG. The font
is subsetted per page, so every page is scanned and the glyph sets unioned;
that is how STATUS turns up if any page happens to use it.

Glyph coordinates are in font units with y pointing up, so the transform flips
y and shifts by the ascent to land in a normal top-left SVG viewBox.

Usage: python3 extract_suit_font.py <rulebook.pdf> <outdir>
Requires: pymupdf, fonttools.
"""
import sys, os, io
import fitz
from fontTools.cffLib import CFFFontSet
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen


def glyph_svg(charstrings, name, pad=20):
    bp = BoundsPen(None)
    charstrings[name].draw(bp)
    if bp.bounds is None:
        return None
    x0, y0, x1, y1 = bp.bounds
    pen = SVGPathPen(None)
    charstrings[name].draw(pen)
    d = pen.getCommands()
    if not d:
        return None
    w = (x1 - x0) + 2 * pad
    h = (y1 - y0) + 2 * pad
    # font units are y-up; flip and translate into the viewBox
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}">'
            f'<g transform="translate({pad - x0:.0f} {y1 + pad:.0f}) scale(1 -1)">'
            f'<path d="{d}" fill="#ffffff"/></g></svg>')


def main(pdf, outdir):
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf)
    seen, written = set(), {}
    for pno in range(len(doc)):
        for f in doc[pno].get_fonts(full=True):
            xref, ext, _, name = f[0], f[1], f[2], f[3]
            if 'STCC' not in name or xref in seen:
                continue
            seen.add(xref)
            info = doc.extract_font(xref)
            if len(info) < 4 or not info[3]:
                continue
            cff = CFFFontSet()
            cff.decompile(io.BytesIO(info[3]), None)
            cs = cff[cff.fontNames[0]].CharStrings
            for g in cs.keys():
                key = g.replace('.liga', '').lower()
                if key in ('.notdef', 'space', 'slash') or key in written:
                    continue
                svg = glyph_svg(cs, g)
                if not svg:
                    continue
                open(os.path.join(outdir, 'suit-' + key + '.svg'), 'w').write(svg)
                written[key] = len(svg)
                print(f'ok suit-{key:12} {len(svg):6d} bytes   (page {pno + 1}, {name.split("+")[-1]})')
    print(f'\n{len(written)} glyphs: {", ".join(sorted(written))}')


if __name__ == '__main__':
    main(*sys.argv[1:])
