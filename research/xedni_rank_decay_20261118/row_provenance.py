#!/usr/bin/env python3
"""Strict, hash-linked provenance gate for natural Xedni analysis rows.

The validator is deliberately independent of the producer pipeline.  It does
not infer that a bounded proposal search proves independence: ``bounded_no_hit``
always has ``selected_dependence=UNKNOWN``.  A negative dependence label is
accepted only with a separately retained complete-lattice absence certificate.

All evidence paths are relative to one caller-supplied root.  When a root is
provided, every descriptor is re-hashed from a regular, non-symlink file and
path traversal/aliasing is rejected.  Hash strings without the underlying
files are therefore insufficient for executable provenance verification.

This module intentionally returns ``HASH_GRAPH_ONLY`` and
``production_eligible=false`` even after all implemented semantic replays.
The repository has neither a trusted independent execution-receipt verifier
nor a complete relation-lattice absence verifier, so this producer-side gate
must not authorize natural rows or a production decay verdict.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any, Iterable

from prime_manifest import is_prime_u32
import public_boundary
import rank_magma
import rank_pari
import relation_certificate
import relation_pari


SCHEMA = "xedni.rank-decay-row-provenance/v1"
INVENTORY_SCHEMA = "xedni.relation-inventory/v1"
WORK_SCHEMA = "xedni.row-work-accounting/v1"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+-]{0,191}\Z")
ROW_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+/|=,-]{0,511}\Z")
ROLE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9_.:+-]{0,191}"
    r"(?:/[A-Za-z0-9][A-Za-z0-9_.:+-]{0,191})*\Z"
)
MEDIA_TYPE = re.compile(r"[a-z0-9][a-z0-9.+-]*/[A-Za-z0-9][A-Za-z0-9.+-]{0,95}\Z")

ROOT_KEYS = {
    "schema",
    "row_id",
    "bindings",
    "artifacts",
    "tools",
    "relation_inventory",
    "work",
    "envelope_sha256",
}
BINDING_KEYS = {
    "freeze_manifest_sha256",
    "roster_sha256",
    "roster_row_sha256",
    "prime_manifest_sha256",
    "protocol_sha256",
    "amendment_sha256",
    "master_seed_sha256",
    "stage_seed_sha256",
    "p",
    "bits",
    "r",
    "source_private_sha256",
    "source_public_sha256",
    "public_private_link_sha256",
    "lift_sha256",
    "local_sha256",
}
ARTIFACT_KEYS = {"role", "path", "sha256", "bytes", "media_type"}
TOOL_KEYS = {
    "name",
    "status",
    "adapter_sha256",
    "version",
    "version_sha256",
    "executable_sha256",
    "command",
    "command_sha256",
    "script_sha256",
    "transcript_sha256",
    "version_returncode",
    "version_timed_out",
    "returncode",
    "timed_out",
    "effort",
    "timeout_seconds",
}
TOOL_STATUSES = {"ran", "timeout", "error", "unavailable", "not_run"}
INVENTORY_KEYS = {
    "schema",
    "status",
    "selected_dependence",
    "proposer_report_sha256",
    "replay_report_sha256",
    "complete_for_frozen_budget",
    "complete_relation_lattice",
    "absence_certificate_sha256",
    "candidate_count",
    "replayed_count",
    "exact_relation_count",
    "counted_relation_count",
    "candidates",
    "inventory_sha256",
}
INVENTORY_STATUSES = {
    "unknown",
    "bounded_no_hit",
    "certified_absence",
    "certified_relation",
}
DEPENDENCE_STATES = {"CERT_YES", "CERT_NO", "UNKNOWN"}
CANDIDATE_KEYS = {
    "candidate_id",
    "vector",
    "vector_sha256",
    "proposal_sha256",
    "eligible_for_replay",
    "replay_status",
    "replay_sha256",
    "certificate_sha256",
    "counted",
}
REPLAY_STATUSES = {"not_replayed", "rejected", "exact_false", "exact_true"}
WORK_KEYS = {
    "schema",
    "complete",
    "source_generation_candidates",
    "local_construction_candidates",
    "lift_candidates",
    "relation_candidates",
    "relation_replays",
    "rank_calls",
    "rejected_candidates",
    "duplicate_candidates",
    "cpu_ns",
    "wall_ns",
    "peak_rss_bytes",
    "retained_bytes",
    "work_report_sha256",
    "work_sha256",
}

ROSTER_KEYS = {
    "schema",
    "stage",
    "status",
    "factors",
    "source_master_seed",
    "executable_roster",
    "blocked_roster",
    "counts",
    "input_hashes",
    "roster_sha256",
}
ROSTER_ROW_KEYS = {
    "stage",
    "bits",
    "slot",
    "p",
    "family",
    "r",
    "lift",
    "local_arm",
    "index",
    "source_key",
    "source_index",
    "source_master_seed",
    "local_seed",
    "row_id",
    "status",
}
PRIME_MANIFEST_KEYS = {
    "schema",
    "master_seed",
    "bit_sizes",
    "slots_per_bit_size",
    "derivation",
    "miller_rabin_bases",
    "generator_sha256",
    "primes",
}
PRIME_ROW_KEYS = {
    "bits",
    "slot",
    "hash_candidate",
    "downward_odd_steps",
    "prime",
}
PROPOSER_RECEIPT_SCHEMA = "xedni.relation-proposer-inventory/v1"
PROPOSER_KEYS = {
    "schema",
    "row_id",
    "r",
    "status",
    "complete_for_frozen_budget",
    "candidates",
    "receipt_sha256",
}
PROPOSER_CANDIDATE_KEYS = {
    "candidate_id",
    "vector",
    "eligible_for_replay",
    "proposal_sha256",
}
REPLAY_RECEIPT_SCHEMA = "xedni.relation-replay-inventory/v1"
REPLAY_KEYS = {"schema", "row_id", "status", "replays", "receipt_sha256"}
REPLAY_ENTRY_KEYS = {
    "candidate_id",
    "replay_status",
    "replay_sha256",
    "certificate_sha256",
}
FREEZE_KEYS = {
    "schema",
    "status",
    "natural_rows_authorized",
    "implementation_commit",
    "master_seed",
    "blockers",
    "files",
    "rosters",
    "binary",
    "tools",
    "analysis",
}

BASE_ARTIFACT_BINDINGS = {
    "freeze_manifest": "freeze_manifest_sha256",
    "roster": "roster_sha256",
    "roster_row": "roster_row_sha256",
    "prime_manifest": "prime_manifest_sha256",
    "protocol": "protocol_sha256",
    "amendment": "amendment_sha256",
    "source_private": "source_private_sha256",
    "source_public": "source_public_sha256",
    "public_private_link": "public_private_link_sha256",
    "lift": "lift_sha256",
    "local": "local_sha256",
}


class ProvenanceError(ValueError):
    """Malformed, incomplete, aliased, or hash-inconsistent row evidence."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def canonical_json(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ProvenanceError("canonical_json", str(exc)) from exc
    return rendered.encode("ascii")


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _exact_keys(value: Any, expected: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProvenanceError("schema", f"{context} must be an object")
    actual = set(value)
    if actual != expected:
        raise ProvenanceError(
            "schema",
            f"{context} keys differ: missing={sorted(expected-actual)}, "
            f"extra={sorted(actual-expected)}",
        )
    return value


def _plain_int(value: Any, context: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ProvenanceError("type", f"{context} must be an integer >= {minimum}")
    return value


def _boolean(value: Any, context: str) -> bool:
    if not isinstance(value, bool):
        raise ProvenanceError("type", f"{context} must be a boolean")
    return value


def _token(value: Any, context: str) -> str:
    if not isinstance(value, str) or TOKEN.fullmatch(value) is None:
        raise ProvenanceError("token", f"{context} is not a safe nonempty token")
    return value


def _row_id(value: Any, context: str) -> str:
    if not isinstance(value, str) or ROW_ID.fullmatch(value) is None:
        raise ProvenanceError("token", f"{context} is not a safe nonempty row id")
    return value


def _role(value: Any, context: str) -> str:
    if not isinstance(value, str) or ROLE.fullmatch(value) is None:
        raise ProvenanceError("token", f"{context} is not a canonical artifact role")
    return value


def _hex(value: Any, context: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise ProvenanceError("hash", f"{context} must be a lowercase SHA-256")
    return value


def _self_hash(value: dict[str, Any], field: str, context: str) -> None:
    observed = _hex(value[field], f"{context}.{field}")
    payload = {key: item for key, item in value.items() if key != field}
    expected = object_sha256(payload)
    if observed != expected:
        raise ProvenanceError(
            "self_hash", f"{context}.{field} mismatch: expected {expected}"
        )


def seal_inventory(value: dict[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(value)
    sealed.pop("inventory_sha256", None)
    sealed["inventory_sha256"] = object_sha256(sealed)
    return sealed


def seal_work(value: dict[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(value)
    sealed.pop("work_sha256", None)
    sealed["work_sha256"] = object_sha256(sealed)
    return sealed


def seal_envelope(value: dict[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(value)
    sealed.pop("envelope_sha256", None)
    sealed["envelope_sha256"] = object_sha256(sealed)
    return sealed


def describe_artifact(
    role: str, path: str, evidence_root: Path, media_type: str = "application/json"
) -> dict[str, Any]:
    _role(role, "artifact.role")
    relative = _safe_relative_path(path, "artifact.path")
    candidate = _resolve_artifact(evidence_root, relative, "artifact.path")
    return {
        "role": role,
        "path": relative.as_posix(),
        "sha256": file_sha256(candidate),
        "bytes": candidate.stat().st_size,
        "media_type": media_type,
    }


def _safe_relative_path(value: Any, context: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ProvenanceError("path", f"{context} is not a canonical POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix():
        raise ProvenanceError("path", f"{context} must be canonical and relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ProvenanceError("path", f"{context} contains traversal or empty parts")
    return path


def _resolve_artifact(root: Path, relative: PurePosixPath, context: str) -> Path:
    root_resolved = root.resolve(strict=True)
    candidate = root_resolved.joinpath(*relative.parts)
    current = root_resolved
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise ProvenanceError("path", f"{context} traverses a symlink")
        except OSError as exc:
            raise ProvenanceError("path", f"{context} cannot be inspected: {exc}") from exc
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ProvenanceError("path", f"{context} does not resolve: {exc}") from exc
    try:
        common = os.path.commonpath((str(root_resolved), str(resolved)))
    except ValueError as exc:
        raise ProvenanceError("path", f"{context} escapes the evidence root") from exc
    if common != str(root_resolved) or not resolved.is_file():
        raise ProvenanceError("path", f"{context} is not a regular file in the root")
    return resolved


def _read_artifact_no_follow(
    root: Path, relative: PurePosixPath, context: str
) -> tuple[bytes, os.stat_result]:
    """Open every component relative to directory fds and hash the opened inode."""
    root_path = root.resolve(strict=True)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        current = os.open(root_path, directory_flags)
        descriptors.append(current)
        for part in relative.parts[:-1]:
            current = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(current)
        target = os.open(relative.parts[-1], file_flags, dir_fd=current)
        descriptors.append(target)
        metadata = os.fstat(target)
        if not stat.S_ISREG(metadata.st_mode):
            raise ProvenanceError("path", f"{context} is not a regular file")
        chunks = []
        while True:
            block = os.read(target, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
        return b"".join(chunks), metadata
    except OSError as exc:
        raise ProvenanceError("path", f"{context} cannot be opened safely: {exc}") from exc
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _validate_artifacts(
    artifacts: Any, evidence_root: Path | None
) -> tuple[dict[str, dict[str, Any]], dict[str, bytes]]:
    if not isinstance(artifacts, list):
        raise ProvenanceError("schema", "artifacts must be a list")
    by_role: dict[str, dict[str, Any]] = {}
    seen_paths: set[str] = set()
    seen_inodes: dict[tuple[int, int], str] = {}
    raw_by_role: dict[str, bytes] = {}
    for index, raw in enumerate(artifacts):
        context = f"artifacts[{index}]"
        item = _exact_keys(raw, ARTIFACT_KEYS, context)
        role = _role(item["role"], f"{context}.role")
        if role in by_role:
            raise ProvenanceError("artifact_collision", f"duplicate role {role!r}")
        path = _safe_relative_path(item["path"], f"{context}.path")
        path_text = path.as_posix()
        if path_text in seen_paths:
            raise ProvenanceError("artifact_collision", f"duplicate path {path_text!r}")
        digest = _hex(item["sha256"], f"{context}.sha256")
        size = _plain_int(item["bytes"], f"{context}.bytes")
        media = item["media_type"]
        if not isinstance(media, str) or MEDIA_TYPE.fullmatch(media) is None:
            raise ProvenanceError("type", f"{context}.media_type is invalid")
        if evidence_root is not None:
            raw_bytes, metadata = _read_artifact_no_follow(
                evidence_root, path, f"{context}.path"
            )
            inode = (metadata.st_dev, metadata.st_ino)
            if inode in seen_inodes:
                raise ProvenanceError(
                    "artifact_collision",
                    f"roles {seen_inodes[inode]!r} and {role!r} alias one inode",
                )
            seen_inodes[inode] = role
            observed_size = len(raw_bytes)
            if observed_size != size:
                raise ProvenanceError(
                    "artifact_size",
                    f"{context} expected {size} bytes, observed {observed_size}",
                )
            observed_digest = hashlib.sha256(raw_bytes).hexdigest()
            if observed_digest != digest:
                raise ProvenanceError(
                    "artifact_hash",
                    f"{context} expected {digest}, observed {observed_digest}",
                )
            raw_by_role[role] = raw_bytes
        by_role[role] = item
        seen_paths.add(path_text)
    return by_role, raw_by_role


def _require_role(
    by_role: dict[str, dict[str, Any]], role: str, digest: str | None
) -> None:
    if role not in by_role:
        raise ProvenanceError("artifact_missing", f"missing artifact role {role!r}")
    if digest is None or by_role[role]["sha256"] != digest:
        raise ProvenanceError("artifact_binding", f"artifact role {role!r} hash mismatch")


def _validate_bindings(value: Any, row_id: str) -> dict[str, Any]:
    bindings = _exact_keys(value, BINDING_KEYS, "bindings")
    for key in BINDING_KEYS - {"p", "bits", "r"}:
        _hex(bindings[key], f"bindings.{key}")
    prime = _plain_int(bindings["p"], "bindings.p", 2)
    bits = _plain_int(bindings["bits"], "bindings.bits", 2)
    r = _plain_int(bindings["r"], "bindings.r", 2)
    if prime >= 2**32 or not is_prime_u32(prime):
        raise ProvenanceError("prime", "bindings.p is not a certified prime below 2^32")
    if bits != prime.bit_length():
        raise ProvenanceError("prime", "bindings.bits does not match p.bit_length()")
    if r > 9:
        raise ProvenanceError("type", "bindings.r must be at most 9")
    source_hashes = {
        bindings["source_private_sha256"],
        bindings["source_public_sha256"],
        bindings["public_private_link_sha256"],
    }
    if len(source_hashes) != 3:
        raise ProvenanceError(
            "source_link",
            "private source, public projection, and link must be distinct artifacts",
        )
    return bindings


def _validate_tools(
    value: Any,
    by_role: dict[str, dict[str, Any]],
    raw_by_role: dict[str, bytes],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ProvenanceError("schema", "tools must be a list")
    names: set[str] = set()
    validated = []
    for index, raw in enumerate(value):
        context = f"tools[{index}]"
        tool = _exact_keys(raw, TOOL_KEYS, context)
        name = _token(tool["name"], f"{context}.name")
        if name in names:
            raise ProvenanceError("tool_collision", f"duplicate tool name {name!r}")
        names.add(name)
        if tool["status"] not in TOOL_STATUSES:
            raise ProvenanceError("tool_status", f"{context}.status is invalid")
        _hex(tool["adapter_sha256"], f"{context}.adapter_sha256")
        if not isinstance(tool["version"], str) or not tool["version"]:
            raise ProvenanceError("type", f"{context}.version must be nonempty")
        _hex(tool["version_sha256"], f"{context}.version_sha256")
        _hex(tool["executable_sha256"], f"{context}.executable_sha256", nullable=True)
        command = tool["command"]
        command_digest = _hex(
            tool["command_sha256"], f"{context}.command_sha256", nullable=True
        )
        script_digest = _hex(
            tool["script_sha256"], f"{context}.script_sha256", nullable=True
        )
        transcript_digest = _hex(
            tool["transcript_sha256"], f"{context}.transcript_sha256", nullable=True
        )
        version_returncode = tool["version_returncode"]
        if isinstance(version_returncode, bool) or not isinstance(version_returncode, int):
            raise ProvenanceError("tool_version", f"{context}.version_returncode is invalid")
        version_timed_out = _boolean(
            tool["version_timed_out"], f"{context}.version_timed_out"
        )
        returncode = tool["returncode"]
        if returncode is not None and (
            isinstance(returncode, bool) or not isinstance(returncode, int)
        ):
            raise ProvenanceError("tool_evidence", f"{context}.returncode is invalid")
        timed_out = tool["timed_out"]
        if timed_out is not None:
            _boolean(timed_out, f"{context}.timed_out")
        effort = tool["effort"]
        if effort is not None:
            _plain_int(effort, f"{context}.effort")
        timeout_seconds = tool["timeout_seconds"]
        if timeout_seconds is not None and (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or timeout_seconds <= 0
        ):
            raise ProvenanceError("tool_evidence", f"{context}.timeout_seconds is invalid")
        if command is not None:
            if (
                not isinstance(command, list)
                or not command
                or any(not isinstance(part, str) or not part for part in command)
            ):
                raise ProvenanceError("type", f"{context}.command is invalid")
            if command_digest != object_sha256(command):
                raise ProvenanceError("tool_command", f"{context}.command hash mismatch")
        elif command_digest is not None:
            raise ProvenanceError("tool_command", f"{context} has hash without command")

        ran = tool["status"] in {"ran", "timeout", "error"}
        if ran and any(item is None for item in (command_digest, script_digest, transcript_digest)):
            raise ProvenanceError("tool_evidence", f"{context} ran without full evidence")
        if not ran and any(item is not None for item in (command_digest, script_digest, transcript_digest)):
            raise ProvenanceError("tool_evidence", f"{context} did not run but has run evidence")
        if ran and (returncode is None or timed_out is None):
            raise ProvenanceError("tool_evidence", f"{context} lacks return/timed-out evidence")
        if not ran and (returncode is not None or timed_out is not None):
            raise ProvenanceError("tool_evidence", f"{context} has impossible return evidence")
        if ran and timeout_seconds is None:
            raise ProvenanceError("tool_evidence", f"{context} lacks timeout budget")
        if not ran and timeout_seconds is not None:
            raise ProvenanceError("tool_evidence", f"{context} has timeout without a run")
        if name in {"pari_rank", "magma_rank"} and ran and effort is None:
            raise ProvenanceError("tool_evidence", f"{context} lacks rank effort")
        if name == "pari_relation" and effort is not None:
            raise ProvenanceError("tool_evidence", f"{context} has irrelevant rank effort")
        if tool["status"] == "ran" and (returncode != 0 or timed_out):
            raise ProvenanceError("tool_evidence", f"{context} successful status is inconsistent")
        if tool["status"] == "timeout" and timed_out is not True:
            raise ProvenanceError("tool_evidence", f"{context} timeout status is inconsistent")
        if tool["status"] == "error" and returncode == 0 and timed_out is False:
            raise ProvenanceError("tool_evidence", f"{context} error status is inconsistent")
        if tool["status"] == "not_run" and tool["executable_sha256"] is None:
            raise ProvenanceError("tool_evidence", f"{context} not_run lacks pinned executable")
        if tool["status"] == "unavailable" and tool["executable_sha256"] is not None:
            raise ProvenanceError("tool_evidence", f"{context} unavailable has executable hash")

        _require_role(by_role, f"tool/{name}/adapter", tool["adapter_sha256"])
        _require_role(by_role, f"tool/{name}/version", tool["version_sha256"])
        if version_returncode != 0 or version_timed_out:
            raise ProvenanceError("tool_version", f"{context} version probe did not succeed")
        if raw_by_role:
            try:
                version_text = raw_by_role[f"tool/{name}/version"].decode(
                    "utf-8", errors="strict"
                )
            except UnicodeError as exc:
                raise ProvenanceError(
                    "tool_version", f"{context} version transcript is not UTF-8"
                ) from exc
            expected_marker = {
                "pari_rank": "PARI/GP 2.17.2",
                "magma_rank": "2.29-10",
                "pari_relation": "PARI/GP 2.17.2",
            }.get(name)
            if expected_marker is None or expected_marker not in version_text:
                raise ProvenanceError(
                    "tool_version", f"{context} version transcript lacks pinned marker"
                )
            if tool["version"] not in version_text:
                raise ProvenanceError(
                    "tool_version", f"{context}.version is not in its transcript"
                )
        if tool["executable_sha256"] is not None:
            _require_role(by_role, f"tool/{name}/executable", tool["executable_sha256"])
        if ran:
            _require_role(by_role, f"tool/{name}/script", script_digest)
            _require_role(by_role, f"tool/{name}/transcript", transcript_digest)
        validated.append(tool)
    return validated


def _primitive_vector(value: Any, r: int, context: str) -> list[int]:
    if not isinstance(value, list) or len(value) != r:
        raise ProvenanceError("relation_vector", f"{context} must have length r={r}")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        raise ProvenanceError("relation_vector", f"{context} must contain integers")
    nonzero = [item for item in value if item]
    if not nonzero:
        raise ProvenanceError("relation_vector", f"{context} is the zero vector")
    gcd_value = 0
    for item in nonzero:
        gcd_value = math.gcd(gcd_value, abs(item))
    if gcd_value != 1 or nonzero[0] < 0:
        raise ProvenanceError(
            "relation_vector", f"{context} must be primitive and sign-canonical"
        )
    return value


def _validate_inventory(
    value: Any, r: int, by_role: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    inventory = _exact_keys(value, INVENTORY_KEYS, "relation_inventory")
    if inventory["schema"] != INVENTORY_SCHEMA:
        raise ProvenanceError("schema", "unknown relation_inventory.schema")
    if inventory["status"] not in INVENTORY_STATUSES:
        raise ProvenanceError("inventory_status", "unknown relation inventory status")
    if inventory["selected_dependence"] not in DEPENDENCE_STATES:
        raise ProvenanceError("inventory_status", "unknown selected dependence state")
    proposer_digest = _hex(
        inventory["proposer_report_sha256"],
        "relation_inventory.proposer_report_sha256",
    )
    replay_digest = _hex(
        inventory["replay_report_sha256"],
        "relation_inventory.replay_report_sha256",
        nullable=True,
    )
    absence_digest = _hex(
        inventory["absence_certificate_sha256"],
        "relation_inventory.absence_certificate_sha256",
        nullable=True,
    )
    complete_budget = _boolean(
        inventory["complete_for_frozen_budget"],
        "relation_inventory.complete_for_frozen_budget",
    )
    complete_lattice = _boolean(
        inventory["complete_relation_lattice"],
        "relation_inventory.complete_relation_lattice",
    )
    counts = {
        key: _plain_int(inventory[key], f"relation_inventory.{key}")
        for key in (
            "candidate_count",
            "replayed_count",
            "exact_relation_count",
            "counted_relation_count",
        )
    }
    candidates = inventory["candidates"]
    if not isinstance(candidates, list):
        raise ProvenanceError("schema", "relation_inventory.candidates must be a list")
    if counts["candidate_count"] != len(candidates):
        raise ProvenanceError("inventory_count", "candidate_count does not match list")
    ids: set[str] = set()
    vectors: set[str] = set()
    replayed = exact = counted = 0
    for index, raw in enumerate(candidates):
        context = f"relation_inventory.candidates[{index}]"
        candidate = _exact_keys(raw, CANDIDATE_KEYS, context)
        candidate_id = _token(candidate["candidate_id"], f"{context}.candidate_id")
        if candidate_id in ids:
            raise ProvenanceError("candidate_collision", f"duplicate id {candidate_id!r}")
        vector = _primitive_vector(candidate["vector"], r, f"{context}.vector")
        vector_digest = _hex(candidate["vector_sha256"], f"{context}.vector_sha256")
        if vector_digest != object_sha256(vector):
            raise ProvenanceError("candidate_hash", f"{context}.vector hash mismatch")
        if vector_digest in vectors:
            raise ProvenanceError("candidate_collision", "duplicate canonical vector")
        proposal_digest = _hex(
            candidate["proposal_sha256"], f"{context}.proposal_sha256"
        )
        eligible = _boolean(
            candidate["eligible_for_replay"], f"{context}.eligible_for_replay"
        )
        replay_status = candidate["replay_status"]
        if replay_status not in REPLAY_STATUSES:
            raise ProvenanceError("replay_status", f"{context}.replay_status is invalid")
        replay_sha = _hex(
            candidate["replay_sha256"], f"{context}.replay_sha256", nullable=True
        )
        certificate_sha = _hex(
            candidate["certificate_sha256"],
            f"{context}.certificate_sha256",
            nullable=True,
        )
        is_counted = _boolean(candidate["counted"], f"{context}.counted")
        if replay_status == "not_replayed":
            if replay_sha is not None or certificate_sha is not None or is_counted:
                raise ProvenanceError("replay_status", f"{context} has impossible no-replay evidence")
            if eligible and complete_budget:
                raise ProvenanceError(
                    "inventory_incomplete",
                    f"{context} was eligible but not replayed in a complete budget",
                )
        else:
            replayed += 1
            if replay_sha is None:
                raise ProvenanceError("replay_status", f"{context} lacks replay evidence")
            if not eligible:
                raise ProvenanceError("replay_status", f"{context} replays an ineligible candidate")
        if replay_status == "exact_true":
            exact += 1
            if certificate_sha is None:
                raise ProvenanceError("replay_status", f"{context} lacks exact certificate")
        elif certificate_sha is not None or is_counted:
            raise ProvenanceError("replay_status", f"{context} counts a non-exact candidate")
        if is_counted:
            counted += 1

        _require_role(
            by_role,
            f"relation_candidate/{candidate_id}/proposal",
            proposal_digest,
        )
        if replay_sha is not None:
            _require_role(
                by_role, f"relation_candidate/{candidate_id}/replay", replay_sha
            )
        if certificate_sha is not None:
            _require_role(
                by_role,
                f"relation_candidate/{candidate_id}/certificate",
                certificate_sha,
            )
        ids.add(candidate_id)
        vectors.add(vector_digest)

    observed = {
        "replayed_count": replayed,
        "exact_relation_count": exact,
        "counted_relation_count": counted,
    }
    for key, amount in observed.items():
        if counts[key] != amount:
            raise ProvenanceError("inventory_count", f"{key} does not match candidates")
    if replayed and replay_digest is None:
        raise ProvenanceError("inventory_evidence", "replayed candidates lack replay report")
    if not replayed and replay_digest is not None:
        raise ProvenanceError("inventory_evidence", "replay report exists without replays")

    status = inventory["status"]
    dependence = inventory["selected_dependence"]
    if status == "unknown":
        if complete_budget or complete_lattice or absence_digest is not None or exact:
            raise ProvenanceError("inventory_status", "unknown has conclusive evidence")
        expected_dependence = "UNKNOWN"
    elif status == "bounded_no_hit":
        if not complete_budget or complete_lattice or absence_digest is not None or exact:
            raise ProvenanceError("inventory_status", "bounded_no_hit semantics violated")
        expected_dependence = "UNKNOWN"
    elif status == "certified_absence":
        if not complete_budget or not complete_lattice or absence_digest is None or exact:
            raise ProvenanceError("inventory_status", "certified_absence semantics violated")
        expected_dependence = "CERT_NO"
    else:
        if exact < 1 or absence_digest is not None:
            raise ProvenanceError("inventory_status", "certified_relation semantics violated")
        expected_dependence = "CERT_YES"
    if dependence != expected_dependence:
        raise ProvenanceError(
            "inventory_status",
            f"{status} requires selected_dependence={expected_dependence}",
        )

    _self_hash(inventory, "inventory_sha256", "relation_inventory")
    _require_role(by_role, "relation_proposer", proposer_digest)
    if replay_digest is not None:
        _require_role(by_role, "relation_replay", replay_digest)
    if absence_digest is not None:
        _require_role(by_role, "relation_absence", absence_digest)
    return inventory


def _validate_work(
    value: Any,
    inventory: dict[str, Any],
    tools: list[dict[str, Any]],
    by_role: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    work = _exact_keys(value, WORK_KEYS, "work")
    if work["schema"] != WORK_SCHEMA:
        raise ProvenanceError("schema", "unknown work.schema")
    _boolean(work["complete"], "work.complete")
    for key in WORK_KEYS - {
        "schema",
        "complete",
        "work_report_sha256",
        "work_sha256",
    }:
        _plain_int(work[key], f"work.{key}")
    report_digest = _hex(work["work_report_sha256"], "work.work_report_sha256")
    if work["relation_candidates"] != inventory["candidate_count"]:
        raise ProvenanceError("work_count", "work.relation_candidates mismatch")
    if work["relation_replays"] != inventory["replayed_count"]:
        raise ProvenanceError("work_count", "work.relation_replays mismatch")
    expected_rank_calls = sum(
        tool["name"] in {"pari_rank", "magma_rank"}
        and tool["status"] in {"ran", "timeout", "error"}
        for tool in tools
    )
    if work["rank_calls"] != expected_rank_calls:
        raise ProvenanceError(
            "work_count",
            f"work.rank_calls={work['rank_calls']} but evidence has {expected_rank_calls}",
        )
    if inventory["complete_for_frozen_budget"] and not work["complete"]:
        raise ProvenanceError("work_count", "complete proposal budget has incomplete work")
    _self_hash(work, "work_sha256", "work")
    _require_role(by_role, "work_report", report_digest)
    return work


def _json_bytes(raw: bytes, context: str) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ProvenanceError("json", f"{context}: non-finite number {value!r}")
            ),
        )
    except UnicodeError as exc:
        raise ProvenanceError("json", f"{context}: invalid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ProvenanceError("json", f"{context}: invalid JSON: {exc}") from exc


def _semantic_roster_prime_freeze(
    raw: dict[str, bytes],
    bindings: dict[str, Any],
    row_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _exact_keys(
        _json_bytes(raw["prime_manifest"], "prime_manifest"),
        PRIME_MANIFEST_KEYS,
        "prime_manifest",
    )
    if manifest["schema"] != "xedni-rank-decay-primes/v1":
        raise ProvenanceError("prime_manifest", "unknown prime manifest schema")
    if not isinstance(manifest["master_seed"], str) or not manifest["master_seed"]:
        raise ProvenanceError("prime_manifest", "empty master seed")
    _hex(manifest["generator_sha256"], "prime_manifest.generator_sha256")
    if not isinstance(manifest["primes"], list):
        raise ProvenanceError("prime_manifest", "primes must be a list")
    prime_rows = []
    prime_keys: set[tuple[int, int]] = set()
    for index, raw_row in enumerate(manifest["primes"]):
        row = _exact_keys(raw_row, PRIME_ROW_KEYS, f"prime_manifest.primes[{index}]")
        prime = _plain_int(row["prime"], f"prime_manifest.primes[{index}].prime", 2)
        bits = _plain_int(row["bits"], f"prime_manifest.primes[{index}].bits", 2)
        slot = _plain_int(row["slot"], f"prime_manifest.primes[{index}].slot")
        _plain_int(row["hash_candidate"], f"prime_manifest.primes[{index}].hash_candidate")
        _plain_int(
            row["downward_odd_steps"],
            f"prime_manifest.primes[{index}].downward_odd_steps",
        )
        if not is_prime_u32(prime) or prime.bit_length() != bits:
            raise ProvenanceError("prime_manifest", "manifest contains invalid prime")
        key = (bits, slot)
        if key in prime_keys:
            raise ProvenanceError("prime_manifest", "duplicate bit/slot pair")
        prime_keys.add(key)
        prime_rows.append(row)

    roster = _exact_keys(
        _json_bytes(raw["roster"], "roster"), ROSTER_KEYS, "roster"
    )
    if roster["schema"] != "xedni.rank-decay-roster/v1":
        raise ProvenanceError("roster", "unknown roster schema")
    supplied_roster_hash = _hex(roster["roster_sha256"], "roster.roster_sha256")
    roster_payload = {key: value for key, value in roster.items() if key != "roster_sha256"}
    if supplied_roster_hash != object_sha256(roster_payload):
        raise ProvenanceError("roster", "roster self-hash mismatch")
    if not isinstance(roster["executable_roster"], list) or not isinstance(
        roster["blocked_roster"], list
    ):
        raise ProvenanceError("roster", "roster row lists are malformed")
    counts = _exact_keys(roster["counts"], {"executable", "blocked"}, "roster.counts")
    if counts != {
        "executable": len(roster["executable_roster"]),
        "blocked": len(roster["blocked_roster"]),
    }:
        raise ProvenanceError("roster", "roster counts mismatch")
    input_hashes = _exact_keys(
        roster["input_hashes"],
        {"PROTOCOL.md", "AMENDMENT.md", "PRIMES.json"},
        "roster.input_hashes",
    )
    expected_input_hashes = {
        "PROTOCOL.md": hashlib.sha256(raw["protocol"]).hexdigest(),
        "AMENDMENT.md": hashlib.sha256(raw["amendment"]).hexdigest(),
        "PRIMES.json": hashlib.sha256(raw["prime_manifest"]).hexdigest(),
    }
    if input_hashes != expected_input_hashes:
        raise ProvenanceError("roster", "roster input hashes mismatch")

    row = _exact_keys(
        _json_bytes(raw["roster_row"], "roster_row"),
        ROSTER_ROW_KEYS,
        "roster_row",
    )
    if row["status"] != "PLANNED" or row["row_id"] != row_id:
        raise ProvenanceError("roster_row", "row status/id mismatch")
    matches = [candidate for candidate in roster["executable_roster"] if candidate == row]
    if len(matches) != 1:
        raise ProvenanceError("roster_row", "row is not a unique exact roster member")
    row_ids = [candidate.get("row_id") for candidate in roster["executable_roster"]]
    if len(row_ids) != len(set(row_ids)):
        raise ProvenanceError("roster", "duplicate executable row id")
    for name in ("p", "bits", "r"):
        if row[name] != bindings[name]:
            raise ProvenanceError("roster_row", f"row {name} does not match binding")
    if object_sha256(manifest["master_seed"]) != bindings["master_seed_sha256"]:
        raise ProvenanceError("seed", "master seed commitment mismatch")
    if object_sha256(row["source_master_seed"]) != bindings["stage_seed_sha256"]:
        raise ProvenanceError("seed", "stage/source seed commitment mismatch")
    prime_matches = [
        item
        for item in prime_rows
        if item["prime"] == row["p"]
        and item["bits"] == row["bits"]
        and item["slot"] == row["slot"]
    ]
    if len(prime_matches) != 1:
        raise ProvenanceError("prime_manifest", "roster prime is not uniquely manifested")

    freeze = _exact_keys(
        _json_bytes(raw["freeze_manifest"], "freeze_manifest"),
        FREEZE_KEYS,
        "freeze_manifest",
    )
    if freeze["schema"] != "xedni.rank-decay-freeze/v1":
        raise ProvenanceError("freeze", "unknown freeze schema")
    if freeze["natural_rows_authorized"] is not True:
        raise ProvenanceError("freeze", "natural rows are not authorized by the freeze")
    if freeze["master_seed"] != manifest["master_seed"]:
        raise ProvenanceError("freeze", "freeze/prime master seed mismatch")
    frozen_stage = freeze.get("rosters", {}).get(row["stage"])
    if not isinstance(frozen_stage, dict) or frozen_stage.get("sha256") != supplied_roster_hash:
        raise ProvenanceError("freeze", "freeze does not bind this roster")
    frozen_files = freeze["files"]
    if not isinstance(frozen_files, dict):
        raise ProvenanceError("freeze", "freeze.files is malformed")
    suffix_bindings = {
        "PROTOCOL.md": input_hashes["PROTOCOL.md"],
        "AMENDMENT.md": input_hashes["AMENDMENT.md"],
        "PRIMES.json": input_hashes["PRIMES.json"],
    }
    for suffix, expected in suffix_bindings.items():
        matching = [value for path, value in frozen_files.items() if path.endswith(suffix)]
        if matching != [expected]:
            raise ProvenanceError("freeze", f"freeze does not uniquely bind {suffix}")
    return row, freeze


def _semantic_public_boundary(
    raw: dict[str, bytes], bindings: dict[str, Any], row: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    private = _json_bytes(raw["source_private"], "source_private")
    public = _json_bytes(raw["source_public"], "source_public")
    link = _json_bytes(raw["public_private_link"], "public_private_link")
    try:
        private = public_boundary.validate_private_source(private)
        public = public_boundary.validate_public_source(public)
        link = public_boundary.validate_link(link)
        receipt = public_boundary.verify_redaction_link(private, public, link)
    except public_boundary.BoundaryError as exc:
        raise ProvenanceError("public_boundary", str(exc)) from exc
    if link.get("production_eligible") is not True:
        raise ProvenanceError("public_boundary", "test-only redaction link is ineligible")
    for role, value in (
        ("source_private", private),
        ("source_public", public),
        ("public_private_link", link),
    ):
        if canonical_json(value) != raw[role]:
            raise ProvenanceError("public_boundary", f"{role} is not canonical JSON")
    if (
        receipt["private_source_sha256"] != bindings["source_private_sha256"]
        or receipt["public_source_sha256"] != bindings["source_public_sha256"]
        or object_sha256(link) != bindings["public_private_link_sha256"]
    ):
        raise ProvenanceError("public_boundary", "redaction receipt/hash binding mismatch")
    if private["p"] != bindings["p"] or private["bits"] != bindings["bits"]:
        raise ProvenanceError("public_boundary", "source prime/bit binding mismatch")
    if private["max_r"] < bindings["r"]:
        raise ProvenanceError("public_boundary", "source does not contain the selected prefix")
    if private["source_index"] != row["source_index"] or private["family"] != row["family"]:
        raise ProvenanceError("public_boundary", "source index/family roster mismatch")
    if private["master_seed"] != row["source_master_seed"]:
        raise ProvenanceError("public_boundary", "private source seed/roster mismatch")
    return private, public, link


def _semantic_tools(
    raw: dict[str, bytes],
    tools: list[dict[str, Any]],
    lift: dict[str, Any],
) -> None:
    ainvs = lift.get("ainvs") if isinstance(lift, dict) else None
    if not isinstance(ainvs, list) or len(ainvs) != 5:
        raise ProvenanceError("tool_semantics", "lift does not expose five ainvs")
    for tool in tools:
        name = tool["name"]
        module = {
            "pari_rank": rank_pari,
            "magma_rank": rank_magma,
            "pari_relation": relation_pari,
        }.get(name)
        if module is None:
            raise ProvenanceError("tool_semantics", f"unsupported tool {name!r}")
        module_hash = file_sha256(Path(module.__file__).resolve())
        if module_hash != tool["adapter_sha256"]:
            raise ProvenanceError("tool_semantics", f"{name} adapter is not current code")
        if tool["status"] not in {"ran", "timeout", "error"}:
            continue
        try:
            script = raw[f"tool/{name}/script"].decode("utf-8", errors="strict")
            transcript = raw[f"tool/{name}/transcript"].decode(
                "utf-8", errors="strict"
            )
        except UnicodeError as exc:
            raise ProvenanceError(
                "tool_semantics", f"{name} script/transcript is not UTF-8"
            ) from exc
        if name == "pari_rank":
            expected_script = rank_pari.make_script(tuple(int(value) for value in ainvs), tool["effort"])
            parser = rank_pari.parse_transcript
        elif name == "magma_rank":
            expected_script = rank_magma.make_script(tuple(int(value) for value in ainvs), tool["effort"])
            parser = rank_magma.parse_transcript
        else:
            points = lift.get("points")
            if not isinstance(points, list):
                raise ProvenanceError("tool_semantics", "lift points are missing")
            expected_script = relation_pari.make_script(ainvs, points, relation_pari.PARISIZEMAX)
            parser = lambda text: relation_pari.parse_transcript(text, len(points))
        if script != expected_script:
            raise ProvenanceError("tool_semantics", f"{name} script does not replay")
        if tool["status"] == "ran":
            try:
                parser(transcript)
            except (KeyError, TypeError, ValueError) as exc:
                raise ProvenanceError("tool_semantics", f"{name} transcript does not parse") from exc


def _receipt_self_hash(value: dict[str, Any], field: str, context: str) -> None:
    _self_hash(value, field, context)


def _semantic_relation_inventory(
    raw: dict[str, bytes],
    inventory: dict[str, Any],
    row_id: str,
    r: int,
    lift: dict[str, Any],
    private_source: dict[str, Any],
    local: dict[str, Any] | None,
) -> None:
    proposer = _exact_keys(
        _json_bytes(raw["relation_proposer"], "relation_proposer"),
        PROPOSER_KEYS,
        "relation_proposer",
    )
    if proposer["schema"] != PROPOSER_RECEIPT_SCHEMA:
        raise ProvenanceError("relation_inventory", "unknown proposer receipt schema")
    if proposer["row_id"] != row_id or proposer["r"] != r:
        raise ProvenanceError("relation_inventory", "proposer row/r mismatch")
    if proposer["status"] not in {"complete", "incomplete"}:
        raise ProvenanceError("relation_inventory", "unknown proposer status")
    if proposer["complete_for_frozen_budget"] is not (proposer["status"] == "complete"):
        raise ProvenanceError("relation_inventory", "proposer completeness is inconsistent")
    _receipt_self_hash(proposer, "receipt_sha256", "relation_proposer")
    if proposer["complete_for_frozen_budget"] != inventory["complete_for_frozen_budget"]:
        raise ProvenanceError("relation_inventory", "proposer/inventory completeness mismatch")
    if not isinstance(proposer["candidates"], list):
        raise ProvenanceError("relation_inventory", "proposer candidates are malformed")
    proposed: dict[str, tuple[list[int], bool, str]] = {}
    for index, value in enumerate(proposer["candidates"]):
        entry = _exact_keys(
            value, PROPOSER_CANDIDATE_KEYS, f"relation_proposer.candidates[{index}]"
        )
        candidate_id = _token(entry["candidate_id"], "proposer candidate id")
        if candidate_id in proposed:
            raise ProvenanceError("relation_inventory", "duplicate proposer candidate")
        vector = _primitive_vector(entry["vector"], r, "proposer candidate vector")
        eligible = _boolean(entry["eligible_for_replay"], "proposer eligible flag")
        proposal_sha = _hex(entry["proposal_sha256"], "proposer proposal hash")
        proposed[candidate_id] = (vector, eligible, proposal_sha)
    inventoried = {
        item["candidate_id"]: (
            item["vector"],
            item["eligible_for_replay"],
            item["proposal_sha256"],
        )
        for item in inventory["candidates"]
    }
    if proposed != inventoried:
        raise ProvenanceError(
            "relation_inventory", "proposer and retained candidate inventory differ"
        )

    replayed = [item for item in inventory["candidates"] if item["replay_status"] != "not_replayed"]
    if replayed:
        replay = _exact_keys(
            _json_bytes(raw["relation_replay"], "relation_replay"),
            REPLAY_KEYS,
            "relation_replay",
        )
        if replay["schema"] != REPLAY_RECEIPT_SCHEMA or replay["row_id"] != row_id:
            raise ProvenanceError("relation_inventory", "replay receipt schema/row mismatch")
        if replay["status"] != "complete" or not isinstance(replay["replays"], list):
            raise ProvenanceError("relation_inventory", "replay receipt is incomplete")
        _receipt_self_hash(replay, "receipt_sha256", "relation_replay")
        replay_map = {}
        for index, value in enumerate(replay["replays"]):
            entry = _exact_keys(value, REPLAY_ENTRY_KEYS, f"relation_replay.replays[{index}]")
            candidate_id = _token(entry["candidate_id"], "replay candidate id")
            if candidate_id in replay_map:
                raise ProvenanceError("relation_inventory", "duplicate replay candidate")
            replay_map[candidate_id] = (
                entry["replay_status"],
                entry["replay_sha256"],
                entry["certificate_sha256"],
            )
        expected_map = {
            item["candidate_id"]: (
                item["replay_status"],
                item["replay_sha256"],
                item["certificate_sha256"],
            )
            for item in replayed
        }
        if replay_map != expected_map:
            raise ProvenanceError("relation_inventory", "replay receipt/inventory differ")

    for candidate in inventory["candidates"]:
        if candidate["replay_status"] != "exact_true":
            continue
        role = f"relation_candidate/{candidate['candidate_id']}/certificate"
        certificate = _json_bytes(raw[role], role)
        errors = relation_certificate.verify_relation_certificate(
            certificate, lift, private_source, local
        )
        if errors:
            raise ProvenanceError(
                "relation_certificate", f"{candidate['candidate_id']}: {errors}"
            )
    if inventory["status"] == "certified_absence":
        # No complete relation-lattice verifier exists in the current package.
        # A self-described JSON certificate cannot establish independence.
        raise ProvenanceError(
            "absence_verifier_unavailable",
            "CERT_NO is forbidden until a complete-lattice verifier replays the certificate",
        )


def _semantic_work_report(raw: bytes, work: dict[str, Any]) -> None:
    report = _json_bytes(raw, "work_report")
    expected = {
        key: value
        for key, value in work.items()
        if key not in {"work_report_sha256", "work_sha256"}
    }
    if report != expected or canonical_json(report) != raw:
        raise ProvenanceError("work_count", "work report does not exactly replay counters")


def _validate_expected_roles(
    by_role: dict[str, dict[str, Any]], bindings: dict[str, Any], expected: set[str]
) -> None:
    for role, binding_key in BASE_ARTIFACT_BINDINGS.items():
        _require_role(by_role, role, bindings[binding_key])
    extra = sorted(set(by_role) - expected)
    missing = sorted(expected - set(by_role))
    if extra or missing:
        raise ProvenanceError(
            "artifact_schema", f"artifact roles differ: missing={missing}, extra={extra}"
        )


def validate_envelope(
    value: Any, evidence_root: Path | None = None
) -> dict[str, Any]:
    envelope = _exact_keys(value, ROOT_KEYS, "envelope")
    if envelope["schema"] != SCHEMA:
        raise ProvenanceError("schema", f"unknown envelope schema {envelope['schema']!r}")
    row_id = _row_id(envelope["row_id"], "row_id")
    bindings = _validate_bindings(envelope["bindings"], row_id)
    by_role, raw_by_role = _validate_artifacts(envelope["artifacts"], evidence_root)
    tools = _validate_tools(envelope["tools"], by_role, raw_by_role)
    inventory = _validate_inventory(envelope["relation_inventory"], bindings["r"], by_role)
    work = _validate_work(envelope["work"], inventory, tools, by_role)

    expected_roles = set(BASE_ARTIFACT_BINDINGS) | {
        "relation_proposer",
        "work_report",
    }
    if inventory["replay_report_sha256"] is not None:
        expected_roles.add("relation_replay")
    if inventory["absence_certificate_sha256"] is not None:
        expected_roles.add("relation_absence")
    for candidate in inventory["candidates"]:
        prefix = f"relation_candidate/{candidate['candidate_id']}"
        expected_roles.add(f"{prefix}/proposal")
        if candidate["replay_sha256"] is not None:
            expected_roles.add(f"{prefix}/replay")
        if candidate["certificate_sha256"] is not None:
            expected_roles.add(f"{prefix}/certificate")
    for tool in tools:
        prefix = f"tool/{tool['name']}"
        expected_roles.update({f"{prefix}/adapter", f"{prefix}/version"})
        if tool["executable_sha256"] is not None:
            expected_roles.add(f"{prefix}/executable")
        if tool["status"] in {"ran", "timeout", "error"}:
            expected_roles.update({f"{prefix}/script", f"{prefix}/transcript"})
    _validate_expected_roles(by_role, bindings, expected_roles)
    _self_hash(envelope, "envelope_sha256", "envelope")
    semantic_receipts: list[str] = []
    if evidence_root is not None:
        roster_row, _freeze = _semantic_roster_prime_freeze(
            raw_by_role, bindings, row_id
        )
        semantic_receipts.append("freeze_roster_prime_seed")
        private_source, _public_source, _link = _semantic_public_boundary(
            raw_by_role, bindings, roster_row
        )
        semantic_receipts.append("public_private_redaction")
        lift = _json_bytes(raw_by_role["lift"], "lift")
        local = _json_bytes(raw_by_role["local"], "local")
        if not isinstance(lift, dict):
            raise ProvenanceError("lift", "lift evidence must be an object")
        if lift.get("row_id") != row_id or lift.get("r") != bindings["r"]:
            raise ProvenanceError("lift", "lift row/r binding mismatch")
        if local is not None and not isinstance(local, dict):
            raise ProvenanceError("local", "local evidence must be object or null")
        _semantic_tools(raw_by_role, tools, lift)
        semantic_receipts.append("tool_adapter_version_script_transcript")
        _semantic_relation_inventory(
            raw_by_role,
            inventory,
            row_id,
            bindings["r"],
            lift,
            private_source,
            local,
        )
        semantic_receipts.append("relation_inventory_and_certificates")
        _semantic_work_report(raw_by_role["work_report"], work)
        semantic_receipts.append("work_accounting")
    return {
        "schema": "xedni.rank-decay-row-provenance-validation/v1",
        "status": "HASH_GRAPH_ONLY",
        "files_verified": evidence_root is not None,
        "semantic_receipts": semantic_receipts,
        "production_eligible": False,
        "production_blockers": [
            "no independent execution-receipt verifier is trusted",
            "no complete relation-lattice absence verifier is implemented",
        ],
        "row_id": row_id,
        "artifact_count": len(by_role),
        "tool_count": len(tools),
        "relation_status": inventory["status"],
        "selected_dependence": inventory["selected_dependence"],
        "candidate_count": inventory["candidate_count"],
        "work_complete": work["complete"],
        "envelope_sha256": envelope["envelope_sha256"],
    }


def _strict_object(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProvenanceError("json", f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ProvenanceError("json", f"non-finite number {value!r}")
            ),
        )
    except UnicodeError as exc:
        raise ProvenanceError("json", f"invalid UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProvenanceError("json", f"invalid JSON: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelope", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_envelope(
            load_strict_json(args.envelope), args.evidence_root
        )
    except ProvenanceError as exc:
        print(
            json.dumps(
                {"schema": "xedni.rank-decay-row-provenance-validation/v1", "status": "FAIL", "error_code": exc.code, "error": str(exc)},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(2)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

