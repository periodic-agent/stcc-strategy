#!/usr/bin/env python3
"""Push a single file to the stcc-strategy repo via git.

Usage:
    GH_TOKEN=<token> python3 push_to_github.py <local_path> <repo_path> "commit message"
or:
    python3 push_to_github.py <local_path> <repo_path> "commit message" --token-file <path>

Token policy (see WORKFLOW.md, "GitHub Token Handling"):
- The token is NEVER hardcoded in this script and NEVER committed to the repo.
- It is a fine-grained PAT scoped to periodic-agent/stcc-strategy only,
  permission Contents: read/write.
- In Claude sessions, the token lives in project knowledge (git_pat_token.txt)
  and is passed at run time via GH_TOKEN or --token-file.

Implementation: shallow-clones the public repo anonymously, copies the file in,
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


def main():
    args = sys.argv[1:]
    token = get_token(args)
    if len(args) != 3:
        sys.exit('Usage: push_to_github.py <local_path> <repo_path> "commit message"')
    local_path, repo_path, message = args

    if not os.path.isfile(local_path):
        sys.exit(f"Local file not found: {local_path}")

    tmp = tempfile.mkdtemp(prefix="stcc_push_")
    try:
        clone_dir = os.path.join(tmp, "repo")
        # Anonymous clone: repo is public, no token needed (or stored) here.
        run(["git", "clone", "--depth", "1", "--branch", BRANCH,
             f"https://{REPO}", clone_dir], token)

        dest = os.path.join(clone_dir, repo_path)
        os.makedirs(os.path.dirname(dest) or clone_dir, exist_ok=True)
        shutil.copyfile(local_path, dest)

        run(["git", "-C", clone_dir, "config", "user.name", COMMIT_NAME], token)
        run(["git", "-C", clone_dir, "config", "user.email", COMMIT_EMAIL], token)
        run(["git", "-C", clone_dir, "add", repo_path], token)

        status = run(["git", "-C", clone_dir, "status", "--porcelain"], token)
        if not status.strip():
            print(f"No changes: {repo_path} is identical to the repo version. Nothing pushed.")
            return

        run(["git", "-C", clone_dir, "commit", "-m", message], token)
        # One-shot authenticated push; token goes only into this command, not .git/config.
        run(["git", "-C", clone_dir, "push",
             f"https://x-access-token:{token}@{REPO}", f"HEAD:{BRANCH}"], token)
        print(f"Pushed {repo_path} — GitHub Pages will deploy in ~60 s.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
