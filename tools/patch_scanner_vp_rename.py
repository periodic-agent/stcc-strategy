#!/usr/bin/env python3
"""patch_scanner_vp_rename.py -- the bottom-right number is Victory Points, not Glory.

The rulebook calls the number in the bottom-right corner of a card Victory Points (VP). Glory is
a separate thing: a blue token that card text refers to. The scanner conflated the two, so
`glory:4` searched VP while `text:glory` searched for the token, which is confusing.

Scanner-facing rename:
  query key      glory:      ->  vp:      (also victory-points:; `glory:` is REMOVED, not aliased,
                                           because it names the wrong rule)
  help row       "glory value"            ->  "victory points"
  badge tooltip  "Glory 3"                ->  "Victory Points 3"

`text:glory` is untouched and still finds the word Glory in rules text, which is the token.

The help popover also drops the "Clicking any pill writes its token here" note, which stated the
obvious once the pills and the bar had been in use for a while.

The JSON field is still named `glory`; renaming it is the JSON chat's half of this change. The
resolver therefore reads `vp` first and falls back to `glory`, so whichever push lands first,
nothing breaks.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_vp_rename.py [path/to/cards.html]
"""

import sys

EDITS = [
# resolver: accept either field name during the changeover
(
"""      glory: (() => { for (const pr of group) { if (pr.glory !== undefined && pr.glory !== null) return pr.glory; } return null; })(),""",
"""      // `vp` is the rulebook name; `glory` is the old field, still in the JSONs until the
      // data side renames it. Read either, expose one.
      vp: (() => { for (const pr of group) { const v = (pr.vp !== undefined && pr.vp !== null) ? pr.vp : pr.glory; if (v !== undefined && v !== null) return v; } return null; })(),"""
),
# key charset gains the hyphen so victory-points: parses as a key
(
"""  const tokRe=/(-)?(?:([A-Za-z]+)\\s*(:|>=|<=|>|<))?("([^"]*)"|[^\\s"]+)/g;""",
"""  const tokRe=/(-)?(?:([A-Za-z][A-Za-z-]*)\\s*(:|>=|<=|>|<))?("([^"]*)"|[^\\s"]+)/g;"""
),
# parser key
(
"""    } else if(key==='glory'){""",
"""    } else if(key==='vp'||key==='victory-points'||key==='victorypoints'){"""
),
# parser comments
(
"""  // A key may be followed by ':' or by a comparison operator, so both glory>4 and
  // glory:>4 parse. The operator is captured separately from the value.""",
"""  // A key may be followed by ':' or by a comparison operator, so both vp>4 and
  // vp:>4 parse. The operator is captured separately from the value."""
),
(
"""    // glory:>=4 puts the operator in the value; move it onto op.""",
"""    // vp:>=4 puts the operator in the value; move it onto op."""
),
# matcher
(
"""  // Glory: a card with no glory value never matches a glory test, in either direction.
  if(gloryTests.length && !gloryTests.every(t=>gloryMatches(c.glory,t))) return false;
  if(negGlory.some(t=>gloryMatches(c.glory,t))) return false;""",
"""  // VP: a card with no victory-point value never matches a vp test, in either direction.
  if(vpTests.length && !vpTests.every(t=>vpMatches(c.vp,t))) return false;
  if(negVp.some(t=>vpMatches(c.vp,t))) return false;"""
),
(
"""function gloryMatches(g,t){""",
"""function vpMatches(g,t){"""
),
# state
(
"""let gloryTests   = [];          // [{op,n}] from glory:N / glory>N""",
"""let vpTests      = [];          // [{op,n}] from vp:N / vp>N"""
),
(
"""  gloryTests=q.glory; negGlory=q.negGlory;""",
"""  vpTests=q.vp; negVp=q.negVp;"""
),
(
"""             glory:[],negGlory:[],positions:[],negPositions:[],variants:[],negVariants:[],""",
"""             vp:[],negVp:[],positions:[],negPositions:[],variants:[],negVariants:[],"""
),
(
"""      if(Number.isFinite(n)) put(res.glory,res.negGlory,{op:(op===':'?'=':op)||'=',n:n});""",
"""      if(Number.isFinite(n)) put(res.vp,res.negVp,{op:(op===':'?'=':op)||'=',n:n});"""
),
# help row
(
"""    <div class="qh-row"><code>glory:4</code> · <code>glory&gt;=3</code><span>glory value; cards without glory never match</span></div>""",
"""    <div class="qh-row"><code>vp:4</code> · <code>vp&gt;=3</code><span>victory points, the number bottom-right; cards without a value never match</span></div>"""
),
# help: drop the pill-shortcut note
(
"""    <div class="qh-note">Clicking any pill writes its token here \u2014 the pills are shortcuts for this language.</div>
""",
""""""
),
# card face: badge tooltip and the value it reads
(
"""  if(!foci.length && c.glory!==null && c.glory!==undefined){
    el.classList.add('has-focus');
    // negative glory prints warm on the card; tint the delta, nothing else
    const gloryFill=(c.glory<0)?'"#f0a893"':'"#c3cfdd"';
    corner='<svg class="glorybadge" viewBox="0 0 32 29" title="Glory '+c.glory+'">'""",
"""  if(!foci.length && c.vp!==null && c.vp!==undefined){
    el.classList.add('has-focus');
    // a negative value prints warm on the card; tint the delta, nothing else
    const gloryFill=(c.vp<0)?'"#f0a893"':'"#c3cfdd"';
    corner='<svg class="glorybadge" viewBox="0 0 32 29" title="Victory Points '+c.vp+'">'"""
),
(
"""      +'<text x="16" y="21.7" text-anchor="middle" font-size="20" font-weight="700" fill="#10161f" font-family="Antonio,sans-serif">'+c.glory+'</text></svg>';""",
"""      +'<text x="16" y="21.7" text-anchor="middle" font-size="20" font-weight="700" fill="#10161f" font-family="Antonio,sans-serif">'+c.vp+'</text></svg>';"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "vpMatches" in src:
        print("already patched; nothing to do")
        return 0
    out = src
    for old, new in EDITS:
        n = out.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for {old.splitlines()[0][:60]!r}", file=sys.stderr)
            return 1
        out = out.replace(old, new, 1)
    # negGlory is declared alongside the other negated buckets; rename in place.
    out = out.replace("let negGlory=[], negPositions=new Set(), negVariants=new Set();",
                      "let negVp=[], negPositions=new Set(), negVariants=new Set();", 1)
    open(path, "w", encoding="utf-8").write(out)
    print(f"patched {path}: {len(EDITS)} exact-string replacements + negVp rename")
    return 0


if __name__ == "__main__":
    sys.exit(main())
