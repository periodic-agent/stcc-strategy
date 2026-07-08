"""Compare effective CSS old vs new for converted guides + global safety checks."""
import re, sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
from parse import tokenize, normalize, FILES
from convert import convert, STCC, theme, MARKET

def props(decl):
    d = {}
    for part in decl.split(';'):
        if ':' in part:
            k, v = part.split(':', 1)
            d[k.strip()] = ' '.join(v.split()).rstrip()
    return d

def env_from_root(rootdecl):
    return props(rootdecl)

def expand(v, env, depth=0):
    if depth > 8: return v
    def sub(m):
        name = m.group(1).strip()
        return expand(env[name], env, depth+1) if name in env else m.group(0)
    return re.sub(r'var\((--[a-z0-9-]+)\)', sub, v, flags=re.I)

def effective(rule_list, env, themecls=None):
    """rule_list: (media, sel, decl). Returns {(media,sel): {prop: expanded}}, resolving
    body.theme-x prefixed selectors into their base selector when themecls matches."""
    out = {}
    for media, sel, decl in rule_list:
        for s in [x.strip() for x in sel.split(',')]:
            if s == ':root' or s.startswith('body.theme-'):
                m = re.match(r'body\.(theme-\w+)\s+(.+)', s)
                if m and themecls == m.group(1):
                    s = m.group(2).strip()
                else:
                    continue
            key = (media, s)
            out.setdefault(key, {}).update({k: expand(v, env) for k, v in props(decl).items()})
    return out

def old_effective(f, css):
    rules = tokenize(css)
    env = {}
    for media, sel, decl in rules:
        if sel == ':root': env.update(props(decl))
    return effective([(m,s,d) for m,s,d in rules if s != ':root'], env)

def new_effective(f, inline):
    t = theme(f)
    rules = tokenize(STCC)
    env = {}
    for media, sel, decl in rules:
        if sel == ':root': env.update(props(decl))
        if t and sel == f'body.{t}': env.update(props(decl))
    eff = effective([(m,s,d) for m,s,d in rules if s not in (':root',) or True], env, t)
    for r in inline:
        for m_, s_, d_ in tokenize(r):
            for s in [x.strip() for x in s_.split(',')]:
                eff.setdefault((m_, s), {}).update({k: expand(v, env) for k, v in props(d_).items()})
    return eff

report_lines = []
for path in sys.argv[1:]:
    f = os.path.basename(path)
    html, css, inline, t = convert(path)
    old = old_effective(f, css)
    new = new_effective(f, inline)
    print(f"== {f} (theme={t})")
    for key, oprops in sorted(old.items()):
        nprops = new.get(key)
        if nprops is None:
            print(f"  MISSING in new: {key}"); continue
        for p, v in oprops.items():
            nv = nprops.get(p)
            if nv is None:
                print(f"  {key} lost prop {p}: {v}")
            elif ' '.join(nv.split()).lower() != ' '.join(v.split()).lower():
                print(f"  DIFF {key} {p}: OLD[{v}] NEW[{nv}]")
    # selectors in new that old lacked, where the page actually uses the class/element
    body = re.sub(r'<style>.*?</style>','',open(path).read(),flags=re.S)
    classes = set(re.findall(r'class="([^"]+)"', body))
    used = set()
    for cs in classes: used.update(cs.split())
    for (media, s), nprops in new.items():
        if (media, s) in old: continue
        base = re.sub(r'::?[a-z-]+$','',s)
        toks = re.findall(r'\.([\w-]+)', base)
        eltag = re.match(r'^([a-z0-9]+)$', base)
        applies = (toks and all(tk in used for tk in toks)) or (eltag and re.search(f'<{base}[ >]', body))
        if applies:
            print(f"  NEW rule now applies: {(media, s)} -> {nprops}")
    print()
