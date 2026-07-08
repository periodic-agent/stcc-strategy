import re, os, json, sys, unicodedata

APPLY = '--apply' in sys.argv
cards = json.load(open('/tmp/chk/box1.json'))
cards = cards if isinstance(cards,list) else cards.get('cards')
HAVE = set(os.listdir('/tmp/chk/img/box1'))
PROMO = set(os.listdir('/tmp/chk/img/promo1'))
def norm(s): return re.sub(r'\s+',' ',unicodedata.normalize('NFKD',s).replace('’',"'").replace('&amp;','&')).strip().lower()
def slug(s):
    s = norm(s).replace("'","").replace('.','').replace(',','')
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')
BYNAME = {norm(c['name']): ('img/box1/'+c['filename']) for c in cards if c['filename'] in HAVE}
PROMO_BY_SLUG = {f[:-4]: 'img/promo1/'+f for f in PROMO}
ALIAS = {'borg spatial trajector': 'img/box1/borg-spatial-trajectory.jpg'}

def lookup(title):
    n = norm(title)
    n = re.sub(r'\s*[—-]\s*promo pack \d+$','',n)
    n = re.sub(r'\s*\([^)]*\)\s*$','',n).strip()
    return BYNAME.get(n) or ALIAS.get(n) or PROMO_BY_SLUG.get(slug(n))

def migrate(g):
    h = open(f'{g}.html').read()
    orig = len(h)
    covered, unmatched, dropped_tokens = set(), [], []
    def h3_repl(m):
        title = re.sub('<[^>]+>','',m.group(1))
        fn = lookup(title)
        if not fn:
            unmatched.append(title); return m.group(0)
        covered.add(fn)
        alt = re.sub(r'\s*[—-]\s*Promo Pack \d+\s*$','',re.sub(r'\s*\([^)]*\)\s*$','',title)).strip()
        return m.group(0) + f'\n<div class="card-img"><img src="{fn}" alt="{alt}" loading="lazy" onclick="openLightbox(this)"></div>'
    h = re.sub(r'<h3[^>]*>(.*?)</h3>', h3_repl, h)
    def img_repl(m):
        tag = m.group(0)
        alt = re.search(r'alt="([^"]*)"', tag).group(1) if 'alt="' in tag else ''
        keep = []
        for seg in re.split(r'\s—\s', alt):
            for t in re.split(r',', seg):
                t = re.sub(r'^\s*\w[\w ]*:\s*','',t).strip()
                if not t: continue
                fn = lookup(t)
                if fn and fn not in covered:
                    covered.add(fn)
                    keep.append(f'<img src="{fn}" alt="{t}" loading="lazy" onclick="openLightbox(this)">')
                elif not fn:
                    dropped_tokens.append(t)
        return '\n'.join(keep)
    h = re.sub(r'<img[^>]*src="data:image/[a-z]+;base64,[^"]+"[^>]*>', img_repl, h)
    h = re.sub(r'<div class="card-row">\s*</div>\s*', '', h)
    if APPLY: open(f'{g}.html','w').write(h)
    print(f"== {g}: {orig//1024}K -> {len(h)//1024}K | h3 unmatched: {unmatched} | scan tokens dropped: {dropped_tokens} | b64 left: {len(re.findall('base64,',h))-1}")

for g in ['persons','allies','cargo','locations','ships','encounters-incidents']:
    migrate(g)
