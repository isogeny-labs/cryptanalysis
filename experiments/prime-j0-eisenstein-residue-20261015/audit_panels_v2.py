#!/usr/bin/env python3
"""Independent structural and paired-ratio audit of retained panel archives.

This validates archived pair ledgers and declared A/A limits. It does not
revalidate native executable behavior, fixture semantics, host isolation, or
the specialized analyzer's other proof and provenance checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import tarfile
from collections import Counter


REQUIRED = {"manifest.json", "summary.json", "runs.jsonl", "pairs.jsonl"}
CALIBRATION_PREFIX = "cal_"


def _json(raw: bytes, label: str):
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON in {label}: {exc}") from exc


def _jsonl(raw: bytes, label: str):
    rows = []
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        rows.append(_json(line, f"{label}:{number}"))
    return rows


def interval_qualifies(interval, aa_passed: bool) -> bool:
    """Fail closed for both improvement and regression directional intervals."""
    if not aa_passed or not isinstance(interval, (list, tuple)) or len(interval) != 2:
        return False
    low, high = interval
    if (not isinstance(low, (int, float)) or isinstance(low, bool)
            or not isinstance(high, (int, float)) or isinstance(high, bool)
            or not math.isfinite(low) or not math.isfinite(high) or low > high):
        return False
    return low > 1.0 or high < 1.0


def recompute_pair_ratio(reference_ms, candidate_ms, stated_ratio) -> float:
    """Check stored pair ratio against finite, positive raw arm times."""
    values = (reference_ms, candidate_ms, stated_ratio)
    if any(not isinstance(value, (int, float)) or isinstance(value, bool)
           or not math.isfinite(value) for value in values):
        raise ValueError("arm times and pair ratio must be finite numbers")
    if reference_ms <= 0 or candidate_ms <= 0 or stated_ratio <= 0:
        raise ValueError("arm times and pair ratio must be positive")
    ratio = float(reference_ms) / float(candidate_ms)
    if not math.isclose(float(stated_ratio), ratio, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("pair speedup does not match raw arm times")
    return ratio


def _safe_members(tf: tarfile.TarFile):
    files = {}
    roots = set()
    seen = set()
    for member in tf.getmembers():
        p = pathlib.PurePosixPath(member.name)
        if p.is_absolute() or ".." in p.parts or not p.parts:
            raise ValueError(f"unsafe archive path: {member.name!r}")
        if member.name in seen:
            raise ValueError(f"duplicate archive path: {member.name!r}")
        seen.add(member.name)
        roots.add(p.parts[0])
        if member.issym() or member.islnk() or member.isdev():
            raise ValueError(f"non-regular archive member: {member.name!r}")
        if member.isfile():
            files[member.name] = member
        elif not member.isdir():
            raise ValueError(f"unsupported archive member type: {member.name!r}")
    return roots, files


def _find_rules(root: pathlib.Path, summary: dict):
    hashes = summary.get("artifact_sha256", {})
    candidates = []
    for p in sorted(root.glob("*.json")):
        try:
            rule = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if "aa_acceptance" not in rule:
            continue
        expected = None
        for artifact, digest in hashes.items():
            if artifact.endswith("/" + p.name):
                expected = digest
                break
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if expected == actual:
            candidates.append((p, rule))
    if len(candidates) != 1:
        return None
    return candidates[0]


def audit_archive(archive: pathlib.Path, experiment_dir: pathlib.Path):
    with tarfile.open(archive, "r:gz") as tf:
        roots, members = _safe_members(tf)
        shallow = {}
        for name in members:
            p = pathlib.PurePosixPath(name)
            if len(p.parts) == 2:
                shallow.setdefault(p.parts[0], set()).add(p.parts[1])
        candidate_roots = sorted(root for root, names in shallow.items()
                                  if REQUIRED.issubset(names))
        if len(candidate_roots) != 1:
            return {"archive": archive.name, "supported": False,
                    "reason": "missing standard panel ledger files"}
        root = candidate_roots[0]
        by_basename = {pathlib.PurePosixPath(name).name: info for name, info in members.items()
                       if pathlib.PurePosixPath(name).parts[0] == root
                       and len(pathlib.PurePosixPath(name).parts) == 2}

        def read(name):
            return tf.extractfile(by_basename[name]).read()

        manifest = _json(read("manifest.json"), "manifest.json")
        summary = _json(read("summary.json"), "summary.json")
        runs = _jsonl(read("runs.jsonl"), "runs.jsonl")
        pairs = _jsonl(read("pairs.jsonl"), "pairs.jsonl")

    manifest_digest = hashlib.sha256(read_bytes_from_archive(archive, root + "/manifest.json")).hexdigest()
    if summary.get("manifest_sha256") and summary["manifest_sha256"] != manifest_digest:
        raise ValueError("summary manifest_sha256 does not match archived manifest")
    rules_match = _find_rules(experiment_dir, summary)
    if rules_match is None:
        return {"archive": archive.name, "supported": False,
                "reason": "no unique local rules file matches an archived artifact hash",
                "runs": len(runs), "pairs": len(pairs)}
    rules_path, rules = rules_match
    aa_limits = rules["aa_acceptance"]
    if (not isinstance(aa_limits, list) or len(aa_limits) != 2
            or any(not isinstance(x, (int, float)) or isinstance(x, bool)
                   or not math.isfinite(x) for x in aa_limits)
            or aa_limits[0] > aa_limits[1]):
        raise ValueError(f"invalid A/A acceptance in {rules_path.name}")

    cases = {row["id"]: row for row in manifest.get("cases", [])}
    if not cases or len(cases) != len(manifest.get("cases", [])):
        raise ValueError("manifest cases missing or duplicated")
    run_by_serial = {}
    for run in runs:
        serial = run.get("serial")
        if not isinstance(serial, int) or serial in run_by_serial:
            raise ValueError("run serials missing, noninteger, or duplicated")
        if run.get("case") not in cases or run.get("variant") not in ("reference", "candidate"):
            raise ValueError(f"run {serial} has unknown case or variant")
        if run.get("command") != cases[run["case"]].get(run["variant"]):
            raise ValueError(f"run {serial} command differs from its manifest arm")
        if run.get("status") != "valid" or run.get("issues") or run.get("timed_out") or run.get("returncode") != 0:
            raise ValueError(f"run {serial} is not a valid successful arm")
        timing = run.get("online_ms")
        field_timing = (run.get("fields") or {}).get("online_ms")
        if (not isinstance(timing, (int, float)) or isinstance(timing, bool)
                or not math.isfinite(timing) or timing <= 0):
            raise ValueError(f"run {serial} online_ms must be finite and positive")
        if field_timing is None or not math.isfinite(float(field_timing)) or not math.isclose(
                float(field_timing), float(timing), rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"run {serial} fields.online_ms disagrees with online_ms")
        run_by_serial[serial] = run

    pair_index = {}
    ratio_by_key = {}
    serial_uses = Counter()
    for pair in pairs:
        key = (pair.get("repeat"), pair.get("case"))
        if (not isinstance(key[0], int) or isinstance(key[0], bool)
                or key in pair_index or key[1] not in cases):
            raise ValueError(f"duplicate or unknown pair key {key!r}")
        refs = pair.get("run_serials")
        if not isinstance(refs, dict) or set(refs) != {"reference", "candidate"}:
            raise ValueError(f"pair {key!r} lacks exact reference/candidate serial mapping")
        try:
            ref = run_by_serial[refs["reference"]]
            cand = run_by_serial[refs["candidate"]]
        except KeyError as exc:
            raise ValueError(f"pair {key!r} refers to missing run serial") from exc
        for variant, run in (("reference", ref), ("candidate", cand)):
            if run["variant"] != variant or (run["repeat"], run["case"]) != key:
                raise ValueError(f"pair {key!r} serial mapping has mismatched identity")
            serial_uses[run["serial"]] += 1
        stated = pair.get("speedup")
        try:
            ratio = recompute_pair_ratio(ref["online_ms"], cand["online_ms"], stated)
        except ValueError as exc:
            raise ValueError(f"pair {key!r}: {exc}") from exc
        if pair.get("status") != "valid" or pair.get("issues"):
            raise ValueError(f"pair {key!r} is not marked valid")
        pair_index[key] = pair
        ratio_by_key[key] = ratio

    if len(serial_uses) != len(run_by_serial) or any(n != 1 for n in serial_uses.values()):
        raise ValueError("run serials are not covered exactly once by pairs")
    expected_keys = {(r, case) for r in range(int(rules["repetitions"])) for case in cases}
    if set(pair_index) != expected_keys:
        raise ValueError(f"pair-key coverage differs from rules/manifest: expected {len(expected_keys)}, got {len(pair_index)}")
    for count_field in ("valid_pairs", "expected_pairs"):
        if count_field in summary and summary[count_field] != len(pairs):
            raise ValueError(f"summary {count_field} differs from pair ledger")

    calibration = sorted(name for name in cases if name.startswith(CALIBRATION_PREFIX))
    if not calibration:
        return {"archive": archive.name, "supported": False,
                "reason": "no calibration cases to enforce A/A", "runs": len(runs), "pairs": len(pairs)}
    aa_outside = []
    low, high = map(float, aa_limits)
    for repeat in range(int(rules["repetitions"])):
        for case in calibration:
            ratio = ratio_by_key[(repeat, case)]
            if not low <= ratio <= high:
                aa_outside.append({"repeat": repeat, "case": case, "ratio": ratio})
    aa_passed = not aa_outside
    return {
        "archive": archive.name, "supported": True,
        "rules": rules_path.name, "runs": len(runs), "pairs": len(pairs),
        "cases": sorted(cases), "calibration_cases": calibration,
        "ratio_rows_recomputed": len(ratio_by_key),
        "aa_acceptance": [low, high], "aa_failures": aa_outside,
        "aa_passed": aa_passed,
        "a_a_is_required_for_either_direction": True,
    }


def read_bytes_from_archive(archive: pathlib.Path, member_name: str) -> bytes:
    with tarfile.open(archive, "r:gz") as tf:
        return tf.extractfile(member_name).read()


def audit_directory(experiment_dir: pathlib.Path):
    results = []
    for archive in sorted(experiment_dir.glob("*.tar.gz")):
        try:
            results.append(audit_archive(archive, experiment_dir))
        except Exception as exc:
            results.append({"archive": archive.name, "supported": False,
                            "reason": f"validation error: {type(exc).__name__}: {exc}"})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", type=pathlib.Path,
                        default=pathlib.Path(__file__).parent)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = audit_directory(args.directory)
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        supported = sum(row["supported"] for row in results)
        print(f"archives={len(results)} supported={supported} unsupported={len(results)-supported}")
        for row in results:
            state = "PASS" if row["supported"] else "UNSUPPORTED"
            detail = row.get("reason") or f"runs={row.get('runs', '?')} pairs={row.get('pairs', '?')} A/A={'pass' if row.get('aa_passed') else 'fail'}"
            print(f"{state}\t{row['archive']}\t{detail}")
    return 0 if results and all(row["supported"] or "reason" in row for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
