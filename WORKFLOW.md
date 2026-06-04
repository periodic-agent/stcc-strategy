## Session Startup

Files live on GitHub Pages at:
- **Live site:** https://periodic-agent.github.io/stcc-strategy/
- **Raw files:** https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/[filename]

At the start of each session, fetch the files you'll be editing using `web_fetch`:
```
web_fetch("https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/index.html")
web_fetch("https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/shran.html")
... etc.
```

Do NOT fetch WORKFLOW.md — it lives in project knowledge and is always current there.

Always work from the fetched live version. Never assume file content from memory or previous sessions.

After editing, save to `/mnt/user-data/outputs/` and call `present_files` to surface the file for download. Never render files inline in chat.

```python
# Correct output pattern
bash: write file to /mnt/user-data/outputs/filename.html
present_files(["/mnt/user-data/outputs/filename.html"])
```

Periodic_agent pushes to GitHub manually after downloading.

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
  footer{background:var(--bg);border-top:1px solid var(--border);padding:1.5rem;text-align:center;font-size:0.75rem;color:var(--muted);line-height:1.8;}
  footer a{color:var(--blue);text-decoration:none;}
  @media(max-width:600px){.chapter-header{padding:2rem 1rem 1.5rem;}.card-row img{height:170px;}.board-pair{grid-template-columns:1fr;}}
</style>
```

---

## Index Structure (index.html)

```
Box 1 — Captain's Chair (blue)
  Captains: Shran✓, Picard✓, Burnham✓, Sisko✓, Sela✓, Koloth✓
  Location & Market: Persons✓, Allies✓, Ships✓, Cargo✓, Locations✓, Encounters & Incidents✓

Box 2 — To Boldly Go (red)
  Captains: Georgiou, Soval, Kirk, Archer, Rebner, Khan (all Soon)
  Location & Market: TBG Persons✓, TBG Locations✓, Cargo/Ships/Allies/E&I (Soon)

Box 3 — Second Contact (amber)
  Captains: (Soon)
  Location & Market: Commons, Locations, Rewards (all Soon)

Box 4 — Strategy Guides (gray)
  Solo & Conspiracy✓, 5-Year Mission✓, Playing Against Picard✓
  Combining Markets (Soon), Wesley Crusher Guide (Soon)
```

To flip an entry from Soon → Live:
- Remove `soon` from class: `entry blue-box soon` → `entry blue-box`
- Remove `<span class="entry-badge badge-soon">Soon</span>`
- Set `href` to correct filename

---

## Current Live Guides

| Guide | File | Status |
|---|---|---|
| Shran Strategy Guide | `shran.html` | ✅ Live |
| Picard Strategy Guide | `picard.html` | ✅ Live |
| Burnham Strategy Guide | `burnham.html` | ✅ Live |
| Sisko Strategy Guide | `sisko.html` | ✅ Live |
| Sela Strategy Guide | `sela.html` | ✅ Live |
| Koloth Strategy Guide | `koloth.html` | ✅ Live |
| Person Deck Guide | `persons.html` | ✅ Live |
| Cargo Deck Guide | `cargo.html` | ✅ Live |
| Ship Deck Guide | `ships.html` | ✅ Live |
| Ally Deck Guide | `allies.html` | ✅ Live |
| Location Deck Guide | `locations.html` | ✅ Live |
| Encounter & Incident Decks | `encounters-incidents.html` | ✅ Live |
| TBG Location Guide | `tbg-locations.html` | ✅ Live |
| TBG Person Deck Guide | `tbg-persons.html` | ✅ Live |
| Solo & Conspiracy | `solo.html` | ✅ Live |
| 5-Year Mission | `five-year-mission.html` | ✅ Live |
| Playing Against Picard | `vs-picard.html` | ✅ Live |

> **Note:** Always verify live count by fetching `index.html` at session start — project knowledge may lag behind.

---

## Pending — Known Guides to Add (from BGG)

### To Boldly Go
- 6 captain guides: Georgiou, Soval, Kirk, Archer, Rebner, Khan
- Cargo, Ships, Ally, Encounters & Incidents market guides

### Second Contact
- Pike, Freeman captains
- Full market guides: Commons, Locations, Rewards

### Strategy Guides
- Combining Markets (`combining-markets.html`)
- Wesley Crusher Guide (`wesley-crusher-guide.html`)

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
