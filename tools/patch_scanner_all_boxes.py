#!/usr/bin/env python3
"""patch_scanner_all_boxes.py -- Box row: default to the three main boxes, add an "All" pill.

Changes (27 Jul 2026):
1. `DEFAULT_BOXES` / `ALL_BOXES` constants declared before `activeBoxes`, which now opens on
   Captain's Chair + To Boldly Go + Second Contact instead of Captain's Chair alone. Promos
   stay off by default.
2. A gray "All" pill leads the Box row. One click selects every box including both promos;
   a second click, while all five are on, returns to the three-box default.
3. `syncBoxPills()` reflects `activeBoxes` back into the pill row, so the All pill lights up
   only while all five boxes are selected and dims the moment any box is toggled off.

Exact-string replacements; each must match exactly once. Verify with:
    node tools/test_scanner.mjs .

Usage: python3 tools/patch_scanner_all_boxes.py [path/to/card-browser-mockup.html]
"""

import sys

EDITS = [
# --- CSS: gray All pill, sitting ahead of the box pills ---------------------
(
""".box-pill{font-family:'Exo 2',sans-serif;font-size:0.72rem;padding:0.22rem 0.75rem;border-radius:3px;border:1px solid var(--border);color:var(--muted);cursor:pointer;transition:all 0.15s;user-select:none;}""",
""".box-pill{font-family:'Exo 2',sans-serif;font-size:0.72rem;padding:0.22rem 0.75rem;border-radius:3px;border:1px solid var(--border);color:var(--muted);cursor:pointer;transition:all 0.15s;user-select:none;}
.box-pill[data-box="all"]{border-color:#7a8aaa;color:#9aa8bc;margin-right:0.35rem;}
.box-pill[data-box="all"]:hover{border-color:#a8b4c8;color:#c8d2e0;}
.box-pill[data-box="all"].active{background:#7a8aaa;border-color:#7a8aaa;color:#0a0e1a;font-weight:600;}"""
),
# --- default selection ------------------------------------------------------
(
"""let activeBoxes  = new Set(["core"]);""",
"""// The three main boxes open selected; promos stay off until asked for.
// The "All" pill toggles between ALL_BOXES and DEFAULT_BOXES.
const DEFAULT_BOXES = ['core','tbg','2nd'];
const ALL_BOXES     = ['core','tbg','2nd','promo1','promo2'];
let activeBoxes  = new Set(DEFAULT_BOXES);"""
),
# --- global helper: pill row follows activeBoxes -----------------------------
(
"""function clearAll(){""",
"""// Reflect activeBoxes back into the Box pill row. The All pill is active only while
// every box is selected, so it dims as soon as any single box is toggled off.
function syncBoxPills(){
  document.querySelectorAll('.box-pill').forEach(p=>{
    const id=p.dataset.box;
    if(id==='all') p.classList.toggle('active', ALL_BOXES.every(b=>activeBoxes.has(b)));
    else p.classList.toggle('active', activeBoxes.has(id));
  });
}

function clearAll(){"""
),
# --- build the row: All pill first, individual pills keep it in sync ---------
(
"""const boxContainer = document.getElementById('boxFilters');
boxDefs.forEach(({id,label})=>{
  const p=document.createElement('span');
  p.className='box-pill'+(id==='core'?' active':'');
  p.dataset.box=id; p.textContent=label;
  p.onclick=()=>{ if(activeBoxes.has(id)) activeBoxes.delete(id); else activeBoxes.add(id); p.classList.toggle('active'); render(); };
  boxContainer.appendChild(p);
});""",
"""const boxContainer = document.getElementById('boxFilters');

// "All" leads the row: select everything, or fall back to the default three.
const allPill=document.createElement('span');
allPill.className='box-pill'; allPill.dataset.box='all'; allPill.textContent='All';
allPill.onclick=()=>{
  const everythingOn = ALL_BOXES.every(b=>activeBoxes.has(b));
  activeBoxes.clear();
  (everythingOn ? DEFAULT_BOXES : ALL_BOXES).forEach(b=>activeBoxes.add(b));
  syncBoxPills(); render();
};
boxContainer.appendChild(allPill);

boxDefs.forEach(({id,label})=>{
  const p=document.createElement('span');
  p.className='box-pill';
  p.dataset.box=id; p.textContent=label;
  p.onclick=()=>{ if(activeBoxes.has(id)) activeBoxes.delete(id); else activeBoxes.add(id); syncBoxPills(); render(); };
  boxContainer.appendChild(p);
});
syncBoxPills();"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "card-browser-mockup.html"
    src = open(path, encoding="utf-8").read()
    if "ALL_BOXES" in src:
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
