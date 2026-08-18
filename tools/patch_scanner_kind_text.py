#!/usr/bin/env python3
"""patch_scanner_kind_text.py -- search text inside one kind of operation strip.

`text:` (and its alias `rules:`) search the concatenated strip text of a card, so they cannot
tell a phrase in a Reaction from the same phrase in a Play. Each of the 13 strip kinds now
doubles as a query key that searches only strips of that kind:

    reaction:"after putting a shady"    the phrase must sit in a Reaction strip
    activation:draw   play:enlist   passive:cloak   cost:glory

Negation works the same way: `-passive:cloak` drops cards whose Passive mentions cloak while
leaving cards that mention it elsewhere. `strip:<kind>` remains a presence test and `text:`
remains card-wide. The keys are generated from STRIP_KINDS, so a new kind in the data is
searchable without touching the parser.

The qualifier line of a strip (its "Action, Requires 3 Military" prefix) is searched along with
the body, since that is where costs and requirements live.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_kind_text.py [path/to/cards.html]
"""

import sys

EDITS = [
# parser: result bucket
(
"""             strips:[],negStrips:[],text:[],negText:[]};""",
"""             strips:[],negStrips:[],text:[],negText:[],kindText:[],negKindText:[]};"""
),
# parser: the 13 kinds become keys, before the name fallback
(
"""    } else if(key==='variant'){
      const v = (lv==='updated'||lv==='update') ? 'update'
              : (lv==='duplicate'||lv==='reprint'||lv==='dupe') ? 'duplicate' : lv;
      put(res.variants,res.negVariants,v);
    } else {""",
"""    } else if(key==='variant'){
      const v = (lv==='updated'||lv==='update') ? 'update'
              : (lv==='duplicate'||lv==='reprint'||lv==='dupe') ? 'duplicate' : lv;
      put(res.variants,res.negVariants,v);
    } else if(vocab.stripKinds && vocab.stripKinds[key]){
      // A strip kind used as a key searches only strips of that kind: reaction:"after putting".
      put(res.kindText,res.negKindText,{kind:key,term:lv});
    } else {"""
),
# vocab
(
"""  QUERY_VOCAB={allBoxes:ALL_BOXES,decks,suits,positions,""",
"""  // Every strip kind is also a query key; generated, so new kinds need no parser change.
  const stripKinds={};
  STRIP_KINDS.forEach(([k])=>{ stripKinds[k]=true; });
  QUERY_VOCAB={allBoxes:ALL_BOXES,decks,suits,positions,stripKinds,"""
),
# state
(
"""let activeStrips=new Set(), negStrips=new Set(), textTerms=[], negText=[];""",
"""let activeStrips=new Set(), negStrips=new Set(), textTerms=[], negText=[];
let kindText=[], negKindText=[];   // [{kind,term}] from reaction:"..." and friends"""
),
# applyQuery
(
"""  textTerms=q.text; negText=q.negText;""",
"""  textTerms=q.text; negText=q.negText;
  kindText=q.kindText; negKindText=q.negKindText;"""
),
# matcher
(
"""  if(textTerms.length||negText.length){
    const blob=(c.strips||[]).map(x=>x.text||'').join(' ').toLowerCase();
    if(textTerms.length && !textTerms.every(t=>blob.includes(t))) return false;
    if(negText.some(t=>blob.includes(t))) return false;
  }""",
"""  if(textTerms.length||negText.length){
    const blob=(c.strips||[]).map(x=>x.text||'').join(' ').toLowerCase();
    if(textTerms.length && !textTerms.every(t=>blob.includes(t))) return false;
    if(negText.some(t=>blob.includes(t))) return false;
  }
  if(kindText.length||negKindText.length){
    // Qualifier rides with the body: "Action, Requires 3 Military" is searchable text too.
    const inKind=(kind,term)=>(c.strips||[]).some(x=>
      String(x.kind||'').toLowerCase()===kind &&
      ((x.text||'')+' '+(x.qual||'')).toLowerCase().includes(term));
    if(kindText.length && !kindText.every(t=>inKind(t.kind,t.term))) return false;
    if(negKindText.some(t=>inKind(t.kind,t.term))) return false;
  }"""
),
# help bubble: the new row sits with the other strip rows
(
"""    <div class="qh-row"><code>text:cloak</code> &middot; <code>text:"gain 2"</code><span>search the rules text of every strip</span></div>""",
"""    <div class="qh-row"><code>text:cloak</code> &middot; <code>text:"gain 2"</code><span>search the rules text of every strip</span></div>
    <div class="qh-row"><code>reaction:"putting a shady"</code> &middot; <code>activation:draw</code><span>text inside one kind of strip; every strip name is a key</span></div>"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "kindText" in src:
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
