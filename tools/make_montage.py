#!/usr/bin/env python3
"""Tile card images into labeled 2x2 montages so a Claude session can read
four card faces per image view instead of one. Used to seed the card database.

Usage: python3 make_montage.py <image_dir> [<image_dir2> ...] <out_dir>
Cards are thumbnailed to 460x640; filename printed under each card.
"""
import sys, glob, os
from PIL import Image, ImageDraw

*srcs, out = sys.argv[1:]
os.makedirs(out, exist_ok=True)
files = []
for d in srcs:
    files += sorted(glob.glob(os.path.join(d, '*.jpg'))) + sorted(glob.glob(os.path.join(d, '*.webp')))
CW, CH, LBL = 460, 640, 28
for i in range(0, len(files), 4):
    canvas = Image.new('RGB', (CW*2, (CH+LBL)*2), 'white')
    d = ImageDraw.Draw(canvas)
    for j, f in enumerate(files[i:i+4]):
        im = Image.open(f); im.thumbnail((CW, CH))
        x, y = (j%2)*CW, (j//2)*(CH+LBL)
        canvas.paste(im, (x+(CW-im.width)//2, y))
        d.text((x+10, y+CH+6), os.path.basename(os.path.dirname(f))+'/'+os.path.basename(f), fill='black')
    canvas.save(os.path.join(out, f'm{i//4:02d}.jpg'), quality=88)
print(len(files), 'cards ->', (len(files)+3)//4, 'montages in', out)
