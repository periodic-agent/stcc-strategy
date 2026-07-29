#!/usr/bin/env python3
"""
split_promo_json.py -- one-off migration: promo packs get their own JSON files.

Decision (Jul 2026): one box = one JSON = one image folder. Promo packs are
linked to an expansion wave, not to a single box (Promo Pack 2 shipped with
both To Boldly Go and Second Contact), so parking their data inside an era
box JSON no longer fits. This script:

  1. moves the 5 `source: "Promo"` rows out of box1.json into promo1.json
     (rows unchanged, order preserved; box1.json drops 255 -> 250 records);
  2. seeds promo2.json with the 6 Promo Pack 2 cards whose images already
     live in img/promo2/. Name, suit and card number were read from the card
     faces; traits and icons are left empty pending the card OCR pass
     (ISSUES.md Issue 5). game_box mirrors promo1's convention
     ("Promo Pack 1" / "Promo Pack 2").

The scanner change that consumes these files (BOX_SOURCES entries with a
`key` per file, source-file stamping in loadBoxes, rawBoxKey fallback) is in
card-browser-mockup.html, same commit.

Usage: python3 tools/split_promo_json.py   (run from repo root; idempotent)
"""
import json

PROMO2_SEED = [
    {"id": "drones-of-cube-90182", "name": "Drones of Cube 90182", "suit": "Ally",
     "card_number": "0ALL01/?", "filename": "drones-of-cube-90182.jpg"},
    {"id": "frank-hollander", "name": "Frank Hollander", "suit": "Cargo",
     "card_number": "0CAR02/?", "filename": "frank-hollander.jpg"},
    {"id": "golden-statue-of-obrien", "name": "Golden Statue of O'Brien", "suit": "Cargo",
     "card_number": "0CAR03/?", "filename": "golden-statue-of-obrien.jpg"},
    {"id": "starbase-80", "name": "Starbase 80", "suit": "Location",
     "card_number": "0LOC01/?", "filename": "starbase-80.jpg"},
    {"id": "subspace-rhapsody", "name": "Subspace Rhapsody", "suit": "Incident",
     "card_number": "0INC03/?", "filename": "subspace-rhapsody.jpg"},
    {"id": "uss-cabot", "name": "U.S.S. Cabot", "suit": "Ship",
     "card_number": "0SHI02/?", "filename": "uss-cabot.jpg"},
]


def main():
    box1 = json.load(open("box1.json", encoding="utf-8"))
    promo = [r for r in box1 if r.get("source") == "Promo"]
    rest = [r for r in box1 if r.get("source") != "Promo"]

    if promo:  # first run; on re-run box1.json is already clean
        with open("promo1.json", "w", encoding="utf-8") as f:
            json.dump(promo, f, indent=2, ensure_ascii=False)
            f.write("\n")
        with open("box1.json", "w", encoding="utf-8") as f:
            json.dump(rest, f, indent=2, ensure_ascii=False)
            f.write("\n")
    print(f"box1.json: {len(rest)} records; promo1.json: {len(promo) or 'unchanged'}")

    rows = []
    for s in PROMO2_SEED:
        rows.append({
            "id": s["id"], "name": s["name"], "suit": s["suit"],
            "source": "Promo", "game_box": "Promo Pack 2",
            "card_number": s["card_number"],
            "species_traits": [], "regular_traits": [], "other_traits": [],
            "filename": s["filename"], "icons": [],
        })
    with open("promo2.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"promo2.json: {len(rows)} records (traits/icons pending OCR, Issue 5)")


if __name__ == "__main__":
    main()
