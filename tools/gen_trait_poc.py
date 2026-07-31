#!/usr/bin/env python3
"""Generate mockups/trait-icons-poc.html from extracted cyclopedia icons.

Inputs: icons/ (trait medallions) and icons_sf/ (skill/focus icons), produced by
tools/extract_trait_icons.py and tools/extract_skillfocus_icons.py.
Usage: python3 gen_trait_poc.py <icons_dir> <skillfocus_dir> <out_html>
"""
import sys, base64, glob, os, io
from PIL import Image, ImageDraw

SPECIES = {'alien', 'human', 'klingon', 'romulan', 'trill', 'ferengi', 'betazoid', 'android', 'synthetic'}
OTHER = {'attack', 'ongoing', 'wildcard'}

def b64(f):
    return 'data:image/png;base64,' + base64.b64encode(open(f, 'rb').read()).decode()

def _shape_mask(size, octagon, ss=4):
    """Clean geometric mask at supersampled resolution: octagon (species) or circle."""
    s = size * ss
    m = Image.new('L', (s, s), 0)
    d = ImageDraw.Draw(m)
    if octagon:
        c = 0.30 * s  # corner cut, mirrors the card's octagon clip
        d.polygon([(c, 0), (s - c, 0), (s, c), (s, s - c), (s - c, s), (c, s), (0, s - c), (0, c)], fill=255)
    else:
        d.ellipse([0, 0, s - 1, s - 1], fill=255)
    return m.resize((size, size), Image.LANCZOS)

def _is_octagon(img):
    """Detect the medallion's shape from its own alpha. Probe the four points
    at 15% in from each bbox corner: a circle is still opaque there (distance
    from center ~0.495 < 0.5), an octagon with ~30% corner cuts is not
    (x+y = 0.30 boundary)."""
    from PIL import ImageFilter as _IF
    a = img.split()[3]
    # denoise: hard threshold + erosion kills flood-fill edge specks that
    # otherwise inflate the bbox to the crop edges
    clean = a.point(lambda v: 255 if v > 200 else 0).filter(_IF.MinFilter(5))
    bbox = clean.getbbox()
    if not bbox:
        return False
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    px = clean.load()

    def width_at(fy):
        y = int(y0 + fy * h)
        row = [x for x in range(x0, x1) if px[x, y] > 128]
        return (max(row) - min(row) + 1) if row else 0

    # An octagon reaches full width by ~30% height (its corner cuts end);
    # a circle only at 50%. Measured: octagons >= 0.97, circles <= 0.91.
    ratio = (width_at(0.30) + width_at(0.70)) / (2 * max(width_at(0.50), 1))
    return ratio > 0.94

def b64_outlined(f, trait, size=96, border=2):
    """Composite the extracted art onto a crisp white octagon/circle backing:
    white shape full-size, art clipped to the inset shape. Removes ragged
    flood-fill edges and gives every medallion a clean thin white border.
    Shape (octagon vs circle) is auto-detected from the source art, since the
    cyclopedia does not map shape strictly to trait family (e.g. Imperial is
    an octagon despite being a regular trait)."""
    octagon = _is_octagon(Image.open(f).convert('RGBA'))
    art = Image.open(f).convert('RGBA').resize((size, size), Image.LANCZOS)
    inner = _shape_mask(size - 2 * border, octagon)
    art_c = art.resize((size - 2 * border, size - 2 * border), Image.LANCZOS)
    clipped = Image.new('RGBA', inner.size, (0, 0, 0, 0))
    clipped.paste(art_c, (0, 0), inner)
    outer = _shape_mask(size, octagon)
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    white = Image.new('RGBA', (size, size), (255, 255, 255, 255))
    canvas.paste(white, (0, 0), outer)
    canvas.paste(clipped, (border, border), clipped)
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def b64_skill_banner(f, widen=1.2):
    """Skill icons print as a banner rooted in the card's left edge. The
    cyclopedia's D block is near-square, so extend it leftward: every row is
    padded with its own leftmost opaque color (handles the tricolor Any).
    The Variable '?' gets a white banner backing instead."""
    img = Image.open(f).convert('RGBA')
    w, h = img.size
    W = int(w * widen)
    canvas = Image.new('RGBA', (W, h), (0, 0, 0, 0))
    key = os.path.basename(f)
    if 'variable' in key:
        ss = 4
        m = Image.new('L', (W * ss, h * ss), 0)
        d = ImageDraw.Draw(m)
        r = h * ss // 2
        d.rectangle([0, 0, W * ss - r, h * ss], fill=255)
        d.pieslice([W * ss - 2 * r, 0, W * ss, h * ss], -90, 90, fill=255)
        m = m.resize((W, h), Image.LANCZOS)
        white = Image.new('RGBA', (W, h), (255, 255, 255, 255))
        canvas.paste(white, (0, 0), m)
        q = img.resize((int(w * 0.8), int(h * 0.8)), Image.LANCZOS)
        canvas.paste(q, ((W - q.width) // 2, (h - q.height) // 2), q)
    else:
        canvas.paste(img, (W - w, 0), img)
        px = img.load()
        cp = canvas.load()
        for y in range(h):
            row = [x for x in range(w) if px[x, y][3] > 200]
            if not row:
                continue
            lx = min(row)
            color = px[min(lx + 2, w - 1), y]
            for x in range(0, W - w + lx + 2):
                cp[x, y] = color
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def b64_svg(f):
    return 'data:image/svg+xml;base64,' + base64.b64encode(open(f, 'rb').read()).decode()

def main(icons_dir, sf_dir, out):
    tr = {os.path.basename(f)[:-4]: b64_outlined(f, os.path.basename(f)[:-4])
          for f in sorted(glob.glob(icons_dir + '/*.png'))}
    fsvg = {os.path.basename(f)[:-4]: b64_svg(f) for f in sorted(glob.glob('icons_svg/focus-*.svg'))}
    import re as _re
    def _white_svg(f):
        t = open(f).read()
        t = _re.sub(r'fill="rgb\([^"]*\)"', 'fill="#fff"', t)
        return 'data:image/svg+xml;base64,' + base64.b64encode(t.encode()).decode()
    ssvg = {os.path.basename(f)[:-4].replace('suit-', ''): _white_svg(f)
            for f in sorted(glob.glob('icons_svg/suit-*.svg'))}
    sf = {os.path.basename(f)[:-4]: b64(f) for f in sorted(glob.glob(sf_dir + '/*.png'))}
    sfb = {os.path.basename(f)[:-4]: b64_skill_banner(f) for f in sorted(glob.glob(sf_dir + '/*.png'))
           if os.path.basename(f).startswith('skill-')}
    fam = lambda t: 'species' if t in SPECIES else 'other' if t in OTHER else 'regular'

    def fp(t, icon=True):
        cls = {'species': 'species-pill', 'regular': 'regular-pill', 'other': 'other-pill'}[fam(t)]
        img = f'<img src="{tr[t]}" alt="">' if icon else ''
        return f'<span class="{cls}{" pillx" if icon else ""}">{img}{t.capitalize()} (12)</span>'

    def vchip(t, z=1):
        cls = {'species': 'ctag-species', 'regular': 'ctag-regular', 'other': 'ctag-other'}[fam(t)]
        if t == 'wildcard': cls = 'ctag-variable'
        return f'<div class="vt" style="z-index:{z}"><img src="{tr[t]}" alt=""><span class="ctag {cls}">{t.upper()}</span></div>'

    def card(name, suit, suitcol, skills, traits, focus, num, cls, fmode):
        """fmode: 'stripes' = diagonal focus stripes over the corner (card-accurate);
        'text' = icon+text focus chip above the band"""
        sk = ''.join(f'<img class="skimg" src="{sfb["skill-" + s]}" alt="" title="{s.capitalize()} skill">' for s in skills)
        traits = sorted(traits, key=lambda t: len(t))
        tr_ = ''.join(vchip(t, z=len(traits) - i) for i, t in enumerate(traits))
        corner = ''
        if focus:
            corner = f'<img class="focorner" src="{fsvg["focus-" + focus]}" alt="" title="{focus.capitalize()} focus">'
        numchip = ''
        if num:
            parts = num.split(' ', 1)
            meta = f'<span class="meta">{parts[1]}</span>' if len(parts) > 1 else ''
            numchip = f'<span class="cid">{parts[0]}{meta}</span>'
        bottom = ''
        if numchip:
            bottom = f'<div class="ce-bottom">{numchip}</div>'
        return f'''<div class="card-entry" data-cls="{cls}" style="border-left:2px solid {suitcol}">
<div class="ce-row"><div class="ce-main">
<div class="name-banner" style="background:{suitcol}">{name}</div>
<div class="suit-banner" style="background:{suitcol}"><img src="{ssvg[suit.lower()]}" alt="">{suit}</div>
<div class="card-skills">{sk}</div>
</div><div class="ce-traits">{tr_}</div></div>
{bottom}{corner}</div>'''

    demo = ['human', 'klingon', 'romulan', 'betazoid', 'starfleet', 'scientist', 'engineer',
            'ambassador', 'telepath', 'shady', 'attack', 'ongoing', 'wildcard']
    sheet = ''.join(f'<div class="cell"><img src="{v}" alt=""><div>{k}</div></div>' for k, v in tr.items())
    order = ['skill-research', 'skill-influence', 'skill-military', 'skill-any', 'skill-variable',
             'focus-research', 'focus-influence', 'focus-military', 'focus-any']
    sfrow = ''.join(f'<div class="cell big"><img src="{sf[k]}" alt=""><div>{k}</div></div>' for k in order if k in sf)

    DEMO_CARDS = [
        ('Bruce Maddox', 'Person', 'var(--person)', ['research'], ['human', 'engineer', 'starfleet', 'scientist'], 'research', '', 'common'),
        ('Bird-of-Prey', 'Ship', '#7a8aaa', ['influence'], ['klingon', 'attack', 'romulan'], '', '1SHI01/13', 'common'),
        ('Lursa', 'Person', 'var(--person)', [], ['shady', 'klingon'], 'military', '2PER10/26 • Duplicate', 'captaindeck'),
        ('Delta Vega', 'Location', '#4ac48a', ['military'], [], 'any', '1LOC08/20', 'location'),
        ('Keyla Detmer', 'Person', 'var(--person)', ['variable', 'variable'], ['human', 'pilot', 'starfleet', 'synthetic'], '', '', 'captaindeck'),
    ]
    row_text = ''.join(card(*c, 'text') for c in DEMO_CARDS)

    html = f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>Skill Banners &amp; Trait Icons POC — ST:CC Card Scanner</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;400;600&family=Antonio:wght@600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0a0e1a;--bg2:#0f1628;--blue:#4a9fd4;--blue2:#7ec8f0;--muted:#7a8aaa;--border:rgba(74,159,212,0.25);
--person:#d9bd45;--sp-bg:rgba(220,140,60,0.12);--sp-bd:rgba(220,140,60,0.45);--sp-tx:#e09050;
--rg-bg:rgba(74,159,212,0.10);--rg-bd:rgba(74,159,212,0.35);--rg-tx:#7ec8f0;
--ot-bg:rgba(200,60,60,0.10);--ot-bd:rgba(200,60,60,0.35);--ot-tx:#e05a5a;}}
body{{font-family:'Exo 2',sans-serif;font-weight:300;background:var(--bg);color:#ccd6f0;padding:2rem;max-width:1100px;margin:0 auto}}
h1{{font-family:Orbitron,sans-serif;font-size:1.1rem;color:#d4699f;letter-spacing:.08em}}
h2{{font-family:Orbitron,sans-serif;font-size:.8rem;color:#7ec8f0;letter-spacing:.15em;text-transform:uppercase;margin:2.2rem 0 .8rem}}
p.note{{font-size:.85rem;color:var(--muted);max-width:74ch;line-height:1.6}}
.pill-row{{display:flex;flex-wrap:wrap;gap:.35rem;margin:.5rem 0}}
.species-pill,.regular-pill,.other-pill{{font-size:.68rem;padding:.18rem .55rem;border-radius:3px;border:1.5px solid;cursor:pointer;user-select:none;display:inline-flex;align-items:center;gap:.35rem}}
.species-pill{{border-color:var(--sp-bd);color:var(--sp-tx);background:var(--sp-bg)}}
.regular-pill{{border-color:var(--rg-bd);color:var(--rg-tx);background:var(--rg-bg)}}
.other-pill{{border-color:var(--ot-bd);color:var(--ot-tx);background:var(--ot-bg)}}
.pillx img{{width:18px;height:18px}}
.pill-row.compact .pillx img{{width:14px;height:14px}}
.card-entry{{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:.6rem;width:195px;min-height:175px;position:relative;overflow:hidden;display:flex;flex-direction:column}}
/* card number: dark chip, flush left in the bottom row */
.cid{{background:#14171f;color:#e8ecf5;display:inline-block;margin-left:-0.6rem;
  font-family:'Antonio',sans-serif;font-size:.6rem;font-weight:600;letter-spacing:.07em;
  padding:.12rem .55rem .12rem .55rem;border-radius:0 999px 999px 0;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.22)}}
.cid .meta{{color:#8a94ac;font-weight:400;margin-left:.35rem}}
/* focus: the true-SVG cyclopedia asset, nested flush into the rounded corner */
.focorner{{position:absolute;right:-1px;bottom:-1px;height:42px;width:auto;z-index:2}}
.ce-row{{display:flex;gap:.4rem;align-items:flex-start}}
.ce-main{{flex:1;min-width:0}}
/* name + suit: left-rooted colored banners, rounded end, like the printed card */
.name-banner{{display:block;width:fit-content;margin-left:-0.6rem;max-width:calc(100% + .1rem);
  padding:.08rem .85rem .08rem .6rem;border-radius:0 999px 999px 0;background:#555;
  color:#fff;font-family:'Antonio',sans-serif;font-weight:600;font-size:.82rem;
  letter-spacing:.05em;text-transform:uppercase;line-height:1.2;margin-bottom:.3rem}}
.suit-banner{{display:inline-flex;align-items:center;gap:.4rem;align-self:flex-start;margin-left:-0.6rem;
  padding:0 .8rem 0 .6rem;height:18px;box-sizing:border-box;border-radius:0 999px 999px 0;background:#555;
  color:#fff;font-family:'Antonio',sans-serif;font-weight:600;font-size:.72rem;
  letter-spacing:.06em;text-transform:uppercase;margin-bottom:.5rem}}
.suit-banner img{{height:.95em;width:auto}}
.card-suit-bar{{display:flex;align-items:center;gap:.35rem;margin-bottom:.45rem}}
.suit-dot{{width:6px;height:6px;border-radius:50%}}
.suit-label{{font-family:'Antonio',sans-serif;font-size:.82rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase}}
.card-skills{{display:flex;flex-direction:column;align-items:flex-start;gap:.3rem;margin-left:-0.6rem}}
.skimg{{height:28px;width:auto}}
.card-skill{{font-size:.6rem;padding:.09rem .32rem;border-radius:2px;border:1px solid;display:inline-flex;align-items:center;gap:.32rem}}
.card-skill .ci{{width:18px;height:18px}}
.sk-research{{background:rgba(46,134,184,0.10);color:#5cb4e4;border-color:rgba(46,134,184,0.35)}}
.sk-influence{{background:rgba(232,212,74,0.08);color:#e8d44a;border-color:rgba(232,212,74,0.3)}}
.sk-military{{background:rgba(224,90,90,0.08);color:#e57a6e;border-color:rgba(224,90,90,0.32)}}
.is-focus{{position:relative;overflow:hidden;padding-right:.85em}}
.is-focus::after{{content:'';position:absolute;right:-5px;bottom:-5px;width:11px;height:11px;transform:rotate(45deg);background:currentColor;opacity:.75}}
.focorner{{position:absolute;right:2px;bottom:5px;width:34px;height:34px;z-index:2}}
.ce-traits{{display:flex;flex-direction:row;align-items:flex-start;justify-content:flex-end;gap:0;flex:none;max-width:55%;flex-wrap:wrap}}
.vt{{display:flex;flex-direction:column;align-items:center;position:relative;margin-left:-4px}}
.vt:first-child{{margin-left:0}}
.vt img{{width:26px;height:26px;z-index:2}}
.vt .ctag{{writing-mode:vertical-rl;text-orientation:sideways;display:flex;align-items:center;justify-content:center;padding:.65rem 0 .36rem;width:18px;line-height:1;font-family:'Antonio',sans-serif;font-size:.66rem;font-weight:600;letter-spacing:.05em;border-radius:0 0 999px 999px;margin-top:-5px;border:none}}
/* solid card-style pills: white label on the family color, like the printed cards */
.ctag-species{{background:#e2a04a;color:#fff}}
.ctag-regular{{background:#8ec6d8;color:#fff}}
.ctag-other{{background:#c85340;color:#fff}}
.ctag-variable{{background:#eef1f6;color:#20242e}}
.ce-bottom{{margin-top:auto;padding-top:.4rem;display:flex;justify-content:space-between;align-items:flex-end;position:relative;z-index:3}}
.ce-num{{font-size:.55rem;color:var(--muted);letter-spacing:.06em}}
.ce-focus{{margin-left:auto}}
.row{{display:flex;gap:1rem;flex-wrap:wrap}}
.sheet{{display:flex;flex-wrap:wrap;gap:14px}}
.cell{{text-align:center;font-size:.6rem;color:var(--muted)}}
.cell img{{width:52px;height:52px;display:block;margin:0 auto 4px;object-fit:contain}}
.cell.big img{{width:64px;height:64px}}
footer{{margin-top:3rem;border-top:1px solid var(--border);padding-top:1rem;font-size:.72rem;color:var(--muted);line-height:1.8}}
</style></head><body>
<h1>SKILL BANNERS &amp; TRAIT ICONS — PROOF OF CONCEPT v3</h1>
<p class="note">Icon grammar: solid "D" block = skill, diagonal stripe with black wedge = focus,
color = specialty, tricolor = Any, black ? = Variable. Skills are now banner-only (no text) in
every variant. Two focus treatments are presented below for comparison.</p>

<h2>1 — The full skill &amp; focus icon set</h2>
<div class="sheet">{sfrow}</div>

<h2>2 — Compact entries: true-SVG focus asset nested in the rounded corner</h2>
<div class="row">{row_text}</div>

<h2>4 — Filter pills: text-only vs 14px medallions (same pill height) vs 18px</h2>
<div class="pill-row">{''.join(fp(t, False) for t in demo)}</div>
<div class="pill-row compact">{''.join(fp(t) for t in demo)}</div>
<div class="pill-row">{''.join(fp(t) for t in demo)}</div>

<h2>5 — All extracted trait medallions (22 of ~40)</h2>
<div class="sheet">{sheet}</div>

<footer>Proof of concept only, not linked from the compendium. Trait and skill iconography &#169;
WizKids; vector redraws from the STCC Traits Cyclopedia v2.1 (attribution handled by
Periodic_agent). Extraction: tools/extract_trait_icons.py, tools/extract_skillfocus_icons.py;
page generated by tools/gen_trait_poc.py.</footer>
</body></html>'''
    open(out, 'w').write(html)
    print('wrote', out, len(html), 'bytes')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
