# ST:CC Compendium — Open Issues

Tracked improvements for the site. Ordered by priority.

---

## Issue 1 — Exposed GitHub PAT (security, urgent)

**Problem:** `push_to_github.py` in the public repo root contains a hardcoded Personal Access Token. Anyone can read it; bots scan public repos for tokens within minutes. GitHub secret scanning may also auto-revoke it without warning.

**Fix:**
1. Revoke the current token (GitHub → Settings → Developer settings → Personal access tokens). Assume compromised.
2. Create a fine-grained PAT scoped to `stcc-strategy` only, permission Contents: read/write.
3. Modify `push_to_github.py` to read the token from an environment variable (`os.environ["GH_TOKEN"]`) instead of hardcoding it. Provide the token per session when a push is needed.

**Note:** the old token remains in git history; harmless once revoked.

**Status:** DONE — 04 Jul 2026. Old token revoked; fine-grained PAT in project knowledge; push_to_github.py v2 reads GH_TOKEN/--token-file. Token expiry: check GitHub if pushes start failing with auth errors.

---

## Issue 2 — Duplicated CSS across all guides (maintainability)

**Problem:** Every guide (18+) carries a full inline copy of the design system. Sitewide changes (e.g. adding `.chapter-date`) require editing every file. Copies drift out of sync over time.

**Fix:**
1. Extract the canonical design system to a shared `css/stcc.css`.
2. Handle box color themes with a body class (`<body class="theme-tbg">`) overriding the `:root` variables, rather than separate stylesheets per box.
3. Replace each guide's `<style>` block with `<link rel="stylesheet" href="css/stcc.css">`. Keep only guide-specific rules inline, if any.
4. Update WORKFLOW.md template accordingly.

**Migration:** one guide first as proof, verify rendering, then batch-convert the rest.

**Status:** DONE — 04 Jul 2026. css/stcc.css live; all 22 guides converted (3-guide pilot, then batch). Themes via body classes (theme-tbg, theme-sc). Verified by effective-style comparison; four guides had latent undefined-var bugs, now fixed.

---

## Issue 3 — Base64 images inline in HTML (performance)

**Problem:** Card and board images are embedded as base64 in guide HTML. Pages are heavy, load slowly on mobile, and guides are effectively un-diffable in git. WORKFLOW.md already flags this as temporary ("until the library grows"); with 18 live guides, that point is passed.

**Fix (revised 04 Jul 2026, per Periodic_agent):**
1. Tabletop card scans: REMOVE. For each card discussed in the guide text, insert its individual image from the existing library (`img/box1/[card].jpg`, matched by name against box1.json) at the point of discussion, as `.card-img` or `.card-row`, with `loading="lazy"`. Full resolution as-is; lightbox provides zoom. No web derivatives.
2. Board/setup photos (captain boards, reinforcement layouts): no library equivalent; extract from base64 to `img/guides/[guide]/` and keep in place.
3. Before removing any scan, check McCue's verbatim text for references to it ("as shown above"); replacement images go in the same position.
4. Audit all guides so every `<img>` has `loading="lazy"`.
5. Heads-up to McCue before the first converted guide goes live (approved).

**Migration:** per-guide, same proof-then-batch approach as Issue 2. Doing Issues 2 and 3 together per guide minimizes push cycles.

**Status:** DONE — 04 Jul 2026. All 12 core guides on library card images (~19 MB base64 removed); boards in img/guides/[captain]/; five-year-mission charts extracted; TBG embedded card art extracted to img/box2/ as JPG (35 cards, seeds the Box 2 scanner library, box2.json still pending). CDN dependency CLOSED — 04 Jul 2026: all 46 remaining CDN card images downloaded (download_box_images.py, run by Periodic_agent), pushed to img/box2/ and img/box3/, and all 6 CDN-linked guides relinked to local files with lazy loading. Zero geekdo references remain. Card database workbook seeded from all card faces: 77/82 rows tagged; open gaps are the 4 tiny updated-repeat images (Borg Spatial Trajector, Lirpa, Phasers, Orb of Time) and Tellarites (no image anywhere). Untouched by design: solo, vs-picard (no card images).

---

## Issue 4 — Furniture gaps on seven older guides (found by verify_guide v2 sweep, 19 Jul 2026)

**Problem (corrected 19 Jul):** every guide had a top nav link, but six guides lacked the bottom `Back to Compendium` bar (combining-markets, promo-pack-2, sc-market-locations-rewards, tbg-allies, tbg-encounters-incidents, tbg-ships); four of those used a variant top nav (`<nav>` + "ST:CC Compendium" wording) instead of the documented snippet; tbg-locations had an unclosed `<footer>` (its navs were fine).

**Fix:** normalized the four variant top navs to `<div id="top" class="nav-bar">` + "Back to Compendium"; added the bottom bar before `<footer>` on the six; closed the footer on tbg-locations; regenerated the seven canonical text files. Fixer ships as `tools/fix_furniture_issue4.py` (Rule 7).

**Status:** DONE — 19 Jul 2026. Full sweep: 26/26 guides PASS verify_guide v2.
