#!/usr/bin/env python3
"""
build_scanner_data.py -- inject canonical card JSON into the Card Scanner.

WHY THIS EXISTS
---------------
The Card Scanner (card-browser-mockup.html) holds its card data as a single
inline `const ALL_CARDS = [ ... ];` array. That array uses a *flattened* schema
that differs from the canonical per-box JSON files (box1.json, box2.json, ...).
The original flattener was written in an early session and never saved to tools/;
this script is the reconstructed, authoritative transform. Re-derived empirically
by diffing ALL_CARDS entries against box1.json (0 mismatches across 255 cards).

CANONICAL schema (box1.json / box2.json, one object per card):
    id, name, suit,
    source,            # deck: "Common" or captain name
    game_box,          # "Captain's Chair" | "To Boldly Go" | "Second Contact"
                       #   | "Promo Pack 1" | "Promo Pack 2"
    species_traits[], regular_traits[], other_traits[],
    filename,          # "" when no image (scanner shows NO IMAGE placeholder)
    icons[]            # [{"type": "Skill"|"Focus", "specialty": <spec>}]
                       #   specialty in {Research, Influence, Military, Any, Variable}

FLATTENED schema (ALL_CARDS entry, consumed by the scanner JS):
    id, name, suit,
    deck,              # <- source
    box,               # <- game_box mapped: Captain's Chair->core,
                       #    To Boldly Go->tbg, Second Contact->2nd,
                       #    Promo Pack 1->promo1, Promo Pack 2->promo2
    species[],         # <- species_traits
    regular[],         # <- regular_traits
    other[],           # <- other_traits
    skills[],          # <- icons flattened to "<specialty> <type>" strings,
                       #    e.g. {"type":"Focus","specialty":"Influence"} -> "Influence Focus"
    filename

The scanner derives ALL filter pills (species/regular/other/skills) and box+deck
membership from these fields, so wiring a new box in is purely a data operation:
add its flattened entries to ALL_CARDS. Box toggles key off `box`, deck pills off
`deck`; both already enumerated in the HTML (DECK_ORDER / DECK_BOX / BOX_FOLDER).

USAGE
    python build_scanner_data.py card-browser-mockup.html box1.json box2.json [...] \
           -o card-browser-mockup.html
Rebuilds the ENTIRE ALL_CARDS array from the given JSON files, in the order given,
and rewrites the inline array in-place. Idempotent. Regenerate whenever any boxN.json
changes (e.g. community adds Box 2 cards).
"""
import json, re, sys, argparse

GAME_BOX_TO_KEY = {
    "Captain's Chair": "core",
    "To Boldly Go":    "tbg",
    "Second Contact":  "2nd",
    "Promo Pack 1":    "promo1",
    "Promo Pack 2":    "promo2",
}

def flatten(card):
    box = GAME_BOX_TO_KEY.get(card["game_box"])
    if box is None:
        raise ValueError(f"unknown game_box {card['game_box']!r} for card {card.get('id')!r}")
    return {
        "id": card["id"],
        "name": card["name"],
        "suit": card["suit"],
        "deck": card["source"],
        "box": box,
        "species": card.get("species_traits", []),
        "regular": card.get("regular_traits", []),
        "other": card.get("other_traits", []),
        "skills": [f'{ic["specialty"]} {ic["type"]}' for ic in card.get("icons", [])],
        "filename": card.get("filename", ""),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("json_files", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    flat = []
    for jf in a.json_files:
        for c in json.load(open(jf, encoding="utf-8")):
            flat.append(flatten(c))

    html = open(a.html, encoding="utf-8").read()
    pat = re.compile(r'const ALL_CARDS = \[.*?\];', re.S)
    if not pat.search(html):
        sys.exit("ERROR: could not find `const ALL_CARDS = [...]` in HTML")
    payload = "const ALL_CARDS = " + json.dumps(flat, ensure_ascii=False) + ";"
    html = pat.sub(lambda _: payload, html, count=1)
    open(a.out, "w", encoding="utf-8").write(html)
    print(f"Injected {len(flat)} cards from {len(a.json_files)} file(s) into {a.out}")

if __name__ == "__main__":
    main()
