## Session Startup

Files live on GitHub Pages at:
- **Live site:** https://periodic-agent.github.io/stcc-strategy/
- **Raw files:** https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/[filename]

At the start of each session, fetch BOTH PROJECT_BRIEF.md and WORKFLOW.md from the live repo, plus any files you'll be editing. `web_fetch` FAILS (permissions error) — use bash urllib instead:
```python
import urllib.request
url = 'https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/[filename]'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as r:
    html = r.read().decode()
```

The live repo is authoritative — fetch live, including WORKFLOW.md. Do NOT work from project knowledge copies; they may be stale. Never assume file content from memory or previous sessions.

After editing, save to `/mnt/user-data/outputs/` and call `present_files` to surface the file for review. Never render files inline in chat.

```python
# Correct output pattern
bash: write file to /mnt/user-data/outputs/filename.html
present_files(["/mnt/user-data/outputs/filename.html"])
```

## Session Startup Smoke Test (any model)

Before touching content in a new session: (1) fetch PROJECT_BRIEF.md and WORKFLOW.md from the live repo; (2) confirm the token file is readable from project knowledge; (3) dry-run the push script against an unchanged file — expected output: "No changes ... Nothing pushed." Two minutes, proves the whole pipeline. Session tooling (CSS parser/verifier, guide migrators, montage generator, workbook builder) lives in `tools/` — adapt those, don't reinvent.

---

**Push: Claude pushes to GitHub directly via `push_to_github.py`, but ONLY after Periodic_agent reviews the presented file and explicitly approves. Never push before the go-ahead.**

```
GH_TOKEN=<token> python3 push_to_github.py <local_path> <repo_path> "commit message"
```
Fetch the script from the live repo before running. It shallow-clones the repo, copies the file in, commits, and pushes via git with a one-shot authenticated URL (no GitHub API dependency; `api.github.com` is blocked in some sandboxes while git over HTTPS works). Files deploy via GitHub Pages in ~60 seconds.

---

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

# ST:CC Compendium — Workflow Summary
## For continuity across sessions

---

## Project Overview

A strategy compendium for **Star Trek: Captain's Chair** hosted at:
**https://periodic-agent.github.io/stcc-strategy/**

GitHub repo: **https://github.com/periodic-agent/stcc-strategy**

Content by **Matthew McCue (mdmccu2)** from BGG forums.
Formatted by **Periodic_agent**

---

## Rules

1. **Verbatim by default.** McCue's text is reproduced as posted — no summarizing, no rewriting, no restructuring. Format only: headings, paragraph breaks, image placement.
1a. **Periodic_agent-directed edits are sanctioned (Jul 2026).** McCue now trusts Periodic_agent with corrections. When Periodic_agent says edit, we edit — no pushback, no re-confirmation. Every text edit goes through the guide config's `"replace"` list (never a silent hand-edit to the HTML), so there is an audit trail and the fix survives reimports. The verify gate enforces this: unlisted deviations still fail.
2. **Paragraph breaks** must sometimes be identified by asking for the last sentence of each paragraph when the source text runs together (BGG strips formatting).
3. **Image credit** footer on every guide: `Card images © WizKids.`
4. **Attribution** footer on every guide: `Content by Matthew McCue (mdmccu2) · Formatting by Periodic_agent`
5. **Back to Compendium** link at top and bottom of every guide.
6. **Card Scanner footer** is different: `Card images © WizKids.` only — no content attribution line. Contributors will be acknowledged separately as the project grows.

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
| Card Scanner | `card-browser-mockup.html` (filename kept as-is during development) |

---

## Workflow Per New Guide

### Step 1 — Capture BGG thread
- Use **SingleFile** browser extension → saves full thread as `.html`

### Step 2 — Download card images
- Run adapted `download_images.py` (stdlib only, no deps)
- Claude extracts CDN URLs from the SingleFile HTML and produces the script
- Images batch-download from BGG CDN to local folder
- Upload all images to Claude in next chat
- Note: BGG switched to embedding base64 WebP directly in newer threads vs older CDN-hosted JPEGs, so new guides will not require manual downloads.

### Step 3 — Send to Claude
Upload:
- The SingleFile `.html`
- All card images

Claude will:
- Extract verbatim text (strip comments, strip HTML garbage)
- Identify section headers (H2/H3)
- Ask for paragraph break endings if sections run together
- Embed images as base64 (or CDN ref if base64 not available)
- Produce styled `guidename.html` using the canonical CSS below
- **Automatically update `index.html`** — flip the matching entry from Soon → Live
- **Set `Last updated` date** in the footer to today's date
- **Generate TOC** — pill grid for market guides, section list for captain guides, with back-to-top links

### Step 4 — Upload to GitHub
- Drop new `.html` + updated `index.html` in repo root
- Pages deploys in ~60 seconds

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
- **New guides:** link stcc.css + set the theme class. Do NOT paste a full CSS block; the canonical CSS below is retired (kept as color reference only).
- **Lightbox:** CSS is in stcc.css, but each guide still needs the lightbox HTML + script snippet (see Lightbox section).

### Box 1 — Captain's Chair: **Blue**
- Accent: `#4a9fd4` / `#7ec8f0`
- Header gradient: `#061020 → #0d1e3a`
- Border: `rgba(74,159,212,0.25)`
- Gold (h3): `#c8a84b`

### Box 2 — To Boldly Go: **Red**
- Accent: `#d44a4a` / `#f07e7e`
- Header gradient: `#160608 → #2a0e10`
- Border: `rgba(212,74,74,0.25)`

### Box 3 — Second Contact: **Amber**
- Accent: `#c8a84b` / `#e8c96a`
- Border: `rgba(200,168,75,0.25)`

### Fonts
- Headers: `Orbitron` (Google Fonts)
- Body: `Exo 2` (Google Fonts)

### Card images
- Captain guide photos: scrollable horizontal `.card-row` (height: 220px, mobile: 170px)
- Single card images (TBG style): `.card-img` block (max-width: 260px)
- All images: lightbox on click
- All images: `loading="lazy"` — served from `/img/cards/[box]/[filename].jpg`

### Navigation
```html
<div class="nav-bar"><a href="index.html">← Back to Compendium</a></div>
```
Top and bottom of every guide. Top nav goes **before** `<header>`.

### Hero / Chapter Header
```html
<header class="chapter-header">
  <div class="chapter-label">Captain's Chair · Strategy Guide</div>
  <h1 class="chapter-title"><span>CaptainName</span> Strategy Guide</h1>
  <div class="chapter-meta">By Matthew McCue (mdmccu2)</div>
  <div class="chapter-tags">
    <span class="tag">Trait1</span><span class="tag">Trait2</span>
  </div>
</header>
```

### Footer
```html
<footer>
  Card images © WizKids.<br>
  Content by Matthew McCue (mdmccu2) · Formatting by Periodic_agent
</footer>
```
The date is the day the guide was built/rebuilt. Update it whenever the source guide is edited on BGG and reimported.

### chapter-date CSS
Now in stcc.css; no per-guide CSS needed.

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

**Market guides** (Person, Ally, Ship, Cargo, Location, Encounters & Incidents) get a **pill grid** below the header.

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

## Card Database

### File structure
```
data/
  box1.json    -- Captain's Chair, complete (255 cards)
  box2.json    -- To Boldly Go, pending
  box3.json    -- Second Contact, pending
```

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

### Suit color palette (Card Scanner)
| Suit | Color |
|---|---|
| Person | `#e8a94a` amber |
| Ally | `#9b6ecf` purple |
| Ship | `#7a8aaa` gray |
| Cargo | `#3a6aaa` dark blue |
| Location | `#4ac48a` green |
| Encounter | `#d4699f` pink |
| Incident | `#e05a5a` red |
| Captain | `#c8a84b` gold |
| Directive | `#7a8aaa` muted |
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
**Boxes:** Captain's Chair (blue `#4a9fd4`), To Boldly Go (red `#c0392b`), 2nd Contact (gold `#c8a84b`)
**Promo Packs** (separate section below Box): Pack 1 (blue), Pack 2 (red) — unselected by default

**Deck pills (always visible, color-coded by box):**
- Core (blue): Common, Sisko, Picard, Koloth, Burnham, Sela, Shran
- TBG (red): Georgiou, Soval, Kirk, Archer, Rebner, Khan
- 2nd Contact (gold): Pike, Riker, Freeman

### Default state on load
- Captain's Chair box selected; TBG and 2nd Contact unselected
- No deck pills selected (= all 255 Core cards visible)
- All trait/skill sections expanded

### Image view
- Toggle between Cards (pill view) and Images view
- Image view uses `loading="lazy"` — only loads visible images
- Image placeholder shown until `/img/cards/[box]/[filename].jpg` exists
- Image assets pending volunteer scanning

### Update cycle (revised 04 Jul 2026)
**The community sheet on Google Drive is canonical for Box 2 and Box 3 card data.**
- File: `stcc-card-database.xlsx` on Periodic_agent's Drive (kept as .xlsx; volunteers edit via shared link in Sheets Office mode). Drive file ID stays constant.
- Tabs: README, TBG (Box 2), Second Contact (Box 3), Vocabulary. Status column tracks progress (AI-seeded — verify / verified / needs entry / unreadable). Card image column links to the live site.
- **Never regenerate the sheet wholesale.** To add cards: read the live sheet (Google Drive connector), merge by Card code (fallback key: box + name + suit), append ONLY new rows, hand Periodic_agent the updated .xlsx. Periodic_agent updates Drive via right-click → Manage versions → Upload new version (keeps the ID and the shared link; never delete-and-reupload).
- Existing rows are never modified by a merge; "verified" statuses and Contributor credits survive every update.
- **New guide imports feed the database:** when a TBG/2C guide is imported, extract its card images to `img/box2/` or `img/box3/` (convention names) AND read the card faces into new sheet rows before the guide ships.
- Scanner build: read the sheet, validate traits against the Vocabulary tab (flag novel traits, don't reject), emit `box2.json` / `box3.json`, re-inject into the Card Scanner. Same schema as box1.json.
- Card codes (e.g. 2PER07/26) are the stable ids; optional for volunteers, backfilled during verification. Dagger (†) marks updated repeats from the core box.

### Analytics
GoatCounter tracker included: `https://stcc-compendium.goatcounter.com/count`

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
| `2nd` | 2nd Contact | `img/box3/` | `box3.json` |
| `promo1` | Promo Pack 1 | `img/promo1/` | `box1.json` |
| `promo2` | Promo Pack 2 | `img/promo2/` | `box2.json` (expected) |

**Promo data vs image split:** Promo cards are stored as data *inside* the main box JSON for their era — Promo Pack 1 cards live in `box1.json` (tagged `source:"Promo"`, `box:"promo1"`), and Promo Pack 2 cards are expected to live in `box2.json`. But their *images* get their own folders (`img/promo1/`, `img/promo2/`) because the scanner treats promo packs as separate boxes in the UI. So a promo card's data and its image folder come from different places — this is intentional.

In the scanner code this table is the `BOX_FOLDER = { core:'box1', tbg:'box2', '2nd':'box3', promo1:'promo1', promo2:'promo2' }` constant. Image src is built as `img/<BOX_FOLDER[box]>/<filename>`. A missing image (404) falls back to a `NO IMAGE` placeholder via `onerror`, so partial image coverage is fine — only Box 1 Locations have images so far; everything else shows the placeholder until uploaded.

> **Why this table exists:** the original Image-view gap was an undocumented mismatch between the scanner's internal keys (`core`/`tbg`/`2nd`) and the on-disk folders (`box1`/`box2`/`box3`). Documenting the bridge — not just the path — is what prevents a future instance from reintroducing it. If you add a box, add its row here AND to `BOX_FOLDER` in the scanner in the same change.

> **id / filename invariant:** both fields must always share the same stem. If one is corrected, regenerate the other in the same pass. Anything that keys off `id` then stays aligned with the image filename.

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

### Link styling (add to guide CSS)
```css
  .lore a{color:#c8a84b;text-decoration:none;border-bottom:1px dotted rgba(200,168,75,0.5);}
  .lore a:hover{color:#e8c878;border-bottom-color:#e8c878;}
```

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

Guides with a Gaming Rules! playthrough get a **Video Playthroughs** section at the bottom (before the bottom nav-bar), with YouTube thumbnail cards.

Current mapping:
| Guide | Video | URL |
|---|---|---|
| shran.html | Shran vs Sisko | `youtu.be/fpGOnYvySBY` |
| koloth.html | Koloth vs Sisko | `youtu.be/MbuPbqFmk0s` |
| sisko.html | Koloth vs Sisko + Sela vs Sisko | `youtu.be/MbuPbqFmk0s` + `youtu.be/L0U4rMzRcJY` |
| sela.html | Sela vs Sisko | `youtu.be/L0U4rMzRcJY` |
| solo.html | Solo Tutorial pt.1 + pt.2 | `youtube.com/live/XBHZl0Qdveg` + `youtube.com/live/goYrEDVUSC4` |
| vs-picard.html | Two-player tutorial + Riker vs Picard Bot | `youtube.com/live/qZnTVD4yOpU` + `youtu.be/CWhCX4qdp6Y` |

TBG guides — add when built:
| Future guide | Video | URL |
|---|---|---|
| georgiou.html | Georgiou solo | `youtu.be/WUWw63FQ_Vk` |
| rebner.html | Freeman vs Rebner | `youtu.be/5g1vaB_wxiw` |
| archer.html | Archer vs Soval | `youtu.be/BAHNWO2Yuuw` |
| soval.html | Archer vs Soval | `youtu.be/BAHNWO2Yuuw` |
| kirk.html | Kirk vs Khan | `youtu.be/Pc0k1oeT1r8` |
| khan.html | Kirk vs Khan | `youtu.be/Pc0k1oeT1r8` |

Second Contact (pending):
- Pike solo: `youtu.be/YawshG7D0JU`

---

## Image Extraction Notes

### Promo / CDN-only guides — images must be user-downloaded (learned Jul 2026, Promo Pack 2)

Some BGG threads embed card images ONLY as `cf.geekdo-images.com` CDN URLs (no base64 in the SingleFile HTML). The Promo Pack 2 thread was one of these. For these:

- **The sandbox CANNOT download the images.** BGG's CDN returns `403 Forbidden` to server-side/sandboxed fetches. It serves normally from a real browser/OS network. So Claude generates a `download_[guide]_images.py` script, Periodic_agent runs it locally, and uploads the resulting files. Claude then pushes them to the repo. There is no way around the 403 from inside the session.
- **The HTML usually carries only the `__medium` (500x500) variant.** To get higher resolution, the download script should try resolution variants largest-first per image (`__original` -> `__large` -> `__medium`) and keep the first that resolves. Do not assume `__medium` is the best available.
- **BGG "png" cards often arrive as palette-mode PNG data with a `.jpg` extension.** Before pushing, convert them to real JPEG (`Image.open(f).convert('RGB').save(out,'JPEG',quality=92)`) so the file content matches the `.jpg` name the guide/JSON expect. Keep the convention filenames (promo cards: no deck prefix).
- **Promo images live in their own folder** per the box-key table: Promo Pack 1 -> `img/promo1/`, Promo Pack 2 -> `img/promo2/`. Data still lives in the era's box JSON (`box1.json` / `box2.json`), images do not.
- Once uploaded, switch the guide's `<img src>` from the CDN URL to the local `img/promo2/<name>.jpg` path so the site self-hosts.

### BGG SingleFile HTML — two image formats encountered:

### BGG SingleFile HTML — two image formats encountered:
1. **CSS `--sf-img-N` variables with CDN `content=""` URLs** (Shran guide)
   → Extract URLs → run `download_images.py` → upload → embed as base64
2. **Base64 WebP in `src=""` attribute** (TBG Locations guide)
   → Extract directly from HTML with Python/base64
3. **CDN-only fallback** (some images only have `content=` URL, no base64)
   → Use CDN URL as `<img src="">` directly — works on GitHub Pages

### Image download script pattern
Claude generates `download_[guide]_images.py` per guide by extracting CDN URLs from the SingleFile HTML. Script uses stdlib only (`urllib.request`), no deps. Alt text from the SingleFile HTML is used to name files meaningfully (e.g. `burnham_board_basic.jpg`).

### Known image sets
- **Shran:** `shran_board_basic`, `shran_board_advanced`, `shran_available_1/2/3`, `shran_reinforcement`, `shran_development_1/2`
- **Burnham:** `burnham_board_basic`, `burnham_board_advanced`, `burnham_1` through `burnham_7`
- **TBG Locations:** 6 embedded WebP + 3 CDN (Cold Station 12, Tanuga IV, Tellar Prime)

> ~~Images stay as **base64 in HTML**~~ **Superseded (Jul 2026):** images now live in `img/box1|box2|box3/` (cards, `<captain>-<card>.jpg`) and `img/guides/<captain>/` (board photos). See the Guide Build Pipeline section.

---

## Session Delta — 05 Jun 2026

### Index Structure Changes

**Box naming (current):**
- Box 1: `Captain's Chair — Core Box` (blue)
- Box 2: `Captain's Chair — To Boldly Go` (red)
- Box 3: `Captain's Chair — Second Contact (Expansion)` (amber)
- Box 4: `Other Guides` (gray)
- Box banner subtitle: `Strategy Guides` on all four boxes

**Entry sub-text:** empty for all guide entries. Keep complexity ratings on captain entries. Keep "Core Box · Beta" on Card Scanner.

**Card Scanner:** sits as a prominent `box-banner purple` above Box 1 — NOT inside a card-grid. Purple dot (`#d4699f`), full-width, links to `card-browser-mockup.html`. Title: "Card Scanner", subtitle: "Explore all cards and decks".

```html
<a href="card-browser-mockup.html" class="box-banner purple">
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

**Second Contact** box is now live in the index (amber). Pike and Freeman captains + market guides all Soon.

**New Soon entries in Other Guides:** `combining-markets.html`, `wesley-crusher-guide.html`

---

### Chapter Label Convention (finalized)

- Core Box guides: `Captain's Chair` — no "Strategy Guide" or "Strategy Compendium" suffix
- TBG guides: `To Boldly Go`
- Guide h1 titles: captain name only (e.g. `Thy'Lek S

---

## Session Delta — 15 Jul 2026

### Guide Build Pipeline (tools/)

Guide creation is now scripted. The model never retypes McCue's text; the
scripts move it verbatim from the SingleFile capture into the styled HTML.

```
python3 tools/build_guide.py <singlefile.html> tools/configs/<slug>.json --out out/
python3 tools/verify_guide.py out/<slug>.html out/<slug>_text.txt --config tools/configs/<slug>.json --img-root out/
```

- **tools/build_guide.py** — extracts McCue's first post (balanced gg-markup-content), decodes all images (quoted and unquoted `src=` base64 WebP) to JPG with site naming, emits marked verbatim text, and builds the styled guide from `tools/guide-template.html`. All judgment calls live in the per-guide JSON config: cuts, lore paragraphs, inserted structural H2s (Missions, Captain Card & Starting Components), image name overrides, board alts, TOC label shortening, videos.
- **tools/verify_guide.py** — machine gate before push: verbatim fidelity line-by-line, image refs resolve, anchors resolve, HTML balanced, footer/lightbox/GoatCounter furniture present. Exit 1 = do not push.
- **tools/configs/georgiou.json** — real example config; copy and adapt per guide.
- Validated by regenerating georgiou.html from its BGG capture: word-for-word identical output.

**Per-guide session procedure (cheap path):**
1. `git clone --depth 1` the repo (see cache warning below). One call.
2. Write the config JSON (model judgment: cuts, lore, headers, tags, video from the Video Playthroughs table).
3. Run build + verify in one bash call. Fix config, not output, if verify fails.
4. Present draft for Periodic_agent's review; wait for approval; push guide + images + index flip with `push_to_github.py -m` (multi-file, one commit).
5. Update the index: flip Soon → Live (`badge-video` ▶ span if the guide has a video), bump `hero-date`.

### Current conventions (supersede older sections above)

- **Shared stylesheet:** all guides link `css/stcc.css?v=N` and set `<body class="theme-tbg">` (TBG) or `theme-sc` (Second Contact); Core Box = no class. No per-guide CSS except market-guide `.toc-card` colors.
- **Image folders:** cards `img/box1|box2|box3/<captain>-<card>.jpg`; captain boards `img/guides/<captain>/<captain>-board-basic|advanced.jpg`. JPG quality 90.
- **Footer (current):** `Card images © WizKids.<br>Guides by Matthew McCue (mdmccu2) · Website by Periodic_agent`
- **Chapter date:** `Posted <BGG post date>` (not build date).
- **Captain guide TOC:** `.toc-list` Contents from H2 sections; market guides keep `.toc-card` pill grid.

### Cost discipline (learned 14–15 Jul 2026, Georgiou = CA$15 the manual way)

- **raw.githubusercontent.com serves stale files** (hours-old cache observed). `git clone --depth 1` and work from the local clone; it is one call and always current.
- **Never fetch full guide pages into the chat context** to check conventions; grep the local clone instead. Conventions are documented here; trust this file first, verify with grep second.
- **Batch bash calls.** Every tool round-trip replays the whole conversation; ten probes cost more than one scripted call.
- **Model choice:** with build+verify scripts as the gate, build sessions can run on a cheaper model (Sonnet); verbatim fidelity is enforced mechanically, not by model care.

### Known site nit

- `.badge-video` class is used on Live captain entries in index.html but has no CSS definition (renders with base `.entry-badge` style). Pre-existing; harmless; define it whenever index.html gets its next styling pass.
