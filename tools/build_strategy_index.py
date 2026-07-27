#!/usr/bin/env python3
"""
build_strategy_index.py -- ST:CC Compendium

Builds data/strategy-index.json: for every card in box1/2/3.json, the list of
guide passages where McCue discusses it. The Card Scanner reads this file to
show a "Strategy" badge on a card pill and, on click, a drawer of quoted
passages linking into the guides.

Two match modes, in priority order:

  1. ANCHOR  -- a guide has <h2 id="card-id"> or <h3 id="card-id">. Market
                guides are built this way, so the mapping is exact and needs
                no text matching at all. Highest confidence.
  2. TEXT    -- the card's name appears in a guide paragraph, matched on
                normalized text with word boundaries. Used for captain and
                strategy guides, which have no per-card anchors.

Snippets are whole <p> elements, never sentence windows: McCue's text is
reproduced verbatim per project rule 1, and a paragraph can never be cropped
mid-thought.

Tuning lives in tools/strategy_index_config.json, not in this file.

Usage:
    python tools/build_strategy_index.py [--repo .] [--out data/strategy-index.json]
                                         [--report] [--check]

    --report   print coverage stats and the highest-frequency matches, for
               eyeballing false positives after a content change.
    --check    exit 1 if the on-disk index differs from a fresh build. For CI.

Stdlib only. Python 3.8+.
"""

import argparse
import collections
import datetime
import glob
import json
import os
import re
import sys
import unicodedata

BOX_FILES = ["box1.json", "box2.json", "box3.json"]

RE_DROP = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
RE_PARA = re.compile(r"<p\b([^>]*)>(.*?)</p>", re.S | re.I)
RE_HEAD = re.compile(r"<h([1-6])\b([^>]*)>(.*?)</h\1>", re.S | re.I)
RE_ID = re.compile(r'id="([^"]+)"')
RE_CLASS = re.compile(r'class="([^"]*)"')
RE_TAGS = re.compile(r"<[^>]+>")
RE_ENT = re.compile(r"&(?:[a-zA-Z]+|#\d+);")
RE_TITLE = re.compile(r'<h1[^>]*class="chapter-title"[^>]*>(.*?)</h1>', re.S | re.I)
RE_LABEL = re.compile(r'<div[^>]*class="chapter-label"[^>]*>(.*?)</div>', re.S | re.I)


# ---------------------------------------------------------------- utilities

def normalize(s):
    """Lowercase, strip accents, drop periods/apostrophes, collapse the rest
    to single spaces. 'U.S.S. Enterprise-C' -> 'uss enterprise c'."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"[.'`]", "", s.lower())
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def untag(fragment):
    """HTML fragment -> plain text, whitespace collapsed."""
    t = RE_TAGS.sub(" ", fragment)
    t = RE_ENT.sub(lambda m: {"&amp;": "&", "&nbsp;": " ", "&quot;": '"',
                              "&#39;": "'", "&lt;": "<", "&gt;": ">"}.get(m.group(0), " "), t)
    return " ".join(t.split())


def truncate(text, limit):
    if len(text) <= limit:
        return text, False
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut, True


# ---------------------------------------------------------------- loading

def load_cards(repo):
    """card_id -> record. First box wins on duplicate ids."""
    cards = {}
    for fname in BOX_FILES:
        path = os.path.join(repo, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            for rec in json.load(fh):
                cards.setdefault(rec["id"], rec)
    return cards


def parse_guide(path):
    """Return (meta, blocks) where blocks are ordered dicts of
    {kind: 'p'|'h', text, anchor, cls}. Anchor is the id of the nearest
    preceding heading that has one."""
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    html = RE_DROP.sub(" ", html)

    title_m = RE_TITLE.search(html)
    label_m = RE_LABEL.search(html)
    meta = {
        "title": untag(title_m.group(1)) if title_m else os.path.basename(path),
        "label": untag(label_m.group(1)) if label_m else "",
    }

    events = []
    for m in RE_HEAD.finditer(html):
        idm = RE_ID.search(m.group(2))
        events.append((m.start(), "h", untag(m.group(3)), idm.group(1) if idm else None, None))
    for m in RE_PARA.finditer(html):
        clsm = RE_CLASS.search(m.group(1))
        events.append((m.start(), "p", untag(m.group(2)), None, clsm.group(1) if clsm else ""))
    events.sort(key=lambda e: e[0])

    blocks = []
    anchor, heading = None, None
    for _, kind, text, aid, cls in events:
        if kind == "h":
            heading = text
            if aid:
                anchor = aid
        elif text:
            blocks.append({"text": text, "anchor": anchor, "heading": heading, "cls": cls or ""})
    return meta, blocks


# ---------------------------------------------------------------- matching

def build_surface_forms(cards, cfg):
    """normalized surface form -> list of card ids that can produce it."""
    stop = {normalize(w) for w in cfg["stopwords"]}
    forms = collections.defaultdict(list)
    for cid, rec in cards.items():
        n = normalize(rec["name"])
        if len(n) < cfg["min_name_length"] or n in stop:
            continue
        forms[n].append(cid)
        for extra in cfg["aliases"].get(cid, []):
            forms[normalize(extra)].append(cid)
    return forms


def choose_card(candidates, cards, guide_file, cfg):
    """Several cards share a surface form (Utilize, Recruit, Analyze...).
    Inside a captain guide, attribute to that captain's own printing."""
    if len(candidates) == 1:
        return candidates[0]
    prefix = cfg["deck_prefix_by_guide"].get(guide_file)
    if prefix:
        own = [c for c in candidates if c.startswith(prefix + "-") or c == prefix]
        if own:
            return own[0]
    common = [c for c in candidates if cards[c].get("source") == "Common"]
    if common:
        return common[0]
    return sorted(candidates)[0]


def index_guide(path, cards, forms, cfg):
    """Return card_id -> {'count': n, 'hits': [{anchor, heading, snippet, mode}]}"""
    guide_file = os.path.basename(path)
    meta, blocks = parse_guide(path)
    found = collections.defaultdict(lambda: {"count": 0, "hits": []})

    # Mode 1: exact section anchors.
    anchored = set()
    seen_anchor = set()
    for i, b in enumerate(blocks):
        aid = b["anchor"]
        if not aid or aid not in cards or aid in seen_anchor:
            continue
        seen_anchor.add(aid)
        anchored.add(aid)
        body = [x for x in blocks[i:] if x["anchor"] == aid][: cfg["max_hits_per_guide"]]
        for blk in body:
            snip, trunc = truncate(blk["text"], cfg["snippet_max_chars"])
            found[aid]["hits"].append({
                "anchor": aid, "heading": blk["heading"], "snippet": snip,
                "truncated": trunc, "mode": "anchor", "lore": "lore" in blk["cls"],
            })
        found[aid]["count"] = len(body)

    # Mode 2: name occurrences in paragraph text.
    patterns = {
        form: re.compile(r"(?<![a-z0-9])" + re.escape(form) + r"(?![a-z0-9])")
        for form in forms
    }
    for b in blocks:
        if cfg.get("skip_lore_in_text_mode", True) and "lore" in b["cls"]:
            continue  # lore paragraphs are episode trivia, not strategy discussion
        ntext = normalize(b["text"])
        for form, pat in patterns.items():
            if form not in ntext or not pat.search(ntext):
                continue
            cid = choose_card(forms[form], cards, guide_file, cfg)
            if cid in anchored:
                continue
            entry = found[cid]
            entry["count"] += 1
            if len(entry["hits"]) < cfg["max_hits_per_guide"]:
                snip, trunc = truncate(b["text"], cfg["snippet_max_chars"])
                entry["hits"].append({
                    "anchor": b["anchor"], "heading": b["heading"], "snippet": snip,
                    "truncated": trunc, "mode": "text", "lore": "lore" in b["cls"],
                })
    return meta, dict(found)


# ---------------------------------------------------------------- driver

def build(repo, cfg):
    guides = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(repo, "*.html"))
        if os.path.basename(p) not in cfg["exclude_files"]
    )
    cards = load_cards(repo)
    forms = build_surface_forms(cards, cfg)

    guide_meta = {}
    per_card = collections.defaultdict(list)
    for gfile in guides:
        meta, found = index_guide(os.path.join(repo, gfile), cards, forms, cfg)
        if not found:
            continue
        guide_meta[gfile] = meta
        for cid, entry in found.items():
            per_card[cid].append({
                "guide": gfile,
                "count": entry["count"],
                "hits": entry["hits"],
            })

    for cid in per_card:
        # anchor guides first, then by mention count
        per_card[cid].sort(
            key=lambda e: (0 if e["hits"] and e["hits"][0]["mode"] == "anchor" else 1, -e["count"])
        )

    return {
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "tools/build_strategy_index.py",
        "guide_count": len(guide_meta),
        "card_count": len(per_card),
        "guides": guide_meta,
        "cards": {cid: per_card[cid] for cid in sorted(per_card)},
    }


def report(index, cards):
    print("guides indexed : %d" % index["guide_count"])
    print("cards with hits: %d of %d (%.0f%%)"
          % (index["card_count"], len(cards), 100.0 * index["card_count"] / max(1, len(cards))))
    modes = collections.Counter(
        h["mode"] for e in index["cards"].values() for g in e for h in g["hits"])
    print("hit modes      : %s" % dict(modes))
    tot = sorted(((sum(g["count"] for g in e), cid) for cid, e in index["cards"].items()),
                 reverse=True)[:15]
    print("\ntop mentions (scan for false positives):")
    for n, cid in tot:
        guides = ", ".join(g["guide"].replace(".html", "") for g in index["cards"][cid])
        print("  %3d  %-30s %s" % (n, cards[cid]["name"], guides))
    orphan = [cid for cid in cards if cid not in index["cards"]]
    print("\ncards with no guide mention: %d" % len(orphan))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default=os.path.join("data", "strategy-index.json"))
    ap.add_argument("--config", default=os.path.join("tools", "strategy_index_config.json"))
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    cfg_path = args.config if os.path.isabs(args.config) else os.path.join(args.repo, args.config)
    with open(cfg_path, encoding="utf-8") as fh:
        cfg = json.load(fh)

    index = build(args.repo, cfg)
    cards = load_cards(args.repo)
    payload = json.dumps(index, ensure_ascii=False, indent=1, sort_keys=False)

    out_path = args.out if os.path.isabs(args.out) else os.path.join(args.repo, args.out)

    if args.check:
        if not os.path.exists(out_path):
            print("MISSING %s" % out_path, file=sys.stderr)
            return 1
        with open(out_path, encoding="utf-8") as fh:
            current = json.load(fh)
        fresh = json.loads(payload)
        current.pop("generated", None)
        fresh.pop("generated", None)
        if current != fresh:
            print("STALE: %s does not match a fresh build. Run "
                  "python tools/build_strategy_index.py" % out_path, file=sys.stderr)
            return 1
        print("OK: %s is current." % out_path)
        return 0

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(payload)

    # Companion file: just the ids, for the badge pass at scanner start-up.
    # The scanner loads this always and the full index only when a drawer opens.
    badge_path = os.path.join(os.path.dirname(out_path), "strategy-cards.json")
    badges = {"generated": index["generated"],
              "cards": {cid: sum(g["count"] for g in e) for cid, e in index["cards"].items()}}
    badge_json = json.dumps(badges, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with open(badge_path, "w", encoding="utf-8") as fh:
        fh.write(badge_json)
    print("wrote %s (%.0f KB)" % (badge_path, len(badge_json) / 1024.0))
    print("wrote %s (%.0f KB, %d cards, %d guides)"
          % (out_path, len(payload) / 1024.0, index["card_count"], index["guide_count"]))

    if args.report:
        print()
        report(index, cards)
    return 0


if __name__ == "__main__":
    sys.exit(main())
