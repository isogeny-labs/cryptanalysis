#!/usr/bin/env python3
"""Replay the frozen proof unchanged, then check the same claims with current tools."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

STUDY = "experiments/chained-transfer-public-target"
REFERENCE = f"{STUDY}/ci_induced_transfer/reference-01.sha256"
PRODUCER = "3d49af7f3d0a28e76b79e4825c9d2324e85853d2"
HISTORICAL = "41e35d8c701484a6ca5406ecbf7bb83278be6073"
AMENDMENTS = frozenset({
    ".github/workflows/chained-transfer-induced-proof.yml", "pcc/keyring.json", "tools/lean/current-corpus-gate.py",
    "tools/lean/test_current_corpus_gate.py", "tools/pcc/pcc.py", "tools/pcc/test_pcc.py",
})


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_path(repo: Path, producer: Path, name: str) -> Path:
    if name.startswith("../crypto/"):
        root, relative = producer, name[len("../crypto/"):]
    else:
        root, relative = repo, name
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(p in {".", ".."} for p in parts):
        raise ValueError(f"unsafe sealed path: {name}")
    result = root.joinpath(*parts)
    if result.is_symlink() or not result.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"sealed path escapes its checkout: {name}")
    return result


def verify_files(repo: Path, producer: Path, frozen: Path, frozen_producer: Path,
                 contract: dict) -> list[dict]:
    if contract["schema"] != "induced-transfer.dual-replay/v1":
        raise ValueError("unknown replay contract")
    if contract["historical_consumer"] != HISTORICAL:
        raise ValueError("historical consumer pin changed")
    if contract["producer"] != PRODUCER:
        raise ValueError("original producer pin changed")
    amendments = contract["verifier_amendments"]
    if set(amendments) != AMENDMENTS:
        raise ValueError("only the six explicitly amended workflow/verifier/keyring inputs may differ")
    original = (frozen / REFERENCE).read_bytes()
    if digest(original) != contract["historical_reference_sha256"]:
        raise ValueError("frozen reference changed")
    if (repo / REFERENCE).read_bytes() != original:
        raise ValueError("current checkout rewrote the frozen reference")
    rows = []
    seen = set()
    for line in original.decode().splitlines():
        expected, name = line.split("  ", 1)
        if name in seen or len(expected) != 64:
            raise ValueError("malformed or duplicate original guard")
        seen.add(name)
        historical = digest(source_path(frozen, frozen_producer, name).read_bytes())
        if historical != expected:
            raise ValueError(f"historical sealed input changed: {name}")
        current = digest(source_path(repo, producer, name).read_bytes())
        amendment = amendments.get(name)
        if amendment:
            if amendment["historical_sha256"] != expected:
                raise ValueError(f"amendment lost original binding: {name}")
            wanted = amendment["current_sha256"]
        else:
            wanted = expected
        if current != wanted:
            raise ValueError(f"current sealed input changed: {name}")
        rows.append({"path": name, "historical_sha256": expected, "current_sha256": current})
    if not AMENDMENTS.issubset(seen):
        raise ValueError("amended input absent from original guard")
    return rows


def head(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--producer", type=Path, required=True)
    ap.add_argument("--frozen-consumer", type=Path, required=True)
    ap.add_argument("--frozen-producer", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo, producer, frozen, frozen_producer, out = (
        p.resolve() for p in (args.repo, args.producer, args.frozen_consumer,
                             args.frozen_producer, args.out))
    for root in (repo, producer, frozen, frozen_producer):
        if out.is_relative_to(root) or root.is_relative_to(out):
            raise ValueError("outputs must be outside every source checkout")
    out.mkdir(parents=True, exist_ok=False)
    contract = json.loads((repo / "tools/lean/induced-transfer-current-contract.json").read_text())
    state = {"schema": "induced-transfer.dual-replay-receipt/v1", "phases": [],
             "scope": "unsigned proof replay only; no new trust or execution/cost standing"}
    env = os.environ.copy()
    env["ELAN_TOOLCHAIN"] = "leanprover/lean4:v4.34.1"

    def save() -> None:
        (out / "dual-replay.json").write_text(json.dumps(state, indent=2) + "\n")

    def phase(name: str, command: list[str], cwd: Path, limit: int = 300) -> None:
        entry = {"name": name, "command": command, "timeout_seconds": limit}
        state["phases"].append(entry)
        save()
        with (out / f"{name}.txt").open("wb") as stream:
            try:
                process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                code = process.wait(timeout=limit)
                entry["exit"] = code
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                entry["status"] = "timeout"
                save()
                raise
        save()
        if code:
            raise RuntimeError(f"{name} failed with exit {code}; retained log: {out / (name + '.txt')}")

    try:
        if head(frozen) != HISTORICAL:
            raise ValueError("wrong frozen consumer checkout")
        if head(producer) != contract["producer"] or head(frozen_producer) != contract["producer"]:
            raise ValueError("wrong original producer checkout")
        original = subprocess.check_output(["git", "show", f"{HISTORICAL}:{REFERENCE}"], cwd=frozen)
        if (frozen / REFERENCE).read_bytes() != original:
            raise ValueError("frozen reference does not match its immutable Git object")
        state["source_guards"] = verify_files(repo, producer, frozen, frozen_producer, contract)
        state["consumer_head"] = head(repo)
        state["historical_consumer_head"] = head(frozen)
        state["producer_head"] = head(producer)
        save()
        phase("historical-replay", ["bash", f"{STUDY}/ci_induced_transfer/check-01.sh",
              str(frozen_producer), str(out / "historical")], frozen, 1500)
        phase("current-pcc-tests", [sys.executable, "-m", "unittest", "tools/pcc/test_pcc.py"], repo)
        phase("current-pcc-canary", [sys.executable, "tools/pcc/pcc.py", "canary"], repo)
        phase("current-corpus-tests", [sys.executable, "-m", "unittest", "tools/lean/test_current_corpus_gate.py", "tools/lean/test_source_dispositions.py", "tools/lean/test_registered_mathlib_sources.py", "tools/lean/test_formal_projects.py"], repo)
        phase("current-proof-controls", ["bash", "tools/lean/selftest/run.sh"], repo)
        current = out / "current"
        current.mkdir()
        source = f"{STUDY}/original-induced-transfer-01/lean/InducedFullTransfer.lean"
        (current / "consumer-head.txt").write_text(head(repo) + "\n")
        (current / "actual-consumer-InducedFullTransfer.lean").write_bytes((repo / source).read_bytes())
        (current / "actual-producer-InducedFullTransfer.lean").write_bytes((repo / source).read_bytes())
        phase("current-consumer-proof", ["bash", "tools/lean/proof-gate.sh", "--out",
              str(current / "consumer-proofs"), source], repo, 120)
        (producer / "target").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="induced-current-", dir=producer / "target") as stage:
            staged = Path(stage) / "InducedFullTransfer.lean"
            staged.write_bytes((repo / source).read_bytes())
            env["ELAN_TOOLCHAIN"] = "leanprover/lean4:v4.35.0"
            phase("current-producer-proof", ["bash", "tools/lean/proof-gate.sh", "--out",
                  str(current / "producer-proofs"), str(staged.relative_to(producer))], producer, 120)
        env["ELAN_TOOLCHAIN"] = "leanprover/lean4:v4.34.1"
        for claim in (repo / f"{STUDY}/ci_induced_transfer/statement-bindings-01.txt").read_text().splitlines():
            phase(f"binding-{claim}", [sys.executable, "tools/pcc/pcc.py", "verify",
                  f"pcc/claims/{claim}.json", "--json"], repo, 120)
            (current / f"binding-{claim}.txt").write_bytes((out / f"binding-{claim}.txt").read_bytes())
        phase("current-exact-coverage", [sys.executable,
              f"{STUDY}/ci_induced_transfer/validate_receipts_01.py", str(repo), str(current)], repo)
        state["source_guards_after"] = verify_files(repo, producer, frozen, frozen_producer, contract)
        state["status"] = "pass"
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        state["status"] = "fail"
        state["error"] = str(exc)
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        try:
            state["source_guards_final"] = verify_files(repo, producer, frozen, frozen_producer, contract)
        except (OSError, ValueError) as exc:
            state["final_source_guard_error"] = str(exc)
            state["status"] = "fail"
        save()
        if state.get("status") == "fail":
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
