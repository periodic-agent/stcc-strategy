#!/usr/bin/env python3
"""Sample operation-strip colours from the four reference card scans.

Box bounds are listed explicitly rather than auto-detected. Auto-detection by
row uniformity works for the light boxes but fails on the blue ones, where the
reversed (white on blue) text breaks uniformity as badly as artwork does; with
only four cards in play, a table read off the scans is more honest than a
detector tuned until it happens to agree.

Colour correction follows the method Periodic_agent documented: average a
region rather than a pixel (the halftone is visible at scan resolution), take a
near-white box on the SAME card as that scan's white reference, and scale by
the ratio of a fixed target to that reference. The target is not guessed: it is
solved so that Archer's ENDGAME box reproduces the approved, already-shipped
#eecac7 / #e03511. Every other box is then derived by the identical transform,
so the whole palette is consistent with what is live.

Usage: python3 extract_strip_colors.py <img_dir> <out.json> [crop_dir]
"""
import sys, os, json
import numpy as np
from PIL import Image

SHIPPED_ENDGAME_BODY = np.array([0xee, 0xca, 0xc7], float)
SHIPPED_ENDGAME_BAR = np.array([0xe0, 0x35, 0x11], float)

# card -> [(key, label, y0, y1)], read off the 1170x1635 scans
BOXES = {
    'archer-jonathan-archer': [
        ('resupply', 'RESUPPLY', 1081, 1324),
        ('endgame', 'ENDGAME', 1341, 1506),
    ],
    'archer-earth': [
        ('cleanup', 'CLEAN-UP', 766, 1082),
        ('table', 'REACTION + PASSIVE', 1094, 1508),
    ],
    'sukal': [
        ('banner', 'no keyword', 1028, 1142),
        ('passive', 'PASSIVE', 1148, 1321),
        ('special', 'SPECIAL', 1331, 1504),
    ],
    'riker-brad-boimler-lt-jg': [
        ('play', 'PLAY + SUPPORT', 825, 1312),
        ('activation', 'ACTIVATION', 1327, 1497),
    ],
}


def hexof(rgb):
    return '#%02x%02x%02x' % tuple(int(round(min(255, max(0, v)))) for v in rgb)


def read(card, img_dir):
    return np.asarray(Image.open(os.path.join(img_dir, card + '.jpg')).convert('RGB')).astype(int)


def measure(im, y0, y1):
    """Bar colour, bar width in px, body colour, and the keyword ink."""
    mid = slice(y0 + 6, y1 - 6)
    body = np.median(im[mid, 320:1000].reshape(-1, 3), axis=0).astype(float)
    bar = np.median(im[mid, 3:17].reshape(-1, 3), axis=0).astype(float)
    width = next((x for x in range(2, 90)
                  if np.abs(np.median(im[mid, x:x + 3].reshape(-1, 3), axis=0) - body).max() < 14), 0)
    # keyword ink: pixels on the first text line that are neither the body nor
    # the body text. A black or white keyword returns None and is set by polarity.
    line = im[y0 + 4:min(y0 + 56, y1), 40:560].reshape(-1, 3).astype(float)
    off = np.abs(line - body).max(1) > 50
    sat = (line.max(1) - line.min(1)) > 48
    ink = line[off & sat]
    kw = np.median(ink, axis=0) if len(ink) > 60 else None
    return bar, width, body, kw


def main(img_dir, out_json, crop_dir=None):
    # solve the correction target from the shipped ENDGAME values
    ai = read('archer-jonathan-archer', img_dir)
    ref = measure(ai, *BOXES['archer-jonathan-archer'][0][2:])[2]      # RESUPPLY body, near-white
    eg_bar, _, eg_body, _ = measure(ai, *BOXES['archer-jonathan-archer'][1][2:])
    target = SHIPPED_ENDGAME_BODY * ref / eg_body
    print('correction target solved from the shipped ENDGAME:', target.round(1))
    print('  bar check:', hexof(eg_bar * target / ref), 'vs shipped', hexof(SHIPPED_ENDGAME_BAR))
    print()

    out = {}
    for card, rows in BOXES.items():
        im = read(card, img_dir)
        got = [(k, lbl, y0, y1) + measure(im, y0, y1) for k, lbl, y0, y1 in rows]
        cref = max((g[6] for g in got), key=lambda c: float(np.mean(c)))   # lightest body on this card
        gain = target / cref
        for k, lbl, y0, y1, bar, bw, body, kw in got:
            corr_body = body * gain
            polarity = 'light' if float(np.mean(corr_body)) > 168 else 'dark'
            out[k] = {
                'label': lbl, 'card': card, 'y': [y0, y1],
                'bar': hexof(bar * gain), 'body': hexof(corr_body),
                'bar_px': bw, 'bar_pct': round(100 * bw / im.shape[1], 2),
                'keyword': hexof(kw * gain) if kw is not None else None,
                'text': polarity,
                'raw': {'bar': [int(v) for v in bar], 'body': [int(v) for v in body]},
            }
            print(f'{k:11} {lbl:19} bar={out[k]["bar"]} body={out[k]["body"]} '
                  f'kw={out[k]["keyword"] or "-":8} barw={bw:3d}px  text={polarity}')
            if crop_dir:
                os.makedirs(crop_dir, exist_ok=True)
                Image.open(os.path.join(img_dir, card + '.jpg')).crop(
                    (6, max(0, y0 - 6), 1164, min(im.shape[0], y1 + 6))).save(
                    os.path.join(crop_dir, k + '.png'))
    json.dump(out, open(out_json, 'w'), indent=1)
    print('\nwrote', out_json)


if __name__ == '__main__':
    main(*sys.argv[1:])
