#!/usr/bin/env python3
"""patch_scanner_easter_egg.py -- one hidden query in the search box.

Typing exactly two bare words, "picard" and "combo", in either order and with nothing else in
the bar, returns a fixed hand of four cards. Any other query, including "picard" on its own, is
untouched: the trigger requires the name terms to be exactly the pair, so nothing a user might
type by accident lands here.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_easter_egg.py [path/to/cards.html]
"""

import sys

EDITS = [
(
"""let gloryTests   = [];          // [{op,n}] from glory:N / glory>N""",
"""let comboIds     = null;        // set by the hidden query below, else null
// Hidden queries: exact bare-word set -> a fixed hand of card ids.
const EASTER_EGGS = [
  { words:['combo','picard'],
    ids:['picard-daystrom-institute','moriarty','picard-uss-bozeman','holographic-drone-ship'] }
];
let gloryTests   = [];          // [{op,n}] from glory:N / glory>N"""
),
(
"""  gloryTests=q.glory; negGlory=q.negGlory;""",
"""  // A hidden query takes over completely: no other token is present to combine with.
  const bare=[...nameTerms].sort().join(' ');
  const egg=EASTER_EGGS.find(e=>e.words.join(' ')===bare);
  comboIds = egg ? new Set(egg.ids) : null;
  gloryTests=q.glory; negGlory=q.negGlory;"""
),
(
"""function cardMatches(c){
  // Box membership (promos now live in activeBoxes as promo1/promo2)
  if(!activeBoxes.has(c.box)) return false;""",
"""function cardMatches(c){
  if(comboIds) return comboIds.has(c.id) && activeBoxes.has(c.box);
  // Box membership (promos now live in activeBoxes as promo1/promo2)
  if(!activeBoxes.has(c.box)) return false;"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "EASTER_EGGS" in src:
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
