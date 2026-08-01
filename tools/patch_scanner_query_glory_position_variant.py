#!/usr/bin/env python3
"""patch_scanner_query_glory_position_variant.py -- three new search keys.

Adds to the query language in cards.html:

  glory:4  glory>4  glory>=4  glory<3  glory:>=4     numeric, on the resolved glory value.
                                                     A card with no glory never matches, in any
                                                     direction, including negation of a range.
  position:reserve  position:incident-deck           starting-position indicator. Hyphens stand
  position:"incident deck"                           in for spaces so phones need no quotes.
  variant:update  variant:duplicate                  matches the badge as displayed, which is
  variant:updated variant:reprint                    computed against the selected boxes: with
                                                     only Box 1 showing, a card reprinted in
                                                     Box 2 wears no badge and does not match.

All three honour the leading '-' negation the rest of the language uses.

Per the convention recorded in WORKFLOW.md, the patched text is built in memory and only then
written, so a failed patch cannot truncate the scanner.

Exact-string replacements; each must match exactly once. Verify with:
    node tools/test_scanner_query.mjs
    node tools/test_scanner.mjs .

Usage: python3 tools/patch_scanner_query_glory_position_variant.py [path/to/cards.html]
"""

import sys

EDITS = [
# 1. parser: new result buckets, comparison-aware tokenizer, three new keys ----
(
"""function parseQuery(text, vocab){
  const res={boxes:[],decks:[],suits:[],tags:[],skills:[],names:[],
             negBoxes:[],negDecks:[],negSuits:[],negTags:[],negSkills:[],negNames:[]};
  const tokRe=/(-)?(?:([A-Za-z]+):)?("([^"]*)"|[^\\s"]+)/g;""",
"""function parseQuery(text, vocab){
  const res={boxes:[],decks:[],suits:[],tags:[],skills:[],names:[],
             negBoxes:[],negDecks:[],negSuits:[],negTags:[],negSkills:[],negNames:[],
             glory:[],negGlory:[],positions:[],negPositions:[],variants:[],negVariants:[]};
  // A key may be followed by ':' or by a comparison operator, so both glory>4 and
  // glory:>4 parse. The operator is captured separately from the value.
  const tokRe=/(-)?(?:([A-Za-z]+)\\s*(:|>=|<=|>|<))?("([^"]*)"|[^\\s"]+)/g;"""
),
(
"""    const neg=!!m[1];
    const key=(m[2]||'').toLowerCase();
    const val=(m[4]!==undefined?m[4]:m[3]).trim();
    if(!val) continue;
    const lv=val.toLowerCase();""",
"""    const neg=!!m[1];
    const key=(m[2]||'').toLowerCase();
    let op=(m[3]||'');
    let val=(m[5]!==undefined?m[5]:m[4]).trim();
    if(!val) continue;
    // glory:>=4 puts the operator in the value; move it onto op.
    const opInVal=val.match(/^(>=|<=|>|<|=)\\s*(.*)$/);
    if(opInVal && key){ op=opInVal[1]==='='?':':opInVal[1]; val=opInVal[2].trim(); }
    if(!val) continue;
    const lv=val.toLowerCase();"""
),
(
"""    } else if(key==='focus'){
      put(res.skills,res.negSkills,(vocab.focusShort&&vocab.focusShort[lv])||val);
    } else {""",
"""    } else if(key==='focus'){
      put(res.skills,res.negSkills,(vocab.focusShort&&vocab.focusShort[lv])||val);
    } else if(key==='glory'){
      const n=Number(lv);
      if(Number.isFinite(n)) put(res.glory,res.negGlory,{op:(op===':'?'=':op)||'=',n:n});
    } else if(key==='position'){
      // Hyphens stand in for spaces: position:incident-deck === position:"incident deck".
      const norm=lv.replace(/-/g,' ').replace(/\\s+/g,' ');
      put(res.positions,res.negPositions,(vocab.positions&&vocab.positions[norm])||val);
    } else if(key==='variant'){
      const v = (lv==='updated'||lv==='update') ? 'update'
              : (lv==='duplicate'||lv==='reprint'||lv==='dupe') ? 'duplicate' : lv;
      put(res.variants,res.negVariants,v);
    } else {"""
),
# 2. state -------------------------------------------------------------------
(
"""let nameTerms    = [];
// Negated counterparts, from "-key:value" / "-word" tokens (query language)
let negDecks=new Set(), negSuits=new Set(), negTags=new Set(), negSkills=new Set(), negNames=[];""",
"""let nameTerms    = [];
let gloryTests   = [];          // [{op,n}] from glory:N / glory>N
let activePositions = new Set();
let activeVariants  = new Set();
// Negated counterparts, from "-key:value" / "-word" tokens (query language)
let negDecks=new Set(), negSuits=new Set(), negTags=new Set(), negSkills=new Set(), negNames=[];
let negGlory=[], negPositions=new Set(), negVariants=new Set();"""
),
# 3. vocab -------------------------------------------------------------------
(
"""  QUERY_VOCAB={allBoxes:ALL_BOXES,decks,suits:map(SUITS_DISPLAY),""",
"""  // Position vocabulary is read from the data, not hardcoded, so a new indicator
  // in a future box is searchable the day it lands.
  const positions={};
  FULL_POOL.forEach(c=>{ const p=c.position_indicator; if(p) positions[String(p).toLowerCase()]=p; });
  QUERY_VOCAB={allBoxes:ALL_BOXES,decks,suits:map(SUITS_DISPLAY),positions,"""
),
# 4. applyQuery --------------------------------------------------------------
(
"""  nameTerms=q.names.map(t=>t.toLowerCase()); negNames=q.negNames.map(t=>t.toLowerCase());""",
"""  nameTerms=q.names.map(t=>t.toLowerCase()); negNames=q.negNames.map(t=>t.toLowerCase());
  gloryTests=q.glory; negGlory=q.negGlory;
  activePositions=new Set(q.positions); negPositions=new Set(q.negPositions);
  activeVariants=new Set(q.variants);   negVariants=new Set(q.negVariants);"""
),
# 5. matcher -----------------------------------------------------------------
(
"""  if(activeSkills.size && ![...activeSkills].every(s=>c.skills.includes(s))) return false;
  if([...negSkills].some(s=>c.skills.includes(s))) return false;
  return true;
}""",
"""  if(activeSkills.size && ![...activeSkills].every(s=>c.skills.includes(s))) return false;
  if([...negSkills].some(s=>c.skills.includes(s))) return false;
  // Glory: a card with no glory value never matches a glory test, in either direction.
  if(gloryTests.length && !gloryTests.every(t=>gloryMatches(c.glory,t))) return false;
  if(negGlory.some(t=>gloryMatches(c.glory,t))) return false;
  const pos=c.position_indicator;
  if(activePositions.size && !(pos && activePositions.has(pos))) return false;
  if(pos && negPositions.has(pos)) return false;
  // Variant matches the badge as displayed, which depends on the selected boxes.
  if(activeVariants.size && !(c.badgeKind && activeVariants.has(c.badgeKind))) return false;
  if(c.badgeKind && negVariants.has(c.badgeKind)) return false;
  return true;
}

function gloryMatches(g,t){
  if(g===null||g===undefined) return false;
  const n=Number(g);
  if(!Number.isFinite(n)) return false;
  switch(t.op){
    case '>':  return n >  t.n;
    case '<':  return n <  t.n;
    case '>=': return n >= t.n;
    case '<=': return n <= t.n;
    default:   return n === t.n;
  }
}"""
),
# 6. help bubble -------------------------------------------------------------
(
"""    <div class="qh-row"><code>box:promo1</code> · <code>box:all</code><span>promos in; empty bar = the three main boxes</span></div>""",
"""    <div class="qh-row"><code>box:promo1</code> · <code>box:all</code><span>promos in; empty bar = the three main boxes</span></div>
    <div class="qh-row"><code>glory:4</code> · <code>glory&gt;=3</code><span>glory value; cards without glory never match</span></div>
    <div class="qh-row"><code>position:reserve</code> · <code>position:incident-deck</code><span>starting position; hyphens for spaces</span></div>
    <div class="qh-row"><code>variant:update</code> · <code>variant:duplicate</code><span>cards wearing that badge in the current boxes</span></div>"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "gloryMatches" in src:
        print("already patched; nothing to do")
        return 0
    out = src
    for old, new in EDITS:
        n = out.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for block starting {old.splitlines()[0][:60]!r}",
                  file=sys.stderr)
            return 1
        out = out.replace(old, new, 1)
    # Content is complete before anything is opened for writing (WORKFLOW.md convention).
    open(path, "w", encoding="utf-8").write(out)
    print(f"patched {path}: {len(EDITS)} exact-string replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
