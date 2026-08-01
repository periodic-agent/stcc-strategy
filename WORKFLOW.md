# ST:CC Compendium — Workflow
## Single source of operational truth.

---

## Session Startup

Files live on GitHub Pages at:
- **Live site:** https://periodic-agent.github.io/stcc-strategy/
- **GitHub repo:** https://github.com/periodic-agent/stcc-strategy

The live repo is authoritative — fetch live, including WORKFLOW.md. Do NOT work from project knowledge copies; they may be stale. Never assume file content from memory or previous sessions.

**Preferred fetch: one shallow clone.** `raw.githubusercontent.com` serves stale files (hours-old cache observed) and is proxy-blocked in some sessions. `git clone --depth 1 https://github.com/periodic-agent/stcc-strategy.git` works through the same proxy, is always current, and provides every repo file locally, including images. One call.

**Never trust a raw fetch for currency.** `raw.githubusercontent.com` and `web_fetch` sit behind CDN and tool caches: they may fail outright (permissions error) or — worse — return HTTP 200 with a silently stale copy hours old (observed: an index.html missing two live guides; a pre-consolidation WORKFLOW.md). A clone always returns the true current tip. If a single-file fetch is unavoidable, treat the result as possibly stale and verify against a clone before acting on it. urllib fallback:
```python
import urllib.request
url = 'https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/[filename]'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as r:
    html = r.read().decode()
```

After editing, save outputs and call `present_files` to surface the file for review. Never render files inline in chat.

### Session Startup Smoke Test (any model)

Before touching content in a new session: (1) fetch PROJECT_BRIEF.md and WORKFLOW.md from the live repo; (2) confirm the token file AND the PII denylist (`pii_denylist.txt`) are readable from project knowledge — the push script fails closed without both; (3) dry-run the push script against an unchanged file — expected output: "No changes ... Nothing pushed." Two minutes, proves the whole pipeline. Session tooling (CSS parser/verifier, guide migrators, montage generator, workbook builder) lives in `tools/` — adapt those, don't reinvent.

### Cost discipline (learned 14–15 Jul 2026)

- `git clone --depth 1` and work from the local clone; do not probe raw URLs file by file.
- **Never fetch full guide pages into the chat context** to check conventions; grep the local clone instead. Conventions are documented here; trust this file first, verify with grep second.
- **Batch bash calls.** Every tool round-trip replays the whole conversation; ten probes cost more than one scripted call.
- **Model choice:** with build+verify scripts as the gate, build sessions can run on a cheaper model (Sonnet); verbatim fidelity is enforced mechanically, not by model care.

---

## Push Pipeline

**Push: Claude pushes to GitHub directly via `push_to_github.py`, but ONLY after Periodic_agent reviews the presented file and explicitly approves. Never push before the go-ahead.**

```
GH_TOKEN=<token> python3 push_to_github.py --pii-file <path_to_pii_denylist.txt> <local_path> <repo_path> "commit message"
```
Fetch the script from the live repo before running. It shallow-clones the repo, copies the file in, commits, and pushes via git with a one-shot authenticated URL (no GitHub API dependency; `api.github.com` is blocked in some sandboxes while git over HTTPS works). Files deploy via GitHub Pages in ~60 seconds. Multi-file commits: `-m "msg" local:repo local:repo ...`.

Since v3 the script refuses to run without the PII denylist (`--pii-file` or `PII_FILE` env; see Anonymity Rules below). No denylist = no push, by design.

## GitHub Token Handling

**The token is NOT in the repo and NOT in the script.** It is a **fine-grained PAT** scoped to `periodic-agent/stcc-strategy` only, permission **Contents: read/write** (plus mandatory Metadata: read). Worst-case leak damage is limited to this one repo.

**Where it lives:** project knowledge file `git_pat_token.txt`. Every project chat can read it; Periodic_agent never types it.

**How to use it at push time:** read the token from the project knowledge file and pass it to the script via the `GH_TOKEN` environment variable, or point the script at the file directly:
```
python3 push_to_github.py <local_path> <repo_path> "message" --token-file <path_to_git_pat_token.txt>
```

**WARNING — token hygiene rules for every session:**
1. NEVER write the token value into any file saved to outputs or pushed to the repo. Not in scripts, not in HTML comments, not in WORKFLOW.md deltas.
2. NEVER print the token in chat, in logs, or in command echoes. The push script scrubs it from its own output; keep it that way.
3. NEVER hardcode it back into `push_to_github.py`. The previous hardcoded token was exposed publicly and had to be revoked (Jul 2026).
4. If the token ever appears in a pushed file or in the public repo history: tell Periodic_agent immediately so he can revoke it on GitHub.

**Expiry:** fine-grained PATs expire (1 year max). If a push fails with an auth error, the likely cause is expiry; Periodic_agent mints a new token and replaces `git_pat_token.txt` in project knowledge.

---

## Anonymity Rules

**This is an anonymous project.** The site owner appears everywhere — files, commit messages, configs, docs, chat-visible output — only as **Periodic_agent** (GitHub: periodic-agent). The owner's real name, personal email addresses, and machine username must never appear in anything that leaves the session.

**The denylist:** `pii_denylist.txt` lives in **project knowledge** (next to `git_pat_token.txt`), NEVER in the repo, never in outputs destined for pushing. One term per line, `#` for comments.

**The gate (fail closed):** `push_to_github.py` v3 refuses to push unless given the denylist (`--pii-file <path>` or `PII_FILE` env). It scans file contents (binary-safe, case-insensitive), repo paths, and the commit message; any hit blocks the entire push and reports the term masked. It also refuses to push the denylist itself. There is no bypass flag.

**Reusable standalone gate:** `tools/push_gate.py` — same scan logic plus `--scan-dir` (walk a folder) and `--scan-git-history` (scan every object in a repo's full history). Stdlib only; vendor it into any other project alongside its own denylist.

**Hygiene rules for every session:**
1. Watch indirect leaks: local Windows paths in tracebacks or logs, script headers, EXIF in photographed cards, autofilled author fields, example email addresses.
2. Never paste the denylist contents into chat, pushed files, or WORKFLOW deltas; refer to terms masked if a hit must be discussed.
3. If a personal identifier ever lands in the public repo: tell Periodic_agent immediately; remediation is a git-filter-repo rewrite, force-push, and GitHub support purge.

**Audit (quarterly, and before any public announcement):**
```
git clone https://github.com/periodic-agent/stcc-strategy.git audit && \
python3 audit/tools/push_gate.py --pii-file <path_to_pii_denylist.txt> --scan-git-history audit
```
Expected output: `push_gate: clean — no denylisted term in any object of audit`.

---

## Project Overview

A strategy compendium for **Star Trek: Captain's Chair** hosted at:
**https://periodic-agent.github.io/stcc-strategy/**

GitHub repo: **https://github.com/periodic-agent/stcc-strategy**

Content by **Matthew McCue (mdmccu2)** from BGG forums.
Formatted by **Periodic_agent**

### Design Principle: Guides vs Tools

- Guides = McCue's strategy content, formatted by Periodic_agent
- Tools = built by Periodic_agent (Card Scanner, future tools)
- Keep these conceptually separate: don't add mechanical card data to guides; link to Card Scanner instead
- "Guides are for guiding, Card Scanner is a fun tool"

---

## Rules

1. **Verbatim by default.** McCue's text is reproduced as posted — no summarizing, no rewriting, no restructuring. Format only: headings, paragraph breaks, image placement.
1a. **Periodic_agent-directed edits are sanctioned (Jul 2026).** McCue trusts Periodic_agent as the editor of record. When Periodic_agent says edit, we edit — no pushback, no re-confirmation. The model NEVER alters guide text on its own initiative: it flags, Periodic_agent decides. Approved changes are canonical.
1b. **Canonical text — text/<slug>.txt.** Every guide ships with its canonical text file: the approved wording of the whole page, generated by `tools/extract_text.py` and committed in the SAME commit as the guide HTML (a guide push without its canonical file is incomplete — extension of Rule 7). Import flow: build verbatim → the model FLAGS typos/inconsistencies with context → Periodic_agent approves or rejects each flag → approved corrections are applied via the config `"replace"` list at build time (a pattern that matches nothing is a hard build error) → the built page's extracted text becomes `text/<slug>.txt`. `verify_guide.py` compares the page against the canonical EXACTLY — alterations, insertions, deletions, and reorderings all fail.
1c. **After a guide ships, its HTML is the source of truth.** Corrections edit the HTML and regenerate `text/<slug>.txt` with `tools/extract_text.py` in one approved commit. Nothing is added to the guide config after import — the config is the record of the import, not an editing history. `build_guide.py` refuses to rebuild a shipped guide; `--reimport` is reserved for genuine re-imports (McCue edited the BGG source, or a builder change must be replayed).
2. **Paragraph breaks** must sometimes be identified by asking for the last sentence of each paragraph when the source text runs together (BGG strips formatting).
3. **Image credit** footer on every guide: `Card images © WizKids.`
4. **Attribution** footer on every guide: `Guides by Matthew McCue (mdmccu2) · Website by Periodic_agent`
5. **Back to Compendium** link at top and bottom of every guide.
6. **Card Scanner footer** is different: `Card images © WizKids.` only — no content attribution line. Contributors will be acknowledged separately as the project grows.
7. **Generators ship with their output.** Any script that generated or transformed pushed content ships in `tools/` in the same commit as that content. A push of generated files without its generator is incomplete.

> **Tier principle:** place each convention at the tier that matches the cost of breaking it. Prose here reminds; a `_note` on the artifact catches whoever is holding it; a non-zero exit prevents. A convention that has been broken once gets promoted a tier, not restated.

---

## File Naming Convention

| Guide | Filename |
|---|---|
| Shran | `shran.html` |
| TBG Locations | `tbg-locations.html` |
| Picard | `picard.html` |
| Burnham | `burnham.html` |
| Sisko | `sisko.html` |
| Sela | `sela.html` |
| Koloth | `koloth.html` |
| TBG captain guides | `tbg-[name].html` |
| Market guides | `persons.html`, `allies.html`, `ships.html`, `cargo.html`, `locations.html`, `encounters-incidents.html` |
| Strategy guides | `solo.html`, `five-year-mission.html`, `vs-picard.html` |
| Card Scanner | `cards.html` (renamed 2026-07-29 from `card-browser-mockup.html`, which now redirects to it; keep the stub, links were published under the old path) |

---

## Guide Build Pipeline (tools/) — the workflow for every new guide

Guide creation is scripted. The model never retypes McCue's text; the scripts move it verbatim from the SingleFile capture into the styled HTML.

### Step 0 — Capture BGG thread (Periodic_agent)
- Use **SingleFile** browser extension → saves full thread as `.html`; upload it to the session.

### Steps 1–5 — Per-guide session procedure (cheap path)
1. `git clone --depth 1` the repo (see Session Startup). One call.
2. Write the config JSON (model judgment: cuts, lore, headers, tags, video from the Video Playthroughs table).
3. Run build + verify in one bash call. Fix config, not output, if verify fails.
4. Present draft for Periodic_agent's review; wait for approval; push guide + images + index flip with `push_to_github.py --pii-file <denylist> --token-file <token> -m` (multi-file, one commit; both files from project knowledge — the script fails closed without the denylist).
5. Update the index: flip Soon → Live (`badge-video` ▶ span if the guide has a video), bump `hero-date`.

```
python3 tools/build_guide.py <singlefile.html> tools/configs/<slug>.json --out out/
python3 tools/verify_guide.py out/<slug>.html out/text/<slug>.txt --img-root out/
```

- **tools/build_guide.py** — extracts McCue's first post (balanced gg-markup-content), decodes all images (quoted and unquoted `src=` base64 WebP) to JPG with site naming, emits marked verbatim text, and builds the styled guide from `tools/guide-template.html`. All judgment calls live in the per-guide JSON config: cuts, lore paragraphs, inserted structural H2s (Missions, Captain Card & Starting Components), image name overrides, board alts, TOC label shortening, videos.
- **tools/verify_guide.py** — machine gate before push: page text matches `text/<slug>.txt` exactly (via `tools/extract_text.py`, the same extractor that generates it), image refs resolve, anchors resolve, HTML balanced, footer/lightbox/GoatCounter furniture present. Exit 1 = do not push.
- **tools/extract_text.py** — canonical text extractor; single source of truth for both generation and verification. Build emits `out/text/<slug>.txt` automatically; commit it alongside the guide.
- **tools/configs/georgiou.json** — real example config; copy and adapt per guide.
- Validated by regenerating georgiou.html from its BGG capture: word-for-word identical output.

If the thread's images are CDN-only, see "Promo / CDN-only guides" under Image Extraction Notes before building.

---

## HTML Design System

### Shared stylesheet — css/stcc.css (since 04 Jul 2026)

All 22 guides link one shared stylesheet instead of carrying inline CSS:
```html
<link rel="stylesheet" href="css/stcc.css?v=1">
```
- **Theme by body class:** Core Box = plain `<body>`; To Boldly Go = `<body class="theme-tbg">`; Second Contact = `<body class="theme-sc">`. Theme classes override only the accent variables (`--accent`, `--accent2`, `--accent-rgb`, `--border`, `--ui`, `--hdr-edge`, `--hdr-mid`, `--title-glow`).
- **Semantic variables:** rules use `var(--accent)` etc., never `--blue`/`--red`/`--amber` (those names are retired).
- **Cache:** GitHub Pages serves with max-age 600 s, so stcc.css changes propagate within ~10 min on their own. Bump `?v=` in all guides only if a change must land instantly.
- **Inline `<style>` is kept ONLY for:** market guide `.toc-card`/`.toc-card:hover` suit colors (2 rules per guide); `sc-market-locations-rewards.html` `.toc-grid-label` margin-top; `vs-picard.html` `ul`/`li`/`li strong` list styles. Everything else belongs in stcc.css.
- **New guides:** link stcc.css + set the theme class. Do NOT paste a full CSS block.
- **Lightbox:** CSS is in stcc.css, but each guide still needs the lightbox HTML + script snippet (see Lightbox section).

### Box color reference

**Box 1 — Captain's Chair: Blue**
- Accent: `#4a9fd4` / `#7ec8f0`
- Header gradient: `#061020 → #0d1e3a`
- Border: `rgba(74,159,212,0.25)`
- Gold (h3): `#c8a84b`

**Box 2 — To Boldly Go: Red**
- Accent: `#d44a4a` / `#f07e7e`
- Header gradient: `#160608 → #2a0e10`
- Border: `rgba(212,74,74,0.25)`

**Box 3 — Second Contact: Amber**
- Accent: `#c8a84b` / `#e8c96a`
- Border: `rgba(200,168,75,0.25)`

### Fonts
- Headers: `Orbitron` (Google Fonts)
- Body: `Exo 2` (Google Fonts)

### Card images in guides
- Cards: `img/box1|box2|box3/<name>.jpg` per the Card Image Filename Convention below; captain boards: `img/guides/<captain>/<captain>-board-basic|advanced.jpg`.
- **Display-image standard (Jul 2026):** the repo carries display copies only — max width 1170 px (native iPhone width; lightbox renders 1:1), JPG quality 80, progressive, ~500-600 KB per card. High-resolution originals stay on local disk, off git. Every image import runs `tools/shrink_card_images.py` over the new files before pushing; the script skips anything already within the standard.
- Captain guide photos: scrollable horizontal `.card-row` (height: 220px, mobile: 170px)
- Single card images (TBG style): `.card-img` block (max-width: 260px)
- All images: lightbox on click
- All images: `loading="lazy"`

### Navigation
```html
<div class="nav-bar"><a href="index.html">← Back to Compendium</a></div>
```
Top and bottom of every guide. Top nav goes **before** `<header>`.

### Hero / Chapter Header
```html
<header class="chapter-header">
  <div class="chapter-label">Captain's Chair</div>
  <h1 class="chapter-title"><span>CaptainName</span></h1>
  <div class="chapter-meta">By Matthew McCue (mdmccu2)</div>
  <div class="chapter-date">Posted [BGG post date]</div>
  <div class="chapter-tags">
    <span class="tag">Trait1</span><span class="tag">Trait2</span>
  </div>
</header>
```

### Chapter Label Convention (finalized)
- Core Box guides: `Captain's Chair` — no "Strategy Guide" or "Strategy Compendium" suffix
- TBG guides: `To Boldly Go`
- Guide h1 titles: captain name only (e.g. `Thy'Lek Shran`, `Koloth, the Dahar Master`)

### Chapter date
`Posted <BGG post date>` (the date McCue posted the guide on BGG, not the build date). `.chapter-date` CSS is in stcc.css; no per-guide CSS needed. Author credit goes in the chapter header; posted date underneath.

### Footer
```html
<footer>
  Card images © WizKids.<br>
  Guides by Matthew McCue (mdmccu2) · Website by Periodic_agent
</footer>
```

### Lightbox
```html
<div id="lightbox" onclick="this.classList.remove('open')">
  <img id="lightbox-img" src="" alt="">
</div>
<script>
function openLightbox(img) {
  document.getElementById('lightbox-img').src = img.src;
  document.getElementById('lightbox').classList.add('open');
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.getElementById('lightbox').classList.remove('open');
});
</script>
```
All images use `onclick="openLightbox(this)"`.

### Navigation — Table of Contents & Back to Top

- **Captain guides:** `.toc-list` Contents built from H2 sections, with back-to-top links.
- **Market guides** (Person, Ally, Ship, Cargo, Location, Encounters & Incidents): **pill grid** below the header. TOC label reads "Jump to Card."

Structural TOC CSS (`.toc-grid`, `.toc-grid-label`, `.toc-cards`) is in stcc.css. The individual `.toc-card` link rule is NOT in stcc.css — it must be pasted inline in each market guide, in full, because it carries the per-guide suit color. Copy the WHOLE rule (font, padding, border-radius, `color`, `background`, `text-decoration:none`, transition), not just the border line. The only per-guide variable is the suit color in `border` and `:hover` `border-color`.

If you copy only the border/color lines and omit `color`/`text-decoration:none`/`background`/`padding`/`border-radius`, the pills fall back to default blue underlined browser anchors (this bug shipped in promo-pack-2 on 09 Jul 2026 and had to be patched). Canonical full rule:
```html
<style>
  .toc-card{font-family:'Exo 2',sans-serif;font-size:0.75rem;font-weight:400;padding:0.2rem 0.6rem;border:1px solid <SUIT>55;border-radius:3px;color:#ccd6f0;text-decoration:none;background:var(--bg2);transition:background 0.15s,border-color 0.15s;}
  .toc-card:hover{background:var(--bg3);border-color:<SUIT>;}
</style>
```
Replace `<SUIT>` with the suit hex from the Card Scanner palette table below.

---

## Index Conventions (index.html)

**Box naming (current):**
- Box 1: `Captain's Chair — Core Box` (blue)
- Box 2: `Captain's Chair — To Boldly Go` (red)
- Box 3: `Captain's Chair — Second Contact (Expansion)` (amber)
- Box 4: `Other Guides` (gray)
- Box banner subtitle: `Strategy Guides` on all four boxes

**Entry sub-text:** empty for all guide entries. Keep complexity ratings on captain entries. Keep "Core Box · Beta" on Card Scanner.

**Card Scanner:** sits as a prominent `box-banner purple` above Box 1 — NOT inside a card-grid. Purple dot (`#d4699f`), full-width, links to `cards.html`. Title: "Card Scanner", subtitle: "Explore all cards and decks".

```html
<a href="cards.html" class="box-banner purple">
  <div class="box-dot"></div>
  <div>
    <div class="box-banner-title">Card Scanner</div>
    <div class="box-banner-sub">Explore all cards and decks</div>
  </div>
</a>
```

```css
.box-banner.purple { background: rgba(212,105,159,0.08); border: 1px solid rgba(212,105,159,0.3); }
.box-banner.purple .box-dot { background: #d4699f; box-shadow: 0 0 8px #d4699f; }
.box-banner.purple .box-banner-title { color: #d4699f; }
a.box-banner { text-decoration: none; transition: transform 0.2s, border-color 0.2s; }
a.box-banner:hover { transform: translateY(-2px); border-color: #d4699f; }
```

**Live/Soon flips:** when a guide ships, flip its entry Soon → Live, add the `badge-video` ▶ span if the guide has a video, bump `hero-date`.

**Known nit:** `.badge-video` class is used on Live captain entries but has no CSS definition (renders with base `.entry-badge` style). Pre-existing; harmless; define it whenever index.html gets its next styling pass.

---

## Analytics

GoatCounter script on every page including future guides:
```html
<script data-goatcounter="https://stcc-compendium.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
```
Place just before `</body>`. Tracker endpoint: `https://stcc-compendium.goatcounter.com/count`.

---

## Card Database

### File structure
```
box1.json    -- Captain's Chair, complete (250 cards)                         [repo ROOT]
box2.json    -- To Boldly Go, live (248 cards incl. Khan deck)                [repo ROOT]
box3.json    -- Second Contact, live (99 cards: Common, Freeman, Pike, Riker) [repo ROOT]
promo1.json  -- Promo Pack 1, complete (5 cards, split out of box1.json)      [repo ROOT]
promo2.json  -- Promo Pack 2, seeded (6 cards; traits/icons pending, Issue 5) [repo ROOT]
```
The boxN.json files live at the **repo root**, not in a `data/` folder.

### Scanner data — runtime fetch + id resolver

The Card Scanner (`cards.html`) loads card data at **runtime**. On page
load it `fetch`es every file in `BOX_SOURCES` (`box1.json`, `box2.json`, `box3.json`,
`promo1.json`, `promo2.json`) into `RAW_BOXES`, stamping each card with its source
file's box key (`_srcBox`) — the source file, not the card's `game_box`, decides
which box a card belongs to. There is **no inline `ALL_CARDS` array and no
build-time injection**.
To wire a new box, add one line to `BOX_SOURCES` and push its JSON — nothing else.
(`tools/build_scanner_data.py` was the old inline injector; it is **legacy**, no longer
part of the pipeline.)

`resolveCards(pool)` groups the selected boxes' raw cards **by `id`** and emits one
record per id:
- **text** = the `updated` printing if any, else the earliest-box printing;
- **image** = newest box with a non-empty `filename` whose text matches the resolved
  version (an `updated` printing takes only its own image);
- **glory** = coalesced across ALL printings of the id (first non-null wins) — Box 1
  reprints inherit the Box 2/3 annotation; `null` on every printing means no badge;
- **copies** = number of physical printings; **badge** = `update` beats `duplicate`,
  read only from the group's own variants (never looks forward, so adding a later box
  never changes an existing badge).

Because the whole dedup joins on `id`, a reprint/updated card **must** share its `id`
with the Box 1 original — which checks 1 and 4 (below) enforce at build time.

`normIcons` flattens `icons` to `"<specialty> <type>"` strings, **one per object**, and
the pill view renders one pill per string. Icon multiplicity is therefore encoded as
**repeated objects, never a `count` field** (see Icon schema).

**`game_box` is an exact-string contract.** `GAMEBOX_KEY` maps `"Captain's Chair"`→core,
`"To Boldly Go"`→tbg, `"Second Contact"`→2nd. `rawBoxKey` `console.warn`s and returns
**null** (card omitted) on any unrecognized `game_box`; it no longer silently defaults to
core. `build_box2_from_sheet.py` enforces the same allow-list and hard-fails, so a typo
cannot reach a JSON file. The internal box key (`core`/`tbg`/`2nd`/`promo1`/`promo2`) is
opaque and separate from these display strings — `2nd` stays `2nd` even though its label
reads "Second Contact".

### Canonical JSON schema (per card)
```json
{
  "id": "bruce-maddox",
  "name": "Bruce Maddox",
  "suit": "Person",
  "source": "Common",
  "game_box": "Captain's Chair",
  "species_traits": ["Human"],
  "regular_traits": ["Starfleet", "Scientist", "Engineer"],
  "other_traits": [],
  "icons": [
    {"specialty": "Research", "type": "Skill"},
    {"specialty": "Research", "type": "Focus"}
  ],
  "filename": "bruce-maddox.jpg"
}
```

### Trait classification — rulebook p.36 (canonical)
**Species Traits:** Alien, Aenar, Andorian, Android, Bajoran, Betazoid, Borg, Breen, Cardassian, Changeling, Ferengi, Human, Jem'Hadar, Kelpien, Klingon, Orion, Pakled, Reman, Romulan, Synthetic, Tellarite, Transcendent, Trill, Vorta, Vulcan, XB, Xindi

**Regular Traits:** Ambassador, Anomaly, Augment, Beverage, Business, Cloak, Communication, Creature, Doctor, Dominion, Engineer, Helmet, Hologram, Imperial, Mind Control, Ops, Pilot, Maquis, Scientist, Security, Shady, Spy, Starbase, Starfleet, Telepath, Time Travel, Weapon

**Other Traits:** Attack, Ongoing, Surprise, Wildcard

### Icon schema — rulebook p.17
- `specialty`: Research / Influence / Military / Any / Variable
- `type`: Skill / Focus
- **Any** + Skill or Focus: counts for all three specialties in the relevant filter
- **Variable** Skill: conditional value, shown in its own filter category
- No "Wild" terminology — not a rulebook term, eliminated from schema
- **Repeated objects, no `count`.** One `{type,specialty}` object per printed icon; a
  card with two Military Skills is two objects, not `{count:2}`. `normIcons` renders one
  pill per object, so repeats display correctly with no scanner logic. (Box 1 used a
  `count` field until Jul 2026; removed for a uniform one-object-per-icon model.)

### Icon filtering logic
- Selecting Research Skill returns: Research Skill + Any Skill cards
- Selecting Research Focus returns: Research Focus + Any Focus cards
- Selecting Variable returns: Variable Skill cards only
- Same logic applies to Influence and Military

### Suit conventions
- Market suits: Person, Ally, Ship, Cargo, Location, Encounter, Incident
- Crew deck only: Captain, Directive, Status
- **Captain and Directive are acceptable deviations from the rulebook** -- not official "suits" but used as suit values in the database for practical filtering. Noted and intentional.
- Captain cards colored gold, Directive cards gray, Status cards light blue

### Card-face design (live since 31 Jul 2026)

`cards.html` renders each card as a mini card face built from vector assets
extracted from the fan-made Traits Cyclopedia v2.1 PDF (extractors in `tools/`:
`extract_trait_icons.py`, `extract_skillfocus_icons.py`, `extract_focus_svg.py`,
`extract_suit_svg.py`; page builder `tools/build_scanner_v3.py`, which patches a
copy of the pre-card-face scanner and emits `cardface-assets.js`).

- **`cardface-assets.js`** (repo root, ~1.8 MB): data-URI bundle of 62 trait
  medallions (white-ringed on cards, bare in filter chips), 5 skill banners,
  4 true-SVG focus icons, 9 suit glyphs. Loaded with a `?v=<md5-8>` content
  hash for cache busting. Rebuild via `build_scanner_v3.py` whenever assets change.
- **Card entry**: name + suit in left-rooted colored banners (suit glyph in the
  suit banner), skill banners flush left, traits as vertical pills sorted
  shortest-first with overlapping medallions, focus icon bleeding into the
  rounded lower-right corner. No-focus cards with non-null `glory` show a glory
  badge there instead (horizontal white oval, enlarged delta overhanging ~2 px,
  Antonio digit). Card number + Update/Duplicate markers bottom-left; the "New"
  banner is retired. Clicking any card with an image (`has-img`) opens the
  plain image lightbox at that card in BOTH views (no caption, no guide links;
  decision 31 Jul 2026: image only, for a cleaner experience).
  `buildStrategyDrawer`/`toggleStrategy` remain in code but have no UI entry
  point. Cards without an image are not clickable.
  Wildcard is the only trait banner with black text: pale salmon `#f6c9bd`
  (all other trait banners carry white text on their family color).
- **Card footer**: a 1px rule spans the footer row (`.ce-footrow::before`) at the
  chips' centreline; the opaque number chip (`.cid2`, left-rooted, rounded right
  only), the starting-position pill (`.posin`) and the corner focus/glory art
  mask it, so the line reads as running out of the number chip, behind the pill,
  and into the corner icon. `.posin` shows `position_indicator` (uppercase,
  same Antonio size as the card number, rounded both ends), absolutely centred
  on the card. `placePosPills()` runs at the end of `render()` and measures each
  pill: one that would touch the number chip (the chip widens with an
  Update/Duplicate mark) is right-anchored instead via `.wide`; 18 of 403 pills
  today. The footer renders when any of card number, badge, or position exists.
- **`position_indicator`**: present on every record in all five JSONs, string or
  null; 415 of 610 non-null. Values seen: Available, Development, Reserve,
  Starting, Advanced, Captain, Discard, Deployed, Rewards, Controlled Location,
  Status, Incident Deck, Solo Campaign, Solo Challenge. The resolver coalesces
  it across printings (first non-null wins), like `glory`.
- **`away_team`**: on **Captain-suit records only** (all 16; no other record carries
  the key). The away-team size printed on the captain card, stored as a **string**
  because two captains print a plus: Archer `"2+"`, Pike `"4+"`. Wrathful Khan
  (`2KHA01B/22`) holds `""` — it is the flip side of Khan Noonien Singh and the value
  is not tracked, the same treatment as Devastated Ceti Alpha V's position indicator.
- **Font**: Antonio 600 (Google Fonts) for all card-vocabulary elements;
  Orbitron/Exo 2 remain for page chrome.
- **Filter chips**: rulebook-style banners; outline-only at rest (colored border
  + text via the `--cc` CSS var, icon kept), color-filled with white text when
  active. Every chip row shares one geometry: 22px height, Antonio 600 at
  `.86rem`, `.03em` tracking, uppercase, count in a `.62rem` dimmed `.cnt` slot.
  Skills/Focus (`.skill-pill`) kept the older Exo 2 metrics and rendered ~1.2px
  shorter until 1 Aug 2026; they now inherit the same block. The Skills chips
  use a mirrored banner asset (`CARDFACE.skillChip`, `b64_skill_banner(chip=True)`):
  the cap sits on the LEFT so it nests concentrically inside the pill's rounded
  edge, flat edge on the right, sized to the chip's 19px inner height so the two
  radii match; the card banners (`CARDFACE.skill`) keep the printed orientation,
  cap right. The generator mirrors the block (glyph positions mirror with it, so
  they are guaranteed to fit), then flips each proximity-merged glyph cluster
  back inside its own box, skipping any flip whose result would spill off the
  field (only Any, whose symbols stay mirrored). Their active state
  is still a translucent family-colour wash rather than the solid fill used by
  trait and suit chips. Counts always render (incl. "(0)") in a per-chip width-locked slot so
  selection never reflows the row.
- **Shareable URLs**: the search-bar state mirrors to `location.hash`
  (`#q=...`) via `history.replaceState`; restored on load, back/forward handled
  by `hashchange`. Documented in the help popover.
- **Glory data**: `glory` key on every box2/box3 card, integer or `null`
  (uniform shape; focus cards are always `null` because they print "?").
  Box 1 and promos carry no glory key; the resolver treats absent as null.
- `tools/test_scanner.mjs` runs the harness against `cards.html` including
  local external scripts (`cardface-assets.js`); run it plus
  `tools/test_scanner_query.mjs` before any scanner push.
- `mockups/trait-icons-poc.html` (generator `tools/gen_trait_poc.py`) is the
  design sandbox that fed this work; `cards_v3.html` was the working preview and
  now redirects to `cards.html`.

### Suit color palette (Card Scanner)
| Suit | Color |
|---|---|
| Person | `#c9ab35` gold-amber (dimmed for white text) |
| Ally | `#9b6ecf` purple |
| Ship | `#7a8aaa` gray |
| Cargo | `#3a6aaa` dark blue |
| Location | `#4ac48a` green |
| Encounter | `#d4699f` pink |
| Incident | `#e05a5a` red |
| Captain | `#c8a84b` gold |
| Directive | `#8494ad` muted |
| Status | `#88aacc` light blue |

### Trait badge styling
- **Species Traits** — octagonal icon per rulebook; orange badges (`#e09050`)
- **Regular Traits** — blue badges (`#7ec8f0`)
- **Other Traits** — red badges (`#e05a5a`). Attack, Ongoing, Surprise, Wildcard

### Filter logic
- AND logic: selecting multiple traits returns cards matching ALL selected traits
- Deselecting all deck pills = show all cards from active boxes (no deck filter)
- Box selection is independent of deck selection
- Promo packs bypass the deck filter entirely

### Box and deck structure
**Boxes:** Captain's Chair (blue `#4a9fd4`), To Boldly Go (red `#c0392b`), Second Contact (gold `#c8a84b`)
**Promo Packs** (separate section below Box): Pack 1 (blue), Pack 2 (red) — unselected by default

**Deck pills (always visible, color-coded by box):**
- Core (blue): Common, Sisko, Picard, Koloth, Burnham, Sela, Shran
- TBG (red): Georgiou, Soval, Kirk, Archer, Rebner, Khan
- Second Contact (gold): Pike, Riker, Freeman

### Default state on load
- All three main boxes selected (`DEFAULT_BOXES = core, tbg, 2nd`); promo packs off until asked for (the All pill or `box:promo1`/`box:promo2` pulls them in)
- Search bar empty (empty bar = the default view); no deck pills selected
- All trait/skill sections expanded

### Query language (search bar)
The search bar is the scanner's single state; pills are shortcuts that write tokens into it and light up by re-parsing it. Grammar: `key:value` tokens, spaces mean AND, leading `-` negates, quotes for multi-word values, bare words match card names, unknown keys fall back to name text. Keys (full words, no aliases): `box:` (`core`/`tbg`/`2nd`/`promo1`/`promo2`/`all`), `deck:` (captain name, or `common` = commons of every visible box), `suit:`, `trait:`, `skill:` and `focus:` (one-word icon values: `skill:military`, `focus:influence`, `skill:any`, `skill:variable`; the flattened long form `skill:"military skill"` also parses). Empty bar = the three main boxes, no other filters; `box:` tokens replace the default box set wholesale. The parser lives between `QUERY_PARSER_START/END` markers in `cards.html`; `tools/test_scanner_query.mjs` extracts and tests that exact code (`node tools/test_scanner_query.mjs`, run after any scanner search change). All matching still flows through the single `cardMatches` predicate; the "?" beside the bar opens the syntax popover.

### Image view
- Toggle between Cards (pill view) and Images view
- Image view uses `loading="lazy"` — only loads visible images
- Image src is built as `img/<BOX_FOLDER[box]>/<filename>` (see box-key bridge table below); a missing image (404) falls back to a `NO IMAGE` placeholder via `onerror`, so partial image coverage is fine
- Image assets pending volunteer scanning

### Update cycle (revised 29 Jul 2026)
**The Google Drive sheet is RETIRED for Boxes 1-3.** Card data for Captain's Chair, To
Boldly Go, Second Contact and both promo packs is complete; the five JSON files at repo
root are now the canonical card database and are edited directly, like box1.json always
was. The sheet, its volunteer workflow, and `tools/build_box2_from_sheet.py` go dormant
until Box 4/5 land, at which point this cycle reactivates for the new box only. The
"fix the sheet, never the JSON" rule applies only while a box is on the active sheet
pipeline. Historical description of the cycle follows, kept for that reactivation.
- File: `stcc-card-database.xlsx` on Periodic_agent's Drive (kept as .xlsx; volunteers edit via shared link in Sheets Office mode). Drive file ID stays constant.
- Tabs: README, TBG (Box 2), Second Contact (Box 3), Vocabulary. Status column tracks progress (AI-seeded — verify / verified / needs entry / unreadable). Card image column links to the live site.
- **Never regenerate the sheet wholesale.** To add cards: read the live sheet (Google Drive connector), merge by Card code (fallback key: box + name + suit), append ONLY new rows, hand Periodic_agent the updated .xlsx. Periodic_agent updates Drive via right-click → Manage versions → Upload new version (keeps the ID and the shared link; never delete-and-reupload).
- Existing rows are never modified by a merge; "verified" statuses and Contributor credits survive every update.
- **New guide imports feed the database:** when a TBG/Second Contact guide is imported, extract its card images to `img/box2/` or `img/box3/` (convention names) AND read the card faces into new sheet rows before the guide ships.
- Scanner build: read the sheet, validate traits against the Vocabulary tab (flag novel traits, don't reject), emit `box2.json` / `box3.json`, re-inject into the Card Scanner. Same schema as box1.json.
- Card codes (e.g. 2PER07/26) are the stable ids; optional for volunteers, backfilled during verification. See the variant convention below.
- **Duplicate card names within a deck are legitimate** — a deck can contain two copies (e.g. Big Helmet ×2 in Rebner, codes 2REB21/22 and 2REB22/22). Give the second card's `id` a `-2` suffix and keep both rows; do NOT deduplicate.

### Card number and variant (duplicate handling)

Column A of the sheet carries the printed card number and encodes duplicate status.
Contributors enter the number exactly as printed, e.g. `2PER14/26†`.

```
^(\d)([A-Z]+)(\d+)([A-Z]?)/(\d+)\s*(.)?$
   box  set    num  face  total  marker   (face = optional A/B letter on double-sided cards, e.g. 2KHA01A/22)
```

| marker | codepoint | `variant` | meaning |
|---|---|---|---|
| *(none)* | — | `original` | new in this box |
| `•` | U+2022 | `reprint` | gameplay-identical to the Box 1 card |
| `†` | U+2020 | `updated` | new traits or errata |
| anything else | — | **hard fail** | build stops |

`build_box2_from_sheet.py` emits `variant` and `card_number` onto every record.

**The hard fail is not optional and is not a comment on contributor care.** Sheets
autocorrect, mobile keyboards and paste from other sources silently substitute `·`
(U+00B7) or `∙` (U+2219) for `•` with no visible change to the typist. A silent fallback
to `original` is the one failure that hides itself: a `†` card would look brand new and
the resolver would never fire on it. All bad markers are collected and reported together
with their codepoints, so a single run fixes every cell.

A **blank** card number is not "no marker", it is `unclassified`. Treating it as
`original` would reintroduce the same silent failure through another door.

#### The four validation checks

1. **(gate)** Every `•`/`†` row must resolve to an existing Box 1 card, joined on `slug(name)`.
2. **(report)** Reverse check, the more valuable one: any **unmarked** Box 2 card whose name matches a Box 1 `id` is a missed transcription, which silently double-counts traits in a combined market with nothing visibly wrong on screen. Restricted to `deck == Common`: only market cards are reprinted across boxes, while captain decks legitimately reuse names (Georgiou's "Hostile Contact", Soval's "Energy Drain"). Flagging those every build trains people to ignore the check.
3. **(report)** For every `•` row, diff the trait fields against the Box 1 record. They are identical by definition, so any difference means the card should have been `†` — a change that would otherwise propagate silently to Box-1-only players. Trait **order** is not semantic; compare sorted.
4. **(gate)** Identity: a Box 2 `id` collides with a Box 1 `id` **if and only if** the card is marked. Bidirectional and sharper than 1 and 2 because it joins on `id` rather than name. An unmarked collision is a missed transcription; a marked card that does *not* collide is naming drift between the sheet's image cell and Box 1.

The script also prints the full `•`/`†` list for a human eyeball pass, turning the
classification from an assumption into something verified once.

#### Why there is no `supersedes` pointer

Box 2 stores `variant` only. Because a reprint keeps the same name, its `id` is already
identical to the Box 1 `id`, so the runtime pairing is a one-liner:

```js
const original = ALL_CARDS.find(x => x.box === 'core' && x.id === card.id);
```

A stored `supersedes` field would hold the exact string `id` already holds. Worse, it
would **bridge a name mismatch and let the two spellings drift apart indefinitely**.
Checks 1 and 4 are gates precisely so this `id` match can be trusted: they guarantee
every marked card resolves and no unmarked card collides. This is not theoretical —
it caught `Borg Spatial Trajector` vs `Trajectory`, a `•` on `Tellarites` that has no
Box 1 counterpart, and `Phlox` carrying `phlox-nx01.jpg` (id `phlox-nx01` would never
have matched `phlox`). A pointer field would have hidden the last one completely.

### Printed misprints — database vs guides

When a card's printed text is misprinted, the **card database follows the printed card**;
a strategy guide follows **McCue's prose**. Example: the core and TBG cards both read
`Xindi-Reptillian Battleship` (double-l misprint), so `box1.json`/`box2.json` use that
spelling — which also lets the id-resolver dedup the two printings. `ships.html` keeps
`Xindi-Reptilian` because that word sits in McCue's verbatim paragraph (Rule 1). When the
two diverge, **both are correct**, and the image file may exist under each spelling. The
id-resolver joins on `id`, so a printed-name correction to box1 must carry through name +
id + filename together (and the image renamed to match), or the reprint won't pair.

### Scanner regeneration checklist (box2/box3 → Card Scanner)
Repeatable procedure — run whenever the community sheet gains cards. A future session can follow this as a checklist:
1. **Fetch fresh.** `git clone --depth 1 https://github.com/periodic-agent/stcc-strategy.git` (raw-URL fallback, see Session Startup). `box1.json` and `box2.json` are at the repo **root**.
2. **Read the sheet** via the Google Drive connector — file ID `186ZpFkLQsLX1blU3z45znMPwH9fE6yO3`, tab `TBG (Box 2)` (or `Second Contact (Box 3)`). Read-only; **never write to the sheet.** Export as .xlsx to get all tabs at once. Note: the Drive `.xlsx` export can trail live edits by a few minutes / one refresh — if a regen looks a step behind an edit you just made, re-pull before assuming a bug.
3. **Rebuild `box2.json`** (repo root) with `python tools/build_box2_from_sheet.py sheet.xlsx "TBG (Box 2)" "To Boldly Go" --box1 box1.json -o box2.json`. Canonical schema (identical to box1.json, which also carries `card_number` on all 250 records) plus `variant`: `id` (see Card Image Filename Convention — `id` == filename stem, deck prefix on crew-deck cards), `name`, `suit`, `source` = Deck column, `game_box` = `"To Boldly Go"`, `species_traits`/`regular_traits`/`other_traits` = comma-split, `icons` = one `{type: Skill}` per Skill-icon plus one `{type: Focus}` per Focus-icon (**repeated objects, no `count`**; specialty ∈ Research/Influence/Military/Any/Variable), `filename` (`""` if no image — the scanner shows a NO IMAGE placeholder). Include every row with at least a name and suit, whatever its status. **`game_box` must be exactly one of `Captain's Chair` / `To Boldly Go` / `Second Contact`** — the script hard-fails otherwise. For Box 3 use tab `Second Contact (Box 3)` and `game_box "Second Contact"`.
4. **Validate.** The script runs the four checks above; checks 1 and 4 are gates and exit non-zero (`--warn-unresolved` overrides, use sparingly). Also: no duplicate ids (suffix `-2`, keep both — see duplicate note above), traits against the **Vocabulary** tab (warn on novel, never drop), counts per suit. Fix the **sheet**, never the JSON — hand-edits are overwritten on the next regen.
   - **Holding back an incomplete deck** (e.g. a captain deck whose skill/focus icons are not yet entered) is a **one-off filter at ship time**, applied by dropping those `source` rows after the build — *never* a build-script option. An `--exclude-deck` flag was tried and deliberately removed: once the icons land, a plain regen brings the deck in automatically, which is the behavior you want. No decks are currently held: Khan (TBG) and Pike/Riker (2C) have since shipped, so box2.json carries all 248 TBG cards and box3.json all 99 Second Contact cards.
5. **Wire the box (first time only).** The scanner fetches box JSON at **runtime** — there is no injection step. A brand-new box needs one line added to `BOX_SOURCES` in `cards.html`; boxes already listed need nothing (pushing the JSON is enough). Never run an inline-injection tool.
6. **Preview + present.** Because the scanner fetches at runtime, a local preview must **embed** the data: in a `-preview` copy, replace the `BOX_SOURCES` fetch loop with `RAW_BOXES = window.__BOXES__` and inject `<script>window.__BOXES__={box1:…,box2:…,box3:…,promo1:…,promo2:…}</script>`, and point `IMG_BASE` at the live site (**no `<base>` tag** — it breaks anchor links). Present the changed `boxN.json` and the preview for review.
7. **Push on Periodic_agent's explicit approval only** — the changed `boxN.json` (+ `cards.html` only if `BOX_SOURCES` changed) + `tools/build_box2_from_sheet.py` (Rule 7) in one commit, via `push_to_github.py --pii-file <denylist> --token-file <token>` (both from project knowledge; fails closed without the denylist). Scanner footer stays `Card images © WizKids.` (Rule 6); do not add a content-attribution line.

---

## Card Image Filename Convention

Filenames are derived from the card name as printed, with a deck prefix for crew-deck cards. The live `box1.json` (repo root) is the source of truth — in it, the `id` and `filename` fields share the same stem (`id` == `filename` minus `.jpg`). When adding cards, match an existing sibling in the same deck rather than re-deriving by hand.

### Base rule
1. Lowercase everything
2. Delete apostrophes, periods, and commas entirely — no replacement. `U.S.S.` → `uss`, `V'Ger` → `vger`, `Mek'Leth` → `mekleth`, `Worf, Son of Mogh` drops the comma
3. Strip accents to their base letter (é → e, ï → i, ñ → n, ç → c). Do NOT delete accented characters — keep the base letter so names stay readable
4. Convert spaces to single hyphens; collapse any resulting double hyphens; trim leading/trailing hyphens
5. Extension: `.jpg` (PNG only if transparency is needed)

### Deck prefix (the key rule)
6. **Common and Promo cards have no prefix:** `bird-of-prey.jpg`, `admiral-jarok.jpg`, `vger.jpg`
7. **Crew-deck cards are prefixed with the deck (captain) name:** `sisko-garak.jpg`, `picard-data.jpg`, `koloth-arne-darvin.jpg`
8. Disambiguator suffixes are **replaced by the prefix, not kept**: `Analyze (Picard)` → `picard-analyze.jpg`, never `analyze-picard.jpg` or `analyze-(picard).jpg`. Parentheses never appear in a filename.

### Captain cards double their name — this is intentional
9. Because the rule is "deck prefix + full printed name" with no carve-outs, captain cards repeat their name: `picard-jean-luc-picard.jpg`, `sisko-benjamin-sisko.jpg`, `burnham-michael-burnham.jpg`, `sela-sela.jpg`, `koloth-koloth-the-dahar-master.jpg`. This is deliberate — predictable beats pretty, and "what's on the card" is the one rule with zero exceptions. Do not "fix" the doubling.

### Examples
| Card (printed name) | Deck | Filename |
|---|---|---|
| Bird-of-Prey | Common | `bird-of-prey.jpg` |
| U.S.S. Enterprise-C | Common | `uss-enterprise-c.jpg` |
| V'Ger | Common | `vger.jpg` |
| Garak | Sisko | `sisko-garak.jpg` |
| Worf, Son of Mogh | Sisko | `sisko-worf-son-of-mogh.jpg` |
| Analyze (Picard) | Picard | `picard-analyze.jpg` |
| Jean-Luc Picard | Picard | `picard-jean-luc-picard.jpg` |
| Kang, the Dahar Master | Koloth | `koloth-kang-the-dahar-master.jpg` |

**Format:** JPG preferred, PNG if transparency needed. Full resolution — resize for web later.

**Folder structure & box-key mapping (canonical):**

Images live in numeric box folders on git: `img/box1/`, `img/box2/`, `img/box3/` (flat — filenames are globally unique across all 255 cards, so no per-suit subfolders are needed). JSON files follow the same scheme: `box1.json`, `box2.json`, `box3.json`.

The Card Scanner uses different *internal* box keys (`core`, `tbg`, `2nd`) in its filter logic and CSS. These keys are NOT disk paths. The scanner builds every image path by translating the internal key through this bridge table — it must never use the key directly as a folder name:

| Scanner key | Box | Image folder | JSON file |
|---|---|---|---|
| `core` | Captain's Chair | `img/box1/` | `box1.json` |
| `tbg` | To Boldly Go | `img/box2/` | `box2.json` |
| `2nd` | Second Contact | `img/box3/` | `box3.json` |
| `promo1` | Promo Pack 1 | `img/promo1/` | `promo1.json` |
| `promo2` | Promo Pack 2 | `img/promo2/` | `promo2.json` |

**One box = one JSON = one image folder** (decision Jul 2026, per Periodic_agent): every box, promo packs included, has its own JSON at repo root matching its image folder. Promo packs are linked to an expansion *wave*, not to a single box (Promo Pack 2 shipped alongside both To Boldly Go and Second Contact), so their data no longer lives inside an era box JSON. Promo rows keep `source: "Promo"` and carry `game_box: "Promo Pack 1"` / `"Promo Pack 2"`; the scanner assigns box membership from the source *file* (`_srcBox` stamp in `loadBoxes`), with `game_box` only as fallback for injected preview data. The earlier design (promo data inside box1.json/box2.json) was retired by `tools/split_promo_json.py`.

In the scanner code this table is the `BOX_FOLDER = { core:'box1', tbg:'box2', '2nd':'box3', promo1:'promo1', promo2:'promo2' }` constant. Image src is built as `img/<BOX_FOLDER[box]>/<filename>`. A missing image (404) falls back to a `NO IMAGE` placeholder via `onerror`, so partial image coverage is fine. Coverage as of 29 Jul 2026: `img/box2/` is complete (248/248, contributor scans, reprints and updated cards included) and `img/box3/` is complete (99/99); both at the display standard, 1170 px q80. `img/box1/` holds 248 of 250 (the 2 bot-play Directives are deliberately not done yet); uncovered cards show the placeholder. The Box 2 and Box 3 scans came as contributor image packages, imported by matching the card number printed bottom-left on each face (the unique key in the box JSON) plus title-banner and deck-folder cross-checks; the import scripts and scan-to-card mappings are parked on local disk beside each scan package (`img_table_scans/box N/import_tools/`), deliberately not in the repo.

> **Why this table exists:** the original Image-view gap was an undocumented mismatch between the scanner's internal keys (`core`/`tbg`/`2nd`) and the on-disk folders (`box1`/`box2`/`box3`). Documenting the bridge — not just the path — is what prevents a future instance from reintroducing it. If you add a box, add its row here AND to `BOX_FOLDER` in the scanner in the same change.

> **id / filename invariant:** both fields must always share the same stem. If one is corrected, regenerate the other in the same pass. Anything that keys off `id` then stays aligned with the image filename.

---

## Image Extraction Notes

### Promo / CDN-only guides — images must be user-downloaded (learned Jul 2026, Promo Pack 2)

Some BGG threads embed card images ONLY as `cf.geekdo-images.com` CDN URLs (no base64 in the SingleFile HTML). The Promo Pack 2 thread was one of these. For these:

- **The sandbox CANNOT download the images.** BGG's CDN returns `403 Forbidden` to server-side/sandboxed fetches. It serves normally from a real browser/OS network. So Claude generates a `download_[guide]_images.py` script, Periodic_agent runs it locally, and uploads the resulting files. Claude then pushes them to the repo. There is no way around the 403 from inside the session.
- **The HTML usually carries only the `__medium` (500x500) variant.** To get higher resolution, the download script should try resolution variants largest-first per image (`__original` -> `__large` -> `__medium`) and keep the first that resolves. Do not assume `__medium` is the best available.
- **BGG "png" cards often arrive as palette-mode PNG data with a `.jpg` extension.** Before pushing, convert them to real JPEG (`Image.open(f).convert('RGB').save(out,'JPEG',quality=92)`) so the file content matches the `.jpg` name the guide/JSON expect. Keep the convention filenames (promo cards: no deck prefix).
- **Promo images live in their own folder** per the box-key table: Promo Pack 1 -> `img/promo1/`, Promo Pack 2 -> `img/promo2/`. Data still lives in the era's box JSON (`box1.json` / `box2.json`), images do not.
- Once uploaded, switch the guide's `<img src>` from the CDN URL to the local `img/promo2/<name>.jpg` path so the site self-hosts.

### BGG SingleFile HTML — image formats encountered:
1. **CSS `--sf-img-N` variables with CDN `content=""` URLs** (Shran guide)
   → Extract URLs → run `download_images.py` → upload → embed with site naming
2. **Base64 WebP in `src=""` attribute** (TBG Locations guide)
   → Extract directly from HTML with Python/base64 (build_guide.py handles quoted and unquoted `src=`)
3. **CDN-only fallback** (some images only have `content=` URL, no base64)
   → See the Promo / CDN-only procedure above

### Image download script pattern
Claude generates `download_[guide]_images.py` per guide by extracting CDN URLs from the SingleFile HTML. Script uses stdlib only (`urllib.request`), no deps. Alt text from the SingleFile HTML is used to name files meaningfully (e.g. `burnham_board_basic.jpg`).

### Known image sets
- **Shran:** `shran_board_basic`, `shran_board_advanced`, `shran_available_1/2/3`, `shran_reinforcement`, `shran_development_1/2`
- **Burnham:** `burnham_board_basic`, `burnham_board_advanced`, `burnham_1` through `burnham_7`
- **TBG Locations:** 6 embedded WebP + 3 CDN (Cold Station 12, Tanuga IV, Tellar Prime)

---

## Paragraph Break Identification

When Claude runs together paragraphs (BGG strips line breaks), provide the **last sentence** of each paragraph. Claude will insert `</p><p>` breaks after each.

Example prompt:
> "Section X needs paragraph breaks. Last sentence of each:
> - [last sentence para 1]
> - [last sentence para 2]"

---

## Lore & Cut Paragraphs

When importing a guide, certain paragraphs need to be removed or styled as lore:

**To cut:** provide the first few words — Claude removes the full paragraph.

**To make lore:** provide the first few words — Claude wraps the paragraph in `<p class="lore">`.

(In the scripted pipeline, cuts and lore live in the guide config JSON.)

---

## Structural Safety Rules

When inserting sections (Video Playthroughs, etc.) always insert **before** `</main>`:
```python
html = html.replace('\n</main>', new_section + '\n</main>', 1)
```
Never append after `</main>` — causes duplicate content bugs.

---

## Memory Alpha Episode Links

Episode references in lore paragraphs should link to Memory Alpha.

### URL format
```
https://memory-alpha.fandom.com/wiki/Episode_Title_(episode)
```
- Replace spaces with underscores
- Always append `_(episode)` disambiguator
- Commas in titles stay as-is
- Hyphens in titles stay as-is
- For multi-episode arcs (e.g. `2x1-2`), link to Part 1

### Link styling
```css
  .lore a{color:#c8a84b;text-decoration:none;border-bottom:1px dotted rgba(200,168,75,0.5);}
  .lore a:hover{color:#e8c878;border-bottom-color:#e8c878;}
```
(Now in stcc.css.)

### Automation notes
The regex `([A-Z]+[^:]*\d+x\d+:\s+)([A-Za-z][^,&<\n]+?)` catches most single-episode references automatically. The following patterns require manual linking:
- Second episode in a `A & B` pair
- Episode codes with ranges: `2x1-2`, `1x9-10`, `2x15-16`
- Episodes without colon separator: `ENT 3x6 Exile`
- Titles containing numbers: `Cold Station 12`
- Multi-part titles with commas: `The War Without, The War Within`

Always do a pass after automation to catch the misses.

---

## Video Playthroughs Section

Guides with a content-creator playthrough get a **Video Playthroughs** section at the bottom (before the bottom nav-bar), with YouTube thumbnail cards.

**Featured creators (credit format `Mode · Channel` in `.yt-sub`; full name in the section intro line):**
- Gaming Rules! — Paul Grogan
- slickerdrips — Tom Heath (added 28 Jul 2026)

When a guide carries videos from both creators, the intro line names both: `Playthroughs by Paul Grogan (Gaming Rules!) and Tom Heath (slickerdrips) featuring X:`.

Current mapping (merged 28 Jul 2026 slickerdrips update):
| Guide | Video | URL |
|---|---|---|
| shran.html | Shran vs Sisko | `youtu.be/fpGOnYvySBY` |
| koloth.html | Koloth vs Sisko + Picard vs Koloth (slickerdrips) | `youtu.be/MbuPbqFmk0s` + `youtube.com/watch?v=YCH6G0fO7JU` |
| sisko.html | Koloth vs Sisko + Sela vs Sisko | `youtu.be/MbuPbqFmk0s` + `youtu.be/L0U4rMzRcJY` |
| sela.html | Sela vs Sisko | `youtu.be/L0U4rMzRcJY` |
| picard.html | Two-Player Tutorial + Picard Solo (slickerdrips) + Picard vs Koloth (slickerdrips) | `youtube.com/live/qZnTVD4yOpU` + `youtube.com/watch?v=g9Ng8nUDeUQ&t=9108s` + `youtube.com/watch?v=YCH6G0fO7JU` |
| burnham.html | Burnham Solo | `youtube.com/watch?v=QzXbE_pjKtM` |
| solo.html | Solo Tutorial pt.1 + pt.2 + Burnham Solo | `youtube.com/live/XBHZl0Qdveg` + `youtube.com/live/goYrEDVUSC4` + `youtube.com/watch?v=QzXbE_pjKtM` |
| vs-picard.html | Two-player tutorial + Riker vs Picard Bot | `youtube.com/live/qZnTVD4yOpU` + `youtu.be/CWhCX4qdp6Y` |
| georgiou.html | Georgiou solo + Georgiou vs Kirk (slickerdrips) | `youtu.be/WUWw63FQ_Vk` + `youtube.com/live/dBiG8fv92i0` |
| soval.html | Archer vs Soval | `youtu.be/BAHNWO2Yuuw` |
| five-year-mission.html | Five Year Mission: Picard vs Koloth (slickerdrips) | `youtube.com/watch?v=YCH6G0fO7JU` |

Note: `youtube.com/watch?v=YCH6G0fO7JU` (slickerdrips "Five Year Mission Part 2") deliberately appears in three guides: picard, koloth, and five-year-mission. The picard solo link carries `&t=9108s` — the Picard segment of a longer stream; keep the timestamp.

TBG guides — add when built:
| Future guide | Video | URL |
|---|---|---|
| rebner.html | Freeman vs Rebner | `youtu.be/5g1vaB_wxiw` |
| archer.html | Archer vs Soval | `youtu.be/BAHNWO2Yuuw` |
| kirk.html | Kirk vs Khan + Georgiou vs Kirk (slickerdrips) | `youtu.be/Pc0k1oeT1r8` + `youtube.com/live/dBiG8fv92i0` |
| khan.html | Kirk vs Khan | `youtu.be/Pc0k1oeT1r8` |

Second Contact — add when built:
| Future guide | Video | URL |
|---|---|---|
| pike.html | Pike solo | `youtu.be/YawshG7D0JU` |
| riker.html | Riker vs Freeman (slickerdrips) | `youtube.com/watch?v=CpZMwUrtc8g` |
| freeman.html | Riker vs Freeman (slickerdrips) | `youtube.com/watch?v=CpZMwUrtc8g` |

---

## TBG Persons Guide (build notes, restored)

- File: `tbg-persons.html` — live
- 17 new cards + 9 repeats listed
- Card format: `<p class="lore">` for Notable Episodes + lore text, `<p>` for strategy
- Memory Alpha episode links on all Notable Episodes references
- Phlox image placed before the repeats list
- TOC pill color: gold (`#e8a94a`) matching Core Box Person Deck

---

---

## Session Delta — 25 Jul 2026 (Card Scanner)

### Card Scanner image resolution (canonical)

Resolution of text, badges, copy counts and the "N distinct cards" label stays scoped to the
**selected** boxes. Image lookup does **not**: it searches every loaded printing of the card id,
regardless of which boxes are selected. Without this, a Box 2 reprint (whose own `filename` is
blank) rendered NO IMAGE whenever Box 1 was deselected.

Rules, in order:

1. Only printings whose **text matches the resolved version** qualify. An `updated` card draws
   from `updated` printings only; an original or reprint draws from originals and reprints.
2. **Every printing prefers its own scan** (rule flipped Jul 2026, per Periodic_agent, once
   reprint scans reached full coverage). Printings inside the currently selected boxes rank
   first, newest printing winning among them; printings outside the selection are fallback
   only. Browsing TBG therefore shows the TBG scan of a reprint; browsing Box 1 alone shows
   the Box 1 art. The old "Box 1 art wins" rule is retired.
3. **Updated cards take the newest updated printing.** If its scan has not landed yet the card
   shows NO IMAGE. Superseded art is never shown for a card whose text changed.
4. Promo keys (`promo1`, `promo2`) are absent from `BOX_ORDER`; `boxRank()` sorts them after
   every numbered box so a promo scan cannot outrank a box scan.
5. The lightbox list is built from the image's own box folder (`imgBox`), which can differ from
   the card's resolved box, and skips image-less cards so arrow navigation matches the tiles.

**Data implication for JSON sessions:** leave `filename` blank on reprints. The scanner serves the
Box 1 scan for them. Fill `filename` only when a card has art of its own: a new box original, or an
`updated` card whose new scan exists.

### Scanner testing requirement

`node --check` is not sufficient; it passes on a scanner whose functions are all nested inside
`init()`, which silently kills every inline `onclick` in the browser. Before any scanner push:

```
node tools/test_scanner.mjs .
```

It runs the real inline scripts in a DOM shim, calls `setView` / `clearAll` / `openLightbox` from
global scope the way a click does, asserts the image rules above, and exits non-zero on failure.
Add an assertion whenever a rule is added.

### Known card data quirks

**Xindi-Reptillian Battleship is misprinted on the card itself.** The printed card spells it
"Reptillian" with two Ls; canon spelling is "Reptilian". The database follows the card: `id`, `name`
and `filename` all use `xindi-reptillian-battleship`. This is deliberate. Do not "correct" it in
box1.json, box2.json, or any guide. A stray unreferenced `img/box1/xindi-reptilian-battleship.jpg`
(one L) exists from an earlier pass and is safe to delete.

### Session sync and push (environment note)

`raw.githubusercontent.com` and `api.github.com` can be blocked from the sandbox shell while
`github.com` is reachable. When `web_fetch` or urllib fails, sync with:

```
git clone --depth 1 https://github.com/periodic-agent/stcc-strategy /tmp/repo
```

`push_to_github.py` is unaffected: it pushes over git, not the REST API. Run it from a directory git
can lock (a mounted output folder may refuse `.git` operations; clone under `/tmp`).

---

## Session Delta — 27 Jul 2026 (Strategy Index)

### What shipped

Every card in `box1/2/3.json` is cross-referenced against every guide. In the Card Scanner's
Cards view, a discussed card carries a teal `Strategy` badge (`#5ec8c8`; teal was chosen because
it is the one hue absent from the suit palette, and gray would read as the existing
Update/Duplicate metadata badges). The whole pill is the click target, not the badge. Clicking
opens a full-width row drawer (`grid-column:1/-1`, so the grid never reflows sideways) with the
guide name, section, McCue's paragraphs verbatim, and deep links into the guide. Cards with no
mention get no badge and no click target: a click never returns an empty drawer. Escape closes.
Coverage at ship time: 321 of 549 cards, 26 guides.

### Files

| Path | Role |
|---|---|
| `tools/build_strategy_index.py` | Generator. Stdlib only. `--report` prints coverage and top mentions; `--check` exits 1 if stale (used by CI). |
| `tools/strategy_index_config.json` | Stopwords, aliases, per-guide deck attribution, caps. Tune here, never in the script. |
| `tools/patch_scanner_strategy.py` | Applies the badge + drawer to `cards.html`. Idempotent; asserts every anchor, so a scanner refactor fails loudly. |
| `data/strategy-index.json` | Full index with snippets (~550 KB). Fetched lazily, on first drawer open. |
| `data/strategy-cards.json` | `{card_id: mention_count}` (~8 KB). Fetched at scanner start-up; drives the badge. |
| `tools/strategy-drawer-preview.html` | Standalone interaction preview against live data. Not linked from the site. |
| `.github/workflows/strategy-index.yml` | Rebuilds and commits the index on any push touching `*.html`, `box*.json`, or the generator. Gated on `--check` so the timestamp alone cannot produce a no-op commit. |

The two-file data split is deliberate: 550 KB on every scanner load would be a regression on
mobile, the scanner's primary use case.

### Matching rules (generator)

Two modes; anchor beats text:

1. **Anchor.** A guide heading carries `id="card-id"`. Market guides are built this way, so
   those hits are exact by construction (200 of the 874 total).
2. **Text.** Card name in a `<p>`, matched on normalized text (accents, periods, apostrophes
   stripped) with word boundaries. `U.S.S. Enterprise-C` and `Mek'Leth` match with no special
   cases.

Constraints that make the matches trustworthy:

- **Snippets are whole paragraphs, never sentence windows.** Rule 1 requires verbatim text, and
  a paragraph boundary cannot crop a thought; sentence splitters break on `U.S.S.`, `vs.`, `Dr.`.
- **`<p class="lore">` is excluded from text mode.** Lore is episode trivia, not strategy; this
  is what stops the Memory Alpha location card from matching every Memory Alpha wiki reference.
  Anchor matches keep their lore paragraph, since there the card is the subject.
- **Same-name captain cards** (Utilize, Recruit, Analyze, Set a Course) resolve to the captain's
  own printing inside that captain's guide, via `deck_prefix_by_guide` in the config.
- **Stopwords** (`Orion`, `Vulcan`, `Earth`, `Data`, `Phasers`, `Memory Alpha`, ...) match by
  anchor only. Editing that list is the normal fix for a false positive. After importing any
  guide, run `--report` and scan the top-mentions table; a new name at the top usually wants a
  stopword.

### New conventions

- Guides that discuss specific cards should use `<h3 id="card-id">` (the market-guide pattern).
  That promotes every card in the guide from text matching to an exact anchor and gives the
  drawer a precise deep link.
- `tools/test_scanner.mjs` now also asserts: badge and click wiring on discussed vs undiscussed
  cards, drawer rendering with the McCue attribution line, every index-referenced guide exists
  on disk, every drawer deep link points at an anchor that exists, and every indexed card id
  still exists in `box*.json`. Renaming a guide or a heading id without rebuilding the index
  fails the test instead of shipping dead links. Note: the lightbox file-exists assertion
  requires a full checkout; it false-fails in a sparse clone without `img/`.

### Deferred by choice

Strategy filter pill in the filter row; guide references in the Images-view lightbox caption.
Both ride on the same data with no generator changes.

### Lesson recorded

`patch_scanner_strategy.py` originally opened its output with `open(out, "w")` before the patch
function ran; a failed patch truncated the scanner to zero bytes. Fixed by building the patched
content fully before opening anything for write. Convention for all future patch scripts: never
open the destination for writing until the new content exists in memory.
