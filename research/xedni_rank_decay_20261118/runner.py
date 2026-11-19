#!/usr/bin/env python3
"""Fail-closed planning and control integration for the Xedni decay panel.

``plan`` is read-only. ``preflight-natural`` validates a committed freeze,
required tools, and the r<=6 map boundary before invoking the mandatory resume
checkpoint gate.  This module intentionally has no natural-row command yet:
the retained source evidence and bounded relation proposer are not yet wired
through a freeze-bound public/evaluator process boundary into analysis rows.
Controls can exercise the complete source/local/lift/rank interface via
``run_control`` but are permanently marked ineligible for inference.

Production calls must use the frozen PARI container wrapper (or an equally
exact-hash wrapper around the immutable image ID); a mutable host ``gp`` is not
accepted merely because its banner looks compatible.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import lift_builder
import local_conditions
import prime_manifest
import rank_magma
import rank_pari
import source_generator


SCHEMA = "xedni.rank-decay-runner/v1"
ROSTER_SCHEMA = "xedni.rank-decay-roster/v1"
CONTROL_SCHEMA = "xedni.rank-decay-control-row/v1"
MASTER_SEED = "xedni-rank-decay-20261118-v1"
FAMILIES = ("generic", "j0")
R_VALUES = tuple(range(2, 10))
EXECUTABLE_R_VALUES = tuple(range(2, 7))
LIFTS = ("balanced", "wide", "optimized")
LOCAL_ARMS = ("A_none", "B_reverse_mestre", "P_neutral_crt")
STAGES = {
    "calibration": {"bits": (16, 18), "trials": 2},
    "sentinel": {"bits": tuple(range(16, 33, 2)), "trials": 5},
}
BLOCKED_STAGES = {
    "controls": "controls use named synthetic/known-rank fixtures, not natural roster rows",
    "discovery": "discovery exposure/resource allocation is not committed",
    "replication": "replication trigger, fresh seed, and fresh prime manifest are not committed",
    "mechanisms": (
        "M1-M6 banks/selectors/direct-source baselines and required M4/M5 maps "
        "are not integrated into natural execution"
    ),
}
PARI_TIERS = ((60.0, 0), (300.0, 1))
MAGMA_TIERS = ((300.0, 1), (1800.0, 2))
CHECKPOINT_TIMEOUT_SECONDS = 600.0
DEFAULT_GP = str(HERE / "gp_container_wrapper.sh")
NATURAL_IMPLEMENTATION_GAPS = (
    "relation proposer/certificate outcomes are not integrated into natural rows",
    "no hash-linked public/evaluator subprocess boundary prevents source-scalar access by construction",
    "M1-M6 natural banks/selectors/direct-source baselines and M4/M5 map gates are not integrated",
)
REQUIRED_FROZEN_FILES = (
    "research/xedni_rank_decay_20261118/PROTOCOL.md",
    "research/xedni_rank_decay_20261118/AMENDMENT.md",
    "research/xedni_rank_decay_20261118/PRIMES.json",
    "research/xedni_rank_decay_20261118/HARDWARE.json",
    "research/xedni_rank_decay_20261118/prime_manifest.py",
    "research/xedni_rank_decay_20261118/field.py",
    "research/xedni_rank_decay_20261118/source_generator.py",
    "research/xedni_rank_decay_20261118/gp_container_wrapper.sh",
    "research/xedni_rank_decay_20261118/local_conditions.py",
    "research/xedni_rank_decay_20261118/lift_builder.py",
    "research/xedni_rank_decay_20261118/rank_pari.py",
    "research/xedni_rank_decay_20261118/rank_magma.py",
    "research/xedni_rank_decay_20261118/analyze.py",
    "research/xedni_rank_decay_20261118/sensitivity.py",
    "research/xedni_rank_decay_20261118/mechanism_panels.py",
    "research/xedni_rank_decay_20261118/invariants_pari.py",
    "research/xedni_rank_decay_20261118/relation_certificate.py",
    "research/xedni_rank_decay_20261118/relation_pari.py",
    "research/xedni_rank_decay_20261118/runner.py",
    "research/xedni_lift_success_20261112/sweep.py",
)


class RunnerError(RuntimeError):
    """Preflight/control error that retains its complete evidence record."""

    def __init__(self, code: str, message: str, evidence: dict | None = None):
        super().__init__(message)
        self.code = code
        self.evidence = {} if evidence is None else evidence


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _retained_file_hash(relative: str) -> str:
    path = REPOSITORY / relative
    return file_sha256(path) if path.is_file() else "MISSING"


def _manifest_rows(path: Path | None = None) -> list[dict]:
    manifest_path = HERE / "PRIMES.json" if path is None else path
    try:
        manifest = json.loads(manifest_path.read_text())
        prime_manifest.validate(manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise RunnerError("prime_manifest", f"prime manifest validation failed: {error}") from error
    return copy.deepcopy(manifest["primes"])


def validate_source_cardinality_evidence(source: dict) -> dict:
    """Replay the retained cardinality transcript/accounting envelope."""
    evidence = source.get("cardinality_evidence") if isinstance(source, dict) else None
    if not isinstance(evidence, dict):
        raise RunnerError(
            "source_cardinality_evidence",
            "natural source record lacks cardinality evidence",
        )
    errors = []
    if (
        evidence.get("status") != "complete"
        or evidence.get("returncode") != 0
        or evidence.get("timed_out") is not False
    ):
        errors.append("completion")
    command = evidence.get("command")
    program = evidence.get("program")
    stdout = evidence.get("stdout")
    stderr = evidence.get("stderr")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(item, str) or not item for item in command)
        or command[-2:] != ["-q", "-f"]
    ):
        errors.append("command")
    for name, value in (("program", program), ("stdout", stdout), ("stderr", stderr)):
        if not isinstance(value, str):
            errors.append(name)
    if isinstance(program, str) and evidence.get("program_sha256") != hashlib.sha256(
        program.encode()
    ).hexdigest():
        errors.append("program_sha256")
    try:
        curve = source.get("curve")
        if not isinstance(curve, dict):
            raise ValueError("curve")
        p, a, b = source.get("p"), curve.get("a"), curve.get("b")
        expected_program = source_generator.cardinality_program(p, a, b)
    except (TypeError, ValueError):
        expected_program = None
        errors.append("source_curve")
    if not isinstance(program, str) or program != expected_program:
        errors.append("program_replay")
    if isinstance(stdout, str) and evidence.get("stdout_sha256") != hashlib.sha256(
        stdout.encode()
    ).hexdigest():
        errors.append("stdout_sha256")
    if isinstance(stderr, str) and evidence.get("stderr_sha256") != hashlib.sha256(
        stderr.encode()
    ).hexdigest():
        errors.append("stderr_sha256")
    wall_ns = evidence.get("wall_ns")
    if isinstance(wall_ns, bool) or not isinstance(wall_ns, int) or wall_ns < 0:
        errors.append("wall_ns")
    retained = dict(evidence)
    retained_hash = retained.pop("evidence_sha256", None)
    if retained_hash != object_sha256(retained):
        errors.append("evidence_sha256")
    lines = [line.strip() for line in stdout.splitlines() if line.strip()] if isinstance(stdout, str) else []
    if not lines or not re.fullmatch(r"[0-9]+", lines[0]) or int(lines[0]) != source.get(
        "cardinality"
    ):
        errors.append("cardinality_replay")
    raw_factors = source.get("cardinality_factors")
    expected_factors = (
        [tuple(item) for item in raw_factors]
        if isinstance(raw_factors, list)
        and all(isinstance(item, list) and len(item) == 2 for item in raw_factors)
        else []
    )
    try:
        source_generator.validate_factorization(source.get("cardinality"), expected_factors)
    except (TypeError, ValueError):
        errors.append("source_factorization")
    transcript_factors = []
    for line in lines[1:]:
        match = re.fullmatch(r"([0-9]+)\s+([0-9]+)", line)
        if match is None:
            errors.append("factor_transcript")
            break
        transcript_factors.append((int(match.group(1)), int(match.group(2))))
    if transcript_factors != expected_factors:
        errors.append("factor_replay")
    identity = evidence.get("tool_identity")
    if not isinstance(identity, dict):
        errors.append("tool_identity")
    elif identity.get("kind") == "host_executable":
        if not re.fullmatch(r"[0-9a-f]{64}", str(identity.get("executable_sha256", ""))):
            errors.append("tool_executable_sha256")
        version_transcript = str(identity.get("version_stdout", "")) + "\n" + str(
            identity.get("version_stderr", "")
        )
        if identity.get("version_returncode") != 0 or not re.search(
            r"GP/PARI\s+CALCULATOR\s+Version\s+[0-9]+(?:\.[0-9]+)+",
            version_transcript,
            re.IGNORECASE,
        ):
            errors.append("tool_version")
        if not re.fullmatch(
            r"sha256:[0-9a-fA-F]{64}", str(identity.get("wrapper_image_id", ""))
        ):
            errors.append("wrapper_image_id")
    elif identity.get("kind") == "container":
        if identity.get("image_is_digest_pinned") is not True:
            errors.append("container_image_not_digest_pinned")
        if not re.fullmatch(
            r"(?:[^@\s]+@)?sha256:[0-9a-fA-F]{64}",
            str(identity.get("image", "")),
        ):
            errors.append("container_image")
        if identity.get("image_inspect_returncode") != 0 or not re.fullmatch(
            r"sha256:[0-9a-fA-F]{64}", str(identity.get("observed_image_id", ""))
        ):
            errors.append("container_image_inspect")
        if str(identity.get("image", "")).startswith("sha256:") and identity.get(
            "exact_image_id_matches"
        ) is not True:
            errors.append("container_exact_image_id_mismatch")
    else:
        errors.append("tool_identity_kind")
    result = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "evidence_sha256": evidence.get("evidence_sha256"),
    }
    if errors:
        raise RunnerError(
            "source_cardinality_evidence",
            "source cardinality evidence failed replay",
            result,
        )
    return result


def _row_id(row: dict) -> str:
    return (
        f"{row['stage']}|b={row['bits']}|slot={row['slot']}|p={row['p']}|"
        f"family={row['family']}|r={row['r']}|lift={row['lift']}|"
        f"local={row['local_arm']}|index={row['index']}"
    )


def build_roster(stage: str, manifest_path: Path | None = None) -> dict:
    """Build the deterministic natural-row manifest without executing a row."""
    if stage in BLOCKED_STAGES:
        base = {
            "schema": ROSTER_SCHEMA,
            "stage": stage,
            "status": "BLOCKED",
            "reason": BLOCKED_STAGES[stage],
            "executable_roster": [],
            "blocked_roster": [],
            "counts": {"executable": 0, "blocked": 0},
            "source_master_seed": f"{MASTER_SEED}|stage={stage}",
            "input_hashes": {
                "PROTOCOL.md": _retained_file_hash(
                    "research/xedni_rank_decay_20261118/PROTOCOL.md"
                ),
                "AMENDMENT.md": _retained_file_hash(
                    "research/xedni_rank_decay_20261118/AMENDMENT.md"
                ),
                "PRIMES.json": _retained_file_hash(
                    "research/xedni_rank_decay_20261118/PRIMES.json"
                ),
            },
        }
        base["roster_sha256"] = object_sha256(base)
        return base
    if stage not in STAGES:
        raise RunnerError("stage", f"unknown stage {stage!r}")
    specification = STAGES[stage]
    manifest_rows = [
        row for row in _manifest_rows(manifest_path) if row["bits"] in specification["bits"]
    ]
    executable = []
    blocked = []
    source_master_seed = f"{MASTER_SEED}|stage={stage}"
    for prime_row in manifest_rows:
        for family in FAMILIES:
            for r in R_VALUES:
                for lift in LIFTS:
                    for local_arm in LOCAL_ARMS:
                        for index in range(specification["trials"]):
                            source_key = (
                                f"{stage}|p={prime_row['prime']}|family={family}|index={index}"
                            )
                            row = {
                                "stage": stage,
                                "bits": prime_row["bits"],
                                "slot": prime_row["slot"],
                                "p": prime_row["prime"],
                                "family": family,
                                "r": r,
                                "lift": lift,
                                "local_arm": local_arm,
                                "index": index,
                                "source_key": source_key,
                                "source_index": index,
                                "source_master_seed": source_master_seed,
                                "local_seed": (
                                    f"{MASTER_SEED}|local|{source_key}|r={r}|arm={local_arm}"
                                ),
                            }
                            row["row_id"] = _row_id(row)
                            if r in EXECUTABLE_R_VALUES:
                                row["status"] = "PLANNED"
                                executable.append(row)
                            else:
                                row["status"] = "BLOCKED"
                                row["block_reason"] = (
                                    "r>=7 has no certified plane-cubic-to-Jacobian point map"
                                )
                                blocked.append(row)
    base = {
        "schema": ROSTER_SCHEMA,
        "stage": stage,
        "status": "PLANNED_NO_NATURAL_ROWS_RUN",
        "factors": {
            "bits": list(specification["bits"]),
            "prime_slots": [0, 1, 2],
            "families": list(FAMILIES),
            "r_values": list(R_VALUES),
            "lifts": list(LIFTS),
            "local_arms": list(LOCAL_ARMS),
            "trials_per_cell": specification["trials"],
        },
        "source_master_seed": source_master_seed,
        "executable_roster": executable,
        "blocked_roster": blocked,
        "counts": {"executable": len(executable), "blocked": len(blocked)},
        "input_hashes": {
            "PROTOCOL.md": _retained_file_hash(
                "research/xedni_rank_decay_20261118/PROTOCOL.md"
            ),
            "AMENDMENT.md": _retained_file_hash(
                "research/xedni_rank_decay_20261118/AMENDMENT.md"
            ),
            "PRIMES.json": _retained_file_hash(
                "research/xedni_rank_decay_20261118/PRIMES.json"
            ),
        },
    }
    base["roster_sha256"] = object_sha256(base)
    return base


def _git_file_state(relative: str) -> dict:
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=False,
    )
    changed = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", relative],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "path": relative,
        "tracked": tracked.returncode == 0,
        "clean_against_head": changed.returncode == 0,
        "ls_files_returncode": tracked.returncode,
        "diff_returncode": changed.returncode,
    }


def validate_freeze(
    freeze_path: Path,
    stage: str,
    roster: dict,
    ca_icx: str | Path,
) -> dict:
    """Validate hashes, committed state, roster binding, and exact tool pins."""
    if not freeze_path.is_file():
        raise RunnerError("freeze_missing", f"natural run requires {freeze_path}")
    try:
        freeze = json.loads(freeze_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise RunnerError("freeze_json", f"cannot parse freeze: {error}") from error
    if not isinstance(freeze, dict):
        raise RunnerError("freeze_schema", "freeze root must be a JSON object")
    if freeze.get("natural_rows_authorized") is not True:
        raise RunnerError(
            "natural_rows_not_authorized",
            "freeze must set natural_rows_authorized=true before any natural preflight",
            {
                "path": str(freeze_path),
                "sha256": file_sha256(freeze_path),
                "natural_rows_authorized": freeze.get("natural_rows_authorized"),
            },
        )
    evidence = {
        "path": str(freeze_path),
        "sha256": file_sha256(freeze_path),
        "stage": stage,
        "roster_sha256": roster["roster_sha256"],
        "checks": [],
    }
    files = freeze.get("files")
    if not isinstance(files, dict):
        raise RunnerError("freeze_schema", "freeze.files must be a hash map", evidence)
    errors = []
    for relative in REQUIRED_FROZEN_FILES:
        actual_path = REPOSITORY / relative
        actual_hash = file_sha256(actual_path) if actual_path.is_file() else None
        state = _git_file_state(relative)
        check = {
            **state,
            "expected_sha256": files.get(relative),
            "actual_sha256": actual_hash,
        }
        evidence["checks"].append(check)
        if files.get(relative) != actual_hash or not state["tracked"] or not state["clean_against_head"]:
            errors.append(relative)
    try:
        freeze_relative = str(freeze_path.resolve().relative_to(REPOSITORY))
    except ValueError as error:
        raise RunnerError(
            "freeze_path", "freeze must be inside the repository", evidence
        ) from error
    freeze_state = _git_file_state(freeze_relative)
    evidence["freeze_git_state"] = freeze_state
    if not freeze_state["tracked"] or not freeze_state["clean_against_head"]:
        errors.append(freeze_relative)
    frozen_roster = freeze.get("rosters", {}).get(stage, {})
    if frozen_roster.get("sha256") != roster["roster_sha256"]:
        errors.append(f"roster:{stage}")
    if freeze.get("master_seed") != MASTER_SEED:
        errors.append("master_seed")
    binary_path = Path(ca_icx).expanduser().resolve()
    if not Path(ca_icx).expanduser().is_absolute():
        binary_path = (REPOSITORY / Path(ca_icx).expanduser()).resolve()
    binary_hash = file_sha256(binary_path) if binary_path.is_file() else None
    evidence["binary"] = {"path": str(binary_path), "sha256": binary_hash}
    frozen_binary = freeze.get("binary", {})
    if frozen_binary.get("sha256") != binary_hash:
        errors.append("ca_icx_binary")
    tools = freeze.get("tools", {})
    for name in ("pari", "magma"):
        pin = tools.get(name)
        has_version = isinstance(pin, dict) and isinstance(pin.get("version"), str) and bool(
            pin["version"]
        )
        has_identity = isinstance(pin, dict) and any(
            isinstance(pin.get(key), str) and pin[key]
            for key in ("image_digest", "executable_sha256")
        )
        if not has_version or not has_identity:
            errors.append(f"tool_pin:{name}")
    if errors:
        evidence["errors"] = errors
        raise RunnerError("freeze_mismatch", "freeze validation failed", evidence)
    evidence["status"] = "PASS"
    evidence["freeze"] = freeze
    return evidence


def _tool_is_available(tool: dict, marker: str | None = None) -> bool:
    if not isinstance(tool, dict) or tool.get("available") is not True:
        return False
    if tool.get("version_returncode") != 0 or tool.get("version_timed_out") is not False:
        return False
    transcript = tool.get("version_stdout", "") + "\n" + tool.get(
        "version_stderr", ""
    )
    if marker is not None and marker not in transcript:
        return False
    return True


def _parsed_tool_version(name: str, observed: dict) -> str | None:
    transcript = observed.get("version_stdout", "") + "\n" + observed.get(
        "version_stderr", ""
    )
    if name == "magma":
        match = re.search(r"XEDNI_MAGMA_VERSION=([^\s]+)", transcript)
    elif name == "pari":
        match = re.search(
            r"(?:GP/PARI\s+CALCULATOR\s+)?Version\s+"
            r"([0-9]+(?:\.[0-9]+)+(?:-[0-9]+)?)",
            transcript,
            re.IGNORECASE,
        )
    else:
        return None
    return None if match is None else match.group(1)


def _match_tool_pin(name: str, pin: dict, observed: dict) -> dict:
    """Match a frozen identity to the observed probe; nonempty is not enough."""
    checks = []
    errors = []
    expected_version = pin.get("version")
    if isinstance(expected_version, str) and expected_version:
        actual_version = _parsed_tool_version(name, observed)
        matched = expected_version.strip() == actual_version
        checks.append(
            {
                "field": "version",
                "expected": expected_version,
                "observed": actual_version,
                "matched": matched,
            }
        )
        if not matched:
            errors.append("version")
    expected_path = pin.get("executable_resolved") or pin.get("path")
    if isinstance(expected_path, str) and expected_path:
        actual_path = observed.get("executable_resolved")
        matched = (
            actual_path is not None
            and Path(actual_path).resolve() == Path(expected_path).resolve()
        )
        checks.append(
            {
                "field": "executable_resolved",
                "expected": expected_path,
                "observed": actual_path,
                "matched": matched,
            }
        )
        if not matched:
            errors.append("executable_resolved")
    expected_hash = pin.get("executable_sha256")
    if isinstance(expected_hash, str) and expected_hash:
        actual_path = observed.get("executable_resolved")
        actual_hash = (
            file_sha256(Path(actual_path))
            if isinstance(actual_path, str) and Path(actual_path).is_file()
            else None
        )
        matched = actual_hash == expected_hash
        checks.append(
            {
                "field": "executable_sha256",
                "expected": expected_hash,
                "observed": actual_hash,
                "matched": matched,
            }
        )
        if not matched:
            errors.append("executable_sha256")
    expected_image = pin.get("image_digest")
    if isinstance(expected_image, str) and expected_image:
        actual_image = observed.get("image_digest")
        matched = actual_image == expected_image
        checks.append(
            {
                "field": "image_digest",
                "expected": expected_image,
                "observed": actual_image,
                "matched": matched,
            }
        )
        if not matched:
            errors.append("image_digest")
    if not checks:
        errors.append("no_comparable_identity")
    result = {"tool": name, "checks": checks, "errors": errors}
    if errors:
        raise RunnerError(
            "tool_pin_mismatch", f"{name} does not match its freeze pin", result
        )
    result["status"] = "PASS"
    return result


def checkpoint_gate(
    script: Path | None = None,
    timeout_seconds: float = CHECKPOINT_TIMEOUT_SECONDS,
) -> dict:
    """Invoke the real resume gate; there is deliberately no skip option."""
    gate_script = REPOSITORY / "scripts/checkpoint.sh" if script is None else script
    command = [str(gate_script), "gate"]
    started = time.perf_counter_ns()
    try:
        completed = subprocess.run(
            command,
            cwd=REPOSITORY,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        timed_out = False
        stdout, stderr = completed.stdout, completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout = "" if error.stdout is None else str(error.stdout)
        stderr = "" if error.stderr is None else str(error.stderr)
        returncode = None
    except OSError as error:
        evidence = {
            "command": command,
            "cwd": str(REPOSITORY),
            "returncode": None,
            "stdout": "",
            "stdout_sha256": hashlib.sha256(b"").hexdigest(),
            "stderr": f"{type(error).__name__}: {error}",
            "stderr_sha256": hashlib.sha256(
                f"{type(error).__name__}: {error}".encode()
            ).hexdigest(),
            "timed_out": False,
            "timeout_seconds": timeout_seconds,
            "wall_ns": time.perf_counter_ns() - started,
        }
        raise RunnerError(
            "checkpoint_gate", "mandatory checkpoint gate could not launch", evidence
        ) from error
    evidence = {
        "command": command,
        "cwd": str(REPOSITORY),
        "returncode": returncode,
        "stdout": stdout,
        "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr": stderr,
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "wall_ns": time.perf_counter_ns() - started,
    }
    if timed_out or returncode != 0:
        raise RunnerError("checkpoint_gate", "mandatory checkpoint gate failed", evidence)
    evidence["status"] = "PASS"
    return evidence


def _preflight_core(
    stage: str,
    r_values: tuple[int, ...],
    *,
    freeze_path: Path,
    ca_icx: str | Path,
    gp: str,
    magma: str,
    freeze_check: Callable[..., dict],
    pari_probe: Callable[[str], dict],
    magma_probe: Callable[[str], dict],
    gate_check: Callable[[], dict],
) -> dict:
    roster = build_roster(stage)
    evidence = {
        "schema": SCHEMA,
        "operation": "natural_preflight",
        "stage": stage,
        "requested_r_values": list(r_values),
        "roster_sha256": roster["roster_sha256"],
        "natural_rows_started": 0,
    }
    evidence["freeze"] = freeze_check(freeze_path, stage, roster, ca_icx)
    if (
        not r_values
        or any(isinstance(r, bool) or not isinstance(r, int) for r in r_values)
        or len(set(r_values)) != len(r_values)
    ):
        raise RunnerError(
            "r_values", "r_values must be a nonempty duplicate-free integer tuple", evidence
        )
    invalid_r = [r for r in r_values if r not in EXECUTABLE_R_VALUES]
    if invalid_r:
        evidence["blocked_r_values"] = invalid_r
        raise RunnerError(
            "missing_point_map",
            "r>=7 cannot enter natural execution without a certified point map",
            evidence,
        )
    magma_tool = magma_probe(magma)
    evidence["magma_tool"] = magma_tool
    if not _tool_is_available(magma_tool, "XEDNI_MAGMA_VERSION="):
        raise RunnerError("magma_unavailable", "licensed Magma probe failed", evidence)
    pari_tool = pari_probe(gp)
    evidence["pari_tool"] = pari_tool
    if not _tool_is_available(pari_tool, "PARI"):
        raise RunnerError("pari_unavailable", "PARI/GP probe failed", evidence)
    frozen_tools = evidence["freeze"].get("freeze", {}).get("tools", {})
    try:
        evidence["tool_pin_checks"] = {
            "magma": _match_tool_pin(
                "magma", frozen_tools.get("magma", {}), magma_tool
            ),
            "pari": _match_tool_pin(
                "pari", frozen_tools.get("pari", {}), pari_tool
            ),
        }
    except RunnerError as error:
        evidence["tool_pin_failure"] = error.evidence
        raise RunnerError(error.code, str(error), evidence) from error
    evidence["checkpoint"] = gate_check()
    evidence["status"] = "BLOCKED_NO_NATURAL_EXECUTOR"
    evidence["implementation_gaps"] = list(NATURAL_IMPLEMENTATION_GAPS)
    evidence["preflight_sha256"] = object_sha256(evidence)
    return evidence


def natural_preflight(
    stage: str,
    *,
    freeze_path: Path | None = None,
    ca_icx: str | Path = "suite/target/release/ca-icx",
    gp: str = DEFAULT_GP,
    magma: str = "magma",
    r_values: tuple[int, ...] = EXECUTABLE_R_VALUES,
) -> dict:
    """Production preflight. No dependency injection or gate bypass is exposed."""
    selected_freeze = HERE / "FREEZE.json" if freeze_path is None else freeze_path
    return _preflight_core(
        stage,
        r_values,
        freeze_path=selected_freeze,
        ca_icx=ca_icx,
        gp=gp,
        magma=magma,
        freeze_check=validate_freeze,
        pari_probe=rank_pari.probe_tool,
        magma_probe=rank_magma.probe_tool,
        gate_check=checkpoint_gate,
    )


def _valid_interval(result: dict) -> tuple[int, int] | None:
    bounds = result.get("rank_bounds") if isinstance(result, dict) else None
    if not isinstance(bounds, dict):
        return None
    lower, upper = bounds.get("lower"), bounds.get("upper")
    if (
        isinstance(lower, bool)
        or isinstance(upper, bool)
        or not isinstance(lower, int)
        or not isinstance(upper, int)
        or lower < 0
        or lower > upper
    ):
        return None
    return lower, upper


def _validated_tool_class(
    result: dict,
    r: int,
    *,
    tool_name: str,
    row: dict,
    tool: dict,
    effort: int,
    timeout: float,
) -> tuple[str, tuple[int, int] | None, str]:
    """Recompute a class only after binding the adapter evidence to its call."""
    module = rank_pari if tool_name == "pari" else rank_magma
    try:
        row_id, expected_r, ainvs = rank_pari.validate_row(row)
    except ValueError:
        return "UNKNOWN", None, "invalid_rank_row"
    binding_checks = {
        "adapter": result.get("adapter") == module.ADAPTER,
        "schema_version": result.get("schema_version") == module.SCHEMA_VERSION,
        "row_id": result.get("row_id") == row_id,
        "r": result.get("r") == expected_r == r,
        "ainvs": result.get("ainvs") == [str(value) for value in ainvs],
        "input_sha256": result.get("input_sha256") == object_sha256(row),
        "tool": result.get("tool") == tool,
    }
    failed = sorted(name for name, passed in binding_checks.items() if not passed)
    if failed:
        return "UNKNOWN", None, "adapter_binding_mismatch:" + ",".join(failed)
    execution = result.get("execution")
    if execution is not None:
        if not isinstance(execution, dict):
            return "UNKNOWN", None, "adapter_execution_malformed"
        expected_script = (
            rank_pari.make_script(ainvs, effort)
            if tool_name == "pari"
            else rank_magma.make_script(ainvs, effort)
        )
        expected_command = [
            tool.get("executable_resolved"),
            "-q" if tool_name == "pari" else "-b",
        ]
        if tool_name == "pari":
            expected_command.append("-f")
        execution_checks = {
            "command": execution.get("command") == expected_command,
            "script": execution.get("script") == expected_script,
            "script_sha256": execution.get("script_sha256")
            == hashlib.sha256(expected_script.encode()).hexdigest(),
            "timeout_seconds": execution.get("timeout_seconds") == timeout,
            "timed_out": isinstance(execution.get("timed_out"), bool),
            "stdout": isinstance(execution.get("stdout"), str),
            "stderr": isinstance(execution.get("stderr"), str),
            "wall_ns": (
                isinstance(execution.get("wall_ns"), int)
                and not isinstance(execution.get("wall_ns"), bool)
                and execution["wall_ns"] >= 0
            ),
        }
        failed = sorted(
            name for name, passed in execution_checks.items() if not passed
        )
        if failed:
            return "UNKNOWN", None, "adapter_execution_mismatch:" + ",".join(failed)
    interval = _valid_interval(result)
    if interval is None:
        return "UNKNOWN", None, "missing_or_invalid_bounds"
    if (
        execution is None
        or execution.get("returncode") != 0
        or execution.get("timed_out") is not False
    ):
        return "UNKNOWN", None, "bounds_without_successful_execution"
    try:
        parsed = module.parse_transcript(execution["stdout"])
    except (KeyError, TypeError, ValueError):
        return "UNKNOWN", None, "rank_transcript_replay_failed"
    if (parsed.get("LOWER"), parsed.get("UPPER")) != interval:
        return "UNKNOWN", None, "rank_transcript_bounds_mismatch"
    if tool_name == "pari" and parsed.get("PARISIZEMAX") != rank_pari.DEFAULT_PARISIZEMAX:
        return "UNKNOWN", None, "rank_transcript_parisizemax_mismatch"
    computed, computed_reason = rank_pari.classify(interval[0], interval[1], r)
    if (
        result.get("classification") != computed
        or result.get("reason") != computed_reason
    ):
        return "UNKNOWN", None, "adapter_classification_mismatch"
    return computed, interval, computed_reason


def rank_cascade(
    row: dict,
    pari_tool: dict,
    magma_tool: dict,
    *,
    pari_process: Callable[..., dict] = rank_pari.process_row,
    magma_process: Callable[..., dict] = rank_magma.process_row,
) -> dict:
    """Run frozen PARI/Magma tiers and retain every adapter transcript."""
    if not _tool_is_available(pari_tool):
        raise RunnerError("pari_unavailable", "PARI tool record is not usable", pari_tool)
    if not _tool_is_available(magma_tool, "XEDNI_MAGMA_VERSION="):
        raise RunnerError("magma_unavailable", "Magma tool record is not usable", magma_tool)
    r = row.get("r")
    try:
        _, r, _ = rank_pari.validate_row(row)
    except ValueError as error:
        raise RunnerError("rank_input", f"rank row is invalid: {error}") from error
    calls: list[dict] = []
    pari_result = None
    pari_class = "UNKNOWN"
    pari_interval = None
    for tier, (timeout, effort) in enumerate(PARI_TIERS, 1):
        pari_result = pari_process(row, pari_tool, timeout, effort)
        pari_class, pari_interval, validation_reason = _validated_tool_class(
            pari_result,
            r,
            tool_name="pari",
            row=row,
            tool=pari_tool,
            effort=effort,
            timeout=timeout,
        )
        calls.append(
            {
                "tool": "pari",
                "tier": tier,
                "timeout_seconds": timeout,
                "effort": effort,
                "result": pari_result,
                "validated_classification": pari_class,
                "validation_reason": validation_reason,
            }
        )
        if pari_class != "UNKNOWN":
            break
    if pari_result is None:
        raise RunnerError("rank_internal", "PARI cascade produced no result")

    magma_result = None
    magma_class = "UNKNOWN"
    magma_interval = None
    if pari_class in {"UNKNOWN", "CERT_LT"}:
        for tier, (timeout, effort) in enumerate(MAGMA_TIERS, 1):
            magma_result = magma_process(row, magma_tool, timeout, effort)
            magma_class, magma_interval, validation_reason = _validated_tool_class(
                magma_result,
                r,
                tool_name="magma",
                row=row,
                tool=magma_tool,
                effort=effort,
                timeout=timeout,
            )
            calls.append(
                {
                    "tool": "magma",
                    "tier": tier,
                    "timeout_seconds": timeout,
                    "effort": effort,
                    "result": magma_result,
                    "validated_classification": magma_class,
                    "validation_reason": validation_reason,
                }
            )
            if magma_class != "UNKNOWN":
                break

    intervals = []
    if pari_interval is not None:
        intervals.append(("pari", *pari_interval))
    if magma_interval is not None:
        intervals.append(("magma", *magma_interval))
    conflict = False
    if intervals:
        lower = max(item[1] for item in intervals)
        upper = min(item[2] for item in intervals)
        conflict = lower > upper
    else:
        lower = upper = None
    same_side = pari_class == magma_class and pari_class in {"CERT_LT", "CERT_GE"}
    if conflict:
        classification, reason = "UNKNOWN", "conflicting_certified_bounds"
    elif pari_class == "CERT_GE":
        classification, reason = "CERT_GE", "pari_certified_lower_at_least_r"
    elif pari_class == "CERT_LT" and magma_class == "CERT_LT":
        classification, reason = "CERT_LT", "apparent_event_confirmed_by_magma"
    elif (
        pari_class == "UNKNOWN"
        and pari_interval is not None
        and magma_class in {"CERT_LT", "CERT_GE"}
        and magma_interval is not None
    ):
        combined_class, _ = rank_pari.classify(lower, upper, r)
        if combined_class == magma_class:
            classification = combined_class
            reason = "magma_side_compatible_with_pari_interval"
        else:
            classification, reason = "UNKNOWN", "combined_interval_unresolved"
    else:
        classification, reason = "UNKNOWN", "required_magma_resolution_missing"
    return {
        "schema": "xedni.rank-cascade/v1",
        "classification": classification,
        "reason": reason,
        "rank_bounds": {"lower": lower, "upper": upper},
        "bound_sources": intervals,
        "conflict": conflict,
        "tool_classifications": {"pari": pari_class, "magma": magma_class},
        "two_tool_agreement": same_side,
        "calls": calls,
        "work": {
            "pari_calls": sum(call["tool"] == "pari" for call in calls),
            "magma_calls": sum(call["tool"] == "magma" for call in calls),
            "timeouts": sum(
                call["result"].get("reason") == "timeout" for call in calls
            ),
        },
    }


def run_control(
    source: dict,
    r: int,
    strategy: str,
    local_config: dict | None,
    pari_tool: dict,
    magma_tool: dict,
    *,
    optimizer: Callable[..., dict] | None = None,
    pari_process: Callable[..., dict] = rank_pari.process_row,
    magma_process: Callable[..., dict] = rank_magma.process_row,
) -> dict:
    """Exercise local/lift/rank integration on a named non-natural fixture."""
    started_wall = time.perf_counter_ns()
    started_cpu = time.process_time_ns()
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    lifted = lift_builder.build_lift(
        source,
        r,
        strategy,
        local_config,
        optimizer=optimizer,
    )
    ranked = rank_cascade(
        lifted,
        pari_tool,
        magma_tool,
        pari_process=pari_process,
        magma_process=magma_process,
    )
    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {
        "schema": CONTROL_SCHEMA,
        "status": "CONTROL_ONLY_NO_NATURAL_ROW",
        "inference_eligible": False,
        "source": copy.deepcopy(source),
        "local_conditions": copy.deepcopy(local_config),
        "lift": lifted,
        "rank": ranked,
        "work": {
            "wall_ns": time.perf_counter_ns() - started_wall,
            "cpu_ns": time.process_time_ns() - started_cpu,
            "max_rss_before": rss_before,
            "max_rss_after": rss_after,
            "source_generation_charged_here": False,
            "local_generation_charged_here": False,
            "lift_cost_counters": lifted["cost_counters"],
            "rank_work": ranked["work"],
        },
        "implementation_gaps": list(NATURAL_IMPLEMENTATION_GAPS),
    }
    result["control_sha256"] = object_sha256(result)
    return result


def _write_json(value: dict, output: Path | None) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
        return
    if output.exists():
        raise RunnerError("output_exists", f"refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as destination:
        destination.write(rendered)
        destination.flush()
        # Plans/preflights are small, so make their retained state durable.
        import os

        os.fsync(destination.fileno())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="read-only deterministic roster")
    plan.add_argument("--stage", choices=tuple(STAGES) + tuple(BLOCKED_STAGES), required=True)
    plan.add_argument("--output", type=Path)
    preflight = subparsers.add_parser(
        "preflight-natural", help="validate freeze/tools and invoke mandatory checkpoint gate"
    )
    preflight.add_argument("--stage", choices=tuple(STAGES), required=True)
    preflight.add_argument("--freeze", type=Path, default=HERE / "FREEZE.json")
    preflight.add_argument("--ca-icx", default="suite/target/release/ca-icx")
    preflight.add_argument("--gp", default=DEFAULT_GP)
    preflight.add_argument("--magma", default="magma")
    preflight.add_argument("--r-values", default="2,3,4,5,6")
    preflight.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            _write_json(build_roster(args.stage), args.output)
            return 0
        try:
            r_values = tuple(int(value) for value in args.r_values.split(",") if value)
        except ValueError as error:
            raise RunnerError("r_values", f"invalid --r-values: {args.r_values!r}") from error
        report = natural_preflight(
            args.stage,
            freeze_path=args.freeze,
            ca_icx=args.ca_icx,
            gp=args.gp,
            magma=args.magma,
            r_values=r_values,
        )
        _write_json(report, args.output)
        return 2 if report.get("status", "").startswith("BLOCKED") else 0
    except RunnerError as error:
        failure = {
            "schema": SCHEMA,
            "status": "BLOCKED",
            "reason": error.code,
            "error": str(error),
            "evidence": error.evidence,
            "natural_rows_started": 0,
        }
        print(canonical_json(failure), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
