#!/usr/bin/env python3
"""patch_scanner_dupes.py -- reference copy of the duplicates-across-boxes change.

Approved 26 Aug 2026. This file records what changed and why; the change itself was applied
directly to cards.html because it rewrites resolveCards wholesale rather than by anchor.

The problem: resolveCards collapsed every printing of a card into one record, filed under the
box of the earliest printing. With Captain's Chair deselected a Scientist filter read "7 cards,
6 ..." with no way to see which card was the shared one, and a Box 2 reprint appeared in the
Captain's Chair Common group, a box the visitor had switched off.

1. resolveCards(rawPool, expand)
   - The per-record builder is factored out as mk(chosen, preferOwn). Collapsed mode calls it
     once with the resolved printing, exactly as before. Expanded mode calls it once per
     printing, so a reprint yields one tile per box, each filed under that box's deck group
     via the existing deckKey(), each carrying the group's boxes/copies/badgeKind.
   - preferOwn is set only in expanded mode: an expanded tile shows the scan of the printing it
     represents. Collapsed mode keeps the older rule, newest printing in the selection wins.
   - Per-printing fields (deck, box, card_number, variant, scan) come from that printing;
     shared fields (vp, position, away team, strips) prefer the printing's own value and fall
     back to the group, so an updated printing shows its own text.

2. showDupes state, default ON. Query token `dupes:off` (also no/0/hide), documented in the
   help panel. The checkbox in the Box row writes the token like every other control, and
   syncFilterPills ticks it from the query so a shared dupes:off link arrives unticked.

3. Counts. Deck header and total line always read "N cards · M printings". In expanded mode a
   header's cards is distinct ids and printings is tile count, which agree within a group
   because each box has its own group; collapsed mode is where they diverge, which is the case
   that was unreadable before: "7 cards · 8 printings".

4. otherPrintingsLine(c) puts a plain line on both tile styles, read from FULL_BY_ID so it is
   independent of box selection:
     Also in: To Boldly Go        other printings that share the text
     Updated in: To Boldly Go     a later printing supersedes this one
     Updates: Captain's Chair     shown on the updated printing itself
   Nothing is shown for a card printed in one box only.

Dropped from the original sketch: chip strip, badge tooltips.
"""
print(__doc__)
