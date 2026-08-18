#!/usr/bin/env python3
"""patch_scanner_cost_last.py -- Dev. Cost always renders at the bottom of the strip stack.

85 cards carry their cost strip first in the JSON, which is the order it was transcribed in, not
the order the card prints. On the printed card the development cost sits under the operations.

buildStrips now moves cost strips to the end before the family grouping runs, so the merge of
consecutive same-family strips is computed on the display order rather than the source order.
The sort is stable, so everything else keeps its transcribed sequence.

The data is left alone: this is presentation, and the JSONs stay a faithful transcription.

Content is built in memory and written once. Exact-string replacement, matching once.

Usage: python3 tools/patch_scanner_cost_last.py [path/to/cards.html]
"""

import sys

EDITS = [
(
"""function buildStrips(c){
  const list=c.strips||[];
  if(!list.length) return '';""",
"""function buildStrips(c){
  // Dev. Cost prints under the operations; the transcription often has it first.
  // Stable sort, so nothing else moves.
  const list=(c.strips||[]).slice()
    .map((s,i)=>[s,i])
    .sort((a,b)=>((String(a[0].kind||'').toLowerCase()==='cost')-(String(b[0].kind||'').toLowerCase()==='cost'))||(a[1]-b[1]))
    .map(p=>p[0]);
  if(!list.length) return '';"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "Dev. Cost prints under the operations" in src:
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
    print(f"patched {path}: {len(EDITS)} exact-string replacement")
    return 0


if __name__ == "__main__":
    sys.exit(main())
