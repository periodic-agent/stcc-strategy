#!/usr/bin/env python3
"""push_gate.py — fail-closed denylist gate for outgoing files.

Blocks files, paths, and commit messages containing denylisted terms
(real names, personal emails, machine usernames) BEFORE they leave the
machine. Project-agnostic, stdlib only: vendor this file into any repo.

Usage:
    python3 push_gate.py --pii-file <denylist> [--message "msg"] <file> [<file> ...]
    python3 push_gate.py --pii-file <denylist> --scan-dir <directory>
    python3 push_gate.py --pii-file <denylist> --scan-git-history [<repo_dir>]

Denylist format: one term per line; '#' comments and blank lines ignored.
Matching is case-insensitive and byte-based (works on text and binaries).

Exit codes:
    0  clean
    1  denylisted term found (details on stderr, terms shown masked)
    2  configuration error (denylist missing, empty, or unreadable) — FAIL CLOSED

Design rules:
- The denylist itself must never ship: any scanned file sharing the
  denylist's basename is refused outright.
- Matched terms are never printed in full; output masks them (r***l).
- No network access, no dependencies.
"""

import os
import subprocess
import sys

CHUNK = 1 << 20  # 1 MiB


def die(msg, code):
    print(f"push_gate: {msg}", file=sys.stderr)
    sys.exit(code)


def mask(term_bytes):
    t = term_bytes.decode("utf-8", "replace")
    if len(t) <= 2:
        return "*" * len(t)
    return f"{t[0]}{'*' * (len(t) - 2)}{t[-1]} ({len(t)} chars)"


def load_denylist(path):
    if not path:
        die("no denylist given (--pii-file). Refusing to pass anything. [fail closed]", 2)
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        die(f"cannot read denylist: {e}. [fail closed]", 2)
    terms = []
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith(b"#"):
            terms.append(line.lower())
    if not terms:
        die("denylist is empty. Refusing to pass anything. [fail closed]", 2)
    return terms, os.path.basename(path)


def scan_bytes(data, terms):
    """Return {term: count} for terms found in data (case-insensitive)."""
    low = data.lower()
    return {t: low.count(t) for t in terms if t in low}


def scan_stream(stream, terms):
    """Scan a binary stream in chunks with overlap; return {term: count}."""
    overlap = max(len(t) for t in terms) - 1
    hits = {}
    tail = b""
    while True:
        chunk = stream.read(CHUNK)
        if not chunk:
            break
        buf = (tail + chunk).lower()
        for t in terms:
            n = buf.count(t)
            if n:
                hits[t] = hits.get(t, 0) + n
        tail = chunk[-overlap:] if overlap else b""
    # overlap regions are double-counted only if a term sits fully inside
    # both windows; counts here are advisory — any hit > 0 blocks anyway.
    return hits


def report(label, hits):
    for t, n in hits.items():
        print(f"push_gate: BLOCKED — {label}: {mask(t)} x{n}", file=sys.stderr)


def gate_files(paths, terms, deny_base, message=None):
    bad = False
    if message is not None:
        hits = scan_bytes(message.encode(), terms)
        if hits:
            report("commit message", hits)
            bad = True
    for p in paths:
        if os.path.basename(p) == deny_base:
            print(f"push_gate: BLOCKED — refusing to ship the denylist itself: {p}",
                  file=sys.stderr)
            bad = True
            continue
        hits = scan_bytes(p.encode(), terms)  # the path itself can leak
        if hits:
            report(f"file path '{p}'", hits)
            bad = True
        try:
            with open(p, "rb") as f:
                hits = scan_stream(f, terms)
        except OSError as e:
            die(f"cannot read {p}: {e}. [fail closed]", 2)
        if hits:
            report(p, hits)
            bad = True
    return bad


def walk_dir(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            yield os.path.join(dirpath, fn)


def scan_git_history(repo_dir, terms):
    """Scan every object in the repo (all history, all branches)."""
    proc = subprocess.Popen(
        ["git", "-C", repo_dir, "cat-file", "--batch-all-objects", "--batch"],
        stdout=subprocess.PIPE)
    hits = scan_stream(proc.stdout, terms)
    proc.wait()
    if proc.returncode != 0:
        die(f"git cat-file failed in {repo_dir}. [fail closed]", 2)
    return hits


def main():
    args = sys.argv[1:]

    def take(flag, has_value=True):
        if flag in args:
            i = args.index(flag)
            if has_value:
                try:
                    v = args[i + 1]
                except IndexError:
                    die(f"{flag} requires a value", 2)
                del args[i:i + 2]
                return v
            del args[i]
            return True
        return None

    pii_file = take("--pii-file")
    message = take("--message")
    scan_dir = take("--scan-dir")
    scan_hist = take("--scan-git-history", has_value=False)

    terms, deny_base = load_denylist(pii_file)

    if scan_hist:
        repo = args[0] if args else "."
        hits = scan_git_history(repo, terms)
        if hits:
            report(f"git history of {repo}", hits)
            sys.exit(1)
        print(f"push_gate: clean — no denylisted term in any object of {repo}")
        sys.exit(0)

    paths = list(walk_dir(scan_dir)) if scan_dir else args
    if not paths and message is None:
        die("nothing to scan", 2)

    if gate_files(paths, terms, deny_base, message):
        sys.exit(1)
    n = len(paths)
    print(f"push_gate: clean — {n} file(s)"
          + (" + commit message" if message is not None else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
