import re, glob, json

def tokenize(css):
    """Return list of (media, selector, decl) preserving @media context."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out, i, media = [], 0, ''
    stack = []
    while i < len(css):
        m = re.match(r'\s*@media([^{]+)\{', css[i:])
        if m:
            media = ' '.join(m.group(1).split()); i += m.end(); stack.append('media'); continue
        m = re.match(r'\s*\}', css[i:])
        if m:
            if stack: stack.pop(); media = ''
            i += m.end(); continue
        m = re.match(r'\s*([^{}]+?)\s*\{([^{}]*)\}', css[i:], re.S)
        if m:
            out.append((media, ' '.join(m.group(1).split()), ' '.join(m.group(2).split())))
            i += m.end(); continue
        break
    return out

def normalize(decl_or_sel, f):
    # two-phase var rename to avoid collisions
    if f == 'shran.html':
        pairs = [('--andorian','\x01ACC\x01'), ('--and2','\x01AC2\x01'), ('--accent','\x01WARN\x01')]
        final = {'\x01ACC\x01':'--accent','\x01AC2\x01':'--accent2','\x01WARN\x01':'--warn'}
    elif f.startswith('tbg-'):
        pairs = [('--red2','\x01AC2\x01'), ('--red','\x01ACC\x01')]
        final = {'\x01ACC\x01':'--accent','\x01AC2\x01':'--accent2'}
    elif f.startswith('sc-'):
        pairs = [('--amber2','\x01AC2\x01'), ('--amber','\x01ACC\x01')]
        final = {'\x01ACC\x01':'--accent','\x01AC2\x01':'--accent2'}
    else:
        pairs = [('--blue2','\x01AC2\x01'), ('--blue','\x01ACC\x01')]
        final = {'\x01ACC\x01':'--accent','\x01AC2\x01':'--accent2'}
    s = decl_or_sel
    for a,b in pairs: s = s.replace(a,b)
    for a,b in final.items(): s = s.replace(a,b)
    return s

FILES = sorted(f for f in glob.glob('*.html') if f not in ('harmless_kitten.html','card-browser-mockup.html','cards.html','index.html'))

def parsed(f):
    css = re.search(r'<style>(.*?)</style>', open(f).read(), re.S).group(1)
    return [(m, normalize(s,f), normalize(d,f)) for m,s,d in tokenize(css)]

if __name__ == '__main__':
    from collections import defaultdict
    groups = defaultdict(lambda: defaultdict(list))
    for f in FILES:
        for m,s,d in parsed(f):
            groups[(m,s)][re.sub(r';\s*$','',d)].append(f)
    report = {}
    for (m,s),vars_ in sorted(groups.items()):
        report[f"{m} || {s}"] = {v: fs for v,fs in vars_.items()}
    json.dump(report, open('/sessions/determined-cool-carson/mnt/outputs/csswork/rules.json','w'), indent=1)
    n_conflict = sum(1 for k,v in report.items() if len(v)>1)
    print(f"{len(report)} (media,selector) groups; {n_conflict} with variants")
    for k,v in report.items():
        if len(v)>1: print(' *', k, '->', [len(fs) for fs in v.values()])
