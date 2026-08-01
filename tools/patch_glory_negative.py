#!/usr/bin/env python3
"""Tint the glory badge's delta for negative values.

Negative glory prints in a warm red on the real card; the scanner drew every
delta in the same cool gray. This gives the delta a light red-orange fill when
the value is below zero and leaves the oval, the digit and the geometry alone,
so the accent stays subtle. 35 cards carry a negative glory today (-2 on 33,
-4 on 2).

cards.html is the repo's source of truth and several chats edit it directly,
so this patches the file in place, asserts its anchor, and is idempotent.

Usage: python3 patch_glory_negative.py <cards.html> [out.html]
"""
import sys

COOL, WARM = '#c3cfdd', '#f0a893'   # gray delta; light red-orange for negatives


def patch(s):
    if 'gloryFill' in s:
        print('already patched; nothing to do')
        return s
    old = ('translate(-13 -11.65)" d="M13 3.6c2.3 4 5.2 10.2 7.5 16.1-2.7-2-5.1-2.9-7.5-2.9'
           's-4.8.9-7.5 2.9C7.8 13.8 10.7 7.6 13 3.6z" fill="' + COOL + '"/>\'')
    assert old in s, 'glory delta fill'
    s = s.replace(old, old.replace('fill="' + COOL + '"', 'fill=\'+gloryFill+\''))

    old = "    corner='<svg class=\"glorybadge\" viewBox=\"0 0 32 29\" title=\"Glory '+c.glory+'\">'"
    assert old in s, 'glory badge open tag'
    s = s.replace(old,
                  "    // negative glory prints warm on the card; tint the delta, nothing else\n"
                  "    const gloryFill=(c.glory<0)?'\"" + WARM + "\"':'\"" + COOL + "\"';\n"
                  + old)
    return s


def main(src, out=None):
    s = open(src).read()
    open(out or src, 'w').write(patch(s))
    print('wrote', out or src)


if __name__ == '__main__':
    main(*sys.argv[1:])
