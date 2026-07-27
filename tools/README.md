# tools/ — session tooling for the ST:CC Compendium

Scripts built during the 04 Jul 2026 consolidation sessions. They are the
*methods* behind the CSS consolidation, the image migration, and the card
database seeding. Any future session (any Claude model) should adapt these
instead of reinventing them.

**Path note:** these were written inside a specific sandbox; check the I/O
paths at the top of each script and adjust before running. All are Python 3,
stdlib except PIL (montage, image conversion) and openpyxl (workbook).

| Script | Purpose |
|---|---|
| `parse.py` | Extract + tokenize every guide's `<style>` block (@media-aware); normalize legacy theme vars (`--blue`/`--red`/`--andorian`/`--amber`) to the semantic `--accent` family. Basis for any future CSS folding into css/stcc.css. |
| `convert.py` | Convert a guide from inline CSS to the shared stylesheet: swap `<style>` for the stcc.css link, keep only legit per-guide inline rules, set the theme body class. |
| `verify.py` | Rendering safety net: computes effective styles per selector (vars expanded through theme env) before/after a conversion and diffs per property; flags shared rules newly applying to a page. Run after ANY stylesheet or conversion change. |
| `migrate_shran.py` | First image-migration pilot (h3-sectioned captain guide). Superseded by migrate_captains.py but kept as the simplest worked example. |
| `migrate_captains.py` | Card-image migration for captain guides: boards extracted to img/guides/, tabletop scans removed, per-section library images inserted (h3 or bold-lead paragraph styles), scan-alt fallback rows, unmatched-name reporting. |
| `migrate_markets.py` | Same for market guides; handles Promo Pack suffixes and img/promo1 lookups. |
| `make_montage.py` | Tile card images into labeled 2x2 grids so a session can read 4 card faces per image view. The efficiency trick behind database seeding. |
| `carddata.py` / `carddata2.py` | Structured record of all Box 2/3 cards as read from card faces (carddata2 is the final merged form). Raw material for box2.json / box3.json, independent of the Google Sheet. |
| `build_workbook.py` | Generate stcc-card-database.xlsx from carddata2: 4 tabs, dropdowns, status colors, HYPERLINK image links. NOTE: the live sheet on Periodic_agent's Drive is canonical; never regenerate wholesale over it (see WORKFLOW.md, Card database update cycle). |
| `build_guide.py` | Build a guide from a BGG SingleFile capture + `configs/<slug>.json`: verbatim text, image decode to site naming, TOC, card-id H3 anchors (`h3_ids`), video section. Writes to `out/`, never in place. |
| `verify_guide.py` | Machine gate before any guide push: page text vs `text/<slug>.txt` exactly, image refs, anchors, HTML balance, footer/lightbox/GoatCounter furniture. Exit 1 = do not push. |
| `extract_text.py` | Canonical text extractor, single source of truth for both generating and verifying `text/<slug>.txt`. The post-ship edit loop: edit the HTML, `python3 tools/extract_text.py <guide>.html -o text/<slug>.txt`, then `verify_guide.py`. |
| `fill_image_filenames.py` | Fill `filename` in a box JSON from scans on disk, keyed on the `id` == filename-stem invariant. `original` variants only (reprints resolve to the earliest printing's art). Use when a guide import lands images ahead of the community sheet's image column. |
| `build_strategy_index.py` | Cross-reference every card against every guide -> `data/strategy-index.json` (snippets, lazy-loaded) + `data/strategy-cards.json` (badge counts, loaded at start-up). Config in `strategy_index_config.json`. `--report` for coverage, `--check` for CI staleness. |
| `patch_scanner_strategy.py` | Apply the Strategy badge + guide-passage drawer to `card-browser-mockup.html`. Idempotent, anchor-asserting; builds output in memory before writing (a failed patch must never truncate the scanner). |
| `test_scanner.mjs` | Headless DOM-shim test for the scanner: image resolution rules, lightbox integrity, inline-handler scope, strategy badge/drawer wiring, and index link integrity (guides + anchors + card ids). Run from repo root: `node tools/test_scanner.mjs .` Requires a full checkout (sparse clones without img/ false-fail the lightbox check). |
| `strategy-drawer-preview.html` | Standalone preview of the badge + drawer against live data; served at /tools/ on Pages, not linked from the site. |

## Guide config lifecycle (why replace lists stay short)

A `configs/<slug>.json` is the record of one **import**, not a running patch
file for the page. The `replace` list carries only the corrections approved
*before* the guide shipped, applied at build time so the first published text
is the approved text.

Once a guide is live, **the HTML is the source of truth** (WORKFLOW Rule 1c).
McCue made Periodic_agent his editor of record, so a later correction is made
directly in the guide HTML, followed by

```
python3 tools/extract_text.py <guide>.html -o text/<slug>.txt
python3 tools/verify_guide.py <guide>.html text/<slug>.txt --img-root .
```

and both files go in one reviewed commit. Nothing is added to the config. This
is what keeps replace lists from growing into an editing history that has to be
replayed to understand the page.

The consequence, stated so nobody trips on it: **rebuilding a shipped guide
from its capture reproduces the import, not the live page.** Diff before
copying a rebuild over a shipped file.
