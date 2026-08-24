#!/usr/bin/env python3
"""Operation strips, 22 Aug 2026: two corrections observed on the printed cards.

1. CONTROL is not green. It prints in the same gray box as PLAY / SUPPORT, so
   its family moves from `resupply` to `play`. Because the STRIP filter chip
   and the card-face box both take their colour from STRIP_FAMILY, the one
   table edit recolours both; consecutive PLAY/SUPPORT/CONTROL strips now
   merge into one box the way the card prints them.

2. "Away Team" in strip text is printed as the away-team token (the
   group-of-people bubble already shipped in CARDFACE.token['away-team'] by
   tools/extract_rulebook_icons.py; the captain-card mockup uses the same
   art). Strip text replaces the words with the icon, the same treatment as
   Dilithium / Latinum / Glory / action. "Away Teams" (plural) collapses to
   the same icon; the surrounding count ("up to 2 ...") carries the number.

Idempotent: every edit is guarded, re-running is a no-op.
Usage: python3 tools/patch_strips_awayteam_control.py [cards.html]
"""
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'cards.html'
s = open(path, encoding='utf-8').read()
orig = s
done = []

# ---- 1. CONTROL joins the PLAY family ------------------------------------
old = '"control": "resupply"'
new = '"control": "play"'
if old in s:
    s = s.replace(old, new, 1)
    done.append('STRIP_FAMILY control -> play')
elif new in s:
    done.append('STRIP_FAMILY control already play')
else:
    sys.exit('STRIP_FAMILY anchor not found')

# ---- 2a. stripToken: {awayteam} renders the icon -------------------------
# Strip bodies (gray Play, blue Reaction) sit close to the bubble's navy, so the
# strip copy carries a 1px white outline baked into the SVG (paint-order puts
# the stroke under the fill, so the art itself is untouched). The captain-card
# marker keeps the plain token.
import base64
assets = open('cardface-assets.js', encoding='utf-8').read()
m = re.search(r'"away-team": "data:image/svg\+xml;base64,([^"]+)"', assets)
if not m:
    sys.exit('CARDFACE.token["away-team"] not found in cardface-assets.js')
svg = base64.b64decode(m.group(1)).decode('utf-8')
svg = svg.replace('<path ', '<path stroke="#fff" stroke-width="1" paint-order="stroke" stroke-linejoin="round" ', 1)
svg = svg.replace('viewBox="0 0 22.803 24.989"', 'viewBox="-0.6 -0.6 24.003 26.189"', 1)
outlined = 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode('ascii')
const = "const AWAY_TOKEN_STRIP='" + outlined + "';\n"
if 'const AWAY_TOKEN_STRIP=' in s:
    s = re.sub(r"const AWAY_TOKEN_STRIP='[^']*';\n", const, s, count=1)
    done.append('AWAY_TOKEN_STRIP refreshed')
else:
    anchor = 'function stripIcon(key){\n'
    if anchor not in s:
        sys.exit('stripIcon anchor not found')
    s = s.replace(anchor, const + anchor, 1)
    done.append('AWAY_TOKEN_STRIP: outlined token const')

anchor = "  if(t==='action'){\n"
tok = ("  if(t==='awayteam'){\n"
       "    const src=AWAY_TOKEN_STRIP||stripIcon('away-team');\n"
       "    return src?'<img class=\"stripimg awayteam-tok\" src=\"'+src+'\" alt=\"Away Team\">':'Away Team';\n"
       "  }\n")
if "t==='awayteam'" in s:
    done.append('stripToken awayteam already present')
elif anchor in s:
    s = s.replace(anchor, tok + anchor, 1)
    done.append('stripToken: {awayteam} -> icon')
else:
    sys.exit('stripToken action anchor not found')

# ---- 2b. stripAutoTokens: the words become the token ---------------------
# Runs before the suit pass so "Team" is never mistaken for anything, and
# outside existing tokens so a {trait:...} payload is never rewritten.
anchor = "  Object.keys(STRIP_SUIT_COL).forEach(w=>{\n"
auto = ("  // Away Team prints as the token, singular or plural; the count stays in the text.\n"
        "  t=outsideTokens(t,seg=>seg.replace(/\\bAway Teams?\\b/g,'{awayteam}'));\n")
if "{awayteam}" in s and 'Away Teams?' in s:
    done.append('stripAutoTokens awayteam already present')
elif anchor in s:
    s = s.replace(anchor, auto + anchor, 1)
    done.append('stripAutoTokens: Away Team(s) -> {awayteam}')
else:
    sys.exit('stripAutoTokens suit anchor not found')

# ---- 2c. CSS: the bubble is taller than the resource coins ---------------
css = '.stripimg.awayteam-tok{height:1.45em;vertical-align:-.38em;}\n'
if '.stripimg.awayteam-tok' in s:
    done.append('CSS already present')
else:
    m = re.search(r'\n\.stripimg\{[^\n]*\}\n', s)
    if not m:
        sys.exit('.stripimg CSS rule not found')
    s = s[:m.end()] + css + s[m.end():]
    done.append('CSS: .stripimg.awayteam-tok')

if s != orig:
    open(path, 'w', encoding='utf-8').write(s)
print('\n'.join(done))
