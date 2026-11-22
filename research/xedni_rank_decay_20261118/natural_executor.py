#!/usr/bin/env python3
"""Fail-closed, resumable orchestration skeleton for natural Xedni rows.

This module does not authorize a natural run and has no command-line launcher.
It supplies the missing row-level state machine so a future, separately frozen
runner can inject checkpoint, tool, public-boundary, provenance, and stage
adapters.  The public adapters must be real isolated subprocess adapters; an
in-process Python callable is sufficient only for unit controls.

The executor deliberately treats every bounded relation-search no-hit as
``UNKNOWN``.  Only an exact private replay with a nontrivial relation and an
invertible target coefficient can produce ``CERTIFIED_RECOVERY``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, Mapping

import public_boundary
import rank_magma
import rank_pari
import relation_certificate


SCHEMA = "xedni.natural-executor/v1"
PREFLIGHT_SCHEMA = "xedni.natural-executor-preflight/v1"
ROW_SCHEMA = "xedni.natural-executor-row/v1"
STAGE_SCHEMA = "xedni.natural-executor-stage/v1"
GATE_RESULT_SCHEMA = "xedni.natural-executor-gate-result/v1"
VALIDATOR_RESULT_SCHEMA = "xedni.natural-executor-validator-result/v1"
PRIVATE_LINK_SCHEMA = public_boundary.LINK_SCHEMA
RELATION_VALUE_SCHEMA = "xedni.relation-proposal-set/v1"
EVALUATOR_VALUE_SCHEMA = "xedni.private-evaluator-result/v1"
PROVENANCE_VALUE_SCHEMA = "xedni.row-provenance-result/v1"
RANK_VALUE_SCHEMA = "xedni.rank-cascade-result/v1"
PRODUCTION_READY = False
PRODUCTION_BLOCKERS = (
    "no signed independent verifier backend is configured",
    "public_boundary.PRODUCTION_READY is false",
    "executor is not integrated into runner.py or the authorizing freeze",
)

GATE_NAMES = (
    "checkpoint",
    "tools",
    "public_boundary",
    "provenance",
)
STAGE_NAMES = (
    "source",
    "redact",
    "local",
    "lift",
    "invariants",
    "relation",
    "rank",
    "evaluate",
    "provenance",
)
PUBLIC_STAGE_NAMES = ("local", "lift", "invariants", "relation", "rank")
PUBLIC_ROW_KEYS = ("bits", "slot", "p", "family", "r", "lift", "local_arm")
GOOD_STAGE_STATUSES = {"PASS", "OK", "COMPLETE", "UNKNOWN", "CERTIFIED"}
FORBIDDEN_PUBLIC_KEY_FRAGMENTS = (
    "scalar",
    "secret",
    "private",
    "target_log",
    "dlog",
    "master_seed",
    "source_seed",
)
SENSITIVE_CONFIG_FRAGMENTS = (
    "token",
    "password",
    "credential",
    "access_key",
    "secret_key",
    "private_key",
)
ALLOWED_COMMITMENT_KEYS = {
    "private_source_sha256",
    "private_link_sha256",
    "nonce_commitment_sha256",
}


class ExecutorError(RuntimeError):
    """A fail-closed executor error with a stable machine code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        stage: str | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.evidence = dict(evidence or {})


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ExecutorError("nonfinite_or_nonjson", f"value is not finite JSON: {error}") from error


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_commit(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


def _without_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def _bind_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result[field] = object_sha256(_without_hash(result, field))
    return result


def _validate_bound_hash(value: Mapping[str, Any], field: str, code: str) -> None:
    observed = value.get(field)
    expected = object_sha256(_without_hash(value, field))
    if observed != expected:
        raise ExecutorError(
            code,
            f"{field} mismatch",
            evidence={"expected": expected, "observed": observed},
        )


def _validate_nonnegative_tree(value: Any, path: str = "work") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ExecutorError("work_schema", f"{path} has a non-string/empty key")
            _validate_nonnegative_tree(item, f"{path}.{key}")
        return
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ExecutorError(
            "work_schema", f"{path} must contain only nonnegative numeric leaves"
        )


def _scan_public_keys(value: Any, path: str = "public") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                errors.append(f"{path}: non-string key")
                continue
            lowered = key.lower()
            if any(fragment in lowered for fragment in FORBIDDEN_PUBLIC_KEY_FRAGMENTS):
                errors.append(f"{path}.{key}")
            errors.extend(_scan_public_keys(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_scan_public_keys(item, f"{path}[{index}]"))
    return errors


def _reject_sensitive_config(value: Any, path: str = "config") -> None:
    """Reject credential material recursively, including command arguments."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ExecutorError("config_secret", f"{path} has a non-string key")
            lowered = key.lower()
            if any(fragment in lowered for fragment in SENSITIVE_CONFIG_FRAGMENTS):
                raise ExecutorError("config_secret", f"sensitive key at {path}.{key}")
            _reject_sensitive_config(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_sensitive_config(item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in SENSITIVE_CONFIG_FRAGMENTS):
            raise ExecutorError("config_secret", f"sensitive string at {path}")


def _strict_checks(checks: Any, path: str) -> dict[str, bool]:
    if not isinstance(checks, Mapping) or not checks:
        raise ExecutorError("check_schema", f"{path} checks must be nonempty")
    retained: dict[str, bool] = {}
    for key, value in checks.items():
        if not isinstance(key, str) or not key or not isinstance(value, bool):
            raise ExecutorError("check_schema", f"{path} checks must be named booleans")
        retained[key] = value
    return retained


def _assert_exact_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    if set(value) != expected:
        raise ExecutorError(
            "schema_keys",
            f"{path} keys differ",
            evidence={
                "missing": sorted(expected - set(value)),
                "extra": sorted(set(value) - expected),
            },
        )


def _public_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project only construction factors; never expose source/index seeds."""
    if any(key not in row for key in PUBLIC_ROW_KEYS):
        raise ExecutorError("row_schema", "row lacks a required public factor")
    return {key: json.loads(canonical_json(row[key])) for key in PUBLIC_ROW_KEYS}


@dataclass(frozen=True)
class ExecutorConfig:
    """Frozen bindings for one execution attempt."""

    run_id: str
    stage: str
    natural_rows_authorized: bool
    freeze_sha256: str
    roster_sha256: str
    implementation_commit: str
    command: tuple[str, ...]
    tool_pins: Mapping[str, Any]
    row_token_nonce_sha256: str
    verifier_identity_sha256: str
    production: bool

    def validate(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id:
            raise ExecutorError("config", "run_id must be nonempty")
        if self.stage not in {"calibration", "sentinel", "discovery", "replication"}:
            raise ExecutorError("config", f"unsupported stage {self.stage!r}")
        if self.natural_rows_authorized is not True:
            raise ExecutorError(
                "natural_rows_not_authorized",
                "a committed authorizing freeze is required",
            )
        if not _is_sha256(self.freeze_sha256) or not _is_sha256(self.roster_sha256):
            raise ExecutorError("config", "freeze and roster hashes must be SHA-256")
        if not _is_commit(self.implementation_commit):
            raise ExecutorError("config", "implementation_commit must be a full commit")
        if (
            not isinstance(self.command, tuple)
            or not self.command
            or any(not isinstance(item, str) or not item for item in self.command)
        ):
            raise ExecutorError("config", "command must be a nonempty tuple of strings")
        if not isinstance(self.tool_pins, Mapping) or not self.tool_pins:
            raise ExecutorError("config", "tool_pins must be a nonempty mapping")
        if not _is_sha256(self.row_token_nonce_sha256):
            raise ExecutorError("config", "row token nonce commitment must be SHA-256")
        if not _is_sha256(self.verifier_identity_sha256):
            raise ExecutorError("config", "verifier identity must be SHA-256")
        if not isinstance(self.production, bool):
            raise ExecutorError("config", "production must be boolean")
        if self.production and not (PRODUCTION_READY and public_boundary.PRODUCTION_READY):
            raise ExecutorError(
                "production_blocked",
                "this executor has no signed production verifier backend",
                evidence={"blockers": list(PRODUCTION_BLOCKERS)},
            )
        _reject_sensitive_config(self.command, "config.command")
        _reject_sensitive_config(self.tool_pins, "config.tool_pins")
        if set(self.tool_pins) != {"pari", "magma"}:
            raise ExecutorError("tool_pins", "tool_pins must contain exactly pari and magma")
        pari = self.tool_pins["pari"]
        magma = self.tool_pins["magma"]
        if not isinstance(pari, Mapping) or not isinstance(magma, Mapping):
            raise ExecutorError("tool_pins", "tool pins must be objects")
        _assert_exact_keys(
            pari,
            {"version", "image_digest", "wrapper_sha256"},
            "tool_pins.pari",
        )
        _assert_exact_keys(
            magma,
            {"version", "executable_sha256", "license_fingerprint_sha256"},
            "tool_pins.magma",
        )
        if (
            not isinstance(pari["version"], str)
            or not pari["version"]
            or not isinstance(pari["image_digest"], str)
            or not pari["image_digest"].startswith("sha256:")
            or not _is_sha256(pari["image_digest"][7:])
            or not _is_sha256(pari["wrapper_sha256"])
        ):
            raise ExecutorError("tool_pins", "invalid strict PARI pin")
        if (
            not isinstance(magma["version"], str)
            or not magma["version"]
            or not _is_sha256(magma["executable_sha256"])
            or not _is_sha256(magma["license_fingerprint_sha256"])
        ):
            raise ExecutorError("tool_pins", "invalid strict Magma pin")

    def binding(self) -> dict[str, Any]:
        self.validate()
        tool_pins = json.loads(canonical_json(self.tool_pins))
        return {
            "schema": SCHEMA,
            "run_id": self.run_id,
            "stage": self.stage,
            "freeze_sha256": self.freeze_sha256,
            "roster_sha256": self.roster_sha256,
            "implementation_commit": self.implementation_commit,
            "command": list(self.command),
            "command_sha256": object_sha256(list(self.command)),
            "tool_pins": tool_pins,
            "tool_pins_sha256": object_sha256(tool_pins),
            "row_token_nonce_sha256": self.row_token_nonce_sha256,
            "verifier_identity_sha256": self.verifier_identity_sha256,
            "production": False,
            "production_ready": False,
        }


@dataclass(frozen=True)
class ExecutorAdapters:
    """Injected gates and computation stages.

    Each gate accepts ``binding=...`` and returns ``{"status":"PASS", ...}``.
    Computational adapters accept keyword arguments and return a stage record
    with ``status``, ``value``, and a nonnegative ``work`` mapping.
    """

    checkpoint_gate: Callable[..., Mapping[str, Any]]
    tool_gate: Callable[..., Mapping[str, Any]]
    public_boundary_gate: Callable[..., Mapping[str, Any]]
    provenance_gate: Callable[..., Mapping[str, Any]]
    source: Callable[..., Mapping[str, Any]]
    redact: Callable[..., Mapping[str, Any]]
    local: Callable[..., Mapping[str, Any]]
    lift: Callable[..., Mapping[str, Any]]
    invariants: Callable[..., Mapping[str, Any]]
    relation: Callable[..., Mapping[str, Any]]
    rank: Callable[..., Mapping[str, Any]]
    evaluate: Callable[..., Mapping[str, Any]]
    provenance: Callable[..., Mapping[str, Any]]
    preflight_verifier: Callable[..., Mapping[str, Any]]
    artifact_verifier: Callable[..., Mapping[str, Any]]


def _validate_roster(roster: Mapping[str, Any], config: ExecutorConfig) -> None:
    if not isinstance(roster, Mapping):
        raise ExecutorError("roster_schema", "roster must be an object")
    if roster.get("stage") != config.stage:
        raise ExecutorError("roster_stage", "roster stage differs from execution stage")
    if roster.get("roster_sha256") != config.roster_sha256:
        raise ExecutorError("roster_binding", "config does not bind this roster")
    expected = object_sha256(_without_hash(roster, "roster_sha256"))
    if roster.get("roster_sha256") != expected:
        raise ExecutorError(
            "roster_hash",
            "roster self-hash failed",
            evidence={"expected": expected, "observed": roster.get("roster_sha256")},
        )
    executable = roster.get("executable_roster")
    if not isinstance(executable, list):
        raise ExecutorError("roster_schema", "missing executable_roster")


def _find_roster_row(
    roster: Mapping[str, Any], row: Mapping[str, Any]
) -> dict[str, Any]:
    if not isinstance(row, Mapping) or not isinstance(row.get("row_id"), str):
        raise ExecutorError("row_schema", "row must have a string row_id")
    matches = [item for item in roster["executable_roster"] if item.get("row_id") == row["row_id"]]
    if len(matches) != 1:
        raise ExecutorError("row_roster", "row_id is not unique in executable roster")
    frozen = matches[0]
    if canonical_json(frozen) != canonical_json(row):
        raise ExecutorError("row_roster", "row differs from its frozen roster entry")
    if frozen.get("status") != "PLANNED":
        raise ExecutorError("row_status", "only PLANNED executable rows may run")
    r = frozen.get("r")
    if isinstance(r, bool) or not isinstance(r, int) or not 2 <= r <= 6:
        raise ExecutorError("row_map", "executor skeleton admits only certified r=2..6 rows")
    return json.loads(canonical_json(frozen))


def _gate_attempt(
    name: str, result: Mapping[str, Any], binding_sha256: str
) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise ExecutorError("gate_schema", f"{name} gate returned a non-object")
    retained = json.loads(canonical_json(result))
    _assert_exact_keys(
        retained,
        {"schema", "name", "status", "binding_sha256", "checks", "evidence"},
        f"gate.{name}",
    )
    if retained["schema"] != GATE_RESULT_SCHEMA or retained["name"] != name:
        raise ExecutorError("gate_schema", f"{name} gate identity differs")
    if retained["binding_sha256"] != binding_sha256:
        raise ExecutorError("gate_binding", f"{name} gate binds another run")
    checks = _strict_checks(retained["checks"], f"gate.{name}")
    if retained["status"] not in {"PASS", "FAIL"}:
        raise ExecutorError("gate_schema", f"{name} gate has invalid status")
    if (retained["status"] == "PASS") != all(checks.values()):
        raise ExecutorError("gate_status", f"{name} gate status contradicts checks")
    if not isinstance(retained["evidence"], Mapping):
        raise ExecutorError("gate_schema", f"{name} gate evidence is not an object")
    if name == "public_boundary" and retained["status"] == "PASS":
        evidence = retained["evidence"]
        _assert_exact_keys(
            evidence,
            {"formula_spec", "module_sha256", "production_ready"},
            "gate.public_boundary.evidence",
        )
        public_boundary.validate_m3_formula_spec(evidence["formula_spec"])
        if evidence["module_sha256"] != file_sha256(Path(public_boundary.__file__)):
            raise ExecutorError("public_boundary_gate", "public-boundary module hash differs")
        if evidence["production_ready"] is not False:
            raise ExecutorError("public_boundary_gate", "unexpected production readiness claim")
    attempt = {
        "name": name,
        "status": retained["status"],
        "result": retained,
        "result_sha256": object_sha256(retained),
    }
    return _bind_hash(attempt, "receipt_sha256")


def _validate_gate_attempt(
    name: str, attempt: Mapping[str, Any], binding_sha256: str
) -> None:
    if not isinstance(attempt, Mapping):
        raise ExecutorError("gate_receipt", f"{name} gate receipt is not an object")
    _assert_exact_keys(
        attempt,
        {"name", "status", "result", "result_sha256", "receipt_sha256"},
        f"gate_receipt.{name}",
    )
    _validate_bound_hash(attempt, "receipt_sha256", "gate_receipt_hash")
    if attempt["name"] != name or attempt["result_sha256"] != object_sha256(attempt["result"]):
        raise ExecutorError("gate_receipt", f"{name} gate receipt binding failed")
    replayed = _gate_attempt(name, attempt["result"], binding_sha256)
    if canonical_json(replayed) != canonical_json(attempt):
        raise ExecutorError("gate_receipt", f"{name} gate receipt replay differs")


def _validator_result(
    name: str,
    result: Mapping[str, Any],
    subject_sha256: str,
    verifier_identity_sha256: str,
) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise ExecutorError("validator_schema", f"{name} verifier returned a non-object")
    retained = json.loads(canonical_json(result))
    _assert_exact_keys(
        retained,
        {
            "schema",
            "name",
            "status",
            "subject_sha256",
            "current_input_sha256",
            "verifier_identity_sha256",
            "signature_backend",
            "signature",
            "checks",
            "evidence",
        },
        f"validator.{name}",
    )
    if retained["schema"] != VALIDATOR_RESULT_SCHEMA or retained["name"] != name:
        raise ExecutorError("validator_schema", f"{name} verifier identity differs")
    if retained["subject_sha256"] != subject_sha256:
        raise ExecutorError("validator_binding", f"{name} verifier binds another subject")
    if (
        retained["current_input_sha256"] != subject_sha256
        or retained["verifier_identity_sha256"] != verifier_identity_sha256
    ):
        raise ExecutorError("validator_binding", f"{name} verifier identity/input differs")
    if retained["signature_backend"] != "UNVERIFIED_CONTROL" or not _is_sha256(
        retained["signature"]
    ):
        raise ExecutorError("validator_signature", f"{name} has no accepted control signature")
    checks = _strict_checks(retained["checks"], f"validator.{name}")
    if retained["status"] != "PASS" or not all(checks.values()):
        raise ExecutorError("validator_failed", f"{name} verifier did not pass")
    if not isinstance(retained["evidence"], Mapping):
        raise ExecutorError("validator_schema", f"{name} verifier evidence is not an object")
    return _bind_hash(
        {
            "name": name,
            "status": "PASS",
            "result": retained,
            "result_sha256": object_sha256(retained),
        },
        "receipt_sha256",
    )


def _validate_validator_receipt(
    name: str,
    receipt: Mapping[str, Any],
    subject_sha256: str,
    verifier_identity_sha256: str,
) -> None:
    if not isinstance(receipt, Mapping):
        raise ExecutorError("validator_receipt", f"{name} verifier receipt is not an object")
    _assert_exact_keys(
        receipt,
        {"name", "status", "result", "result_sha256", "receipt_sha256"},
        f"validator_receipt.{name}",
    )
    _validate_bound_hash(receipt, "receipt_sha256", "validator_receipt_hash")
    if receipt["result_sha256"] != object_sha256(receipt["result"]):
        raise ExecutorError("validator_receipt", f"{name} verifier result hash differs")
    replayed = _validator_result(
        name,
        receipt["result"],
        subject_sha256,
        verifier_identity_sha256,
    )
    if canonical_json(replayed) != canonical_json(receipt):
        raise ExecutorError("validator_receipt", f"{name} verifier receipt replay differs")


def _normalize_stage(name: str, result: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise ExecutorError("stage_schema", f"{name} returned a non-object", stage=name)
    retained = json.loads(canonical_json(result))
    expected_keys = {"status", "adapter_status", "value", "work"}
    if "execution" in retained:
        expected_keys.add("execution")
    _assert_exact_keys(retained, expected_keys, f"stage_result.{name}")
    if retained.get("status") != "PASS" or retained.get("adapter_status") != "PASS":
        raise ExecutorError(
            "stage_status",
            f"{name} did not return PASS/PASS",
            stage=name,
            evidence=retained,
        )
    if "value" not in retained:
        raise ExecutorError("stage_schema", f"{name} lacks value", stage=name)
    work = retained.get("work")
    if not isinstance(work, Mapping):
        raise ExecutorError("work_schema", f"{name} lacks work accounting", stage=name)
    _validate_nonnegative_tree(work, f"{name}.work")
    execution = retained.get("execution")
    if execution is not None:
        if not isinstance(execution, Mapping):
            raise ExecutorError(
                "execution_schema", f"{name}.execution is not an object", stage=name
            )
        timeout = execution.get("timeout_seconds")
        timed_out = execution.get("timed_out")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout < 0:
            raise ExecutorError(
                "execution_schema", f"{name} has invalid timeout_seconds", stage=name
            )
        if not isinstance(timed_out, bool):
            raise ExecutorError("execution_schema", f"{name} has invalid timed_out", stage=name)
    stage = {
        "schema": STAGE_SCHEMA,
        "name": name,
        "status": retained["status"],
        "result": retained,
        "result_sha256": object_sha256(retained),
    }
    if execution is not None:
        stage["execution_sha256"] = object_sha256(execution)
    return _bind_hash(stage, "stage_sha256")


def _validate_stage_record(name: str, stage: Mapping[str, Any]) -> None:
    if not isinstance(stage, Mapping):
        raise ExecutorError("stage_record", f"{name} stage is not an object")
    expected = {"schema", "name", "status", "result", "result_sha256", "stage_sha256"}
    if isinstance(stage.get("result"), Mapping) and "execution" in stage["result"]:
        expected.add("execution_sha256")
    _assert_exact_keys(stage, expected, f"stage.{name}")
    _validate_bound_hash(stage, "stage_sha256", "stage_hash")
    if stage["schema"] != STAGE_SCHEMA or stage["name"] != name:
        raise ExecutorError("stage_record", f"{name} stage identity differs")
    if stage["result_sha256"] != object_sha256(stage["result"]):
        raise ExecutorError("stage_record", f"{name} result hash differs")
    replayed = _normalize_stage(name, stage["result"])
    if canonical_json(replayed) != canonical_json(stage):
        raise ExecutorError("stage_record", f"{name} stage replay differs")


def _merge_numeric(target: dict[str, Any], source: Mapping[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, Mapping):
            child = target.setdefault(key, {})
            if not isinstance(child, dict):
                raise ExecutorError("work_schema", f"work shape conflict at {key}")
            _merge_numeric(child, value)
        else:
            target[key] = target.get(key, 0) + value


def _aggregate_work(
    stages: Mapping[str, Mapping[str, Any]], *, failure_safe: bool = False
) -> dict[str, Any]:
    aggregate: dict[str, Any] = {}
    try:
        for stage in stages.values():
            _merge_numeric(aggregate, stage["result"]["work"])
    except Exception as error:
        if not failure_safe:
            raise
        return {
            "aggregation_failed": 1,
            "retained_stage_work_sha256": hashlib.sha256(
                repr(
                    [
                        stage.get("result", {}).get("work")
                        if isinstance(stage, Mapping)
                        else None
                        for stage in stages.values()
                    ]
                ).encode()
            ).hexdigest(),
            "aggregation_error_sha256": hashlib.sha256(
                f"{type(error).__name__}:{error}".encode()
            ).hexdigest(),
        }
    return aggregate


def _summarize_private_source(
    stage: Mapping[str, Any], private_source: Any
) -> dict[str, Any]:
    """Replace private source contents with a one-way commitment."""
    result = json.loads(canonical_json(stage["result"]))
    result["value"] = {
        "status": "PRIVATE_EVALUATOR_ONLY",
        "private_source_sha256": object_sha256(private_source),
    }
    return _normalize_stage("source", result)


def _validate_private_link(
    private_link: Any, private_source: Any, public_source: Mapping[str, Any]
) -> dict[str, Any]:
    try:
        validated_public = public_boundary.validate_public_source(public_source)
        link = public_boundary.validate_link(private_link)
        public_boundary.verify_redaction_link(private_source, validated_public, link)
    except (ValueError, TypeError) as error:
        raise ExecutorError(
            "private_link",
            "public_boundary exact redaction/link replay failed",
            stage="redact",
        ) from error
    return link


def _relation_input_sha256(
    row_token: str,
    public_source: Mapping[str, Any],
    lift: Any,
    invariants: Any,
) -> str:
    return object_sha256(
        {
            "row_token": row_token,
            "public_source_sha256": object_sha256(public_source),
            "lift_sha256": object_sha256(lift),
            "invariants_sha256": object_sha256(invariants),
        }
    )


def _validate_relation_value(value: Any, expected_input_sha256: str, r: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ExecutorError("relation_schema", "relation value is not an object", stage="relation")
    retained = json.loads(canonical_json(value))
    _assert_exact_keys(
        retained,
        {
            "schema",
            "public_input_sha256",
            "finder_outcome",
            "bounded_search_only",
            "candidates",
            "candidate_set_sha256",
        },
        "relation_value",
    )
    if retained["schema"] != RELATION_VALUE_SCHEMA:
        raise ExecutorError("relation_schema", "relation schema differs", stage="relation")
    if retained["public_input_sha256"] != expected_input_sha256:
        raise ExecutorError("relation_binding", "relation binds another public input", stage="relation")
    if retained["bounded_search_only"] is not True:
        raise ExecutorError("relation_schema", "relation search scope must remain bounded", stage="relation")
    candidates = retained["candidates"]
    if not isinstance(candidates, list):
        raise ExecutorError("relation_schema", "relation candidates must be a list", stage="relation")
    seen: set[str] = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            raise ExecutorError("relation_schema", f"candidate {index} is not an object", stage="relation")
        _assert_exact_keys(
            candidate,
            {"candidate_id", "vector", "public_input_sha256", "proposal_sha256"},
            f"relation.candidates[{index}]",
        )
        vector = candidate["vector"]
        if (
            not isinstance(vector, list)
            or len(vector) != r
            or any(isinstance(item, bool) or not isinstance(item, int) for item in vector)
            or not any(vector)
        ):
            raise ExecutorError("relation_schema", f"candidate {index} vector is invalid", stage="relation")
        if candidate["public_input_sha256"] != expected_input_sha256:
            raise ExecutorError("relation_binding", f"candidate {index} input differs", stage="relation")
        proposal_subject = {
            "candidate_id": candidate["candidate_id"],
            "vector": vector,
            "public_input_sha256": expected_input_sha256,
        }
        if candidate["proposal_sha256"] != object_sha256(proposal_subject):
            raise ExecutorError("relation_binding", f"candidate {index} proposal hash differs", stage="relation")
        expected_id = object_sha256(
            {"vector": vector, "public_input_sha256": expected_input_sha256}
        )
        if candidate["candidate_id"] != expected_id or expected_id in seen:
            raise ExecutorError("relation_binding", f"candidate {index} ID is invalid/duplicate", stage="relation")
        seen.add(expected_id)
    if retained["candidate_set_sha256"] != object_sha256(candidates):
        raise ExecutorError("relation_binding", "candidate-set hash differs", stage="relation")
    expected_outcome = (
        "EXACT_Q_RELATION_PROPOSED"
        if candidates
        else "NO_EXACT_Q_RELATION_WITHIN_FROZEN_BUDGET"
    )
    if retained["finder_outcome"] != expected_outcome:
        raise ExecutorError("relation_schema", "finder outcome contradicts candidates", stage="relation")
    return retained


def _validate_evaluator_value(
    value: Any,
    relation: Mapping[str, Any],
    expected_input_sha256: str,
    private_link: Mapping[str, Any],
    private_source: Mapping[str, Any],
    lift: Mapping[str, Any],
    local_config: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(value, Mapping):
        raise ExecutorError("evaluator_schema", "evaluator value is not an object", stage="evaluate")
    retained = json.loads(canonical_json(value))
    _assert_exact_keys(
        retained,
        {
            "schema",
            "status",
            "public_input_sha256",
            "private_link_sha256",
            "candidate_id",
            "proposal_sha256",
            "certificate",
            "certificate_sha256",
        },
        "evaluator_value",
    )
    if retained["schema"] != EVALUATOR_VALUE_SCHEMA:
        raise ExecutorError("evaluator_schema", "evaluator schema differs", stage="evaluate")
    if retained["public_input_sha256"] != expected_input_sha256:
        raise ExecutorError("evaluator_binding", "evaluator public input differs", stage="evaluate")
    if retained["private_link_sha256"] != object_sha256(private_link):
        raise ExecutorError("evaluator_binding", "evaluator private link differs", stage="evaluate")
    candidates = {item["candidate_id"]: item for item in relation["candidates"]}
    if retained["status"] == "NO_CERTIFIED_CANDIDATE":
        if any(retained[key] is not None for key in ("candidate_id", "proposal_sha256", "certificate", "certificate_sha256")):
            raise ExecutorError("evaluator_schema", "empty evaluator result contains a certificate", stage="evaluate")
        return False
    if retained["status"] != "EXACT_REPLAY_CERTIFIED":
        raise ExecutorError("evaluator_schema", "invalid evaluator status", stage="evaluate")
    candidate = candidates.get(retained["candidate_id"])
    if candidate is None or retained["proposal_sha256"] != candidate["proposal_sha256"]:
        raise ExecutorError("evaluator_binding", "evaluator candidate/proposal is not in relation set", stage="evaluate")
    certificate = retained["certificate"]
    if not isinstance(certificate, Mapping):
        raise ExecutorError("evaluator_schema", "certificate is not an object", stage="evaluate")
    if retained["certificate_sha256"] != object_sha256(certificate):
        raise ExecutorError("evaluator_binding", "certificate hash differs", stage="evaluate")
    errors = relation_certificate.verify_relation_certificate(
        dict(certificate), dict(lift), dict(private_source),
        None if local_config is None else dict(local_config),
    )
    if errors:
        raise ExecutorError(
            "evaluator_certificate",
            "exact relation-certificate arithmetic replay failed",
            stage="evaluate",
            evidence={"errors": errors},
        )
    if certificate.get("relation", {}).get("supplied_coefficients") != candidate["vector"]:
        raise ExecutorError("evaluator_binding", "certificate relation differs", stage="evaluate")
    outcome = certificate.get("outcome", {})
    return (
        outcome.get("useful_recovery") == "CERT_YES"
        and outcome.get("relation_proof_verified") is True
        and outcome.get("source_replay_proof_verified") is True
    )


def _validate_provenance_value(value: Any, subject_sha256: str) -> None:
    if not isinstance(value, Mapping):
        raise ExecutorError("provenance_schema", "provenance value is not an object", stage="provenance")
    _assert_exact_keys(
        value,
        {"schema", "status", "subject_sha256", "checks"},
        "provenance_value",
    )
    if value["schema"] != PROVENANCE_VALUE_SCHEMA or value["status"] != "PASS":
        raise ExecutorError("provenance_failed", "provenance status is not PASS", stage="provenance")
    if value["subject_sha256"] != subject_sha256:
        raise ExecutorError("provenance_binding", "provenance binds another draft", stage="provenance")
    checks = _strict_checks(value["checks"], "provenance")
    if not all(checks.values()):
        raise ExecutorError("provenance_failed", "provenance checks did not all pass", stage="provenance")


def _replay_rank_adapter(
    result: Any, row: Mapping[str, Any], module: Any, tool_name: str
) -> str:
    if not isinstance(result, Mapping):
        raise ExecutorError("rank_schema", f"{tool_name} result is not an object", stage="rank")
    row_id, r_value, ainvs = rank_pari.validate_row(dict(row))
    if (
        result.get("adapter") != module.ADAPTER
        or result.get("schema_version") != module.SCHEMA_VERSION
        or result.get("input_sha256") != rank_pari._input_hash(dict(row))
        or result.get("row_id") != row_id
        or result.get("r") != r_value
        or result.get("ainvs") != [str(value) for value in ainvs]
    ):
        raise ExecutorError("rank_binding", f"{tool_name} result binding differs", stage="rank")
    execution = result.get("execution")
    if not isinstance(execution, Mapping):
        raise ExecutorError("rank_schema", f"{tool_name} execution is absent", stage="rank")
    script = execution.get("script")
    if not isinstance(script, str) or execution.get("script_sha256") != hashlib.sha256(script.encode()).hexdigest():
        raise ExecutorError("rank_binding", f"{tool_name} script hash differs", stage="rank")
    if execution.get("timed_out") is True:
        if result.get("classification") != "UNKNOWN":
            raise ExecutorError("rank_replay", f"{tool_name} timeout was promoted", stage="rank")
        return "UNKNOWN"
    if execution.get("returncode") != 0:
        if result.get("classification") != "UNKNOWN":
            raise ExecutorError("rank_replay", f"{tool_name} failure was promoted", stage="rank")
        return "UNKNOWN"
    try:
        parsed = module.parse_transcript(execution.get("stdout", ""))
    except ValueError as error:
        raise ExecutorError("rank_replay", f"{tool_name} transcript failed replay", stage="rank") from error
    lower, upper = parsed["LOWER"], parsed["UPPER"]
    classification, _ = rank_pari.classify(lower, upper, r_value)
    if (
        result.get("rank_bounds") != {"lower": lower, "upper": upper}
        or result.get("classification") != classification
    ):
        raise ExecutorError("rank_replay", f"{tool_name} rank bounds differ", stage="rank")
    return classification


def _validate_rank_value(value: Any) -> str:
    if not isinstance(value, Mapping):
        raise ExecutorError("rank_schema", "rank value is not an object", stage="rank")
    _assert_exact_keys(
        value,
        {"schema", "status", "row", "pari", "magma", "classification"},
        "rank_value",
    )
    if value["schema"] != RANK_VALUE_SCHEMA or value["status"] != "PASS":
        raise ExecutorError("rank_schema", "rank value status/schema differs", stage="rank")
    pari_class = _replay_rank_adapter(value["pari"], value["row"], rank_pari, "pari")
    magma_class = _replay_rank_adapter(value["magma"], value["row"], rank_magma, "magma")
    replayed = pari_class if pari_class == magma_class and pari_class in {"CERT_LT", "CERT_GE"} else "UNKNOWN"
    if value["classification"] != replayed:
        raise ExecutorError("rank_replay", "combined rank classification differs", stage="rank")
    return replayed


def _endpoints(
    rank_stage: Mapping[str, Any], exact_recovery: bool
) -> dict[str, str]:
    rank_class = _validate_rank_value(rank_stage["result"]["value"])

    useful = "CERTIFIED_RECOVERY" if exact_recovery else "UNKNOWN"
    dependence = (
        "CERTIFIED_DEPENDENT"
        if rank_class == "CERT_LT" or exact_recovery
        else "UNKNOWN"
    )
    return {
        "curve_rank": rank_class,
        "selected_dependence": dependence,
        "useful_recovery": useful,
    }


def _artifact_path(output_dir: Path, row_id: str) -> Path:
    safe_id = hashlib.sha256(row_id.encode()).hexdigest()
    return output_dir / "rows" / safe_id[:2] / f"{safe_id}.json"


def _contains_exact_list(value: Any, target: list[Any]) -> bool:
    if isinstance(value, list):
        if value == target:
            return True
        return any(_contains_exact_list(item, target) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_exact_list(item, target) for item in value.values())
    return False


def _assert_no_private_source(artifact: Mapping[str, Any], private_source: Any) -> None:
    if isinstance(private_source, Mapping):
        scalars = private_source.get("ordered_scalars")
        if isinstance(scalars, list) and scalars and _contains_exact_list(artifact, scalars):
            raise ExecutorError("private_retention", "final artifact retains ordered scalars")
    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                lowered = str(key).lower()
                if (
                    any(fragment in lowered for fragment in ("ordered_scalars", "target_scalar", "source_scalar"))
                    and key not in ALLOWED_COMMITMENT_KEYS
                ):
                    raise ExecutorError("private_retention", f"private key retained at {path}.{key}")
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")
    walk(artifact, "artifact")


def _process_start_ticks(pid: int) -> str | None:
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ExecutorError("lock_process", f"cannot inspect process {pid}: {error}") from error
    closing = text.rfind(")")
    fields = text[closing + 2 :].split() if closing >= 0 else []
    if len(fields) < 20:
        raise ExecutorError("lock_process", f"cannot parse process identity for {pid}")
    return fields[19]


def _lock_record(binding_sha256: str, row_sha256: str) -> dict[str, Any]:
    pid = os.getpid()
    start_ticks = _process_start_ticks(pid)
    if start_ticks is None:
        raise ExecutorError("lock_process", "current process identity is unavailable")
    return _bind_hash(
        {
            "schema": "xedni.natural-executor-lock/v1",
            "pid": pid,
            "process_start_ticks": start_ticks,
            "binding_sha256": binding_sha256,
            "row_sha256": row_sha256,
        },
        "lock_sha256",
    )


def _read_lock(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutorError("stale_lock_unverifiable", f"cannot verify lock {path}: {error}") from error
    if not isinstance(value, dict):
        raise ExecutorError("stale_lock_unverifiable", "lock root is not an object")
    _assert_exact_keys(
        value,
        {"schema", "pid", "process_start_ticks", "binding_sha256", "row_sha256", "lock_sha256"},
        "lock",
    )
    _validate_bound_hash(value, "lock_sha256", "lock_hash")
    if value["schema"] != "xedni.natural-executor-lock/v1":
        raise ExecutorError("stale_lock_unverifiable", "lock schema differs")
    if isinstance(value["pid"], bool) or not isinstance(value["pid"], int) or value["pid"] <= 0:
        raise ExecutorError("stale_lock_unverifiable", "lock PID is invalid")
    if not isinstance(value["process_start_ticks"], str) or not value["process_start_ticks"]:
        raise ExecutorError("stale_lock_unverifiable", "lock process identity is invalid")
    return value


def _acquire_lock(
    path: Path, binding_sha256: str, row_sha256: str
) -> tuple[int, list[dict[str, Any]]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    stale: list[dict[str, Any]] = []
    record = _lock_record(binding_sha256, row_sha256)
    for _ in range(2):
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            prior = _read_lock(path)
            if prior["binding_sha256"] != binding_sha256 or prior["row_sha256"] != row_sha256:
                raise ExecutorError("row_locked", "existing lock binds another run/row")
            observed_start = _process_start_ticks(prior["pid"])
            if observed_start is not None and observed_start == prior["process_start_ticks"]:
                raise ExecutorError("row_locked", f"row is active in PID {prior['pid']}")
            if observed_start is not None:
                reason = "pid_reused"
            else:
                reason = "process_absent"
            archive = path.with_name(f"{path.name}.stale.{prior['lock_sha256']}.json")
            if archive.exists():
                archived = _read_lock(archive)
                if archived != prior:
                    raise ExecutorError("stale_lock_unverifiable", "stale-lock archive differs")
            else:
                try:
                    os.link(path, archive)
                except FileExistsError:
                    archived = _read_lock(archive)
                    if archived != prior:
                        raise ExecutorError("stale_lock_unverifiable", "stale-lock archive raced")
            path.unlink()
            stale.append({"reason": reason, "lock": prior, "archive": str(archive)})
            continue
        payload = canonical_json(record) + "\n"
        os.write(descriptor, payload.encode())
        os.fsync(descriptor)
        return descriptor, stale
    raise ExecutorError("row_locked", "could not acquire row lock after stale recovery")


def _release_lock(lock_fd: int, lock: Path, artifact_path: Path) -> None:
    """Release a lease; archive its receipt if no terminal artifact exists."""
    try:
        os.close(lock_fd)
    except OSError:
        pass
    if not lock.exists():
        return
    if not artifact_path.exists():
        try:
            record = _read_lock(lock)
            archive = lock.with_name(
                f"{lock.name}.aborted.{record['lock_sha256']}.json"
            )
            if not archive.exists():
                os.link(lock, archive)
        except Exception:
            # Keep the original lock rather than destroy unverifiable evidence.
            return
    try:
        lock.unlink()
    except OSError:
        pass


def _atomic_write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(value) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise ExecutorError("artifact_exists", f"refusing to overwrite {path}") from error
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def _load_bound_artifact(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutorError("artifact_read", f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise ExecutorError("artifact_schema", "artifact root is not an object")
    _validate_bound_hash(value, "artifact_sha256", "artifact_hash")
    return value


def _preflight_subject(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in receipt.items()
        if key not in {"verifier", "artifact_sha256"}
    }


def _row_subject(artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in artifact.items()
        if key not in {"verifier", "artifact_sha256"}
    }


def _validate_preflight_artifact(
    receipt: Mapping[str, Any], binding: Mapping[str, Any], binding_sha256: str
) -> None:
    _validate_bound_hash(receipt, "artifact_sha256", "preflight_hash")
    if receipt.get("schema") != PREFLIGHT_SCHEMA or receipt.get("binding_sha256") != binding_sha256:
        raise ExecutorError("preflight_binding", "stored preflight binds another run")
    if canonical_json(receipt.get("binding")) != canonical_json(binding):
        raise ExecutorError("preflight_binding", "stored preflight binding differs")
    gates = receipt.get("gates")
    if not isinstance(gates, Mapping) or not set(gates).issubset(set(GATE_NAMES)):
        raise ExecutorError("preflight_schema", "stored preflight gates differ")
    for name, attempt in gates.items():
        _validate_gate_attempt(name, attempt, binding_sha256)
    expected_status = "PASS" if set(gates) == set(GATE_NAMES) and all(
        gates[name]["status"] == "PASS" for name in GATE_NAMES
    ) else "FAILED"
    if receipt.get("status") != expected_status:
        raise ExecutorError("preflight_status", "stored preflight status contradicts gates")
    if receipt.get("verification_standing") != "UNVERIFIED_CONTROL":
        raise ExecutorError("preflight_status", "preflight standing is not explicit")
    if receipt.get("natural_rows_started") != 0:
        raise ExecutorError("preflight_schema", "preflight must precede all natural rows")
    subject_sha256 = object_sha256(_preflight_subject(receipt))
    _validate_validator_receipt(
        "preflight",
        receipt.get("verifier"),
        subject_sha256,
        binding["verifier_identity_sha256"],
    )


def _validate_row_artifact(
    artifact: Mapping[str, Any], binding: Mapping[str, Any], binding_sha256: str,
    row_sha256: str,
) -> None:
    _validate_bound_hash(artifact, "artifact_sha256", "artifact_hash")
    if artifact.get("schema") != ROW_SCHEMA or artifact.get("binding_sha256") != binding_sha256:
        raise ExecutorError("artifact_binding", "stored row binds another run")
    if artifact.get("verification_standing") != "UNVERIFIED_CONTROL":
        raise ExecutorError("artifact_binding", "artifact standing is not explicit")
    if canonical_json(artifact.get("binding")) != canonical_json(binding):
        raise ExecutorError("artifact_binding", "stored row binding differs")
    if artifact.get("row_sha256") != row_sha256:
        raise ExecutorError("artifact_binding", "stored artifact binds another row")
    row_ref = artifact.get("row_ref")
    if not isinstance(row_ref, Mapping) or row_ref.get("row_sha256") != row_sha256:
        raise ExecutorError("artifact_binding", "stored row reference differs")
    stages = artifact.get("stages")
    if not isinstance(stages, Mapping) or not set(stages).issubset(set(STAGE_NAMES)):
        raise ExecutorError("artifact_schema", "stored stages differ")
    for name, stage in stages.items():
        _validate_stage_record(name, stage)
    expected_work = _aggregate_work(
        stages, failure_safe=artifact.get("status") == "FAILED"
    )
    if artifact.get("work") != expected_work:
        raise ExecutorError("artifact_work", "stored work total differs")
    if artifact.get("status") == "COMPLETE":
        if set(stages) != set(STAGE_NAMES):
            raise ExecutorError("artifact_schema", "complete artifact lacks stages")
        source_summary = stages["source"]["result"]["value"]
        if (
            not isinstance(source_summary, Mapping)
            or set(source_summary) != {"status", "private_source_sha256"}
            or source_summary.get("status") != "PRIVATE_EVALUATOR_ONLY"
            or not _is_sha256(source_summary.get("private_source_sha256"))
        ):
            raise ExecutorError("artifact_schema", "private source summary differs")
        redaction = stages["redact"]["result"]["value"]
        if not isinstance(redaction, Mapping):
            raise ExecutorError("redaction_schema", "retained redaction is not an object")
        _assert_exact_keys(redaction, {"public_source", "private_link"}, "retained_redaction")
        public_source = redaction["public_source"]
        private_link = redaction["private_link"]
        if not isinstance(public_source, Mapping) or not isinstance(private_link, Mapping):
            raise ExecutorError("redaction_schema", "retained redaction values differ")
        try:
            public_boundary.validate_public_source(public_source)
            private_link = public_boundary.validate_link(private_link)
        except (ValueError, TypeError) as error:
            raise ExecutorError("private_link", "retained public/private link differs") from error
        if (
            private_link["private_source_sha256"]
            != source_summary["private_source_sha256"]
            or private_link["public_source_sha256"]
            != public_boundary._sha(public_source)
        ):
            raise ExecutorError("private_link", "retained public/private commitments differ")
        row_token = row_ref.get("row_token")
        if not _is_sha256(row_token):
            raise ExecutorError("artifact_binding", "retained row token is invalid")
        relation_input_sha256 = _relation_input_sha256(
            row_token,
            public_source,
            stages["lift"]["result"]["value"],
            stages["invariants"]["result"]["value"],
        )
        public_factors = row_ref.get("public_factors")
        if not isinstance(public_factors, Mapping):
            raise ExecutorError("artifact_binding", "retained public factors differ")
        r_value = public_factors.get("r")
        if isinstance(r_value, bool) or not isinstance(r_value, int):
            raise ExecutorError("artifact_binding", "retained r differs")
        relation_value = _validate_relation_value(
            stages["relation"]["result"]["value"],
            relation_input_sha256,
            r_value,
        )
        exact_recovery = _validate_evaluator_value(
            stages["evaluate"]["result"]["value"],
            relation_value,
            relation_input_sha256,
            private_link,
            {},
            stages["lift"]["result"]["value"],
            stages["local"]["result"]["value"],
        )
        expected_endpoints = _endpoints(stages["rank"], exact_recovery)
        if artifact.get("endpoints") != expected_endpoints:
            raise ExecutorError("artifact_endpoints", "retained endpoints do not replay")
        provenance_subject = {
            key: value
            for key, value in _row_subject(artifact).items()
            if key not in {"stages", "work"}
        }
        provenance_subject["stages"] = {
            key: value for key, value in stages.items() if key != "provenance"
        }
        provenance_subject["work"] = _aggregate_work(provenance_subject["stages"])
        _validate_provenance_value(
            stages["provenance"]["result"]["value"],
            object_sha256(provenance_subject),
        )
    elif artifact.get("status") != "FAILED":
        raise ExecutorError("artifact_schema", "invalid row artifact status")
    subject_sha256 = object_sha256(_row_subject(artifact))
    _validate_validator_receipt(
        "artifact",
        artifact.get("verifier"),
        subject_sha256,
        binding["verifier_identity_sha256"],
    )


class NaturalExecutor:
    """One frozen run's deterministic preflight and row executor."""

    def __init__(
        self,
        config: ExecutorConfig,
        roster: Mapping[str, Any],
        adapters: ExecutorAdapters,
        output_dir: str | Path,
        *,
        row_token_nonce: bytes,
    ) -> None:
        config.validate()
        if not isinstance(row_token_nonce, bytes) or len(row_token_nonce) < 32:
            raise ExecutorError("row_token_nonce", "row token nonce must contain at least 32 bytes")
        if hashlib.sha256(row_token_nonce).hexdigest() != config.row_token_nonce_sha256:
            raise ExecutorError("row_token_nonce", "row token nonce does not match commitment")
        _validate_roster(roster, config)
        self.config = config
        self.roster = json.loads(canonical_json(roster))
        self.adapters = adapters
        self.output_dir = Path(output_dir)
        self.binding = config.binding()
        self.binding_sha256 = object_sha256(self.binding)
        self._row_token_nonce = row_token_nonce

    @property
    def preflight_path(self) -> Path:
        return self.output_dir / "preflight.json"

    def preflight(self) -> dict[str, Any]:
        """Run all global gates or replay the exact immutable receipt."""
        if self.preflight_path.exists():
            receipt = _load_bound_artifact(self.preflight_path)
            _validate_preflight_artifact(receipt, self.binding, self.binding_sha256)
            subject = _preflight_subject(receipt)
            replay = _validator_result(
                "preflight",
                self.adapters.preflight_verifier(
                    subject=subject,
                    subject_sha256=object_sha256(subject),
                    mode="resume",
                ),
                object_sha256(subject),
                self.config.verifier_identity_sha256,
            )
            if canonical_json(replay) != canonical_json(receipt["verifier"]):
                raise ExecutorError("preflight_verifier", "resume verifier receipt differs")
            if receipt["status"] != "PASS":
                raise ExecutorError(
                    "preflight_failed",
                    "retained preflight did not pass",
                    evidence={"path": str(self.preflight_path)},
                )
            return receipt

        gate_functions = {
            "checkpoint": self.adapters.checkpoint_gate,
            "tools": self.adapters.tool_gate,
            "public_boundary": self.adapters.public_boundary_gate,
            "provenance": self.adapters.provenance_gate,
        }
        receipts: dict[str, Any] = {}
        preflight_status = "PASS"
        for name in GATE_NAMES:
            try:
                result = gate_functions[name](binding=json.loads(canonical_json(self.binding)))
                attempt = _gate_attempt(name, result, self.binding_sha256)
            except Exception as error:
                attempt = _gate_attempt(
                    name,
                    {
                        "schema": GATE_RESULT_SCHEMA,
                        "name": name,
                        "status": "FAIL",
                        "binding_sha256": self.binding_sha256,
                        "checks": {"adapter_result_valid": False},
                        "evidence": {
                            "exception_type": type(error).__name__,
                            "message_sha256": hashlib.sha256(str(error).encode()).hexdigest(),
                        },
                    },
                    self.binding_sha256,
                )
            receipts[name] = attempt
            if attempt["status"] != "PASS":
                preflight_status = "FAILED"
                break
        receipt = {
            "schema": PREFLIGHT_SCHEMA,
            "status": preflight_status,
            "verification_standing": "UNVERIFIED_CONTROL",
            "natural_rows_started": 0,
            "binding": self.binding,
            "binding_sha256": self.binding_sha256,
            "gates": receipts,
        }
        subject_sha256 = object_sha256(receipt)
        receipt["verifier"] = _validator_result(
            "preflight",
            self.adapters.preflight_verifier(
                subject=receipt,
                subject_sha256=subject_sha256,
                mode="create",
            ),
            subject_sha256,
            self.config.verifier_identity_sha256,
        )
        receipt = _bind_hash(receipt, "artifact_sha256")
        _atomic_write_new(self.preflight_path, receipt)
        _validate_preflight_artifact(receipt, self.binding, self.binding_sha256)
        if preflight_status != "PASS":
            raise ExecutorError(
                "preflight_failed",
                "preflight gate did not pass; failure retained",
                evidence={"path": str(self.preflight_path)},
            )
        return receipt

    def _row_context(self, row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "binding": json.loads(canonical_json(self.binding)),
            "binding_sha256": self.binding_sha256,
            "row_id": row["row_id"],
            "row_sha256": object_sha256(row),
        }

    def _public_context(self, row: Mapping[str, Any]) -> dict[str, Any]:
        """Opaque binding for public subprocesses; contains no semantic row ID."""
        row_token = hmac.new(
            self._row_token_nonce,
            canonical_json(row).encode(),
            hashlib.sha256,
        ).hexdigest()
        return {
            "binding_sha256": self.binding_sha256,
            "freeze_sha256": self.config.freeze_sha256,
            "roster_sha256": self.config.roster_sha256,
            "tool_pins_sha256": self.binding["tool_pins_sha256"],
            "row_token": row_token,
            "row_token_nonce_sha256": self.config.row_token_nonce_sha256,
        }

    def _existing_row(self, path: Path, row: Mapping[str, Any]) -> dict[str, Any]:
        artifact = _load_bound_artifact(path)
        row_sha256 = object_sha256(row)
        _validate_row_artifact(
            artifact,
            self.binding,
            self.binding_sha256,
            row_sha256,
        )
        subject = _row_subject(artifact)
        replay = _validator_result(
            "artifact",
            self.adapters.artifact_verifier(
                subject=subject,
                subject_sha256=object_sha256(subject),
                mode="resume",
            ),
            object_sha256(subject),
            self.config.verifier_identity_sha256,
        )
        if canonical_json(replay) != canonical_json(artifact["verifier"]):
            raise ExecutorError("artifact_verifier", "resume verifier receipt differs")
        return {"status": "RESUMED", "path": str(path), "artifact": artifact}

    def run_row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        """Run one exact roster row, retaining every success or failure."""
        self.preflight()
        frozen_row = _find_roster_row(self.roster, row)
        path = _artifact_path(self.output_dir, frozen_row["row_id"])
        if path.exists():
            return self._existing_row(path, frozen_row)

        context = self._row_context(frozen_row)
        public_context = self._public_context(frozen_row)
        public_row = _public_row(frozen_row)
        row_ref = {
            "row_sha256": object_sha256(frozen_row),
            "row_token": public_context["row_token"],
            "public_factors": public_row,
        }

        lock = path.with_suffix(path.suffix + ".lock")
        if path.exists():
            return self._existing_row(path, frozen_row)
        lock_fd, stale_locks = _acquire_lock(
            lock, self.binding_sha256, object_sha256(frozen_row)
        )

        stages: dict[str, Any] = {}
        active_stage = "source"
        private_source: Any = None
        try:
            active_stage = "source"
            private_source_stage = _normalize_stage(
                active_stage,
                self.adapters.source(row=frozen_row, context=context),
            )
            private_source = private_source_stage["result"]["value"]
            stages[active_stage] = _summarize_private_source(
                private_source_stage, private_source
            )

            active_stage = "redact"
            stages[active_stage] = _normalize_stage(
                active_stage,
                self.adapters.redact(
                    private_source=private_source,
                    row=frozen_row,
                    context=context,
                ),
            )
            redaction = stages[active_stage]["result"]["value"]
            if not isinstance(redaction, Mapping):
                raise ExecutorError(
                    "redaction_schema",
                    "redaction value is not an object",
                    stage=active_stage,
                )
            _assert_exact_keys(
                redaction, {"public_source", "private_link"}, "redaction.value"
            )
            public_source = redaction.get("public_source")
            if not isinstance(public_source, Mapping) or not isinstance(
                redaction.get("private_link"), Mapping
            ):
                raise ExecutorError(
                    "redaction_schema",
                    "redaction must contain public_source and private_link objects",
                    stage=active_stage,
                )
            private_link = _validate_private_link(
                redaction["private_link"], private_source, public_source
            )
            leaks = _scan_public_keys(public_source)
            if leaks:
                raise ExecutorError(
                    "public_key_leak",
                    "redacted public source contains prohibited key names",
                    stage=active_stage,
                    evidence={"paths": leaks},
                )

            active_stage = "local"
            stages[active_stage] = _normalize_stage(
                active_stage,
                self.adapters.local(
                    public_source=public_source,
                    row=public_row,
                    context=public_context,
                ),
            )
            local_value = stages[active_stage]["result"]["value"]

            active_stage = "lift"
            stages[active_stage] = _normalize_stage(
                active_stage,
                self.adapters.lift(
                    public_source=public_source,
                    local=local_value,
                    row=public_row,
                    context=public_context,
                ),
            )
            lift_value = stages[active_stage]["result"]["value"]

            active_stage = "invariants"
            stages[active_stage] = _normalize_stage(
                active_stage,
                self.adapters.invariants(
                    public_source=public_source,
                    lift=lift_value,
                    row=public_row,
                    context=public_context,
                ),
            )
            invariants_value = stages[active_stage]["result"]["value"]

            relation_input_sha256 = _relation_input_sha256(
                public_context["row_token"],
                public_source,
                lift_value,
                invariants_value,
            )

            active_stage = "relation"
            stages[active_stage] = _normalize_stage(
                active_stage,
                self.adapters.relation(
                    public_source=public_source,
                    lift=lift_value,
                    invariants=invariants_value,
                    relation_input_sha256=relation_input_sha256,
                    row=public_row,
                    context=public_context,
                ),
            )
            relation_value = _validate_relation_value(
                stages[active_stage]["result"]["value"],
                relation_input_sha256,
                frozen_row["r"],
            )

            active_stage = "rank"
            stages[active_stage] = _normalize_stage(
                active_stage,
                self.adapters.rank(
                    public_source=public_source,
                    lift=lift_value,
                    invariants=invariants_value,
                    row=public_row,
                    context=public_context,
                ),
            )

            active_stage = "evaluate"
            stages[active_stage] = _normalize_stage(
                active_stage,
                self.adapters.evaluate(
                    private_source=private_source,
                    private_link=redaction["private_link"],
                    public_source=public_source,
                    lift=lift_value,
                    relation=relation_value,
                    relation_input_sha256=relation_input_sha256,
                    row=frozen_row,
                    context=context,
                ),
            )
            exact_recovery = _validate_evaluator_value(
                stages[active_stage]["result"]["value"],
                relation_value,
                relation_input_sha256,
                private_link,
                private_source,
                lift_value,
                local_value,
            )

            endpoints = _endpoints(stages["rank"], exact_recovery)
            draft = {
                "schema": ROW_SCHEMA,
                "status": "COMPLETE",
                "verification_standing": "UNVERIFIED_CONTROL",
                "binding": self.binding,
                "binding_sha256": self.binding_sha256,
                "row_ref": row_ref,
                "row_sha256": object_sha256(frozen_row),
                "stages": stages,
                "endpoints": endpoints,
                "work": _aggregate_work(stages),
                "lock_evidence": stale_locks,
            }

            active_stage = "provenance"
            provenance_subject_sha256 = object_sha256(draft)
            stages[active_stage] = _normalize_stage(
                active_stage,
                self.adapters.provenance(
                    artifact=draft,
                    subject_sha256=provenance_subject_sha256,
                    row=frozen_row,
                    context=context,
                ),
            )
            _validate_provenance_value(
                stages[active_stage]["result"]["value"],
                provenance_subject_sha256,
            )
            draft["stages"] = stages
            draft["work"] = _aggregate_work(stages)
            subject_sha256 = object_sha256(draft)
            draft["verifier"] = _validator_result(
                "artifact",
                self.adapters.artifact_verifier(
                    subject=draft,
                    subject_sha256=subject_sha256,
                    mode="create",
                ),
                subject_sha256,
                self.config.verifier_identity_sha256,
            )
            _assert_no_private_source(draft, private_source)
            artifact = _bind_hash(draft, "artifact_sha256")
            _validate_row_artifact(
                artifact,
                self.binding,
                self.binding_sha256,
                object_sha256(frozen_row),
            )
            _atomic_write_new(path, artifact)
        except Exception as error:  # the failure itself is durable evidence
            rejected_stage = stages.pop(active_stage, None)
            if isinstance(error, ExecutorError):
                code = error.code
                evidence = error.evidence
                if error.stage is not None:
                    active_stage = error.stage
            else:
                code = "adapter_exception"
                evidence = {}
            failure = {
                "schema": ROW_SCHEMA,
                "status": "FAILED",
                "verification_standing": "UNVERIFIED_CONTROL",
                "binding": self.binding,
                "binding_sha256": self.binding_sha256,
                "row_ref": row_ref,
                "row_sha256": object_sha256(frozen_row),
                "stages": stages,
                "endpoints": {
                    "curve_rank": "UNKNOWN",
                    "selected_dependence": "UNKNOWN",
                    "useful_recovery": "UNKNOWN",
                },
                "work": _aggregate_work(stages, failure_safe=True),
                "lock_evidence": stale_locks,
                "failure": {
                    "stage": active_stage,
                    "code": code,
                    "exception_type": type(error).__name__,
                    "message_sha256": hashlib.sha256(str(error).encode()).hexdigest(),
                    "evidence_sha256": hashlib.sha256(repr(evidence).encode()).hexdigest(),
                    "rejected_stage_sha256": (
                        object_sha256(rejected_stage)
                        if rejected_stage is not None
                        else None
                    ),
                },
            }
            try:
                failure_subject_sha256 = object_sha256(failure)
                failure["verifier"] = _validator_result(
                    "artifact",
                    self.adapters.artifact_verifier(
                        subject=failure,
                        subject_sha256=failure_subject_sha256,
                        mode="create",
                    ),
                    failure_subject_sha256,
                    self.config.verifier_identity_sha256,
                )
                _assert_no_private_source(failure, private_source)
                artifact = _bind_hash(failure, "artifact_sha256")
                _validate_row_artifact(
                    artifact,
                    self.binding,
                    self.binding_sha256,
                    object_sha256(frozen_row),
                )
                _atomic_write_new(path, artifact)
            except Exception:
                raise
        finally:
            _release_lock(lock_fd, lock, path)
        return {"status": artifact["status"], "path": str(path), "artifact": artifact}

    def run_rows(self, rows: list[Mapping[str, Any]]) -> dict[str, Any]:
        """Execute explicit rows in caller order; never silently expand scope."""
        if not isinstance(rows, list):
            raise ExecutorError("row_batch", "rows must be an explicit list")
        row_ids: list[str] = []
        row_hashes: list[str] = []
        for row in rows:
            frozen = _find_roster_row(self.roster, row)
            row_ids.append(frozen["row_id"])
            row_hashes.append(object_sha256(frozen))
        if len(set(row_ids)) != len(row_ids) or len(set(row_hashes)) != len(row_hashes):
            raise ExecutorError("duplicate_rows", "requested rows contain duplicates")
        self.preflight()
        results = [self.run_row(row) for row in rows]
        return {
            "schema": SCHEMA,
            "status": "COMPLETE",
            "binding_sha256": self.binding_sha256,
            "requested_rows": len(rows),
            "complete": sum(item["artifact"]["status"] == "COMPLETE" for item in results),
            "failed": sum(item["artifact"]["status"] == "FAILED" for item in results),
            "resumed": sum(item["status"] == "RESUMED" for item in results),
            "results": results,
        }

