#!/usr/bin/env python3
"""patch_scanner_image_fallback.py -- the transform applied to card-browser-mockup.html
on 25 Jul 2026 (image fallback across box selections).

What it changes, and why:

1. Indexes the full raw pool by card id (`FULL_BY_ID`). Resolution stays scoped to the
   selected boxes, but image lookup must not be: a Box 2 reprint carries an empty
   `filename`, so with only Box 2 selected its Box 1 sibling was filtered out of the pool
   and the card rendered NO IMAGE. Duplicates now fall back to the Box 1 original scan.
2. Adds `boxRank()` so promo keys, which are absent from BOX_ORDER and used to yield
   indexOf -1, sort after the numbered boxes instead of ahead of them.
3. Rewrites the image-candidate block: candidates are drawn from every loaded printing of
   the id, filtered to those whose TEXT matches the resolved version (updated printings for
   an updated card, originals plus reprints otherwise). Duplicates prefer the earliest
   printing (Box 1 art wins); updated cards prefer the newest updated printing. An updated
   card with no new scan yet still shows NO IMAGE rather than superseded art.
4. Fixes the lightbox list to use the image's own box folder (`imgBox`, which can differ
   from the card's resolved box) and to skip image-less cards, so arrow navigation lines up
   with the tiles actually on screen.

Exact-string replacements only; each must match exactly once or the script refuses to run.
Verify afterwards with: node tools/test_scanner.mjs .

Usage: python3 tools/patch_scanner_image_fallback.py [path/to/card-browser-mockup.html]
"""

import sys

EDITS = [
(
"""let FULL_POOL = [];
function buildFullPool(){
  FULL_POOL = [];
  Object.values(RAW_BOXES).forEach(arr=>FULL_POOL.push(...arr));
}""",
"""let FULL_POOL = [];
let FULL_BY_ID = {};   // every loaded printing of an id, regardless of box selection
function buildFullPool(){
  FULL_POOL = [];
  Object.values(RAW_BOXES).forEach(arr=>FULL_POOL.push(...arr));
  FULL_BY_ID = {};
  FULL_POOL.forEach(c=>{ (FULL_BY_ID[c.id]=FULL_BY_ID[c.id]||[]).push(c); });
}"""
),
(
"""// The box-order for resolution: lower index = earlier printing.
const BOX_ORDER = ['core','tbg','2nd'];""",
"""// The box-order for resolution: lower index = earlier printing.
const BOX_ORDER = ['core','tbg','2nd'];
// Promo printings rank after every numbered box, so a promo scan never outranks a box scan.
function boxRank(k){ const i=BOX_ORDER.indexOf(k); return i<0 ? 90 : i; }"""
),
(
"""    let imgCandidates;
    if(chosen.variant==='updated'){
      imgCandidates = group.filter(c=>c===chosen);
    } else {
      // reprints + originals all match text
      imgCandidates = group.slice();
    }
    // prefer newest box first, non-empty filename
    imgCandidates = imgCandidates.sort((a,b)=>BOX_ORDER.indexOf(rawBoxKey(b))-BOX_ORDER.indexOf(rawBoxKey(a)));
    let chosenImg = imgCandidates.find(c=>c.filename && c.filename.trim());""",
"""    // Candidates come from EVERY loaded printing of this id, not just the selected boxes:
    // a Box 2 reprint carries no scan of its own, so with only Box 2 selected it must still
    // fall back to the Box 1 original art.
    const imgPool = FULL_BY_ID[chosen.id] || group;
    let imgCandidates = (chosen.variant==='updated')
      ? imgPool.filter(c=>c.variant==='updated')     // updated text: only updated printings qualify
      : imgPool.filter(c=>c.variant!=='updated');    // base text: originals and reprints share it
    // Duplicates show the earliest printing's scan (Box 1 art wins).
    // Updated cards take the newest updated printing, the one whose text changed.
    const dir = (chosen.variant==='updated') ? -1 : 1;
    imgCandidates = imgCandidates.slice().sort((a,b)=>dir*(boxRank(rawBoxKey(a))-boxRank(rawBoxKey(b))));
    let chosenImg = imgCandidates.find(c=>c.filename && c.filename.trim());"""
),
(
"""      if(viewMode==='image'){
        const folder=BOX_FOLDER[c.box]||'box1';
        VISIBLE_IMG_CARDS.push({src:IMG_BASE+'/'+folder+'/'+c.filename, name:c.name});
      }""",
"""      if(viewMode==='image' && c.imgBox && c.filename){
        // Use the image's own box folder (it can differ from the card's resolved box) so the
        // lightbox list matches the tiles on screen; image-less cards are skipped entirely.
        VISIBLE_IMG_CARDS.push({src:IMG_BASE+'/'+BOX_FOLDER[c.imgBox]+'/'+c.filename, name:c.name});
      }"""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "card-browser-mockup.html"
    src = open(path, encoding="utf-8").read()
    if "FULL_BY_ID" in src:
        print("already patched; nothing to do")
        return 0
    for old, new in EDITS:
        n = src.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for block starting {old.splitlines()[0]!r}",
                  file=sys.stderr)
            return 1
        src = src.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(src)
    print(f"patched {path}: {len(EDITS)} exact-string replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
