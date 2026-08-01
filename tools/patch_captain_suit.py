#!/usr/bin/env python3
"""Add the Captain suit to the Card Scanner: filter chip, card-face treatment,
away-team marker.

cards.html is the repo's source of truth and several chats edit it directly, so
this applies targeted edits to whatever the file currently contains rather than
regenerating the page. Every anchor is asserted, so a refactor upstream fails
loudly here instead of silently dropping a change, and the script is idempotent:
running it on an already-patched file is a no-op.

What it does:
  * "Captain" joins SUITS_DISPLAY (which also registers the suit:Captain token)
  * Captain's colour goes from gold to light gray #d7dce6 on the chip, the card
    banners, and the card's left border; text on those goes black, including the
    chip's active state, where the inherited white would be invisible
  * the chair glyph is darkened by CSS filter wherever it sits on gray (the card
    banner, and the chip's active fill) and stays white at rest, where a black
    glyph would vanish into the dark page
  * captains carrying an away_team value get a speech-bubble marker under the
    suit banner; the value is a string and may be "2+"/"4+", and Wrathful Khan's
    empty value renders nothing, mirroring the printed card

Usage: python3 patch_captain_suit.py <cards.html> [out.html]
"""
import sys

GRAY, INK = '#d7dce6', '#10161f'


def patch(s):
    if 'awayteam' in s:
        print('already patched; nothing to do')
        return s

    # ---- 1. the suit joins the filter row (and the query vocabulary) ----
    old = ('const SUITS_DISPLAY = ["Person","Ally","Ship","Cargo","Location",'
           '"Encounter","Incident","Automated Command"];')
    assert old in s, 'SUITS_DISPLAY'
    s = s.replace(old, 'const SUITS_DISPLAY = ["Captain","Person","Ally","Ship","Cargo","Location",'
                       '"Encounter","Incident","Automated Command"];')

    # ---- 2. Captain's colour, on both the card banners and the chip ----
    n = s.count("'Captain':'#c8a84b'")
    assert n == 2, f'expected 2 SUIT_COL tables, found {n}'
    s = s.replace("'Captain':'#c8a84b'", "'Captain':'" + GRAY + "'")

    # ---- 3. away_team survives the id resolver, like glory and position ----
    old = ("      position_indicator: (() => { for (const pr of group) { if (pr.position_indicator "
           "!== undefined && pr.position_indicator !== null && pr.position_indicator !== '') "
           "return pr.position_indicator; } return null; })(),")
    assert old in s, 'resolver position_indicator'
    s = s.replace(old, old + "\n      away_team: (() => { for (const pr of group) { if (pr.away_team) "
                              "return String(pr.away_team); } return ''; })(),")

    # ---- 4. the marker itself ----
    old = ("    +'<div class=\"sb\" style=\"background:'+col+'\">'+sIcon+c.suit+'</div>'\n")
    assert old in s, 'suit banner in card markup'
    s = s.replace(old, old + "    +awayHTML\n")

    old = "  const badge=badgeInfo(c);"
    assert old in s, 'badgeInfo anchor'
    s = s.replace(old,
                  "  const away=(c.away_team||'').trim();\n"
                  "  const awayHTML=away?('<svg class=\"awayteam\" viewBox=\"0 0 30 27\" role=\"img\" "
                  "aria-label=\"Away team '+away+'\"><title>Away team '+away+'</title>"
                  "<path d=\"M4.2 1.1h21.6a3.1 3.1 0 0 1 3.1 3.1v14.6a3.1 3.1 0 0 1-3.1 3.1"
                  "h-8.2l-2.6 4.6-2.6-4.6H4.2a3.1 3.1 0 0 1-3.1-3.1V4.2a3.1 3.1 0 0 1 3.1-3.1z\" "
                  "fill=\"#1b2f4d\" stroke=\"#fff\" stroke-width=\"1.5\" stroke-linejoin=\"round\"/>"
                  "<text x=\"15\" y=\"16.6\" text-anchor=\"middle\" font-family=\"Antonio,sans-serif\" "
                  "font-weight=\"700\" font-size=\"12\" fill=\"#fff\">'+away+'</text></svg>'):'';\n"
                  + old)

    # ---- 5. styling ----
    old = '.card-entry[data-suit="Captain"]{border-left:2px solid var(--gold);}'
    assert old in s, 'captain left border'
    s = s.replace(old, '.card-entry[data-suit="Captain"]{border-left:2px solid ' + GRAY + ';}')

    old = '</style>'
    assert old in s, 'style close'
    s = s.replace(old, """
/* ===== Captain suit =====
   Captains are not market people: their banners are light gray with black text,
   so the glyph and the chip's active label have to go black too (the inherited
   white would be invisible on the fill). */
.card-entry[data-suit="Captain"] .nb,
.card-entry[data-suit="Captain"] .sb{color:""" + INK + """;}
.suit-pill.suitchip[data-suit="Captain"].active{color:""" + INK + """ !important;}
/* The glyph is white everywhere else; darken it only where it sits on gray.
   A filter beats shipping a second copy of every suit glyph. */
.card-entry[data-suit="Captain"] .sb img,
.suit-pill.suitchip[data-suit="Captain"].active img{filter:brightness(0);}
/* Away-team marker: the printed group-of-people glyph has no vector source, so
   the bubble carries the value itself. Values are strings ("5", "2+"). */
.awayteam{display:block;width:31px;height:28px;margin:.15rem 0 .4rem -0.15rem;}
</style>""", 1)
    return s


def main(src, out=None):
    s = open(src).read()
    open(out or src, 'w').write(patch(s))
    print('wrote', out or src)


if __name__ == '__main__':
    main(*sys.argv[1:])
