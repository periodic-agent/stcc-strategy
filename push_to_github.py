#!/usr/bin/env python3
"""Push one or more files to the stcc-strategy repo via git (one commit).

Usage (single file):
    GH_TOKEN=<token> python3 push_to_github.py --pii-file <denylist> <local_path> <repo_path> "commit message"
Usage (multiple files, one commit):
    GH_TOKEN=<token> python3 push_to_github.py --pii-file <denylist> -m "commit message" <local>:<repo> [<local>:<repo> ...]
Either form also accepts: --token-file <path>

Token policy (see WORKFLOW.md, "GitHub Token Handling"):
- The token is NEVER hardcoded in this script and NEVER committed to the repo.
- It is a fine-grained PAT scoped to periodic-agent/stcc-strategy only,
  permission Contents: read/write.
- In Claude sessions, the token lives in project knowledge (git_pat_token.txt)
  and is passed at run time via GH_TOKEN or --token-file.

Anonymity gate (see WORKFLOW.md, "Anonymity Rules") — v3, FAIL CLOSED:
- Every push is scanned against a denylist of personal identifiers before
  anything leaves the machine: file contents (binary-safe, case-insensitive),
  repo paths, and the commit message.
- The denylist lives in project knowledge (pii_denylist.txt), NEVER in the
  repo, and is passed via --pii-file or the PII_FILE environment variable.
- No denylist = no push. There is no bypass flag; that is the point.
- The denylist file itself is refused as a push target.
- Matches are reported masked (r***l); the script never prints the terms.
- Standalone/reusable version with directory and git-history scan modes:
  tools/push_gate.py.

Implementation: clones the public repo anonymously (shallow, blobless, sparse: only the paths
being pushed are checked out, so the image library is never downloaded), copies the file(s) in,
commits, and pushes with a one-shot authenticated URL. The token is never
written to .git/config and is scrubbed from any error output.

Stdlib only. Requires git on PATH.
"""

import os
import shutil
import subprocess
import sys
import tempfile

REPO = "github.com/periodic-agent/stcc-strategy.git"
BRANCH = "main"
COMMIT_NAME = "periodic-agent"
COMMIT_EMAIL = "periodic-agent@users.noreply.github.com"


def _pii_mask(term):
    t = term.decode("utf-8", "replace")
    return ("*" * len(t)) if len(t) <= 2 else f"{t[0]}{'*' * (len(t) - 2)}{t[-1]}"


def get_pii_terms(args):
    """Load the denylist. FAIL CLOSED: no denylist, no push."""
    path = None
    if "--pii-file" in args:
        i = args.index("--pii-file")
        try:
            path = args[i + 1]
        except IndexError:
            sys.exit("--pii-file requires a path")
        del args[i:i + 2]
    else:
        path = os.environ.get("PII_FILE", "").strip() or None
    if not path:
        sys.exit("No PII denylist: pass --pii-file <path> or set PII_FILE.\n"
                 "The gate fails closed — pushing without it is not supported.\n"
                 "(Denylist lives in project knowledge as pii_denylist.txt.)")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        sys.exit(f"Cannot read PII denylist: {e}. Fail closed — nothing pushed.")
    terms = [l.strip().lower() for l in raw.splitlines()
             if l.strip() and not l.strip().startswith(b"#")]
    if not terms:
        sys.exit("PII denylist is empty. Fail closed — nothing pushed.")
    return terms, os.path.basename(path)


def pii_gate(pairs, message, terms, deny_base):
    """Scan commit message, repo paths, and file contents. Block on any hit."""
    bad = []
    low_msg = message.encode().lower()
    for t in terms:
        if t in low_msg:
            bad.append(f"commit message contains {_pii_mask(t)}")
    for local_path, repo_path in pairs:
        if os.path.basename(local_path) == deny_base or os.path.basename(repo_path) == deny_base:
            bad.append(f"refusing to push the denylist itself: {repo_path}")
            continue
        if any(t in repo_path.encode().lower() for t in terms):
            bad.append(f"repo path leaks a denylisted term: {repo_path}")
        with open(local_path, "rb") as f:
            low = f.read().lower()
        for t in terms:
            n = low.count(t)
            if n:
                bad.append(f"{local_path}: {_pii_mask(t)} x{n}")
    if bad:
        sys.exit("PII GATE BLOCKED THE PUSH:\n  " + "\n  ".join(bad)
                 + "\nNothing was pushed. Clean the files (or fix the denylist) and retry.")


def get_token(args):
    if "--token-file" in args:
        i = args.index("--token-file")
        try:
            path = args[i + 1]
        except IndexError:
            sys.exit("--token-file requires a path")
        del args[i:i + 2]
        with open(path) as f:
            return f.read().strip()
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        sys.exit("No token found: set GH_TOKEN or pass --token-file <path>")
    return token


def run(cmd, token, cwd=None):
    """Run a command; scrub the token from all output before printing."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = (result.stdout + result.stderr).replace(token, "[TOKEN]")
    if result.returncode != 0:
        sys.exit(f"Command failed: {' '.join(c.replace(token, '[TOKEN]') for c in cmd)}\n{out}")
    return out


def parse_args(args):
    """Return (message, [(local, repo), ...]) supporting both CLI forms."""
    if "-m" in args:
        i = args.index("-m")
        try:
            message = args[i + 1]
        except IndexError:
            sys.exit("-m requires a commit message")
        del args[i:i + 2]
        pairs = []
        for a in args:
            if ":" not in a:
                sys.exit(f"Expected <local>:<repo> pair, got: {a}")
            local, repo = a.rsplit(":", 1)
            pairs.append((local, repo))
        if not pairs:
            sys.exit("No <local>:<repo> pairs given")
        return message, pairs
    if len(args) != 3:
        sys.exit('Usage: push_to_github.py <local> <repo> "msg"  |  -m "msg" <local>:<repo> ...')
    return args[2], [(args[0], args[1])]


def main():
    args = sys.argv[1:]
    pii_terms, deny_base = get_pii_terms(args)  # fail closed, before anything else
    token = get_token(args)
    message, pairs = parse_args(args)

    for local_path, _ in pairs:
        if not os.path.isfile(local_path):
            sys.exit(f"Local file not found: {local_path}")

    pii_gate(pairs, message, pii_terms, deny_base)

    tmp = tempfile.mkdtemp(prefix="stcc_push_")
    try:
        clone_dir = os.path.join(tmp, "repo")
        # Anonymous clone: repo is public, no token needed (or stored) here.
        # Blobless + sparse: the repo carries hundreds of card scans, and a full clone takes
        # long enough to be killed by a command timeout. Only the paths being pushed are
        # materialised; their blobs are fetched on demand at checkout.
        run(["git", "clone", "--depth", "1", "--branch", BRANCH,
             "--filter=blob:none", "--sparse",
             f"https://{REPO}", clone_dir], token)
        run(["git", "-C", clone_dir, "sparse-checkout", "set", "--no-cone",
             *("/" + r for _, r in pairs)], token)

        run(["git", "-C", clone_dir, "config", "user.name", COMMIT_NAME], token)
        run(["git", "-C", clone_dir, "config", "user.email", COMMIT_EMAIL], token)

        for local_path, repo_path in pairs:
            dest = os.path.join(clone_dir, repo_path)
            os.makedirs(os.path.dirname(dest) or clone_dir, exist_ok=True)
            shutil.copyfile(local_path, dest)
            run(["git", "-C", clone_dir, "add", repo_path], token)

        status = run(["git", "-C", clone_dir, "status", "--porcelain"], token)
        if not status.strip():
            print("No changes: all files identical to repo versions. Nothing pushed.")
            return

        run(["git", "-C", clone_dir, "commit", "-m", message], token)
        # One-shot authenticated push; token goes only into this command, not .git/config.
        run(["git", "-C", clone_dir, "push",
             f"https://x-access-token:{token}@{REPO}", f"HEAD:{BRANCH}"], token)
        names = ", ".join(r for _, r in pairs)
        print(f"Pushed {len(pairs)} file(s) in one commit: {names} — Pages deploys in ~60 s.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
