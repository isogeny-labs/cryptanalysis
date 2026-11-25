#!/usr/bin/env python3
"""Research gate / pre-push and CI checks.

Enforces the invariants in AGENTS.md ("Research Gate, PCC Ledger & PR Hygiene"):

1. Non-draft freeze: an open, ready-for-review PR may not add `.md` files or
   net-new unverified PCC claims.
2. Evidence binding: every added PCC claim must cite a committed test script
   that defines `eval_point(E, G, Q)`.
3. Debt ceiling: at most 2 unverified PCC claims touched by origin/main...HEAD,
   and no push while `tools/check_lab_parity.py` reports a lock mismatch.

Exit 0 on pass; 2 on block, with a `STATUS: BLOCKED (<reason>)` line.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EVAL_RE = re.compile(
    r"(?im)^\s*(?:pub\s+)?(?:def|fn|function|proc)\s+eval_point\s*\(([^)]*)\)"
)
EVAL_ALT_RE = re.compile(
    r"(?im)^\s*eval_point\s*=\s*(?:function\s*)?\(([^)]*)\)"
)


def _root() -> Path:
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if r.returncode != 0:
        print("STATUS: BLOCKED (not inside a git worktree)")
        raise SystemExit(2)
    return Path(r.stdout.strip())


ROOT = _root()


def run(cmd, timeout=120):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def fail(reason: str) -> None:
    print(f"STATUS: BLOCKED ({reason})")
    raise SystemExit(2)


def diff_entries(base: str):
    r = run(["git", "diff", "--name-status", f"{base}...HEAD"])
    if r.returncode != 0:
        fail(f"cannot diff {base}...HEAD: {(r.stderr or r.stdout).strip()}")
    out = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        out.append((parts[0][0], parts[-1]))
    return out


def claim_id(path: str) -> str:
    return Path(path).stem


def standing(cid: str) -> str:
    pcc = ROOT / "tools" / "pcc" / "pcc.py"
    if not pcc.is_file():
        return "unverified"
    r = run([sys.executable, str(pcc), "standing", cid])
    text = (r.stdout + "\n" + r.stderr).strip()
    m = re.search(r":\s*([A-Za-z_]+)\s*$", text)
    return m.group(1).lower() if m else "unverified"


def proof_paths(claim_path: str):
    try:
        claim = json.loads((ROOT / claim_path).read_text())
    except Exception:
        return
    for proof in claim.get("proofs", []) or []:
        subject = proof.get("subject") or {}
        path = subject.get("path") or proof.get("path")
        if isinstance(path, str) and path:
            yield path


def has_eval_point(path: str) -> bool:
    p = ROOT / path
    if not p.is_file():
        return False
    if run(["git", "ls-files", "--error-unmatch", path]).returncode != 0:
        return False
    text = p.read_text(errors="replace")
    for rx in (EVAL_RE, EVAL_ALT_RE):
        for m in rx.finditer(text):
            params = [
                re.split(r"[:=]", x.strip())[0].strip().lower()
                for x in m.group(1).split(",")
                if x.strip()
            ]
            if {"e", "g", "q"} <= set(params):
                return True
    return False


def pr_is_draft():
    """True/False for an open PR, or None when there is no PR / no gh."""
    event = os.environ.get("GITHUB_EVENT_PATH")
    if event and Path(event).is_file():
        try:
            data = json.loads(Path(event).read_text())
            pr = data.get("pull_request")
            if pr is not None:
                return bool(pr.get("draft"))
        except Exception:
            pass
    if shutil.which("gh") is None:
        return None
    r = run(["gh", "pr", "view", "--json", "isDraft,state"], timeout=20)
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except Exception:
        return None
    if data.get("state") != "OPEN":
        return None
    return bool(data.get("isDraft"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--repo-name", default=ROOT.name)
    ap.add_argument("--skip-pr", action="store_true")
    ap.add_argument("--skip-parity", action="store_true")
    args = ap.parse_args()

    entries = diff_entries(args.base)
    added = [p for s, p in entries if s == "A"]
    added_claims = [p for p in added if p.startswith("pcc/claims/") and p.endswith(".json")]
    touched_claims = [
        p for s, p in entries
        if s in ("A", "M") and p.startswith("pcc/claims/") and p.endswith(".json")
    ]

    # 3. Parity lock must agree before any new research commit is pushed.
    if not args.skip_parity:
        parity = ROOT / "tools" / "check_lab_parity.py"
        if parity.is_file():
            r = run([sys.executable, str(parity), "--repo", args.repo_name])
            if r.returncode != 0:
                detail = (r.stdout + r.stderr).strip().splitlines()
                fail("parity: " + (detail[-1] if detail else "lock mismatch"))

    # 1. Non-draft PR freeze.
    if not args.skip_pr:
        draft = pr_is_draft()
        if draft is False:
            md = [p for p in added if p.endswith(".md")]
            if md:
                fail("non-draft freeze: added .md files: " + ", ".join(md[:5]))
            bad = [claim_id(p) for p in added_claims if standing(claim_id(p)) != "verified"]
            if bad:
                fail("non-draft freeze: new unverified PCC claims: " + ", ".join(bad[:5]))

    # 2. Evidence binding for every new PCC claim.
    for path in added_claims:
        cid = claim_id(path)
        if not any(has_eval_point(p) for p in proof_paths(path)):
            fail(f"evidence: {cid} has no committed eval_point(E, G, Q) test script")

    # 3. Unverified debt ceiling.
    unverified = [claim_id(p) for p in touched_claims if standing(claim_id(p)) == "unverified"]
    if len(unverified) > 2:
        fail(
            f"debt: {len(unverified)} unverified PCC claims touched (>2): "
            + ", ".join(unverified[:5])
        )

    print(
        "STATUS: OK "
        f"(base={args.base}, claims_touched={len(touched_claims)}, "
        f"unverified={len(unverified)}, added_md={sum(p.endswith('.md') for p in added)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
