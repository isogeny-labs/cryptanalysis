#!/usr/bin/env python3
"""Strict signed-receipt verification for prospective natural Xedni rows.

This module verifies byte bindings and Ed25519 signatures, but it never treats
an injected/test keyring as an independent trust anchor.  Production
eligibility requires both the signer and the verifier digest to be present in
``origin/main:pcc/keyring.json``.  The repository currently has no entry in
``trusted_verifiers``; consequently every real execution receipt is
``NOT_COVERED`` until the owner installs and pins a reviewed verifier.

The module has no signing-key generation and never reads a signing secret.
Tests construct fixed control signatures outside this verifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from tools.pcc import pcc as pcc_tool


RECEIPT_SCHEMA = "xedni.verifier-receipt/v1"
PAYLOAD_SCHEMA = "xedni.verifier-receipt-payload/v1"
SIGNATURE_SCHEMA = "xedni.verifier-receipt-signature/v1"
ASSESSMENT_SCHEMA = "xedni.verifier-receipt-assessment/v1"
KEYRING_SCHEMA = "pcc.keyring/v1"
DOMAIN = "xedni.rank-decay.verifier-receipt/v1"
SIGNING_PREFIX = b"xedni.verifier-receipt.signature/v1\x00"
MAX_VALIDITY_SECONDS = 7 * 24 * 60 * 60
ORIGIN_MAIN_REF = "origin/main"
NATURAL_ROW_PURPOSE = "natural-row-verification"
EXECUTION_VERIFIER_KIND = "execution"
# The base keyring currently has no trusted execution verifier.  Enabling this
# interface therefore requires a reviewed owner-pinned keyring update and a
# separate reviewed change here; producer-controlled receipt bytes cannot
# promote themselves.
PRODUCTION_READY = False

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX128 = re.compile(r"[0-9a-f]{128}\Z")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+/@=-]{0,255}\Z")
UTC_SECOND = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")

ROOT_KEYS = {"schema", "payload", "signature", "receipt_sha256"}
PAYLOAD_KEYS = {
    "schema",
    "domain",
    "receipt_id",
    "run_id",
    "purpose",
    "input_sha256",
    "output_sha256",
    "details_sha256",
    "checkpoint_sha256",
    "verifier",
    "keyring_sha256",
    "base_commit",
    "issued_at",
    "expires_at",
    "verdict",
}
VERIFIER_KEYS = {"name", "kind", "sha256"}
SIGNATURE_KEYS = {"schema", "algorithm", "key_id", "payload_sha256", "signature"}
KEYRING_ROOT_REQUIRED = {"schema", "keys", "trusted_verifiers"}
KEYRING_ROOT_ALLOWED = KEYRING_ROOT_REQUIRED | {"note"}
KEY_KEYS_REQUIRED = {"id", "algo", "public_key", "role"}
KEY_KEYS_ALLOWED = KEY_KEYS_REQUIRED | {"revoked"}
TRUSTED_VERIFIER_KEYS = {"name", "kind", "sha256"}
VERDICTS = {"PASS", "FAIL"}


class ReceiptError(ValueError):
    """A stable fail-closed receipt validation error."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ExpectedBindings:
    """Bindings supplied by the caller from the frozen row and verifier."""

    run_id: str
    purpose: str
    input_sha256: str
    output_sha256: str
    details_sha256: str
    checkpoint_sha256: str
    verifier_name: str
    verifier_kind: str
    verifier_sha256: str
    keyring_sha256: str
    base_commit: str

    def __post_init__(self) -> None:
        _token(self.run_id, "expected.run_id")
        _token(self.purpose, "expected.purpose")
        _token(self.verifier_name, "expected.verifier_name")
        _token(self.verifier_kind, "expected.verifier_kind")
        for name in (
            "input_sha256",
            "output_sha256",
            "details_sha256",
            "checkpoint_sha256",
            "verifier_sha256",
            "keyring_sha256",
        ):
            _hash(getattr(self, name), f"expected.{name}")
        if self.base_commit != "CONTROL" and re.fullmatch(r"[0-9a-f]{40}", self.base_commit) is None:
            raise ReceiptError(
                "expected",
                "expected.base_commit must be CONTROL or a frozen Git commit",
            )


def canonical_json(value: Any) -> str:
    """Canonical finite JSON used by every digest and signature."""
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ReceiptError("json", f"value is not finite canonical JSON: {error}") from error


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReceiptError("json_duplicate", f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ReceiptError("json_nonfinite", f"nonfinite JSON constant {value!r}")


def strict_json_loads(raw: str | bytes, context: str = "JSON") -> Any:
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ReceiptError("json_utf8", f"{context}: invalid UTF-8") from error
    if not isinstance(raw, str):
        raise ReceiptError("json_type", f"{context}: expected text or bytes")
    try:
        return json.loads(
            raw,
            object_pairs_hook=_strict_pairs,
            parse_constant=_reject_constant,
        )
    except ReceiptError:
        raise
    except (TypeError, ValueError) as error:
        raise ReceiptError("json_parse", f"{context}: invalid JSON: {error}") from error


def _exact_keys(value: Any, expected: set[str], context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReceiptError("schema", f"{context}: expected object")
    actual = set(value)
    if actual != expected:
        raise ReceiptError(
            "schema",
            f"{context}: keys differ; missing={sorted(expected - actual)!r} "
            f"extra={sorted(actual - expected)!r}",
        )
    return value


def _token(value: Any, context: str) -> str:
    if not isinstance(value, str) or TOKEN.fullmatch(value) is None:
        raise ReceiptError("token", f"{context}: invalid token")
    return value


def _hash(value: Any, context: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise ReceiptError("hash", f"{context}: expected lowercase SHA-256")
    return value


def _strict_ed25519_point(encoded: bytes, context: str) -> None:
    """Require a canonical non-identity point in the prime-order subgroup.

    RFC-compatible verification alone permits small-order public keys on some
    implementations.  In particular, the identity key admits signatures that
    do not depend on a secret.  Repository trust keys and signature ``R``
    values therefore get the stricter validation expected of generated keys.
    """
    point = pcc_tool._ed_decompress(encoded)
    identity = (0, 1, 1, 0)
    if point is None or pcc_tool._ed_compress(point) != encoded:
        raise ReceiptError("signature", f"{context}: noncanonical Ed25519 point")
    if pcc_tool._ed_equal(point, identity):
        raise ReceiptError("signature", f"{context}: Ed25519 identity point is forbidden")
    if not pcc_tool._ed_equal(pcc_tool._ed_mul(pcc_tool._Q, point), identity):
        raise ReceiptError(
            "signature",
            f"{context}: Ed25519 point is outside the prime-order subgroup",
        )


def _strict_ed25519_verify(public: bytes, message: bytes, signature: bytes) -> bool:
    try:
        _strict_ed25519_point(public, "public key")
        if len(signature) != 64:
            return False
        _strict_ed25519_point(signature[:32], "signature R")
    except ReceiptError:
        return False
    return pcc_tool.ed25519_verify(public, message, signature)


def _utc(value: Any, context: str) -> datetime:
    if not isinstance(value, str) or UTC_SECOND.fullmatch(value) is None:
        raise ReceiptError("time", f"{context}: expected UTC second timestamp")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise ReceiptError("time", f"{context}: invalid timestamp") from error
    return parsed.replace(tzinfo=timezone.utc)


def _now(value: datetime | None) -> datetime:
    selected = datetime.now(timezone.utc) if value is None else value
    if selected.tzinfo is None or selected.utcoffset() is None:
        raise ReceiptError("time", "now must be timezone-aware")
    return selected.astimezone(timezone.utc).replace(microsecond=0)


def _payload_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in sorted(PAYLOAD_KEYS - {"receipt_id"})}


def expected_receipt_id(payload: Mapping[str, Any]) -> str:
    return object_sha256(_payload_identity(payload))


def validate_payload(value: Any) -> dict[str, Any]:
    payload = dict(_exact_keys(value, PAYLOAD_KEYS, "payload"))
    if payload["schema"] != PAYLOAD_SCHEMA:
        raise ReceiptError("schema", f"payload.schema must be {PAYLOAD_SCHEMA}")
    if payload["domain"] != DOMAIN:
        raise ReceiptError("domain", "payload domain mismatch")
    _hash(payload["receipt_id"], "payload.receipt_id")
    _token(payload["run_id"], "payload.run_id")
    _token(payload["purpose"], "payload.purpose")
    for name in (
        "input_sha256",
        "output_sha256",
        "details_sha256",
        "checkpoint_sha256",
        "keyring_sha256",
    ):
        _hash(payload[name], f"payload.{name}")
    if payload["base_commit"] != "CONTROL" and re.fullmatch(r"[0-9a-f]{40}", payload["base_commit"]) is None:
        raise ReceiptError(
            "keyring",
            "payload.base_commit must be CONTROL or a frozen Git commit",
        )
    verifier = dict(_exact_keys(payload["verifier"], VERIFIER_KEYS, "payload.verifier"))
    _token(verifier["name"], "payload.verifier.name")
    _token(verifier["kind"], "payload.verifier.kind")
    _hash(verifier["sha256"], "payload.verifier.sha256")
    payload["verifier"] = verifier
    issued = _utc(payload["issued_at"], "payload.issued_at")
    expires = _utc(payload["expires_at"], "payload.expires_at")
    if expires <= issued:
        raise ReceiptError("time", "receipt expiry must follow issuance")
    if (expires - issued).total_seconds() > MAX_VALIDITY_SECONDS:
        raise ReceiptError("time", "receipt validity exceeds the seven-day maximum")
    if payload["verdict"] not in VERDICTS:
        raise ReceiptError("verdict", "payload.verdict must be PASS or FAIL")
    if payload["receipt_id"] != expected_receipt_id(payload):
        raise ReceiptError("receipt_id", "payload receipt_id does not replay")
    return payload


def validate_signature(value: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    signature = dict(_exact_keys(value, SIGNATURE_KEYS, "signature"))
    if signature["schema"] != SIGNATURE_SCHEMA:
        raise ReceiptError("schema", f"signature.schema must be {SIGNATURE_SCHEMA}")
    if signature["algorithm"] != "ed25519":
        raise ReceiptError("signature", "only ed25519 signatures are accepted")
    _token(signature["key_id"], "signature.key_id")
    _hash(signature["payload_sha256"], "signature.payload_sha256")
    if signature["payload_sha256"] != object_sha256(payload):
        raise ReceiptError("signature", "signature payload digest mismatch")
    if not isinstance(signature["signature"], str) or HEX128.fullmatch(signature["signature"]) is None:
        raise ReceiptError("signature", "signature must be 64 lowercase hex bytes")
    return signature


def signing_message(payload: Mapping[str, Any], key_id: str) -> bytes:
    checked = validate_payload(payload)
    signed = {
        "key_id": _token(key_id, "signing key_id"),
        "payload_sha256": object_sha256(checked),
        "payload": checked,
    }
    return SIGNING_PREFIX + canonical_json(signed).encode("ascii")


def make_payload(
    *,
    run_id: str,
    purpose: str,
    input_sha256: str,
    output_sha256: str,
    details_sha256: str,
    checkpoint_sha256: str,
    verifier_name: str,
    verifier_kind: str,
    verifier_sha256: str,
    keyring_sha256: str,
    base_commit: str,
    issued_at: str,
    expires_at: str,
    verdict: str,
) -> dict[str, Any]:
    """Construct an unsigned payload.  This function never handles a secret."""
    payload: dict[str, Any] = {
        "schema": PAYLOAD_SCHEMA,
        "domain": DOMAIN,
        "receipt_id": "0" * 64,
        "run_id": run_id,
        "purpose": purpose,
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "details_sha256": details_sha256,
        "checkpoint_sha256": checkpoint_sha256,
        "verifier": {
            "name": verifier_name,
            "kind": verifier_kind,
            "sha256": verifier_sha256,
        },
        "keyring_sha256": keyring_sha256,
        "base_commit": base_commit,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "verdict": verdict,
    }
    payload["receipt_id"] = expected_receipt_id(payload)
    return validate_payload(payload)


def assemble_receipt(payload: Mapping[str, Any], key_id: str, signature_hex: str) -> dict[str, Any]:
    """Assemble already-signed bytes; no signing secret enters this module."""
    checked_payload = validate_payload(payload)
    signature = {
        "schema": SIGNATURE_SCHEMA,
        "algorithm": "ed25519",
        "key_id": _token(key_id, "key_id"),
        "payload_sha256": object_sha256(checked_payload),
        "signature": signature_hex,
    }
    validate_signature(signature, checked_payload)
    body = {
        "schema": RECEIPT_SCHEMA,
        "payload": checked_payload,
        "signature": signature,
    }
    return {**body, "receipt_sha256": object_sha256(body)}


def validate_receipt(value: Any) -> dict[str, Any]:
    if isinstance(value, (str, bytes)):
        value = strict_json_loads(value, "receipt")
    receipt = dict(_exact_keys(value, ROOT_KEYS, "receipt"))
    if receipt["schema"] != RECEIPT_SCHEMA:
        raise ReceiptError("schema", f"receipt.schema must be {RECEIPT_SCHEMA}")
    payload = validate_payload(receipt["payload"])
    signature = validate_signature(receipt["signature"], payload)
    _hash(receipt["receipt_sha256"], "receipt.receipt_sha256")
    body = {"schema": RECEIPT_SCHEMA, "payload": payload, "signature": signature}
    if receipt["receipt_sha256"] != object_sha256(body):
        raise ReceiptError("receipt_hash", "receipt_sha256 does not replay")
    return {**body, "receipt_sha256": receipt["receipt_sha256"]}


def render_keyring(value: Mapping[str, Any]) -> bytes:
    """Canonical control-keyring bytes.  Repository evaluation uses git bytes."""
    checked = validate_keyring(value)
    return (canonical_json(checked) + "\n").encode("ascii")


def validate_keyring(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ReceiptError("keyring", "keyring must be an object")
    keys = set(value)
    if not KEYRING_ROOT_REQUIRED.issubset(keys) or not keys.issubset(KEYRING_ROOT_ALLOWED):
        raise ReceiptError("keyring", "keyring root keys are not exact")
    if value["schema"] != KEYRING_SCHEMA:
        raise ReceiptError("keyring", f"keyring.schema must be {KEYRING_SCHEMA}")
    if "note" in value and not isinstance(value["note"], str):
        raise ReceiptError("keyring", "keyring.note must be text")
    if not isinstance(value["keys"], list) or not isinstance(value["trusted_verifiers"], list):
        raise ReceiptError("keyring", "keyring keys and trusted_verifiers must be arrays")
    normalized_keys = []
    seen_ids = set()
    seen_public_keys = set()
    for index, raw in enumerate(value["keys"]):
        if not isinstance(raw, Mapping):
            raise ReceiptError("keyring", f"keyring.keys[{index}] must be an object")
        actual = set(raw)
        if not KEY_KEYS_REQUIRED.issubset(actual) or not actual.issubset(KEY_KEYS_ALLOWED):
            raise ReceiptError("keyring", f"keyring.keys[{index}] keys are not exact")
        item = dict(raw)
        key_id = _token(item["id"], f"keyring.keys[{index}].id")
        if key_id in seen_ids:
            raise ReceiptError("keyring", f"duplicate key id {key_id!r}")
        seen_ids.add(key_id)
        if item["algo"] != "ed25519":
            raise ReceiptError("keyring", "only ed25519 keyring keys are supported")
        if not isinstance(item["public_key"], str) or HEX64.fullmatch(item["public_key"]) is None:
            raise ReceiptError("keyring", "keyring public key must be 32 lowercase hex bytes")
        _strict_ed25519_point(
            bytes.fromhex(item["public_key"]),
            f"keyring.keys[{index}].public_key",
        )
        if item["public_key"] in seen_public_keys:
            raise ReceiptError("keyring", "duplicate Ed25519 public key under multiple ids")
        seen_public_keys.add(item["public_key"])
        _token(item["role"], f"keyring.keys[{index}].role")
        if "revoked" in item and not isinstance(item["revoked"], bool):
            raise ReceiptError("keyring", "keyring revoked must be Boolean")
        normalized_keys.append(item)
    normalized_verifiers = []
    seen_verifiers = set()
    for index, raw in enumerate(value["trusted_verifiers"]):
        item = dict(_exact_keys(raw, TRUSTED_VERIFIER_KEYS, f"keyring.trusted_verifiers[{index}]"))
        name = _token(item["name"], f"keyring.trusted_verifiers[{index}].name")
        kind = _token(item["kind"], f"keyring.trusted_verifiers[{index}].kind")
        digest = _hash(item["sha256"], f"keyring.trusted_verifiers[{index}].sha256")
        identity = (name, kind, digest)
        if identity in seen_verifiers:
            raise ReceiptError("keyring", "duplicate trusted verifier identity")
        seen_verifiers.add(identity)
        normalized_verifiers.append(item)
    result = {
        "schema": KEYRING_SCHEMA,
        "keys": normalized_keys,
        "trusted_verifiers": normalized_verifiers,
    }
    if "note" in value:
        result["note"] = value["note"]
    return result


def parse_keyring_bytes(raw: bytes) -> dict[str, Any]:
    return validate_keyring(strict_json_loads(raw, "keyring"))


def _assessment_base(anchor: str) -> dict[str, Any]:
    return {
        "schema": ASSESSMENT_SCHEMA,
        "standing": "INVALID",
        "production_eligible": False,
        "trust_anchor": anchor,
        "keyring_sha256": None,
        "keyring_base_commit": None,
        "receipt_sha256": None,
        "payload_sha256": None,
        "key_id": None,
        "verifier_sha256": None,
        "input_sha256": None,
        "output_sha256": None,
        "verdict": None,
        "signature_valid": False,
        "signer_in_keyring": False,
        "verifier_trusted": False,
        "current": False,
        "reasons": [],
        "notes": [],
    }


def _seal_assessment(value: dict[str, Any]) -> dict[str, Any]:
    value = dict(value)
    value["assessment_sha256"] = object_sha256(value)
    return value


def _check_expected(payload: Mapping[str, Any], expected: ExpectedBindings) -> list[str]:
    reasons = []
    pairs = {
        "run_id": expected.run_id,
        "purpose": expected.purpose,
        "input_sha256": expected.input_sha256,
        "output_sha256": expected.output_sha256,
        "details_sha256": expected.details_sha256,
        "checkpoint_sha256": expected.checkpoint_sha256,
        "keyring_sha256": expected.keyring_sha256,
        "base_commit": expected.base_commit,
    }
    for name, want in pairs.items():
        if payload[name] != want:
            reasons.append(f"payload.{name} does not match the frozen expected binding")
    verifier = payload["verifier"]
    for name, want in {
        "name": expected.verifier_name,
        "kind": expected.verifier_kind,
        "sha256": expected.verifier_sha256,
    }.items():
        if verifier[name] != want:
            reasons.append(f"payload.verifier.{name} does not match the frozen expected binding")
    return reasons


def _keyring_public(keyring: Mapping[str, Any], key_id: str) -> bytes | None:
    for item in keyring["keys"]:
        if (
            item["id"] == key_id
            and item["algo"] == "ed25519"
            and item["role"] == "verifier"
            and item.get("revoked") is not True
        ):
            return bytes.fromhex(item["public_key"])
    return None


def _verifier_trusted(keyring: Mapping[str, Any], verifier: Mapping[str, Any]) -> bool:
    return any(
        item["name"] == verifier["name"]
        and item["kind"] == verifier["kind"]
        and item["sha256"] == verifier["sha256"]
        for item in keyring["trusted_verifiers"]
    )


def _verify(
    receipt_value: Any,
    expected: ExpectedBindings,
    *,
    keyring_raw: bytes,
    anchor: str,
    repository_anchor: bool,
    base_commit: str | None,
    now: datetime | None,
) -> dict[str, Any]:
    result = _assessment_base(anchor)
    result["keyring_base_commit"] = base_commit
    try:
        receipt = validate_receipt(receipt_value)
        keyring = parse_keyring_bytes(keyring_raw)
        keyring_digest = hashlib.sha256(keyring_raw).hexdigest()
        result.update(
            {
                "keyring_sha256": keyring_digest,
                "receipt_sha256": receipt["receipt_sha256"],
                "payload_sha256": object_sha256(receipt["payload"]),
                "key_id": receipt["signature"]["key_id"],
                "verifier_sha256": receipt["payload"]["verifier"]["sha256"],
                "input_sha256": receipt["payload"]["input_sha256"],
                "output_sha256": receipt["payload"]["output_sha256"],
                "verdict": receipt["payload"]["verdict"],
            }
        )
        if receipt["payload"]["keyring_sha256"] != keyring_digest:
            raise ReceiptError("keyring", "receipt is bound to a different keyring")
        if repository_anchor and receipt["payload"]["base_commit"] != base_commit:
            raise ReceiptError("keyring_ref", "receipt is bound to a different base commit")
        expected_errors = _check_expected(receipt["payload"], expected)
        if expected_errors:
            result["reasons"].extend(expected_errors)
            return _seal_assessment(result)
        issued = _utc(receipt["payload"]["issued_at"], "payload.issued_at")
        expires = _utc(receipt["payload"]["expires_at"], "payload.expires_at")
        current = _now(now)
        if current < issued:
            raise ReceiptError("time", "receipt is not yet valid")
        if current > expires:
            raise ReceiptError("time", "receipt has expired")
        result["current"] = True
        public = _keyring_public(keyring, receipt["signature"]["key_id"])
        if public is None:
            raise ReceiptError("signature", "receipt signer is not an active verifier key")
        result["signer_in_keyring"] = True
        signature = bytes.fromhex(receipt["signature"]["signature"])
        if not _strict_ed25519_verify(
            public,
            signing_message(receipt["payload"], receipt["signature"]["key_id"]),
            signature,
        ):
            raise ReceiptError("signature", "Ed25519 signature verification failed")
        result["signature_valid"] = True
        result["verifier_trusted"] = _verifier_trusted(keyring, receipt["payload"]["verifier"])
        if not result["verifier_trusted"]:
            result["standing"] = "NOT_COVERED"
            result["notes"].append("verifier digest is absent from keyring.trusted_verifiers")
            return _seal_assessment(result)
        if not repository_anchor:
            result["standing"] = "NOT_COVERED"
            result["notes"].append("supplied control keyring is not an independent repository trust anchor")
            return _seal_assessment(result)
        if not PRODUCTION_READY:
            result["standing"] = "NOT_COVERED"
            result["notes"].append("receipt interface is not production-enabled in this revision")
            return _seal_assessment(result)
        if receipt["payload"]["verdict"] != "PASS":
            result["standing"] = "TRUSTED_FAIL"
            result["notes"].append("trusted verifier signed a non-PASS verdict")
            return _seal_assessment(result)
        result["standing"] = "TRUSTED_PASS"
        result["production_eligible"] = True
        return _seal_assessment(result)
    except ReceiptError as error:
        result["reasons"].append(f"{error.code}: {error}")
        return _seal_assessment(result)


def verify_control_receipt(
    receipt: Any,
    expected: ExpectedBindings,
    keyring_raw: bytes,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify cryptography against supplied bytes, always as NOT_COVERED."""
    return _verify(
        receipt,
        expected,
        keyring_raw=keyring_raw,
        anchor="SUPPLIED_CONTROL_KEYRING",
        repository_anchor=False,
        base_commit=None,
        now=now,
    )


def load_origin_main_keyring(repo: Path = REPOSITORY) -> tuple[str, bytes]:
    """Load the local PR-base keyring with Git replacement objects disabled.

    ``origin/main`` is only the repository convention used by this disabled
    interface; it is not itself an immutable owner pin.  Before
    ``PRODUCTION_READY`` can be enabled, the gate must additionally compare
    this commit or keyring digest with an owner/CI value outside producer
    control.  The current false gate therefore remains security-significant.
    """
    resolved = repo.resolve()
    # Git's repository-selection variables are producer-controlled in an
    # ordinary process.  Do not let them redirect a supposedly repository-
    # anchored lookup.  Non-Git environment such as PATH is retained so this
    # diagnostic interface remains portable; the independent gate must still
    # run this code and Git binary from an owner-controlled environment.
    git_environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    git_environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    try:
        commit_run = subprocess.run(
            ["git", "rev-parse", "--verify", f"{ORIGIN_MAIN_REF}^{{commit}}"],
            cwd=resolved,
            capture_output=True,
            check=False,
            env=git_environment,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ReceiptError("keyring_ref", f"cannot resolve {ORIGIN_MAIN_REF}: {error}") from error
    if commit_run.returncode != 0:
        raise ReceiptError("keyring_ref", f"{ORIGIN_MAIN_REF} does not resolve")
    try:
        commit = commit_run.stdout.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise ReceiptError("keyring_ref", "base commit is not ASCII") from error
    if HEX64.fullmatch(commit) is not None or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        # SHA-1 repositories use 40 hex; this also rejects noisy output.
        raise ReceiptError("keyring_ref", "base commit id is malformed")
    try:
        keyring_run = subprocess.run(
            ["git", "show", f"{commit}:pcc/keyring.json"],
            cwd=resolved,
            capture_output=True,
            check=False,
            env=git_environment,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ReceiptError("keyring_ref", f"cannot read base keyring: {error}") from error
    if keyring_run.returncode != 0:
        raise ReceiptError("keyring_ref", "base keyring cannot be read")
    parse_keyring_bytes(keyring_run.stdout)
    return commit, keyring_run.stdout


def verify_repository_receipt(
    receipt: Any,
    expected: ExpectedBindings,
    *,
    repo: Path = REPOSITORY,
) -> dict[str, Any]:
    """Verify under ``origin/main``; only this path can become production eligible."""
    if expected.purpose != NATURAL_ROW_PURPOSE:
        result = _assessment_base(f"{ORIGIN_MAIN_REF}:REJECTED")
        result["reasons"].append(
            "purpose: production receipts require natural-row-verification"
        )
        return _seal_assessment(result)
    if expected.verifier_kind != EXECUTION_VERIFIER_KIND:
        result = _assessment_base(f"{ORIGIN_MAIN_REF}:REJECTED")
        result["reasons"].append(
            "verifier_kind: production receipts require execution"
        )
        return _seal_assessment(result)
    resolved_repo = repo.resolve()
    repository_anchor = resolved_repo == REPOSITORY.resolve()
    try:
        commit, keyring_raw = load_origin_main_keyring(resolved_repo)
    except ReceiptError as error:
        result = _assessment_base(f"{ORIGIN_MAIN_REF}:UNAVAILABLE")
        result["standing"] = "NOT_COVERED"
        result["notes"].append(f"{error.code}: {error}")
        return _seal_assessment(result)
    return _verify(
        receipt,
        expected,
        keyring_raw=keyring_raw,
        anchor=f"{ORIGIN_MAIN_REF}:{commit}",
        repository_anchor=repository_anchor,
        base_commit=commit,
        now=None,
    )


def repository_trust_summary(repo: Path = REPOSITORY) -> dict[str, Any]:
    """Report the actual verifier coverage without accepting a receipt."""
    try:
        commit, raw = load_origin_main_keyring(repo)
        keyring = parse_keyring_bytes(raw)
    except ReceiptError as error:
        value = {
            "schema": "xedni.verifier-trust-summary/v1",
            "status": "NOT_COVERED",
            "base_ref": ORIGIN_MAIN_REF,
            "base_commit": None,
            "keyring_sha256": None,
            "active_verifier_keys": 0,
            "trusted_verifier_count": 0,
            "production_ready": False,
            "reason": f"{error.code}: {error}",
        }
        return {**value, "summary_sha256": object_sha256(value)}
    active_keys = sum(
        item["role"] == "verifier" and item.get("revoked") is not True
        for item in keyring["keys"]
    )
    trusted_count = sum(
        item["kind"] == EXECUTION_VERIFIER_KIND for item in keyring["trusted_verifiers"]
    )
    value = {
        "schema": "xedni.verifier-trust-summary/v1",
        "status": (
            "READY" if PRODUCTION_READY and active_keys and trusted_count else "NOT_COVERED"
        ),
        "base_ref": ORIGIN_MAIN_REF,
        "base_commit": commit,
        "keyring_sha256": hashlib.sha256(raw).hexdigest(),
        "active_verifier_keys": active_keys,
        "trusted_verifier_count": trusted_count,
        "production_ready": bool(PRODUCTION_READY and active_keys and trusted_count),
        "reason": (
            None
            if PRODUCTION_READY and active_keys and trusted_count
            else "receipt interface disabled or base keyring has no trusted execution verifier"
        ),
    }
    return {**value, "summary_sha256": object_sha256(value)}


__all__ = [
    "ASSESSMENT_SCHEMA",
    "DOMAIN",
    "EXECUTION_VERIFIER_KIND",
    "ExpectedBindings",
    "MAX_VALIDITY_SECONDS",
    "NATURAL_ROW_PURPOSE",
    "PAYLOAD_SCHEMA",
    "RECEIPT_SCHEMA",
    "ReceiptError",
    "PRODUCTION_READY",
    "SIGNATURE_SCHEMA",
    "assemble_receipt",
    "canonical_json",
    "load_origin_main_keyring",
    "make_payload",
    "object_sha256",
    "parse_keyring_bytes",
    "render_keyring",
    "repository_trust_summary",
    "signing_message",
    "strict_json_loads",
    "validate_keyring",
    "validate_payload",
    "validate_receipt",
    "verify_control_receipt",
    "verify_repository_receipt",
]
