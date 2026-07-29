#!/usr/bin/env python3
"""patch_scanner_strategy_banner.py -- repoint the header "New" banner at the strategy index.

The banner previously advertised To Boldly Go and Second Contact and, on click, selected those
two boxes. Both are selected by default now, so the copy was stale and the handler was a no-op
scroll. It now advertises the guide links and, on click, switches to Cards view (the Strategy
badge only appears there) and scrolls to the results. The banner is tinted teal to match the Strategy badge it points at.

`revealTBG` is replaced by `showStrategy`; the old name had no other callers.

Exact-string replacements; each must match exactly once. Verify with:
    node tools/test_scanner.mjs .

Usage: python3 tools/patch_scanner_strategy_banner.py [path/to/card-browser-mockup.html]
"""

import sys

EDITS = [
# --- banner tinted teal to match the Strategy badge -------------------------
(
""".new-banner{display:inline-flex;align-items:center;gap:0.55rem;margin-top:1rem;padding:0.28rem 0.75rem 0.28rem 0.32rem;background:rgba(212,74,74,0.08);border:1px solid rgba(212,74,74,0.35);border-radius:999px;font-family:'Exo 2',sans-serif;font-size:0.8rem;color:var(--text);text-decoration:none;cursor:pointer;transition:border-color .2s,background .2s,transform .2s;}
.new-banner:hover{border-color:rgba(240,126,126,0.75);background:rgba(212,74,74,0.15);transform:translateY(-1px);}""",
""".new-banner{display:inline-flex;align-items:center;gap:0.55rem;margin-top:1rem;padding:0.28rem 0.75rem 0.28rem 0.32rem;background:rgba(94,200,200,0.07);border:1px solid rgba(94,200,200,0.35);border-radius:999px;font-family:'Exo 2',sans-serif;font-size:0.8rem;color:var(--text);text-decoration:none;cursor:pointer;transition:border-color .2s,background .2s,transform .2s;}
.new-banner:hover{border-color:rgba(111,211,211,0.75);background:rgba(94,200,200,0.14);transform:translateY(-1px);}"""
),
(
"""  <a class="new-banner" onclick="revealTBG(event)" title="Show the To Boldly Go and Second Contact cards"><span class="new-badge">New</span><span>To Boldly Go and Second Contact are available now</span><span class="new-arrow">→</span></a>""",
"""  <a class="new-banner" onclick="showStrategy(event)" title="Cards discussed in the guides carry a Strategy tag"><span class="new-badge">New</span><span>Card search now links to the guides! Look for the Strategy tag</span><span class="new-arrow">→</span></a>"""
),
(
"""function revealTBG(e){
  if(e) e.preventDefault();
  ['tbg','2nd'].forEach(b=>{
    const pill=document.querySelector('.box-pill[data-box="'+b+'"]');
    if(pill && !pill.classList.contains('active')) pill.click();
  });
  const grp=document.getElementById('deckGroups');
  if(grp) grp.scrollIntoView({behavior:'smooth',block:'start'});
}""",
"""function showStrategy(e){
  if(e) e.preventDefault();
  // The Strategy badge lives on the detail cards, so make sure Cards view is up before scrolling.
  if(viewMode !== 'pill') setView('pill');
  const grp=document.getElementById('deckGroups');
  if(grp) grp.scrollIntoView({behavior:'smooth',block:'start'});
}"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "showStrategy" in src:
        print("already patched; nothing to do")
        return 0
    for old, new in EDITS:
        n = src.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for block starting {old.splitlines()[0][:60]!r}",
                  file=sys.stderr)
            return 1
        src = src.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(src)
    print(f"patched {path}: {len(EDITS)} exact-string replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
