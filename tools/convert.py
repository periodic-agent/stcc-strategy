"""Convert a guide to shared-stylesheet form + verify rendering equivalence."""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from parse import tokenize, normalize

CSSLINK = '<link rel="stylesheet" href="css/stcc.css?v=1">'
STCC = open(os.path.join(os.path.dirname(__file__), '..', 'stcc.css')).read()

MARKET = {'persons.html','allies.html','ships.html','cargo.html','locations.html','encounters-incidents.html',
          'tbg-persons.html','tbg-allies.html','tbg-ships.html','tbg-cargo.html','tbg-locations.html',
          'tbg-encounters-incidents.html','sc-market-locations-rewards.html'}
EXTRA_INLINE = {
  'sc-market-locations-rewards.html': ['.toc-grid-label{margin-top:1rem;}'],
  'vs-picard.html': None,  # handled by KEEP list below
}
KEEP_SELECTORS = {
  'vs-picard.html': ['ul','li','li strong'],
}

def theme(f):
    if f.startswith('tbg-'): return 'theme-tbg'
    if f.startswith('sc-'): return 'theme-sc'
    return None

def convert(path):
    f = os.path.basename(path)
    html = open(path).read()
    m = re.search(r'(\s*)<style>(.*?)</style>', html, re.S)
    css = m.group(2)
    rules = tokenize(css)  # keep ORIGINAL (unnormalized) text for inline retention
    inline = []
    keep = list(KEEP_SELECTORS.get(f, []))
    if f in MARKET: keep += ['.toc-card', '.toc-card:hover']
    for media, sel, decl in rules:
        if sel in keep:
            assert not media
            inline.append(normalize(f'{sel}{{{decl}}}', f))
    inline += EXTRA_INLINE.get(f) or [] if not isinstance(EXTRA_INLINE.get(f), type(None)) else []
    repl = m.group(1) + CSSLINK
    if inline:
        repl += m.group(1) + '<style>\n  ' + '\n  '.join(inline) + '\n</style>'
    html = html[:m.start()] + repl + html[m.end():]
    t = theme(f)
    if t:
        html = re.sub(r'<body(\s[^>]*)?>', lambda mm: f'<body class="{t}"' + (mm.group(1) or '') + '>', html, count=1)
    return html, css, inline, t

if __name__ == '__main__':
    for path in sys.argv[1:]:
        html, _, inline, t = convert(path)
        out = '/sessions/determined-cool-carson/mnt/outputs/' + os.path.basename(path)
        open(out,'w').write(html)
        print(f"{os.path.basename(path)}: theme={t}, inline rules={len(inline)} -> {out}")
