#!/usr/bin/env python3
"""patch_scanner_strip_polish.py -- four fixes to how operation strips read.

1. Dev. Cost and No Play lose their filter chips. Both describe card furniture rather than an
   operation, so they cluttered the STRIP row. They remain valid query keys (`strip:cost`,
   `cost:glory`, `banner:`), which is why STRIP_KINDS is untouched and a display-only set does
   the hiding.

2. Strips span the full width of the card. The coloured body sized itself to its text, so a
   short line left a ragged stub; `flex:1` makes every strip run edge to edge the way the
   printed cards do.

3. Bare Military / Research / Influence in strip text become their medallions, the way the
   "<spec> Skill" and "<spec> Focus" pairs already did. 136 lines say things like "gain 1
   Military" with no Skill or Focus after them and were left as words. The specialty icons are
   already in the bundle (CARDFACE.skillChip), so no new asset.

4. The Resupply family, which also carries Control, takes a light green body instead of the
   neutral grey it shared with Play. Its bar is already green; the body now agrees with it.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_strip_polish.py [path/to/cards.html]
"""

import sys

EDITS = [
# 1 -- chips hidden, keys kept
(
"""STRIP_KINDS.forEach(([kind,label])=>{""",
"""// Furniture rather than operations: no chip, but strip:cost / cost: still query.
const STRIP_CHIPS_HIDDEN=new Set(['cost','banner']);
STRIP_KINDS.filter(([kind])=>!STRIP_CHIPS_HIDDEN.has(kind)).forEach(([kind,label])=>{"""
),
# 2 -- full-width strips
(
""".opstrip .body{padding:.2rem .45rem .22rem .4rem;font-family:'Barlow Condensed',sans-serif;
  font-weight:500;font-size:.8rem;line-height:1.24;}""",
""".opstrip .body{flex:1;min-width:0;padding:.2rem .45rem .22rem .4rem;font-family:'Barlow Condensed',sans-serif;
  font-weight:500;font-size:.8rem;line-height:1.24;}"""
),
# 3 -- bare specialty words become medallions
(
"""  Object.keys(STRIP_SUIT_COL).forEach(w=>{""",
"""  // A bare specialty ("gain 1 Military") gets the same medallion as the Skill/Focus pair
  // above; run after that pass so "Military Skill" is already consumed.
  STRIP_SPEC.forEach(sp=>{
    if(sp==='Any'||sp==='Variable') return;
    t=t.replace(new RegExp('\\\\b'+sp+'\\\\b','g'),'{spec:'+sp+'}');
  });
  Object.keys(STRIP_SUIT_COL).forEach(w=>{"""
),
(
"""  if((m=t.match(/^(skill|focus):(.+)$/))){""",
"""  if((m=t.match(/^spec:(.+)$/))){
    const src=(CARDFACE.skillChip||CARDFACE.skill||{})[m[1].toLowerCase()];
    return src?'<img class="stripimg" src="'+src+'" alt="'+m[1]+'">':m[1];
  }
  if((m=t.match(/^(skill|focus):(.+)$/))){"""
),
]

# 4 -- palette: Resupply/Control body goes light green
PALETTE_EDIT = ('"resupply"', '#e9e8e2', '#dff0da')


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "STRIP_CHIPS_HIDDEN" in src:
        print("already patched; nothing to do")
        return 0
    out = src
    for old, new in EDITS:
        n = out.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for {old.splitlines()[0][:60]!r}", file=sys.stderr)
            return 1
        out = out.replace(old, new, 1)

    # The palette is inlined in the page as STRIP_PALETTE; recolour only the resupply body.
    import re
    m = re.search(r'const STRIP_PALETTE=(\{.*?\});', out, re.S)
    if not m:
        print("refusing to patch: STRIP_PALETTE not found", file=sys.stderr)
        return 1
    block = m.group(1)
    rm = re.search(r'"resupply"\s*:\s*\{[^}]*?"body"\s*:\s*"(#[0-9a-fA-F]{6})"', block)
    if not rm:
        print("refusing to patch: resupply body colour not found", file=sys.stderr)
        return 1
    new_block = block[:rm.start(1)] + '#dff0da' + block[rm.end(1):]
    out = out[:m.start(1)] + new_block + out[m.end(1):]

    open(path, "w", encoding="utf-8").write(out)
    print(f"patched {path}: {len(EDITS)} replacements + resupply body colour")
    return 0


if __name__ == "__main__":
    sys.exit(main())
