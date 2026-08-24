#!/usr/bin/env python3
"""patch_scanner_empty_landing.py -- land on an empty Images view.

Three changes to the state a visitor arrives in:

1. The view toggle starts on Images. Scans are what most people come for; the rendered text is
   the second read, not the first.
2. An empty search bar now selects no box at all, so the page opens empty rather than dumping
   556 cards on a phone. As soon as the bar has anything in it, a query with no box token falls
   back to the three main boxes as before, so clicking a deck or suit chip, or typing a name,
   shows results immediately.
3. The empty grid distinguishes the two cases: nothing chosen yet says "Select a box, or start
   typing, to see cards", while a query that genuinely matches nothing keeps "No cards match the
   current filters."

The Cards button is renamed Text, pairing with Images: one shows the scan, the other the text.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_empty_landing.py [path/to/cards.html]
"""

import sys

EDITS = [
# 1 -- buttons: label and which one starts active
(
"""      <button class="vtoggle active" id="btnPill" onclick="setView('pill')">Cards</button>
      <button class="vtoggle" id="btnImg" onclick="setView('image')">Images</button>""",
"""      <button class="vtoggle" id="btnPill" onclick="setView('pill')">Text</button>
      <button class="vtoggle active" id="btnImg" onclick="setView('image')">Images</button>"""
),
# 2 -- default view
(
"""let viewMode     = "pill";""",
"""let viewMode     = "image";   // scans first; the rendered text is the second read"""
),
# 3 -- an empty bar selects nothing; any query still defaults to the three main boxes
(
"""function applyQuery(text){
  const q=parseQuery(text,QUERY_VOCAB);
  activeBoxes=new Set(q.boxes.length?q.boxes.filter(b=>ALL_BOXES.includes(b)):DEFAULT_BOXES);""",
"""function applyQuery(text){
  const q=parseQuery(text,QUERY_VOCAB);
  // Empty bar = empty page. Anything in the bar without an explicit box: token falls back to
  // the three main boxes, so a deck chip or a typed name shows results straight away.
  const asked=String(text||'').trim().length>0;
  activeBoxes=new Set(q.boxes.length?q.boxes.filter(b=>ALL_BOXES.includes(b)):(asked?DEFAULT_BOXES:[]));"""
),
# 3b -- "no box tokens" now means none, so the default trio must be written explicitly
(
"""  const isDefault=target.length===DEFAULT_BOXES.length&&DEFAULT_BOXES.every(b=>target.includes(b));
  const isAll=ALL_BOXES.every(b=>target.includes(b));
  if(isAll) toks.push('box:all');
  else if(!target.length) toks.push('box:none');   // deselecting every box means: show nothing
  else if(!isDefault) target.forEach(b=>toks.push('box:'+b));""",
"""  const isAll=ALL_BOXES.every(b=>target.includes(b));
  // An empty bar now means an empty page, so the three main boxes are written out rather
  // than implied by the absence of tokens.
  if(isAll) toks.push('box:all');
  else if(!target.length) toks.push('box:none');   // deselecting every box means: show nothing
  else target.forEach(b=>toks.push('box:'+b));"""
),
# 3c -- the help row described the old behaviour
(
"""    <div class="qh-row"><code>box:promo1</code> \u00b7 <code>box:all</code><span>promos in; empty bar = the three main boxes</span></div>""",
"""    <div class="qh-row"><code>box:promo1</code> \u00b7 <code>box:all</code><span>promos in; empty bar = empty page</span></div>"""
),
# 3d -- Reset comment now describes the empty landing state
(
"""function clearAll(){
  // Full reset: empty bar = the default view (three main boxes, no filters).
  setQuery('');
}""",
"""function clearAll(){
  // Full reset: an empty bar is the arrival state, no box selected and no filters.
  setQuery('');
}"""
),
# 4 -- empty state tells the visitor what to do
(
"""  if(!total) groups.innerHTML='<div class="no-results">No cards match the current filters.</div>';""",
"""  if(!total){
    const untouched=!activeBoxes.size && !currentQuery().trim();
    groups.innerHTML='<div class="no-results">'
      +(untouched?'Select a box, or start typing, to see cards'
                 :'No cards match the current filters.')+'</div>';
  }"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "scans first; the rendered text is the second read" in src:
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
