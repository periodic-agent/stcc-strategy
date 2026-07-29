#!/usr/bin/env python3
"""patch_push_blobless.py -- stop push_to_github.py from downloading every image on every push.

The push script shallow-cloned the whole repo before committing. With several hundred card
scans in img/, that clone grew past the time a single sandboxed shell command is allowed, so
pushes were being killed before they ran.

The clone is now blobless and sparse: git fetches the commit graph and file list, then pulls
down only the blobs for the paths actually being pushed (needed so `git status` can tell a real
change from a no-op). Latest HTML and JSON still arrive exactly as before; the images stay on
the server unless an image is the thing being pushed.

Exact-string replacements; each must match exactly once.

Usage: python3 tools/patch_push_blobless.py [path/to/push_to_github.py]
"""

import sys

EDITS = [
(
"""        # Anonymous clone: repo is public, no token needed (or stored) here.
        run(["git", "clone", "--depth", "1", "--branch", BRANCH,
             f"https://{REPO}", clone_dir], token)""",
"""        # Anonymous clone: repo is public, no token needed (or stored) here.
        # Blobless + sparse: the repo carries hundreds of card scans, and a full clone takes
        # long enough to be killed by a command timeout. Only the paths being pushed are
        # materialised; their blobs are fetched on demand at checkout.
        run(["git", "clone", "--depth", "1", "--branch", BRANCH,
             "--filter=blob:none", "--sparse",
             f"https://{REPO}", clone_dir], token)
        run(["git", "-C", clone_dir, "sparse-checkout", "set", "--no-cone",
             *("/" + r for _, r in pairs)], token)"""
),
(
"""Implementation: shallow-clones the public repo anonymously, copies the file(s) in,
commits, and pushes with a one-shot authenticated URL.""",
"""Implementation: clones the public repo anonymously (shallow, blobless, sparse: only the paths
being pushed are checked out, so the image library is never downloaded), copies the file(s) in,
commits, and pushes with a one-shot authenticated URL."""
),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "push_to_github.py"
    src = open(path, encoding="utf-8").read()
    if "--filter=blob:none" in src:
        print("already patched; nothing to do")
        return 0
    for old, new in EDITS:
        n = src.count(old)
        if n != 1:
            print(f"refusing to patch: {n} matches for block starting {old.splitlines()[0][:60]!r}",
                  file=sys.stderr)
            return 1
        src = src.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(src)
    print(f"patched {path}: {len(EDITS)} exact-string replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
