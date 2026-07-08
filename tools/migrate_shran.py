import re, base64, os, json, unicodedata

h = open('/sessions/determined-cool-carson/mnt/outputs/shran.html').read()
orig_size = len(h)
cards = json.load(open('/tmp/chk/box1.json'))
cards = cards if isinstance(cards, list) else cards.get('cards')
have = set(os.listdir('/tmp/chk/img/box1'))

def norm(s):
    return re.sub(r'\s+',' ', unicodedata.normalize('NFKD',s).replace('’',"'")).strip().lower()

byname = {norm(c['name']): c['filename'] for c in cards}
# prefer Shran deck variants
SHRAN_PREF = {norm(re.sub(r'\s*\(shran\)','',c['name'],flags=re.I)): c['filename']
              for c in cards if '(shran)' in c['name'].lower()}

def lookup(name):
    n = norm(re.sub(r'\s*\([^)]*\)\s*$','',name))
    return SHRAN_PREF.get(n) or byname.get(n)

# --- 1. boards: extract, relink ---
os.makedirs('/sessions/determined-cool-carson/mnt/outputs/imgwork/repo/img/guides/shran', exist_ok=True)
BOARDS = {'Shran Captain Board — Basic Side':'shran-board-basic.jpg',
          'Shran Captain Board — Advanced Side':'shran-board-advanced.jpg'}
def img_repl(m):
    tag = m.group(0)
    alt = re.search(r'alt="([^"]*)"', tag).group(1)
    if alt in BOARDS:
        data = re.search(r'base64,([^"]+)"', tag).group(1)
        fn = BOARDS[alt]
        open(f'/sessions/determined-cool-carson/mnt/outputs/imgwork/repo/img/guides/shran/{fn}','wb').write(base64.b64decode(data))
        return f'<img src="img/guides/shran/{fn}" alt="{alt}" loading="lazy">'
    return ''  # scans dropped (their empty card-row removed below)
h = re.sub(r'<img[^>]*src="data:image/[a-z]+;base64,[^"]+"[^>]*>', img_repl, h)
h = re.sub(r'<div class="card-row">\s*</div>\s*', '', h)  # empty rows left by scan removal

# --- 2. per-section card images after each h3 ---
missing = []
def h3_repl(m):
    title = re.sub('<[^>]+>','',m.group(1))
    fn = lookup(title)
    if not fn or fn not in have:
        missing.append(title); return m.group(0)
    name = title.replace('"','')
    return (m.group(0) + f'\n<div class="card-img"><img src="img/box1/{fn}" alt="{name}" loading="lazy"></div>')
h = re.sub(r'<h3[^>]*>(.*?)</h3>', h3_repl, h)

# --- 3. captain + Kumari row after the intro paragraph that presents the Kumari ---
anchor = re.search(r'<p>[^<]*starts with the Kumari in play.*?</p>', h, re.S).group(0)
row = ('\n<div class="card-row">'
       f'\n<img src="img/box1/shran-thylek-shran.jpg" alt="Thy’lek Shran" loading="lazy">'
       f'\n<img src="img/box1/shran-kumari.jpg" alt="Kumari" loading="lazy">'
       '\n</div>')
h = h.replace(anchor, anchor + row, 1)

h = h.replace("document.querySelectorAll('.card-row img')",
              "document.querySelectorAll('.card-row img,.card-img img')")
open('/sessions/determined-cool-carson/mnt/outputs/shran.html','w').write(h)
print(f"size: {orig_size//1024}K -> {len(h)//1024}K; unmatched h3: {missing}")
print("remaining base64:", len(re.findall('base64,', h)))
print("lib imgs:", len(re.findall(r'img/box1/', h)), "| board imgs:", len(re.findall(r'img/guides/', h)))
print("imgs w/o lazy:", len([t for t in re.findall(r'<img[^>]+>', h) if 'loading=' not in t and 'lightbox-img' not in t]))
