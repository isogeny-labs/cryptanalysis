#!/usr/bin/env python3
"""Audit committed Lean source pins and source-bound proof receipts.

This is a metadata check, not a Lean kernel build or a semantic review. It
works in sparse checkouts by reading absent tracked files from Git HEAD.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(r"\b(?:sorry|admit|sorryAx|native_decide|axiom)\b")


def lean_code(content: str) -> str:
    """Leave code tokens while blanking nested comments and string literals."""
    result: list[str] = []
    i = 0
    comment_depth = 0
    in_string = False
    while i < len(content):
        if comment_depth:
            if content.startswith("/-", i):
                comment_depth += 1
                i += 2
            elif content.startswith("-/", i):
                comment_depth -= 1
                i += 2
            else:
                i += 1
        elif in_string:
            if content[i] == "\\":
                i += 2
            elif content[i] == '"':
                in_string = False
                i += 1
            else:
                i += 1
        elif content.startswith("--", i):
            end = content.find("\n", i)
            result.append(" ")
            i = len(content) if end < 0 else end
        elif content.startswith("/-", i):
            result.append(" ")
            comment_depth = 1
            i += 2
        elif content[i] == '"':
            result.append(" ")
            in_string = True
            i += 1
        else:
            result.append(content[i])
            i += 1
    return "".join(result)


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def tracked_paths() -> set[str]:
    return {p.decode() for p in git("ls-files", "-z").split(b"\0") if p}


def source_bytes(path: str) -> bytes:
    local = ROOT / path
    if local.is_file():
        return local.read_bytes()
    return git("show", f"HEAD:{path}")


def effective_toolchain(path: str, paths: set[str]) -> str | None:
    parent = PurePosixPath(path).parent
    while True:
        candidate = str(parent / "lean-toolchain")
        if candidate in paths:
            return candidate
        if str(parent) == ".":
            return None
        parent = parent.parent


def receipt_source(path: str, receipt: dict) -> str | None:
    try:
        lean_args = [arg for arg in shlex.split(receipt["command"]) if arg.endswith(".lean")]
    except (KeyError, TypeError, ValueError):
        return None
    if len(lean_args) != 1:
        return None
    return str(PurePosixPath(path).parent / PurePosixPath(lean_args[0]).name)


def audit() -> dict:
    paths = tracked_paths()
    # The gate's intentionally failing Lean fixtures are audit instruments,
    # not research proofs. Their behavior is checked by tools/lean/selftest.
    lean_files = sorted(p for p in paths if p.endswith(".lean") and
                        not p.startswith("tools/lean/"))
    receipts = sorted(p for p in paths if p.endswith("lean-receipt.json"))
    missing_pins: list[str] = []
    forbidden: list[str] = []
    no_local_print: list[str] = []
    versions: dict[str, int] = {}

    for path in lean_files:
        toolchain = effective_toolchain(path, paths)
        if toolchain is None:
            missing_pins.append(path)
        else:
            version = source_bytes(toolchain).decode().strip()
            versions[version] = versions.get(version, 0) + 1
        content = source_bytes(path).decode()
        if FORBIDDEN.search(lean_code(content)):
            forbidden.append(path)
        if "#print axioms" not in content:
            no_local_print.append(path)

    receipt_errors: list[str] = []
    receipt_matches = 0
    for path in receipts:
        try:
            receipt = json.loads(source_bytes(path))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            receipt_errors.append(f"{path}: invalid JSON: {exc}")
            continue
        source = receipt_source(path, receipt)
        if source is None or source not in paths:
            receipt_errors.append(f"{path}: Lean source not found from command")
            continue
        expected = receipt.get("source_sha256")
        actual = hashlib.sha256(source_bytes(source)).hexdigest()
        if expected != actual:
            receipt_errors.append(f"{path}: source SHA-256 mismatch for {source}")
            continue
        toolchain = effective_toolchain(source, paths)
        declared = receipt.get("toolchain") or receipt.get("lean_toolchain")
        if declared and toolchain and declared != source_bytes(toolchain).decode().strip():
            receipt_errors.append(f"{path}: receipt toolchain differs from {toolchain}")
            continue
        receipt_matches += 1

    return {
        "head": git("rev-parse", "HEAD").decode().strip(),
        "lean_files": len(lean_files),
        "effective_toolchains": dict(sorted(versions.items())),
        "missing_toolchain_pins": missing_pins,
        "files_with_forbidden_tokens": forbidden,
        "files_without_local_axiom_print": no_local_print,
        "lean_receipts": len(receipts),
        "matching_source_receipts": receipt_matches,
        "receipt_errors": receipt_errors,
        "scope": "tracked source metadata only; no Lean build or semantic claim check",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write the complete audit as JSON")
    args = parser.parse_args()
    result = audit()
    if args.json:
        args.json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"{result['lean_files']} Lean files; "
        f"{len(result['missing_toolchain_pins'])} unpinned; "
        f"{result['matching_source_receipts']}/{result['lean_receipts']} receipt hashes match; "
        f"{len(result['files_with_forbidden_tokens'])} files with forbidden tokens"
    )
    for key in ("missing_toolchain_pins", "files_with_forbidden_tokens", "receipt_errors"):
        for item in result[key]:
            print(f"FAIL {key}: {item}")
    if result["files_without_local_axiom_print"]:
        print(
            "Separate axiom audit required for: "
            + ", ".join(result["files_without_local_axiom_print"])
        )
    return int(bool(
        result["missing_toolchain_pins"]
        or result["files_with_forbidden_tokens"]
        or result["receipt_errors"]
    ))


if __name__ == "__main__":
    raise SystemExit(main())
