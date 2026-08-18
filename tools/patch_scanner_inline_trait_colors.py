#!/usr/bin/env python3
"""patch_scanner_inline_trait_colors.py -- colour the trait chips inside strip text.

Two parts.

REVERT. The previous commit recoloured the vertical trait pills on the card face and the trait
filter chips. That was the wrong target: those read correctly as they were. Both go back to
their sampled values (species #e2a04a, regular #79b3c7, other #c85340, white labels).

FIX. The chips that sit inline in the strip text were the muted ones: every trait rendered on a
flat slate #556 regardless of family, so KLINGON, STARFLEET and ATTACK all looked the same. They
now take the family colour the vertical pills use, resolved against the live trait lists, so a
trait added to a future box is coloured without touching this code. Wildcard takes the pale
salmon and a dark label, matching .vt-variable.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_inline_trait_colors.py [path/to/cards.html]
"""

import sys

EDITS = [
# --- revert: card-face pills -------------------------------------------------
(
"""/* Site palette, not the scans: the printed cards are far too muted to sample.
   Dark ink because these fills are bright enough that white would be the weaker pair. */
.vt-species{background:#e09050;color:#14161c;}
.vt-regular{background:#4a9fd4;color:#14161c;}
.vt-other{background:#e05a5a;color:#14161c;}""",
""".vt-species{background:#e2a04a;}
.vt-regular{background:#79b3c7;}
.vt-other{background:#c85340;}"""
),
# --- revert: filter chips ----------------------------------------------------
(
"""/* Same palette as the card-face pills; see .vt-species and friends. */
.cp-species{--cc:#e09050;}
.cp-regular{--cc:#4a9fd4;}
.cp-other{--cc:#e05a5a;}
/* Filled, these three are bright enough that near-black beats white. */
.cp-species.active,.cp-regular.active,.cp-other.active{color:#14161c !important;}""",
""".cp-species{--cc:#e2a04a;}
.cp-regular{--cc:#79b3c7;}
.cp-other{--cc:#c85340;}"""
),
# --- fix: inline chips take the family colour --------------------------------
(
"""  if((m=t.match(/^trait:(.+)$/))){
    const k=m[1].toLowerCase().replace(/['\\u2019]/g,'').replace(/\\s+/g,'-');
    const ic=CARDFACE.traitChip[k];
    return '<span class="stripchip'+(ic?'':' plain')+'" style="background:#556">'
      +(ic?'<img src="'+ic+'" alt="">':'')+m[1].toUpperCase()+'</span>';
  }""",
"""  if((m=t.match(/^trait:(.+)$/))){
    const k=m[1].toLowerCase().replace(/['\\u2019]/g,'').replace(/\\s+/g,'-');
    const ic=CARDFACE.traitChip[k];
    const fam=traitFamily(m[1]);
    const col=TRAIT_FAM_COL[fam]||'#556';
    const ink=fam==='variable'?'#141821':'#fff';
    return '<span class="stripchip'+(ic?'':' plain')+'" style="background:'+col+';color:'+ink+'">'
      +(ic?'<img src="'+ic+'" alt="">':'')+m[1].toUpperCase()+'</span>';
  }"""
),
(
"""function stripIcon(key){""",
"""// Family colours shared with the vertical pills on the card face (.vt-species and friends).
const TRAIT_FAM_COL={species:'#e2a04a',regular:'#79b3c7',other:'#c85340',variable:'#f6c9bd'};
// Resolved against the live trait lists rather than a hardcoded table, so a trait that
// arrives with a future box is coloured without an edit here.
function traitFamily(name){
  if(String(name).toLowerCase()==='wildcard') return 'variable';
  const has=(list,n)=>Array.isArray(list)&&list.some(x=>x.toLowerCase()===n);
  const n=String(name).toLowerCase();
  if(has(allSpecies,n)) return 'species';
  if(has(allOther,n))   return 'other';
  if(has(allRegular,n)) return 'regular';
  return 'regular';
}

function stripIcon(key){"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "TRAIT_FAM_COL" in src:
        print("already patched; nothing to do")
        return 0
    out = src
    for old, new in EDITS:
        n = out.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for {old.splitlines()[0][:60]!r}", file=sys.stderr)
            return 1
        out = out.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(out)
    print(f"patched {path}: {len(EDITS)} exact-string replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
