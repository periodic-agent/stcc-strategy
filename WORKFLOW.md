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

**Push: Claude pushes to GitHub directly via `push_to_github.py`, but ONLY after Periodic_agent reviews the presented file and explicitly approves. Never push before the go-ahead.**

```
python push_to_github.py <local_path> <repo_path> "commit message"
```
Fetch the script from the live repo before running. It fetches the current file SHA, base64-encodes content, and PUTs to the repo. Files deploy via GitHub Pages in ~60 seconds.

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

1. **Zero text edits.** McCue's text is reproduced verbatim — no summarizing, no rewriting, no restructuring. Format only: headings, paragraph breaks, image placement.
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

### chapter-date CSS (add to every guide)
```css
  .chapter-date{font-size:0.7rem;color:var(--muted);letter-spacing:0.08em;margin-top:0.3rem;}
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

**Market guides** (Person, Ally, Ship, Cargo, Location, Encounters & Incidents) get a **pill grid** below the header.

Swap blue vars for red equivalents for TBG guides.

```css
<style>
  :root{--bg:#0a0e1a;--bg2:#0f1628;--bg3:#141c35;--blue:#4a9fd4;--blue2:#7ec8f0;--gold:#c8a84b;--text:#ccd6f0;--muted:#7a8aaa;--green:#4ac48a;--border:rgba(74,159,212,0.25);}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:'Exo 2',sans-serif;font-weight:300;background:var(--bg);color:var(--text);line-height:1.75;font-size:1rem;}
  .nav-bar{background:var(--bg);border-bottom:1px solid var(--border);padding:0.75rem 1.5rem;}
  .nav-bar a{font-family:'Orbitron',sans-serif;font-size:0.65rem;letter-spacing:0.15em;color:var(--blue);text-decoration:none;text-transform:uppercase;}
  .chapter-header{background:linear-gradient(135deg,#061020 0%,#0d1e3a 50%,#061020 100%);border-bottom:2px solid var(--blue);padding:3rem 2rem 2rem;text-align:center;position:relative;overflow:hidden;}
  .chapter-header::before{content:'';position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent,transparent 60px,rgba(74,159,212,0.03) 60px,rgba(74,159,212,0.03) 61px);}
  .chapter-label{font-family:'Orbitron',sans-serif;font-size:0.7rem;letter-spacing:0.25em;color:var(--blue);text-transform:uppercase;margin-bottom:0.75rem;}
  .chapter-title{font-family:'Orbitron',sans-serif;font-size:clamp(1.6rem,5vw,2.8rem);font-weight:700;color:#fff;letter-spacing:0.05em;text-shadow:0 0 40px rgba(74,159,212,0.5);}
  .chapter-title span{color:var(--blue2);}
  .chapter-meta{margin-top:1rem;font-size:0.8rem;color:var(--muted);letter-spacing:0.1em;}
  .chapter-tags{display:flex;justify-content:center;gap:0.5rem;margin-top:1rem;flex-wrap:wrap;}
```

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

### Update cycle
1. Volunteer updates Google Sheet or new JSON provided
2. In new session: pull sheet via Google Drive MCP or upload new JSON
3. Rebuild card JSON, re-inject into HTML
4. Present for download, Periodic_agent pushes to GitHub

### Analytics
GoatCounter tracker included: `https://stcc-compendium.goatcounter.com/count`

---

## Card Image Naming Convention

For scanned/cropped card images used in both the Card Scanner and strategy guides:

- Lowercase, hyphens instead of spaces
- Drop all punctuation (apostrophes, periods, commas)
- No accents or special characters

**Examples:**
- Bird-of-Prey → `bird-of-prey.jpg`
- Mek'Leth → `mek-leth.jpg`
- U.S.S. Enterprise-C → `uss-enterprise-c.jpg`
- V'Ger → `vger.jpg`

**Format:** JPG preferred, PNG if transparency needed. Full resolution — resize for web later.

**Folder structure:**
```
/img/cards/core/
/img/cards/tbg/
/img/cards/2nd-contact/
```

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

> Images stay as **base64 in HTML** until the library grows large enough to justify an `images/` folder.

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
- Guide h1 titles: captain name only (e.g. `Thy'Lek Shran`, `Koloth, the Dahar Master`)

---

### Video Playthroughs — Updated Mapping

| Guide | Videos |
|---|---|
| picard.html | Two-Player Tutorial (`youtube.com/live/qZnTVD4yOpU`) |
| burnham.html | Burnham Solo (`youtube.com/watch?v=QzXbE_pjKtM`) |
| solo.html | Tutorial pt.1 + pt.2 + Burnham Solo |
| vs-picard.html | Two-player tutorial + Riker vs Picard Bot |

---

### TBG Persons Guide

- File: `tbg-persons.html` — live
- 17 new cards + 9 repeats listed
- Card format: `<p class="lore">` for Notable Episodes + lore text, `<p>` for strategy
- Memory Alpha episode links on all Notable Episodes references
- Phlox image placed before the repeats list
- TOC pill color: gold (`#e8a94a`) matching Core Box Person Deck

---

### Analytics

GoatCounter script added to all 18 guides + index.html:
```html
<script data-goatcounter="https://stcc-compendium.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
```
Place just before `</body>` on every page including future guides.

---

### Card Scanner Attribution

The Card Scanner footer uses only `Card images © WizKids.` — no McCue content attribution line. Contributors will be acknowledged separately as the project grows.

---

### Design Principle: Guides vs Tools

- Guides = McCue's strategy content, formatted by Periodic_agent
- Tools = built by Periodic_agent (Card Scanner, future tools)
- Keep these conceptually separate: don't add mechanical card data to guides; link to Card Scanner instead
- "Guides are for guiding, Card Scanner is a fun tool"

