#!/usr/bin/env python3
"""patch_scanner_sort_position.py -- order a deck by where its cards start the game.

Requested on BGG: studying a crew deck is easier in the order the cards actually reach the
table, rather than by card number. A second checkbox beside Show duplicates, "Sort by position",
reorders every deck group by the starting-position indicator. Off is unchanged: card number, the
order the JSON carries.

Order (play order, all fifteen values have a slot):
  Captain, Status, Available, Deployed, Controlled Location, Development, Reserve, Discard,
  Incident Deck, Starting, Advanced, Rewards, Solo Campaign, Solo Challenge, then cards with no
  position at all. Ties keep their card-number order, so the sort is stable and a market group
  (almost all position-less) looks the same as before.

The checkbox writes `sort:position` into the query like every other control, so the state
shares, bookmarks and restores; syncFilterPills ticks it from the query.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_sort_position.py [path/to/cards.html]
"""

import sys

EDITS = [
# state + the order itself
(
"""let showDupes    = true;""",
"""let showDupes    = true;
// Deck groups are ordered by card number unless asked for play order.
let sortByPos    = false;
// Play order: the sequence cards reach the table, then the Location values, then the solo
// variants, then anything without a position. Index is the sort key; unknown values land
// just before the position-less cards, so a new indicator is visible rather than hidden.
const POSITION_ORDER = ['Captain','Status','Available','Deployed','Controlled Location',
  'Development','Reserve','Discard','Incident Deck','Starting','Advanced','Rewards',
  'Solo Campaign','Solo Challenge'];
function positionRank(c){
  const p=(c.position_indicator===undefined||c.position_indicator===null)?'':String(c.position_indicator);
  if(!p) return POSITION_ORDER.length+1;
  const i=POSITION_ORDER.indexOf(p);
  return i<0 ? POSITION_ORDER.length : i;
}"""
),
# parser key
(
"""    } else if(key==='dupes'){""",
"""    } else if(key==='sort'){
      res.sort = lv;
    } else if(key==='dupes'){"""
),
(
"""vp:[],negVp:[],positions:[],negPositions:[],variants:[],negVariants:[],dupes:true,""",
"""vp:[],negVp:[],positions:[],negPositions:[],variants:[],negVariants:[],dupes:true,sort:'',"""
),
(
"""  showDupes = q.dupes !== false;""",
"""  showDupes = q.dupes !== false;
  sortByPos = q.sort === 'position' || q.sort === 'pos';"""
),
# the sort itself, applied per deck group so numbering stays intact within a group
(
"""    const matched=ALL_CARDS.filter(c=>deckKey(c)===deck&&cardMatches(c));""",
"""    let matched=ALL_CARDS.filter(c=>deckKey(c)===deck&&cardMatches(c));
    if(sortByPos){
      // Stable: equal positions keep the card-number order they arrived in.
      matched=matched.map((c,i)=>[c,i])
        .sort((a,b)=>(positionRank(a[0])-positionRank(b[0]))||(a[1]-b[1]))
        .map(p=>p[0]);
    }"""
),
# the control
(
"""    <label class="dupes-toggle"><input type="checkbox" id="showDupes" checked onchange="setDupes(this.checked)"> Show duplicates</label>""",
"""    <label class="dupes-toggle"><input type="checkbox" id="showDupes" checked onchange="setDupes(this.checked)"> Show duplicates</label>
    <label class="dupes-toggle"><input type="checkbox" id="sortPos" onchange="setSortPos(this.checked)"> Sort by position</label>"""
),
(
"""function setDupes(on){
  const toks=tokenList(currentQuery()).filter(t=>!/^-?dupes:/i.test(t));
  if(!on) toks.push('dupes:off');
  setQuery(toks.join(' '));
}""",
"""function setDupes(on){
  const toks=tokenList(currentQuery()).filter(t=>!/^-?dupes:/i.test(t));
  if(!on) toks.push('dupes:off');
  setQuery(toks.join(' '));
}
function setSortPos(on){
  const toks=tokenList(currentQuery()).filter(t=>!/^-?sort:/i.test(t));
  if(on) toks.push('sort:position');
  setQuery(toks.join(' '));
}"""
),
(
"""  const dup=document.getElementById('showDupes');
  if(dup) dup.checked=showDupes;""",
"""  const dup=document.getElementById('showDupes');
  if(dup) dup.checked=showDupes;
  const sp=document.getElementById('sortPos');
  if(sp) sp.checked=sortByPos;"""
),
# help row
(
"""    <div class="qh-row"><code>dupes:off</code><span>one tile per card instead of one per printing</span></div>""",
"""    <div class="qh-row"><code>dupes:off</code><span>one tile per card instead of one per printing</span></div>
    <div class="qh-row"><code>sort:position</code><span>order each deck by starting position instead of card number</span></div>"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "POSITION_ORDER" in src:
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
