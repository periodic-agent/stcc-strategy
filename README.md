# ST:CC Strategy Compendium

Community strategy resource for **Star Trek: Captain's Chair**, live at
**https://periodic-agent.github.io/stcc-strategy/**

Strategy content by **Matthew McCue (mdmccu2)**, reproduced verbatim from his BGG forum guides with permission. Compiled and formatted by **Periodic_agent**. Card images © WizKids.

## What's live — 28 guides + the Card Scanner

- **6 Core Box captain guides** — Picard, Shran, Koloth, Sisko, Sela, Burnham
- **6 Core Box market guides** — Persons, Allies, Ships, Cargo, Locations, Encounters & Incidents
- **3 To Boldly Go captain guides** — Georgiou, Soval, Kirk
- **6 To Boldly Go market guides** — same decks, expansion box
- **Second Contact** — Market, Locations & Rewards guide
- **6 strategy guides** — Solo & Conspiracy, 5-Year Mission, Playing Against Picard, Combining Markets, Promo Pack 2, Wesley Crusher
- **Card Scanner** — searchable database of **every card in every box**: Core, To Boldly Go, Second Contact, and both promo packs, all tagged and scanned. Filter by pills or type queries like `trait:klingon suit:person`, `skill:military`, `-deck:sisko`. The community tagging effort is complete — contributors are credited on the site.

## Pending

- Remaining To Boldly Go captain guides (Archer, Rebner, Khan)
- Second Contact captain guides (Pike, Riker, Freeman)

## Using the data and images (yes, you're welcome to)

The card database and card images are a community resource. Link them in
forum posts, Discord, spreadsheets, or your own tools; that's what they're
for. Use the site URLs (stable, CDN-served), not raw git links:

- **Card data:** `https://periodic-agent.github.io/stcc-strategy/box1.json`
  (same pattern for `box2`, `box3`, `promo1`, `promo2`). One JSON object per
  card: name, suit, deck, traits, skill/focus icons, image filename.
- **Card images:** `https://periodic-agent.github.io/stcc-strategy/img/box1/<card-name>.jpg`
  (folders `box1`..`box3`, `promo1`, `promo2`). Filenames are lowercase,
  hyphenated, deck-prefixed for crew cards: `sisko-garak.jpg`,
  `picard-jean-luc-picard.jpg`. The easiest way to grab a link: find the
  card in the [Card Scanner](https://periodic-agent.github.io/stcc-strategy/cards.html)
  and copy the image address.

**Filenames are permanent.** Once a card image ships, its URL never changes,
so your links won't rot.

Card images © WizKids. A pointer back to the Compendium is appreciated but
not required.

## Repo layout

| Path | Contents |
|---|---|
| `*.html` | Guides + index + Card Scanner (root, GitHub Pages) |
| `css/stcc.css` | Shared design system (themes via body class) |
| `img/box1..box3`, `img/promo1..2` | Card image library, one file per card |
| `img/guides/` | Captain boards and chart images per guide |
| `box1..box3.json`, `promo1..2.json` | Card database (repo root) |
| `text/` | Canonical text per guide (verification baseline) |
| `data/` | Strategy index for the Scanner's guide links |
| `tools/` | Build, verify, and maintenance scripts |
| `WORKFLOW.md` | Conventions and procedures (authoritative) |
| `ISSUES.md` | Improvement tracker |

Corrections and card photos welcome — open an issue or find Periodic_agent on the ST:CC Discord.
