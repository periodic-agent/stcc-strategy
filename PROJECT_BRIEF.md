# ST:CC Compendium — Project Brief

## What this is
A community strategy compendium for **Star Trek: Captain's Chair** (ST:CC), a solo/multiplayer board game by WizKids. Content is written by BGG user **Matthew McCue (mdmccu2)**. The compendium formats and hosts his guides as a clean, navigable website.

## People
- **Matthew McCue (mdmccu2)** — content author. Approved this project with two firm conditions (see below).
- **Periodic_agent** — formatter and site builder. Anonymous GitHub identity. Discord handle: Periodic_agent.

## McCue's Two Firm Rules
1. **Zero edits to his text** — verbatim only, no paraphrasing, no corrections, no rewriting. (Periodic_agent-directed corrections are sanctioned via the guide config's replace list; see WORKFLOW.md Rule 1a.)
2. **WizKids image credit** on every guide footer.

## URLs
- **Live site:** https://periodic-agent.github.io/stcc-strategy/
- **GitHub repo:** https://github.com/periodic-agent/stcc-strategy

## File access at session start
**Clone, don't fetch.** Raw-URL fetches (`raw.githubusercontent.com`, `web_fetch`) sit behind caches and can silently serve stale copies:
```
git clone --depth 1 https://github.com/periodic-agent/stcc-strategy.git
```
One call; provides every repo file, current, including WORKFLOW.md and images. The live repo is authoritative — never work from project knowledge copies or from memory. See WORKFLOW.md "Session Startup" for details and fallbacks.

## Project architecture
The project is divided into sub-projects (trackers, JSON database, card scanner, main index, guides) to keep each chat session focused and prevent context overflow. Each sub-project chat handles its own domain.

**This chat (Meta/Merge) is the WORKFLOW.md merge point.** At end of session, each sub-project chat produces a delta. Deltas are brought here, merged against the live WORKFLOW.md, and pushed to GitHub.

End-of-session prompt for any sub-project chat:
> "Fetch the current WORKFLOW.md, incorporate any new conventions or decisions from this session, save updated file to outputs."

## Push pipeline
`push_to_github.py` (repo root) — Claude runs it directly via bash; no manual download or rename needed. Push ONLY after Periodic_agent reviews the presented files and explicitly approves.

```
python3 push_to_github.py --pii-file <denylist> --token-file <token> -m "commit message" <local>:<repo> ...
```

Two files from project knowledge are required at run time, and only these two exist there:
- `git_pat_token.txt` — fine-grained PAT (this repo only, Contents read/write). Never hardcoded, never printed. See WORKFLOW.md "GitHub Token Handling".
- `pii_denylist.txt` — anonymity denylist. The script fails closed without it and scans all outgoing content, paths, and commit messages. See WORKFLOW.md "Anonymity Rules".

Files deploy via GitHub Pages in ~60 seconds.

## Tools
- **cards.html** — interactive Card Scanner. Filters by box, deck, suit, trait, skill, and name search. Data: `box1.json` (255 cards) + `box2.json` (community-sourced, growing). Cards/Images view toggle.
- **tools/** — build pipeline (build_guide.py, verify_guide.py), scanner data generator, image migrators, push gate (push_gate.py). Generators ship with their output (WORKFLOW.md Rule 7).

## Live guides (as of 19 Jul 2026 — the index is authoritative; regenerate this list from index.html when stale)

### Core Box — Captains (all with video where noted)
- picard.html, shran.html, koloth.html, sisko.html, sela.html, burnham.html — all Live

### Core Box — Market Guides
- persons.html, allies.html, ships.html, cargo.html, locations.html, encounters-incidents.html — all Live

### To Boldly Go
- georgiou.html — Live
- tbg-persons.html, tbg-allies.html, tbg-ships.html, tbg-cargo.html, tbg-locations.html, tbg-encounters-incidents.html — Live
- archer.html, soval.html, kirk.html, khan.html, rebner.html — Soon

### Second Contact
- sc-market-locations-rewards.html — Live
- Pike, Freeman captains + remaining market guides — pending McCue

### Other Guides
- solo.html, five-year-mission.html, vs-picard.html, combining-markets.html, promo-pack-2.html — Live
- wesley-crusher-guide.html — Soon

### Site furniture
- Card Scanner banner above Box 1; GoatCounter analytics on all pages.

## Conventions
See WORKFLOW.md for all operational conventions: session startup and smoke test, push pipeline and token/anonymity handling, guide build pipeline, HTML design system (css/stcc.css), card database schema and update cycle, image naming and folders, editorial protocols, and structural safety rules.
