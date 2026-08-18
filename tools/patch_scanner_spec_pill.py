#!/usr/bin/env python3
"""patch_scanner_spec_pill.py -- specialty medallions read as pills, not flags.

The Military / Research / Influence art in the bundle is a pennant: square on the right,
tapering to a point on the left. Inline in a sentence it reads as a little flag.

Each one is now wrapped in a rounded span carrying the specialty's own colour, sampled from the
asset itself (military #ab2242, research #015c80, influence #c0b422). The colour fills the
transparent notch on the left, and `overflow:hidden` with a full border-radius clips the square
right edge, so the glyph sits in a pill rounded at both ends. No new artwork, no bundle change.

The same wrapper covers `<spec> Skill` tokens, which draw from the same pennant art. Focus
tokens are left alone: their asset is the rounded corner marker, a different shape by design.

Content is built in memory and written once. Exact-string replacements, each matching once.

Usage: python3 tools/patch_scanner_spec_pill.py [path/to/cards.html]
"""

import sys

EDITS = [
(
""".stripimg{height:1.35em;width:auto;vertical-align:-.32em;margin:0 .08em;}""",
""".stripimg{height:1.35em;width:auto;vertical-align:-.32em;margin:0 .08em;}
/* The specialty art is a pennant; the pill fills its notch and rounds its square end. */
.specpill{display:inline-flex;align-items:center;height:1.35em;border-radius:999px;
  overflow:hidden;vertical-align:-.32em;margin:0 .08em;}
.specpill img{height:1.35em;width:auto;display:block;}"""
),
(
"""const STRIP_SPEC=['Research','Influence','Military','Any','Variable'];""",
"""const STRIP_SPEC=['Research','Influence','Military','Any','Variable'];
// Sampled from the medallion art itself, so the pill and the glyph agree exactly.
const SPEC_COL={military:'#ab2242',research:'#015c80',influence:'#c0b422',
                any:'#5a6678',variable:'#5a6678'};
function specPill(spec,src,alt){
  const col=SPEC_COL[String(spec).toLowerCase()];
  if(!src) return alt;
  if(!col) return '<img class="stripimg" src="'+src+'" alt="'+alt+'">';
  return '<span class="specpill" style="background:'+col+'"><img src="'+src+'" alt="'+alt+'"></span>';
}"""
),
# Token-safe passes: never rewrite inside an already-built {token}.
(
"""function stripAutoTokens(text){
  let t=text;
  STRIP_SPEC.forEach(sp=>{
    t=t.replace(new RegExp('\\\\b'+sp+' (Skill|Focus)\\\\b','g'),
      (_,k)=>'{'+(k==='Focus'?'focus':'skill')+':'+sp+'}');
  });
  // A bare specialty ("gain 1 Military") gets the same medallion as the Skill/Focus pair
  // above; run after that pass so "Military Skill" is already consumed.
  STRIP_SPEC.forEach(sp=>{
    if(sp==='Any'||sp==='Variable') return;
    t=t.replace(new RegExp('\\\\b'+sp+'\\\\b','g'),'{spec:'+sp+'}');
  });""",
"""// Apply fn only to the parts of the string that are not already inside a {token}.
// Without this, the bare-specialty pass rewrites the payload of {skill:Influence}
// and the strip renders the literal braces.
function outsideTokens(t,fn){
  return String(t).split(/(\\{[^}]*\\})/).map(seg=>seg.charAt(0)==='{'?seg:fn(seg)).join('');
}

function stripAutoTokens(text){
  let t=text;
  STRIP_SPEC.forEach(sp=>{
    t=t.replace(new RegExp('\\\\b'+sp+' (Skill|Focus)\\\\b','g'),
      (_,k)=>'{'+(k==='Focus'?'focus':'skill')+':'+sp+'}');
  });
  // A bare specialty ("gain 1 Military") gets the same medallion as the Skill/Focus pair
  // above; run after that pass so "Military Skill" is already consumed, and only outside
  // the tokens that pass produced.
  STRIP_SPEC.forEach(sp=>{
    if(sp==='Any'||sp==='Variable') return;
    t=outsideTokens(t,seg=>seg.replace(new RegExp('\\\\b'+sp+'\\\\b','g'),'{spec:'+sp+'}'));
  });"""
),
(
"""  if((m=t.match(/^spec:(.+)$/))){
    const src=(CARDFACE.skillChip||CARDFACE.skill||{})[m[1].toLowerCase()];
    return src?'<img class="stripimg" src="'+src+'" alt="'+m[1]+'">':m[1];
  }""",
"""  if((m=t.match(/^spec:(.+)$/))){
    const src=(CARDFACE.skillChip||CARDFACE.skill||{})[m[1].toLowerCase()];
    return specPill(m[1],src,m[1]);
  }"""
),
(
"""  if((m=t.match(/^(skill|focus):(.+)$/))){
    const bank=m[1]==='focus'?CARDFACE.focus:CARDFACE.skillChip;
    const src=bank&&bank[m[2].toLowerCase()];
    return src?'<img class="stripimg" src="'+src+'" alt="'+m[2]+'">':m[2]+' '+m[1];
  }""",
"""  if((m=t.match(/^(skill|focus):(.+)$/))){
    const bank=m[1]==='focus'?CARDFACE.focus:CARDFACE.skillChip;
    const src=bank&&bank[m[2].toLowerCase()];
    if(!src) return m[2]+' '+m[1];
    // Focus art is already a rounded marker; only the pennant needs the pill.
    return m[1]==='focus'
      ? '<img class="stripimg" src="'+src+'" alt="'+m[2]+'">'
      : specPill(m[2],src,m[2]);
  }"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.html"
    src = open(path, encoding="utf-8").read()
    if "specPill" in src:
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
