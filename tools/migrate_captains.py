import re, base64, os, json, sys, unicodedata

APPLY = '--apply' in sys.argv
cards = json.load(open('/tmp/chk/box1.json'))
cards = cards if isinstance(cards, list) else cards.get('cards')
HAVE = set(os.listdir('/tmp/chk/img/box1'))
def norm(s): return re.sub(r'\s+',' ',unicodedata.normalize('NFKD',s).replace('’',"'").replace('&amp;','&')).strip().lower()
BYNAME = {norm(c['name']): c['filename'] for c in cards}
CAPTAIN = {  # guide -> captain card filename
  'koloth': BYNAME[norm('Koloth, the Dahar Master')], 'picard': BYNAME[norm('Jean-Luc Picard')],
  'sela': BYNAME[norm('Sela')], 'sisko': BYNAME[norm('Benjamin Sisko')], 'burnham': BYNAME[norm('Michael Burnham')]}

def make_lookup(tag):
    pref = {norm(re.sub(r'\s*\(%s\)'%tag,'',c['name'],flags=re.I)): c['filename']
            for c in cards if f'({tag})' in c['name'].lower()}
    def lookup(name):
        n = norm(name)
        while True:
            n2 = re.sub(r'\s*[—-]\s*discard pile$','',n)
            n2 = re.sub(r'\s*\([^)]*\)\s*$','',n2).strip()
            if n2 == n: break
            n = n2
        fn = pref.get(n) or BYNAME.get(n)
        return fn if fn and fn in HAVE else None
    return lookup

def scan_tokens(alt):
    toks = []
    for seg in re.split(r'\s—\s', alt):
        for part in re.split(r',', seg):
            part = re.sub(r'^\s*\w[\w ]*:\s*', '', part).strip()  # drop "Reserve:" style labels
            if part: toks.append(part)                                # try full part first
            for t in re.split(r'\s+and\s+', part):
                t = t.strip()
                if t and t != part: toks.append(t)
    return toks

def migrate(g):
    h = open(f'{g}.html').read()
    orig = len(h)
    lookup = make_lookup(g)
    report = {'unmatched_sections': [], 'unmatched_tokens': [], 'rows': []}

    # --- sections ---
    covered = set()
    imgdiv = lambda fn, name: f'\n<div class="card-img"><img src="img/box1/{fn}" alt="{name}" loading="lazy" onclick="openLightbox(this)"></div>'
    if g == 'burnham':
        def para_repl(m):
            title = m.group(2)
            fn = lookup(title)
            if not fn:
                report['unmatched_sections'].append(title); return m.group(0)
            covered.add(fn)
            return m.group(0) + imgdiv(fn, re.sub(r'\s*\([^)]*\)\s*$','',title))
        h = re.sub(r'(<p><strong>([^<]{3,60})</strong>.*?</p>)', para_repl, h, flags=re.S)
    else:
        def h3_repl(m):
            title = re.sub('<[^>]+>','',m.group(1))
            fn = lookup(title)
            if not fn:
                report['unmatched_sections'].append(title); return m.group(0)
            covered.add(fn)
            return m.group(0) + imgdiv(fn, re.sub(r'\s*\([^)]*\)\s*$','',re.sub(r'\s*[—-]\s*Discard Pile$','',title)))
        h = re.sub(r'<h3[^>]*>(.*?)</h3>', h3_repl, h)

    # --- embeds ---
    os.makedirs(f'imgwork/repo/img/guides/{g}', exist_ok=True)
    def img_repl(m):
        tag = m.group(0)
        alt = (re.search(r'alt="([^"]*)"', tag) or [None,''])[1] if 'alt="' in tag else ''
        if 'captain board' in alt.lower():
            side = 'advanced' if 'advanced' in alt.lower() else 'basic'
            fn = f'{g}-board-{side}.jpg'
            data = re.search(r'base64,([^"]+)"', tag).group(1)
            if APPLY: open(f'imgwork/repo/img/guides/{g}/{fn}','wb').write(base64.b64decode(data))
            return f'<img src="img/guides/{g}/{fn}" alt="{alt}" loading="lazy" onclick="openLightbox(this)">'
        # card scan: build replacement row from uncovered cards in alt
        row_imgs = []
        for t in scan_tokens(alt):
            if re.search(r'captain card', t, re.I):
                fn = CAPTAIN[g]
            else:
                fn = lookup(t)
            if not fn:
                report['unmatched_tokens'].append((alt[:40], t)); continue
            if fn in covered: continue
            covered.add(fn)
            row_imgs.append(f'<img src="img/box1/{fn}" alt="{t}" loading="lazy" onclick="openLightbox(this)">')
        if row_imgs:
            report['rows'].append((alt[:50], len(row_imgs)))
            return '\n'.join(row_imgs)
        return ''
    h = re.sub(r'<img[^>]*src="data:image/[a-z]+;base64,[^"]+"[^>]*>', img_repl, h)
    h = re.sub(r'<div class="card-row">\s*</div>\s*', '', h)

    if APPLY:
        open(f'{g}.html','w').write(h)
    n_lazy_missing = len([t for t in re.findall(r'<img[^>]+>', h) if 'loading=' not in t and 'lb-img' not in t and 'lightbox-img' not in t and 'youtube' not in t])
    print(f"== {g}: {orig//1024}K -> {len(h)//1024}K | sections unmatched: {report['unmatched_sections']} | token misses: {report['unmatched_tokens']} | scan rows kept: {report['rows']} | imgs missing lazy: {n_lazy_missing} | b64 left: {len(re.findall('base64,',h))-1}")

for g in ['koloth','picard','sela','sisko','burnham']:
    migrate(g)
