#!/usr/bin/env python3
"""Standalone preview of the proposed Captain card-face treatment.

Renders a handful of captain cards using the LIVE cards.html CSS and the live
asset bundle, with the proposed changes applied in memory only:
  - name + suit banners light gray (#d7dce6) with black text, black chair glyph
  - card left border light gray instead of gold
  - away-team marker under the suit banner: the real glyph from the rulebook
    back cover, with the count on a tab beneath it
Nothing here writes or pushes cards.html; it exists to look at the design.
"""
import re, json, base64, sys, os

GRAY, INK = '#d7dce6', '#10161f'

def main(live_dir='live_sync', out='mockups_captain_preview.html'):
    page = open(f'{live_dir}/cards.html').read()
    assets = open(f'{live_dir}/cardface-assets.js').read()
    CF = json.loads(assets[assets.index('{'):assets.rindex(';')])

    dark = re.sub(r'fill="rgb\([^"]*\)"', 'fill="' + INK + '"',
                  open('icons_svg/suit-captain.svg').read())
    chair = 'data:image/svg+xml;base64,' + base64.b64encode(dark.encode()).decode()

    css = page[page.index('<style>') + 7: page.index('</style>')]

    caps = []
    for b in ('box1', 'box2', 'box3'):
        for c in json.load(open(f'{live_dir}/{b}.json')):
            if c.get('suit') == 'Captain':
                caps.append(c)
    order = ['Jean-Luc Picard', 'Michael Burnham', 'Jonathan Archer',
             'Christopher Pike', 'Sela', 'Wrathful Khan']
    picked = [c for n in order for c in caps if c['name'] == n]

    away_icon = ('data:image/svg+xml;base64,'
                 + base64.b64encode(open('icons_rb/away-team.svg', 'rb').read()).decode())

    def away_svg(v):
        """The away-team mark with its count.

        The glyph is the printed one, transcribed from the rulebook back cover,
        so the drawn speech bubble that stood in for it is gone. The count sits
        on a tab beneath, as on the card; values are strings and may be two
        characters ("2+", "4+"), so one size serves them all.
        """
        if not v:
            return ''
        return ('<span class="awayteam"><img src="' + away_icon + '" alt="Away team">'
                '<span class="atn">' + v + '</span></span>')

    def card(c):
        traits = sorted(c['species_traits'] + c['regular_traits'] + c['other_traits'],
                        key=len)
        vt = ''
        for i, t in enumerate(traits):
            key = t.lower().replace("'", '').replace('’', '')
            key = re.sub(r'\s+', '-', key)
            ic = CF['trait'].get(key)
            fam = ('variable' if t == 'Wildcard'
                   else 'species' if t in c['species_traits']
                   else 'other' if t in c['other_traits'] else 'regular')
            vt += ('<div class="vt" style="z-index:%d">' % (len(traits) - i)
                   + ('<img src="%s" alt="">' % ic if ic else '<span class="vt-spacer"></span>')
                   + '<span class="vctag vt-%s">%s</span></div>' % (fam, t.upper()))
        foci = [i for i in c['icons'] if i['type'] == 'Focus']
        corner = ''
        if foci:
            f = CF['focus'].get(foci[0]['specialty'].lower())
            if f:
                corner = '<img class="focorner" src="%s" alt="">' % f
        pos = c.get('position_indicator') or ''
        num = c.get('card_number') or ''
        foot = ''
        if num or pos:
            foot = ('<div class="ce-bottom"><div class="ce-footrow">'
                    '<span class="cid2">' + num + '</span>'
                    + ('<span class="posin">' + pos + '</span>' if pos else '')
                    + '</div></div>')
        return ('<div class="card-entry cap' + (' has-focus' if corner else '') + '" data-suit="Captain">'
                '<div class="ce-row"><div class="ce-main">'
                '<div class="nb" style="background:' + GRAY + '">' + c['name'] + '</div>'
                '<div class="sb" style="background:' + GRAY + '">'
                '<img src="' + chair + '" alt="">CAPTAIN</div>'
                + away_svg((c.get('away_team') or '').strip())
                + '</div><div class="ce-traits2">' + vt + '</div></div>'
                + foot + corner + '</div>')

    extra = """
/* ---- proposed Captain treatment (mockup only) ---- */
.card-entry.cap{border-left:2px solid %s;}
.card-entry.cap .nb,.card-entry.cap .sb{color:%s;}
.awayteam{display:flex;flex-direction:column;align-items:center;width:fit-content;
  margin:.15rem 0 .4rem -0.1rem;}
.awayteam img{width:27px;height:auto;display:block;}
.awayteam .atn{margin-top:-5px;min-width:19px;padding:0 .18rem;border-radius:3px;
  background:#2f5f96;border:1.5px solid #fff;color:#fff;font-family:'Antonio',sans-serif;
  font-weight:700;font-size:.72rem;line-height:1.25;text-align:center;}
""" % (GRAY, INK)

    html = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<title>Captain card mockup</title>'
            '<link href="https://fonts.googleapis.com/css2?family=Antonio:wght@600'
            '&family=Orbitron:wght@600;700&family=Exo+2:wght@400;600&display=swap" rel="stylesheet">'
            '<style>' + css + extra + '</style></head><body>'
            '<div style="padding:2rem;max-width:1200px;margin:0 auto">'
            '<h2 style="font-family:Orbitron,sans-serif;color:#e8ecf5;letter-spacing:.08em;'
            'font-size:1rem">CAPTAIN CARD MOCKUP</h2>'
            '<p style="font-family:\'Exo 2\',sans-serif;color:#8a94ac;font-size:.85rem;max-width:60ch">'
            'Light gray banners with black text and a black chair glyph, gray left border, '
            'away-team marker under the suit banner. Wrathful Khan carries no away team, '
            'mirroring the printed card. Preview only; cards.html is untouched.</p>'
            '<div class="card-grid">' + ''.join(card(c) for c in picked) + '</div>'
            '</div></body></html>')
    open(out, 'w').write(html)
    print('wrote', out, len(html) // 1024, 'KB,', len(picked), 'cards')

if __name__ == '__main__':
    main(*sys.argv[1:])
