#!/usr/bin/env python3
"""patch_scanner_empty_landing_fix.py -- actually open empty.

The previous change taught applyQuery that an empty bar selects no box, but the page never
called applyQuery on load: `activeBoxes` was initialised to DEFAULT_BOXES at declaration and
init() rendered straight from it, so a visitor still landed on all three boxes. The harness
missed it because its assertions called applyQuery('') first, which is not what the page does.

Two changes:
  - activeBoxes starts empty; DEFAULT_BOXES stays the fallback applyQuery uses once the bar has
    something in it.
  - init() runs the query path in both branches: a hash query if one was shared, otherwise
    applyQuery('') plus a pill sync, so what renders always reflects the bar.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_empty_landing_fix.py [path/to/cards.html]
"""

import sys

EDITS = [
(
"""let activeBoxes  = new Set(DEFAULT_BOXES);""",
"""let activeBoxes  = new Set();   // empty bar, empty page; DEFAULT_BOXES is the fallback in applyQuery"""
),
# currentQuery must never be undefined: init() now reads it before anything is typed
(
"""function currentQuery(){ return document.getElementById('searchInput').value; }""",
"""function currentQuery(){ return document.getElementById('searchInput').value||''; }"""
),
(
"""// restore a shared/bookmarked query from the URL hash
{const m=location.hash.match(/^#q=(.+)$/);
 if(m){const q=decodeURIComponent(m[1]);
   document.getElementById('searchInput').value=q;
   applyQuery(q); syncBoxPills(); syncFilterPills();}}""",
"""// Restore a shared/bookmarked query from the URL hash, otherwise apply the empty bar so the
// rendered state always comes from the query, never from the initial variables.
{const m=location.hash.match(/^#q=(.+)$/);
 const q=m?decodeURIComponent(m[1]):'';
 if(m) document.getElementById('searchInput').value=q;
 applyQuery(q); syncBoxPills(); syncFilterPills();}"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "empty bar, empty page" in src:
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
