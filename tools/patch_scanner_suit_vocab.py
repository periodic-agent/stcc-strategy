#!/usr/bin/env python3
"""patch_scanner_suit_vocab.py -- suit search covers every suit, and bare suit words work.

Two related fixes in cards.html:

1. The query suit vocabulary was built from SUITS_DISPLAY, the eight pill suits, so Captain,
   Directive and Status had no lowercase entry: `suit:captain` matched nothing while
   `suit:Captain` worked. The vocabulary now folds over every suit present in the card data,
   with SUITS_DISPLAY kept for entries like Automated Command that may have no cards yet.

2. A bare word that names a suit now returns the union of that suit's cards and cards with the
   word in their name: `status` gives Status cards plus any card called "... status ...", while
   `suit:status` stays exact. Negation follows the same rule, so `-captain` drops both.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_suit_vocab.py [path/to/cards.html]
"""

import sys

EDITS = [
(
"""  QUERY_VOCAB={allBoxes:ALL_BOXES,decks,suits:map(SUITS_DISPLAY),positions,""",
"""  // Suits are folded from the DATA, not from the pill list: Captain, Directive and Status
  // have cards but no pill, and used to be unmatchable in lowercase.
  const suits=map(SUITS_DISPLAY);
  FULL_POOL.forEach(c=>{ if(c.suit) suits[String(c.suit).toLowerCase()]=c.suit; });
  QUERY_VOCAB={allBoxes:ALL_BOXES,decks,suits,positions,"""
),
(
"""  const lname=c.name.toLowerCase();
  if(nameTerms.length && !nameTerms.every(t=>lname.includes(t))) return false;
  if(negNames.some(t=>lname.includes(t))) return false;""",
"""  // A bare word matches the card name OR its suit, so "status" finds Status cards as well as
  // cards with status in the name. suit: stays exact.
  const lname=c.name.toLowerCase();
  const lsuit=(c.suit||'').toLowerCase();
  const bare=t=>lname.includes(t)||lsuit===t;
  if(nameTerms.length && !nameTerms.every(bare)) return false;
  if(negNames.some(bare)) return false;"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "const bare=t=>" in src:
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
