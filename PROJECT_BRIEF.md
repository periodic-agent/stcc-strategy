# ST:CC Compendium — Project Brief

## What this is
A community strategy compendium for **Star Trek: Captain's Chair** (ST:CC), a solo/multiplayer board game by WizKids. Content is written by BGG user **Matthew McCue (mdmccu2)**. The compendium formats and hosts his guides as a clean, navigable website.

## People
- **Matthew McCue (mdmccu2)** — content author. Approved this project with two firm conditions (see below).
- **Periodic_agent** — formatter and site builder. Anonymous GitHub identity. Discord handle: Periodic_agent.

## McCue's Two Firm Rules
1. **Zero edits to his text** — verbatim only, no paraphrasing, no corrections, no rewriting.
2. **WizKids image credit** on every guide footer.

## URLs
- **Live site:** https://periodic-agent.github.io/stcc-strategy/
- **GitHub repo:** https://github.com/periodic-agent/stcc-strategy
- **Raw file base:** https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/

## File fetch pattern
To fetch any guide at session start:
```
web_fetch https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/[filename]
```
Example:
```
web_fetch https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/index.html
web_fetch https://raw.githubusercontent.com/periodic-agent/stcc-strategy/main/WORKFLOW.md
```
Always fetch the live version. Never work from memory or cached content.

## Project architecture
The project is divided into sub-projects (trackers, JSON database, card scanner, main index, guides) to keep each chat session focused and prevent context overflow. Each sub-project chat handles its own domain.

**This chat (Meta/Merge) is the WORKFLOW.md merge point.** At end of session, each sub-project chat produces a delta. Deltas are brought here, merged against the live WORKFLOW.md, and pushed to GitHub.

End-of-session prompt for any sub-project chat:
> "Fetch the current WORKFLOW.md, incorporate any new conventions or decisions from this session, save updated file to outputs."

## Push pipeline
`push_to_github.py` is in the repo root. Claude runs it directly via bash_tool -- no manual download or rename needed.

Usage (Claude runs this internally):
```
python push_to_github.py <local_path> <repo_path> "commit message"
```

PAT token is hardcoded in the script. Claude fetches the script from the live repo, runs it, confirms the push. Files go straight to GitHub, GitHub Pages deploys in ~60 seconds.

## Live guides (as of 02 Jun 2026)

### Core Box — Captains
- picard.html — Jean-Luc Picard (Complexity 1)
- shran.html — Thy'Lek Shran (Complexity 2)
- koloth.html — Koloth, the Dahar Master (Complexity 3)
- sisko.html — Benjamin Sisko (Complexity 4)
- sela.html — Sela (Complexity 5)
- burnham.html — Michael Burnham (Complexity 7)

### Core Box — Market Guides
- persons.html, cargo.html, ships.html, allies.html, locations.html, encounters-incidents.html

### Strategy Guides
- solo.html — Solo & Conspiracy
- five-year-mission.html — 5-Year Mission
- vs-picard.html — Playing Against Picard

### To Boldly Go
- tbg-locations.html — Location Guide
- tbg-persons.html — Person Deck Guide

### Second Contact (all Soon)
- Pike, Freeman captains + market guides (pending McCue)

### Strategy Guides
- solo.html, five-year-mission.html, vs-picard.html
- combining-markets.html — Combining Markets (Soon)
- wesley.html — Wesley Crusher Guide (Soon)

## Conventions
See WORKFLOW.md for all formatting conventions including:
- CSS design system and variables
- Card property list format (.card-props)
- Lore paragraph styling (.lore)
- Video playthroughs section template
- Memory Alpha episode link format
- Posted/edited date format
- Footer attribution format
- Structural safety rules (always insert before </main>)
- Image extraction notes (unquoted src= pattern)
