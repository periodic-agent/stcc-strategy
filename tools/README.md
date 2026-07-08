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
