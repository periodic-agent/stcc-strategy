#!/usr/bin/env python3
"""
build_box2_from_sheet.py -- build canonical boxN.json from the community sheet.

Step 3 of the "Scanner regeneration checklist" in WORKFLOW.md. Reads the
stcc-card-database.xlsx export (Google Drive file 186ZpFkLQsLX1blU3z45znMPwH9fE6yO3)
and emits the canonical per-box JSON consumed by tools/build_scanner_data.py.
The sheet is READ-ONLY; this script never writes to Drive.

Sheet columns (TBG (Box 2) / Second Contact (Box 3) tabs):
  A Card code | B Name | C Suit | D Deck | E Subtype | F Species traits
  G Regular traits | H Other traits | I Skill icons (left) | J Focus icons (bottom-right)
  K Glory | L Card image | M Status | N Contributor | O Notes

Rules applied (see WORKFLOW.md):
  - include every row with at least a Name and a Suit, whatever its Status
  - id = slug(name): lowercase, drop ' . , then non-alnum -> single hyphen
  - col I -> icons type "Skill"; col J -> icons type "Focus"
  - filename "" when no image (scanner renders a NO IMAGE placeholder)
  - duplicate ids get a -2 suffix and are KEPT (decks can hold two copies)
  - traits validated against the Vocabulary tab: novel traits warn, never dropped

Usage:
  python build_box2_from_sheet.py sheet.xlsx "TBG (Box 2)" "To Boldly Go" -o box2.json
"""
import openpyxl, json, re, argparse
from collections import Counter, defaultdict

ICON_SPECIALTIES = {"Research", "Influence", "Military", "Any", "Variable"}

def slug(name):
    s = name.lower()
    for ch in ("'", "’", ".", ","):
        s = s.replace(ch, "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def make_id(name, deck, filename):
    """box1 convention (verified across all 255 core cards): id == filename stem.
    Crew-deck cards carry a deck prefix and drop any trailing "(Captain)"
    parenthetical from the name; Common/Promo cards take no prefix.
      "Analyze (Picard)" / Picard -> picard-analyze   (file picard-analyze.jpg)
      "Reinforce"        / Common -> reinforce
    When the sheet already supplies an image, that stem is authoritative."""
    if filename:
        return filename[:-4] if filename.lower().endswith(".jpg") else slug(filename)
    base = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip() or name
    if deck and deck not in ("Common", "Promo"):
        return f"{slug(deck)}-{slug(base)}"
    return slug(base)

def splitlist(v):
    return [x.strip() for x in str(v).split(",") if x.strip()] if v is not None else []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx"); ap.add_argument("tab"); ap.add_argument("game_box")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    wb = openpyxl.load_workbook(a.xlsx, data_only=True)
    ws = wb[a.tab]
    voc = wb["Vocabulary"]
    sp_ok, rg_ok, ot_ok, newexp = set(), set(), set(), set()
    for r in range(2, voc.max_row + 1):
        c1, c2, c3, c4 = (voc.cell(r, i).value for i in (1, 2, 3, 4))
        if c1: sp_ok.add(str(c1).strip())
        if c2: rg_ok.add(str(c2).strip())
        if c3: ot_ok.add(str(c3).strip())
        if c4: newexp.add(re.sub(r"\s*\(.*?\)", "", str(c4)).strip())

    cards = []
    for r in range(2, ws.max_row + 1):
        name, suit = ws.cell(r, 2).value, ws.cell(r, 3).value
        if not name or not str(name).strip() or not suit or not str(suit).strip():
            continue
        img = ws.cell(r, 12).value
        cards.append({
            "id": make_id(str(name).strip(),
                          (str(ws.cell(r, 4).value).strip() if ws.cell(r, 4).value else "") or "Common",
                          str(img).strip() if img and str(img).strip() else ""),
            "name": str(name).strip(),
            "suit": str(suit).strip(),
            "source": (str(ws.cell(r, 4).value).strip() if ws.cell(r, 4).value else "") or "Common",
            "game_box": a.game_box,
            "species_traits": splitlist(ws.cell(r, 6).value),
            "regular_traits": splitlist(ws.cell(r, 7).value),
            "other_traits": splitlist(ws.cell(r, 8).value),
            "filename": str(img).strip() if img and str(img).strip() else "",
            "icons": [{"type": "Skill", "specialty": s} for s in splitlist(ws.cell(r, 9).value)]
                   + [{"type": "Focus", "specialty": s} for s in splitlist(ws.cell(r, 10).value)],
        })

    seen = defaultdict(int); warns = []
    for c in cards:
        seen[c["id"]] += 1
        if seen[c["id"]] > 1:
            new = f'{c["id"]}-{seen[c["id"]]}'
            warns.append(f'duplicate id {c["id"]!r} ({c["name"]}) -> {new}')
            c["id"] = new

    novel = {k: set() for k in ("species_traits", "regular_traits", "other_traits")}
    oks = {"species_traits": sp_ok, "regular_traits": rg_ok, "other_traits": ot_ok}
    bad_icons = set()
    for c in cards:
        for k in novel:
            for t in c[k]:
                if t not in oks[k]: novel[k].add(t)
        for ic in c["icons"]:
            if ic["specialty"] not in ICON_SPECIALTIES: bad_icons.add(ic["specialty"])

    json.dump(cards, open(a.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"TOTAL: {len(cards)}")
    print("PER SUIT:", dict(Counter(c["suit"] for c in cards)))
    print("PER DECK:", dict(Counter(c["source"] for c in cards)))
    wi = sum(1 for c in cards if c["filename"])
    print(f"IMAGES: {wi} with / {len(cards)-wi} without")
    for w in warns: print("WARN:", w)
    for k, v in novel.items():
        if v: print(f"NOVEL {k}: documented={sorted(v & newexp)} UNDOCUMENTED={sorted(v - newexp)}")
    print("BAD ICON SPECIALTIES:", sorted(bad_icons) or "none")

if __name__ == "__main__":
    main()
