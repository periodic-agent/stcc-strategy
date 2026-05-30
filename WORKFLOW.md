# ST:CC Compendium — Workflow Summary
## For continuity across sessions

---

## Project Overview

A strategy compendium for **Star Trek: Captain's Chair** hosted at:
**https://periodic-agent.github.io/stcc-strategy/**

GitHub repo: **https://github.com/periodic-agent/stcc-strategy**

Content by **Matthew McCue (mdmccu2)** from BGG forums.
Formatted by **Periodic_agent**.

---

##  Rules

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
- Note: BGG switched to embedding base64 WebP directly in newer threads vs older CDN-hosted JPEGs, so new guides will note require manual downloads. 

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
  Content by Matthew McCue (mdmccu2) · Formatting by Periodic_agent · Last updated DD-MM-YYYY
</footer>
```
The date is the day the guide was built/rebuilt. Update it whenever the source guide is edited on BGG and reimported.
The date is the day the guide was built/rebuilt. Update it whenever the source guide is edited on BGG and reimported.

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

**Market guides** (Person, Ally, Ship, Cargo, Location, Encounters & Incidents) get a **pill grid** below the header. Each pill links to its h3 card anchor. Color matches the deck's index color:

| Deck | Color |
|---|---|
| Person | `#e8a94a` amber |
| Ally | `#9b6ecf` purple |
| Ship | `#7a8aaa` gray |
| Cargo | `#3a6aaa` dark blue |
| Location | `#4ac48a` green |
| Encounter | `#d4699f` pink |
| Incident | `#e05a5a` red |

For Encounters & Incidents, pill color is set per-pill via inline `style=` (pink for Encounters, red for Incidents).

```html
<nav class="toc-grid">
  <div class="toc-grid-label">Jump to card</div>
  <div class="toc-cards">
    <a href="#slug" class="toc-card">Card Name</a>
    ...
  </div>
</nav>
```

**Captain guides** get a **section list** below the header (Introduction excluded):

```html
<nav class="toc-list">
  <div class="toc-list-label">Contents</div>
  <ol>
    <li><a href="#slug">Section Name</a></li>
    ...
  </ol>
</nav>
```

**Back-to-top links** appear after every card entry (after the last `</p>` before the next `<h3>` or `<h2>`):

```html
<a href="#top" class="back-top">↑ back to top</a>
```

The top nav-bar must have `id="top"` for the anchor to work:
```html
<div id="top" class="nav-bar"><a href="index.html">← Back to Compendium</a></div>
```

**Required CSS additions** (append to canonical CSS block):
```css
  .toc-grid{max-width:860px;margin:1.5rem auto 0;padding:0 1.5rem;}
  .toc-grid-label{font-family:'Orbitron',sans-serif;font-size:0.6rem;letter-spacing:0.2em;text-transform:uppercase;color:var(--muted);margin-bottom:0.6rem;}
  .toc-cards{display:flex;flex-wrap:wrap;gap:0.4rem;}
  .toc-card{font-family:'Exo 2',sans-serif;font-size:0.75rem;font-weight:400;padding:0.2rem 0.6rem;border:1px solid [COLOR]55;border-radius:3px;color:[COLOR];text-decoration:none;background:var(--bg2);transition:background 0.15s,border-color 0.15s;}
  .toc-card:hover{background:var(--bg3);border-color:[COLOR];}
  .toc-list{max-width:860px;margin:1.5rem auto 0;padding:0 1.5rem;}
  .toc-list-label{font-family:'Orbitron',sans-serif;font-size:0.6rem;letter-spacing:0.2em;text-transform:uppercase;color:var(--muted);margin-bottom:0.6rem;}
  .toc-list ol{list-style:none;display:flex;flex-wrap:wrap;gap:0.3rem 1.5rem;padding:0 0 0 1rem;margin:0;border-left:2px solid var(--border);}
  .toc-list li{font-size:0.8rem;}
  .toc-list a{color:var(--blue2);text-decoration:none;}
  .toc-list a:hover{color:#fff;text-decoration:underline;}
  .back-top{display:block;text-align:right;font-family:'Orbitron',sans-serif;font-size:0.55rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);text-decoration:none;margin-top:0.25rem;margin-bottom:0.5rem;}
  .back-top:hover{color:var(--blue);}
```



---

## Canonical CSS — Box 1 (Blue)

Copy this verbatim for every Captain's Chair guide. Swap blue vars for red equivalents for TBG guides.

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
  .tag{font-family:'Orbitron',sans-serif;font-size:0.6rem;letter-spacing:0.1em;padding:0.2rem 0.6rem;border:1px solid var(--blue);color:var(--blue);border-radius:2px;}
  .content{max-width:860px;margin:0 auto;padding:2rem 1.5rem 4rem;}
  h2{font-family:'Orbitron',sans-serif;font-size:1rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:var(--blue2);border-left:3px solid var(--blue);padding-left:0.75rem;margin:2.5rem 0 1rem;}
  h3{font-family:'Orbitron',sans-serif;font-size:0.8rem;font-weight:400;letter-spacing:0.12em;color:var(--gold);text-transform:uppercase;margin:1.75rem 0 0.5rem;}
  p{margin-bottom:1rem;}
  .card-row{display:flex;gap:0.75rem;overflow-x:auto;padding:1rem 0 0.5rem;margin:1rem 0 1.5rem;scrollbar-width:thin;scrollbar-color:var(--blue) var(--bg2);}
  .card-row::-webkit-scrollbar{height:4px;}
  .card-row::-webkit-scrollbar-track{background:var(--bg2);}
  .card-row::-webkit-scrollbar-thumb{background:var(--blue);border-radius:2px;}
  .card-row img{height:220px;width:auto;border-radius:6px;border:1px solid var(--border);flex-shrink:0;transition:transform 0.2s,box-shadow 0.2s;cursor:zoom-in;}
  .card-row img:hover{transform:translateY(-4px) scale(1.03);box-shadow:0 12px 30px rgba(74,159,212,0.3);border-color:var(--blue);}
  .board-pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1.25rem 0;}
  .board-pair img{width:100%;border-radius:6px;border:1px solid var(--border);cursor:zoom-in;transition:transform 0.2s,box-shadow 0.2s;}
  .board-pair img:hover{transform:translateY(-4px) scale(1.02);box-shadow:0 12px 30px rgba(74,159,212,0.3);border-color:var(--blue);}
  .board-label{font-family:'Orbitron',sans-serif;font-size:0.55rem;letter-spacing:0.15em;color:var(--muted);text-align:center;margin-top:0.4rem;text-transform:uppercase;}
  #lightbox{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.92);z-index:1000;align-items:center;justify-content:center;cursor:zoom-out;}
  #lightbox.open{display:flex;}
  #lightbox img{max-width:90vw;max-height:90vh;border-radius:8px;box-shadow:0 0 60px rgba(74,159,212,0.4);}
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
  Strategy: Solo, 5-Year Mission, Playing Against Picard

Box 2 — To Boldly Go (red)
  Captains: Georgiou, Soval, Kirk, Archer, Rebner, Khan
  Location & Market: TBG Locations✓
```

To flip an entry from Soon → Live:
- Change class `entry blue-box soon` → `entry blue-box` (or `red-box`)
- Change `badge-soon` → `badge-live`
- Change `href` to correct filename

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
Claude generates `download_[guide]_images.py` per guide by extracting CDN URLs
from the SingleFile HTML. Script uses stdlib only (`urllib.request`), no deps.
Alt text from the SingleFile HTML is used to name files meaningfully
(e.g. `burnham_board_basic.jpg`, `burnham_1.jpg` … `burnham_7.jpg`).

### Shran guide images (already in repo as base64):
`shran_board_basic`, `shran_board_advanced`, `shran_available_1/2/3`,
`shran_reinforcement`, `shran_development_1/2`

### TBG Locations images:
6 embedded WebP + 3 CDN (Cold Station 12, Tanuga IV, Tellar Prime)

### Burnham guide images (9 total, base64 embedded):
`burnham_board_basic`, `burnham_board_advanced`, `burnham_1` through `burnham_7`

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

---

## Pending — Known Guides to Add (from BGG)

- Captain's Chair - Playing against Picard (multiplayer + solo)
- Captain's Chair - Guide to 5-Year Mission Strategies
- Captain's Chair - Guide to Solo
- To Boldly Go - Captains (6 captains, see index)

---

## Paragraph Break Identification

When Claude runs together paragraphs (BGG strips line breaks), provide the **last sentence** of each paragraph. Claude will insert `</p><p>` breaks after each.

Example prompt:
> "Section X needs paragraph breaks. Last sentence of each:
> - [last sentence para 1]
> - [last sentence para 2]"

---

## Notes

- Images stay as **base64 in HTML** until the library grows large enough to justify an `images/` folder with file references.
- The 3 missing TBG location images (Cold Station 12, Tanuga IV, Tellar Prime) load from BGG CDN — acceptable for now.
- `crop_cards.py` (perspective transform tool) exists for future individual card extraction — on hold pending McCue's agreement.
- Pictures taken with permission from WizKids.
