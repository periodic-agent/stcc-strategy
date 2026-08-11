#!/usr/bin/env python3
"""patch_scanner_suit_row.py -- suit chips: rulebook order, Directive in, Automated Command out.

- SUITS_DISPLAY follows the rulebook: Captain, Person, Cargo, Ship, Ally, Encounter, Incident,
  Location, Directive.
- Directive gets a chip. Its glyph is already in CARDFACE.suit, so no new asset; the colour
  darkens from #8494ad to #5a6678 so it reads as gray beside Ship's #7a8aaa.
- Automated Command is gone: no card carries the suit, and the disabled chip was a placeholder.
  Its three CSS rules and the disable branch go with it.
- Directive leaves EXCLUDED_SUITS, so its traits and skills count toward the pill numbers the
  way every other chipped suit does. Captain and Status stay excluded; Status remains
  query-only.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_suit_row.py [path/to/cards.html]
"""

import sys

EDITS = [
(
"""const SUITS_DISPLAY = ["Captain","Person","Ally","Ship","Cargo","Location","Encounter","Incident","Automated Command"];
const EXCLUDED_SUITS = new Set(["Captain","Directive","Status"]);""",
"""// Rulebook order. Directive has a chip; Status stays query-only (no glyph, 5 cards).
const SUITS_DISPLAY = ["Captain","Person","Cargo","Ship","Ally","Encounter","Incident","Location","Directive"];
const EXCLUDED_SUITS = new Set(["Captain","Status"]);"""
),
(
""".suit-pill[data-suit="Automated Command"]{border-color:#e8e8f0;color:#e8e8f0;}
.suit-pill[data-suit="Automated Command"]:hover{border-color:#fff;color:#fff;}
.suit-pill.active[data-suit="Automated Command"]{background:#e8e8f0;color:#000;}
""",
""""""
),
(
"""  const SUIT_COL={'Person':'#c9ab35','Ally':'#9b6ecf','Ship':'#7a8aaa','Cargo':'#3a6aaa','Location':'#4ac48a','Encounter':'#d4699f','Incident':'#e05a5a','Captain':'#d7dce6','Directive':'#8494ad','Status':'#88aacc','Automated Command':'#8494ad'};""",
"""  const SUIT_COL={'Person':'#c9ab35','Ally':'#9b6ecf','Ship':'#7a8aaa','Cargo':'#3a6aaa','Location':'#4ac48a','Encounter':'#d4699f','Incident':'#e05a5a','Captain':'#d7dce6','Directive':'#5a6678','Status':'#88aacc'};"""
),
(
"""  p.innerHTML=(gi?'<img src="'+gi+'" alt="">':'')+'<span class="lbl">'+s+'</span>';
  // Automated Command has no data/scans yet -- show but disable until cards land.
  if(s==='Automated Command'){
    p.classList.add('disabled');
    p.title='Coming soon';
  } else {
    p.onclick=()=>toggleToken(tokenOf('suit',s));
  }
  suitContainer.appendChild(p);""",
"""  p.innerHTML=(gi?'<img src="'+gi+'" alt="">':'')+'<span class="lbl">'+s+'</span>';
  p.onclick=()=>toggleToken(tokenOf('suit',s));
  suitContainer.appendChild(p);"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "Automated Command" not in src:
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
