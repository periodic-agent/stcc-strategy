#!/usr/bin/env python3
"""Strip text, 22 Aug 2026: hyphenated trait names become chips.

stripAutoTokens builds each trait regex from the traitChip key with hyphens
turned into spaces ("mind-control" -> "mind control"), so a trait whose printed
name keeps the hyphen (NX-01, key "nx-01") was searched as "nx 01" and never
matched. The pattern now accepts a hyphen or a space at each key hyphen, so
both "Mind Control" and "NX-01" chip. The capital-letter guard is unchanged.
Idempotent. Usage: python3 tools/patch_strip_trait_hyphen.py [cards.html]
"""
import sys
path = sys.argv[1] if len(sys.argv) > 1 else 'cards.html'
s = open(path, encoding='utf-8').read()
old = "    t=t.replace(new RegExp('\\\\b'+k.replace(/-/g,' ')+'\\\\b','gi'),"
new = "    t=t.replace(new RegExp('\\\\b'+k.replace(/-/g,'[- ]')+'\\\\b','gi'),"
if new in s:
    print('already patched')
elif old in s:
    open(path, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    print('trait regex: hyphen or space')
else:
    sys.exit('anchor not found')
