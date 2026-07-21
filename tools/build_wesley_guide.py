#!/usr/bin/env python3
"""Build wesley-crusher-guide.html from the BGG SingleFile capture.

This guide is a ~163-entry rules-reference list, not prose, so it does not fit
tools/build_guide.py's paragraph/image model. It is built here instead, using
the same principles: McCue's text is moved verbatim out of the capture, never
retyped. Card entries become .card-props list items; McCue's own section
headers keep their exact wording and casing and become h2/h3.

Usage:
    python3 build_wesley_guide.py <singlefile.html> <favicon_source.html> [--out DIR]

Writes <out>/wesley-crusher-guide.html and <out>/wesley_text.txt (the marked
verbatim source for tools/verify_guide.py). Verify with:

    python3 tools/verify_guide.py wesley-crusher-guide.html tools/wesley_text.txt \
        --config tools/configs/wesley-crusher-guide.json --img-root .

Stdlib only.
"""

import html as H
import re
import sys
import os


def extract(singlefile_path):
    """Pull post #0 (McCue's article) out of the capture as marked text."""
    h = open(singlefile_path, encoding='utf-8', errors='replace').read()
    arts = [m.start() for m in re.finditer(r'<article _ngcontent[^>]*class="post ', h)]
    seg = h[arts[0]:arts[1]]
    b = seg.rfind('<', 0, seg.find('class="post-body'))
    e = seg.rfind('<', 0, seg.find('class="post-footer'))
    body = seg[b:e]
    body = re.sub(r'<gg[^>]*>|</gg>|<span[^>]*>|</span>|<div[^>]*>|</div>', '', body)
    body = re.sub(r'<br[^>]*>', '\n', body)
    body = re.sub(r'<strong[^>]*>', ' [[B]]', body).replace('</strong>', '[[/B]] ')
    body = H.unescape(re.sub(r'<[^>]+>', '', body))
    return [l.strip() for l in body.split('\n')]


# -*- coding: utf-8 -*-
ARGS = [a for a in sys.argv[1:] if a != '--out']
OUT = '.'
if '--out' in sys.argv:
    OUT = sys.argv[sys.argv.index('--out') + 1]
    ARGS = ARGS[:-1]
SINGLEFILE, FAVICON_SRC = ARGS[0], ARGS[1]

lines = extract(SINGLEFILE)
open(os.path.join(OUT, 'wesley_text.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
L = lambda i: lines[i]

def esc(s):
    return H.escape(s, quote=False)

def split_bold(s):
    """line like '[[B]]Header[[/B]] : rest' -> (header, rest)"""
    m = re.match(r'\s*\[\[B\]\](.*?)\[\[/B\]\]\s*(.*)$', s, re.S)
    return (m.group(1).strip(), m.group(2).strip()) if m else (None, s.strip())

def entry(s):
    """'Name: text' -> li"""
    s = s.strip()
    m = re.match(r'^([^:]+?):(\s*)(.*)$', s)
    if m:
        return '<li><strong>%s:</strong>%s%s</li>' % (
            esc(m.group(1)), m.group(2) or '', esc(m.group(3)))
    return '<li>%s</li>' % esc(s)

def props(idxs):
    return '<ul class="card-props">\n' + '\n'.join(entry(L(i)) for i in idxs) + '\n</ul>'

def para(i):
    return '<p>%s</p>' % esc(L(i))

def slug(s):
    s = s.lower().replace('’', '').replace("'", '').replace('.', '').replace(',', '')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

BACK = '<a href="#top" class="back-top">↑ back to top</a>'

out = []
A = out.append

# ---- Introduction ----
A('  <h2 id="introduction">Introduction</h2>\n')
A('<div class="card-img"><img src="img/promo1/wesley-crusher.jpg" alt="Wesley Crusher" loading="lazy" onclick="openLightbox(this)"></div>\n')
A('  ' + para(0) + '\n')
A('  ' + BACK + '\n')

# ---- General Concepts ----
A('\n  <h2 id="general-concepts">General Concepts</h2>\n')
A('  ' + para(2) + '\n')
A('<ul class="card-props">')
for i in range(3, 10):
    hd, rest = split_bold(L(i))
    A('<li><strong>%s</strong> %s</li>' % (esc(hd), esc(rest)))
A('</ul>\n')
A('  ' + para(11) + '\n')
A('  ' + para(13) + '\n')
A('  ' + BACK + '\n')

def block(title, groups, hid):
    A('\n  <h2 id="%s">%s</h2>\n' % (hid, title))
    for sub, idxs in groups:
        if sub:
            A('<h3 id="%s">%s</h3>' % (slug(hid + '-' + sub), esc(sub)))
        A(props(idxs))
        A(BACK + '\n')

block('Core Box Commons', [
    ('ACTIVATIONS', range(18, 26)),
    ('REACTIONS', range(28, 40)),
    ('PASSIVE and NONE (Do Not Apply)', range(42, 47)),
], 'core-commons')

block('To Boldly Go Commons', [
    ('ACTIVATIONS', range(51, 57)),
    ('REACTIONS', range(59, 66)),
    ('PASSIVE and NONE (Do Not Apply)', range(68, 72)),
], 'tbg-commons')

block('Second Contact Commons:', [
    ('Market Commons', range(76, 81)),
    ('Crossover Rewards', range(83, 91)),
], 'sc-commons')

# ---- Captain sections ----
def captains(title, hid, spans):
    A('\n  <h2 id="%s">%s</h2>\n' % (hid, title))
    for hdr_line, rng, pre in spans:
        name = split_bold(L(hdr_line))[0]
        A('<h3 id="%s">%s</h3>' % (slug(name), esc(name)))
        if pre is not None:
            A('<p>%s</p>' % esc(L(pre)))
        A(props(rng))
        A(BACK + '\n')

captains('Core Box Captains', 'core-captains', [
    (94, range(95, 101), None),
    (102, range(103, 107), None),
    (108, range(109, 116), None),
    (117, range(118, 126), None),
    (127, range(128, 135), None),
    (136, range(137, 148), None),
])

captains('To Boldly Go Captains', 'tbg-captains', [
    (151, range(152, 159), None),
    (160, range(161, 167), None),
    (168, range(169, 176), None),
    (177, range(178, 185), None),
    (186, range(188, 193), 187),
    (194, range(195, 200), None),
])

captains('Second Contact Captains', 'sc-captains', [
    (203, range(204, 217), None),
    (218, range(219, 225), None),
    (226, range(227, 236), None),
])

body = '\n'.join(out)

TOC = """<nav class="toc-list">
  <div class="toc-list-label">Contents</div>
  <ol>
    <li><a href="#introduction">Introduction</a></li>
    <li><a href="#general-concepts">General Concepts</a></li>
    <li><a href="#core-commons">Core Box Commons</a></li>
    <li><a href="#tbg-commons">To Boldly Go Commons</a></li>
    <li><a href="#sc-commons">Second Contact Commons</a></li>
    <li><a href="#core-captains">Core Box Captains</a></li>
    <li><a href="#tbg-captains">To Boldly Go Captains</a></li>
    <li><a href="#sc-captains">Second Contact Captains</a></li>
  </ol>
</nav>"""

FAVICON = re.search(r'<link rel="icon"[^>]*>',
                    open(FAVICON_SRC, encoding='utf-8').read()).group(0)

DESC = ("Wesley Crusher (Encounter) guide for Star Trek: Captain's Chair — how every Person card's "
        "Activations and Reactions work from your Staging Area, by Matthew McCue.")
TITLE = "The Ultimate Guide to Wesley Crusher (Encounter) — ST:CC Compendium"

doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="https://periodic-agent.github.io/stcc-strategy/wesley-crusher-guide.html">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="https://periodic-agent.github.io/stcc-strategy/img/promo1/wesley-crusher.jpg">
<meta property="og:url" content="https://periodic-agent.github.io/stcc-strategy/wesley-crusher-guide.html">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
{FAVICON}
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:ital,wght@0,300;0,400;0,600;1,300&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/stcc.css?v=1">
</head>
<body>

<div id="top" class="nav-bar"><a href="index.html">← Back to Compendium</a></div>

<header class="chapter-header">
  <div class="chapter-label">Captain's Chair</div>
  <h1 class="chapter-title">The Ultimate Guide to <span>Wesley Crusher</span> (Encounter)</h1>
  <div class="chapter-meta">By Matthew McCue (mdmccu2)</div>
  <div class="chapter-date">Posted 21 Jul 2026</div>
  <div class="chapter-tags"><span class="tag">Encounter</span><span class="tag">Promo Pack 1</span><span class="tag">Rules Reference</span><span class="tag">All Boxes</span></div>
</header>

{TOC}

<main class="content">

{body}

</main>

<div class="nav-bar"><a href="index.html">← Back to Compendium</a></div>

<footer>
  Card images &copy; WizKids.<br>
  Guides by <a href="https://boardgamegeek.com/user/mdmccu2" target="_blank">Matthew McCue (mdmccu2)</a> &middot; Website by Periodic_agent
</footer>

<div id="lightbox" onclick="this.classList.remove('open')">
  <img id="lightbox-img" src="" alt="">
</div>

<script>
function openLightbox(img) {{
  document.getElementById('lightbox-img').src = img.src;
  document.getElementById('lightbox').classList.add('open');
}}
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') document.getElementById('lightbox').classList.remove('open'); }});
</script>


<script data-goatcounter="https://stcc-compendium.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>

</body>
</html>"""

dest = os.path.join(OUT, 'wesley-crusher-guide.html')
open(dest, 'w', encoding='utf-8').write(doc)
print('wrote %s (%d bytes, %d card entries)' % (dest, len(doc), doc.count('<li>')))
