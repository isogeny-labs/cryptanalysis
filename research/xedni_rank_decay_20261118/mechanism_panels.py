#!/usr/bin/env python3
"""Outcome-blind selection and admission gates for Xedni panels M1--M6.

This module does not run rank, relation, or recovery code.  It validates what
selectors may see before those outcomes, retains the work of every proposed
candidate, and fails closed at the cubic/Jacobian and isogeny transfer gates.
Certificate truth is an external obligation: this layer checks completeness,
hash binding, and asserted exact-check results, not the mathematics itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re
from typing import Any, Iterable, Mapping, Sequence

import invariants_pari


BANK_SCHEMA = "xedni-mechanism-candidate-bank/v1"
SELECTION_SCHEMA = "xedni-mechanism-selection/v1"
M3_SPEC_SCHEMA = "xedni-m3-selector-spec/v1"
M6_PREDICTOR_SCHEMA = "xedni-m6-linear-predictor/v1"

PANELS = ("M1", "M2", "M3", "M4", "M5", "M6")
DISPOSITIONS = (
    "BLOCKED",
    "NULL_IN_SCOPE",
    "MECHANISM_ONLY",
    "REPLICATED_USEFUL_SIGNAL",
)
M2_LOCAL_ARMS = (
    "A_none",
    "B_reverse_mestre",
    "P_neutral_crt",
    "C_size_matched",
    "I_incompatible",
    "B_reverse_mestre_plus1",
    "B_reverse_mestre_plus2",
    "pairwise_coprime_canary",
)
M2_PRIMARY_ARMS = frozenset(
    {"A_none", "B_reverse_mestre", "P_neutral_crt"}
)
DISCRIMINANT_FEATURES = frozenset(
    {
        "raw_delta",
        "delta_min",
        "max_height",
        "stable_selection_key",
        "candidate_sha256",
        "invariants_sha256",
    }
)
M1_FEATURES = DISCRIMINANT_FEATURES | {"is_balanced"}

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+/-]{0,191}\Z")
FORBIDDEN_FEATURE_FRAGMENTS = (
    "rank",
    "relation",
    "depend",
    "recover",
    "outcome",
    "success",
    "target_scalar",
    "known_scalar",
    "discrete_log",
    "padic_defect",
)
CANDIDATE_KEYS = {
    "candidate_id",
    "q_isomorphism_class",
    "public_features",
    "construction_work",
}
WORK_KEYS = {
    "attempts",
    "rejections",
    "public_group_operations",
    "cpu_ns",
    "retained_bytes",
}
BANK_KEYS = {
    "schema",
    "panel",
    "p",
    "bank_id",
    "constant_k",
    "candidates",
    "candidate_bank_hash",
}


class MechanismError(ValueError):
    """A prospective freeze, selector, or certificate is invalid."""


def _exact_keys(value: Mapping[str, Any], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        raise MechanismError(
            f"{context}: key mismatch; "
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )


def _plain_int(value: Any, context: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise MechanismError(f"{context}: expected an integer >= {minimum}")
    return value


def _finite_number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MechanismError(f"{context}: expected a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise MechanismError(f"{context}: expected a finite number")
    return result


def _canonical_nonzero_integer_text(value: Any, context: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
        raise MechanismError(f"{context}: expected a canonical integer string")
    result = int(value)
    if result == 0:
        raise MechanismError(f"{context}: expected a nonzero integer")
    return result


def _positive_decimal_text(value: Any, context: str) -> Decimal:
    if not isinstance(value, str):
        raise MechanismError(f"{context}: expected a decimal string")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise MechanismError(f"{context}: invalid decimal string") from error
    if not result.is_finite() or result <= 0:
        raise MechanismError(f"{context}: must be strictly positive and finite")
    return result


def _stable_key(value: Any, candidate_sha256: str, context: str) -> tuple[int, str, str, str]:
    if not isinstance(value, list) or len(value) != 4:
        raise MechanismError(f"{context}: expected four stable-key components")
    exponent, significand, candidate_hash, row_id = value
    if isinstance(exponent, bool) or not isinstance(exponent, int):
        raise MechanismError(f"{context}[0]: expected an integer exponent")
    if not isinstance(significand, str) or not re.fullmatch(r"[1-9][0-9]{39}", significand):
        raise MechanismError(f"{context}[1]: expected a 40-digit significand")
    if candidate_hash != candidate_sha256 or HEX64.fullmatch(str(candidate_hash)) is None:
        raise MechanismError(f"{context}[2]: candidate hash mismatch")
    if not isinstance(row_id, str) or not row_id:
        raise MechanismError(f"{context}[3]: invalid row id")
    return exponent, significand, candidate_hash, row_id


def m1_features_from_invariants(
    record: Mapping[str, Any], *, is_balanced: bool | None = None
) -> dict[str, Any]:
    """Replay the invariant adapter's stable selection evidence and hash."""
    if not isinstance(record, Mapping):
        raise MechanismError("M1 invariants: expected an object")
    if (
        record.get("adapter") != invariants_pari.ADAPTER
        or record.get("status") != "OK"
        or record.get("reason") != "computed"
    ):
        raise MechanismError("M1 invariants: adapter did not compute a usable row")
    try:
        features = invariants_pari.selection_evidence(record)
    except (ArithmeticError, KeyError, TypeError, ValueError) as error:
        raise MechanismError(
            f"M1 invariants: selection evidence does not replay: {error}"
        ) from error
    for name in ("raw_delta", "delta_min"):
        _canonical_nonzero_integer_text(features[name], f"M1 invariants.{name}")
    candidate_hash = features["candidate_sha256"]
    if not isinstance(candidate_hash, str) or HEX64.fullmatch(candidate_hash) is None:
        raise MechanismError("M1 invariants.candidate_sha256: invalid hash")
    _stable_key(
        record.get("stable_selection_key"),
        candidate_hash,
        "M1 invariants.stable_selection_key",
    )
    invariant_hash = _hash(features)
    if invariant_hash != record.get("selection_evidence_sha256"):
        raise MechanismError("M1 invariants: selection evidence hash mismatch")
    features["invariants_sha256"] = invariant_hash
    if is_balanced is not None:
        if not isinstance(is_balanced, bool):
            raise MechanismError("M1 invariants.is_balanced: expected a boolean")
        features["is_balanced"] = is_balanced
    return features


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    divisor = 3
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def _token(value: Any, context: str) -> str:
    if not isinstance(value, str) or TOKEN.fullmatch(value) is None:
        raise MechanismError(f"{context}: invalid token")
    return value


def _seed(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise MechanismError(f"{context}: expected a nonempty seed string")
    return value


def _hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _json_copy(value: Any, context: str) -> Any:
    try:
        rendered = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise MechanismError(f"{context}: not canonical finite JSON") from exc
    return json.loads(rendered)


def _reject_outcome_features(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise MechanismError(f"{context}: feature keys must be strings")
            normalized = re.sub(r"[^a-z0-9]+", "_", key.lower())
            if any(fragment in normalized for fragment in FORBIDDEN_FEATURE_FRAGMENTS):
                raise MechanismError(
                    f"{context}.{key}: rank/relation/recovery-derived features are forbidden"
                )
            _reject_outcome_features(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_outcome_features(nested, f"{context}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise MechanismError(f"{context}: non-finite feature")
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise MechanismError(f"{context}: non-JSON feature value")


def _require_exact_features(
    candidates: Sequence[Mapping[str, Any]], names: set[str] | frozenset[str], context: str
) -> None:
    for candidate in candidates:
        actual = set(candidate["public_features"])
        if actual != set(names):
            raise MechanismError(
                f"{context}.{candidate['candidate_id']}: public feature mismatch; "
                f"missing={sorted(set(names) - actual)}, extra={sorted(actual - set(names))}"
            )


def _validate_work(value: Any, context: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise MechanismError(f"{context}: expected an object")
    _exact_keys(value, WORK_KEYS, context)
    return {
        key: _plain_int(value[key], f"{context}.{key}")
        for key in sorted(WORK_KEYS)
    }


def _validate_candidates(value: Any, constant_k: int) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != constant_k:
        raise MechanismError(
            f"candidates: expected exactly the frozen constant K={constant_k} proposals"
        )
    result = []
    identifiers = set()
    for index, candidate in enumerate(value):
        context = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            raise MechanismError(f"{context}: expected an object")
        _exact_keys(candidate, CANDIDATE_KEYS, context)
        candidate_id = _token(candidate["candidate_id"], f"{context}.candidate_id")
        if candidate_id in identifiers:
            raise MechanismError(f"{context}: duplicate candidate_id {candidate_id!r}")
        identifiers.add(candidate_id)
        iso_class = _token(
            candidate["q_isomorphism_class"], f"{context}.q_isomorphism_class"
        )
        features = candidate["public_features"]
        if not isinstance(features, dict):
            raise MechanismError(f"{context}.public_features: expected an object")
        _reject_outcome_features(features, f"{context}.public_features")
        features = _json_copy(features, f"{context}.public_features")
        work = _validate_work(
            candidate["construction_work"], f"{context}.construction_work"
        )
        result.append(
            {
                "candidate_id": candidate_id,
                "q_isomorphism_class": iso_class,
                "public_features": features,
                "construction_work": work,
            }
        )
    return result


def _bank_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: manifest[key]
        for key in sorted(BANK_KEYS - {"candidate_bank_hash"})
    }


def freeze_candidate_bank(
    panel: str,
    p: int,
    bank_id: str,
    candidates: Sequence[Mapping[str, Any]],
    constant_k: int,
) -> dict[str, Any]:
    """Create a hash-bearing manifest before rank/relation outcomes exist."""
    if panel not in PANELS:
        raise MechanismError(f"panel: unknown panel {panel!r}")
    frozen_k = _plain_int(constant_k, "constant_k", 1)
    manifest = {
        "schema": BANK_SCHEMA,
        "panel": panel,
        "p": _plain_int(p, "p", 2),
        "bank_id": _token(bank_id, "bank_id"),
        "constant_k": frozen_k,
        "candidates": _validate_candidates(list(candidates), frozen_k),
    }
    manifest["candidate_bank_hash"] = _hash(manifest)
    return manifest


@dataclass(frozen=True)
class PreparedBank:
    """Canonical snapshot with first-representative Q-isomorphism dedup."""

    panel: str
    p: int
    bank_id: str
    constant_k: int
    candidate_bank_hash: str
    candidates_json: str
    representative_ids: tuple[str, ...]
    duplicate_q_isomorphism_candidates: int
    construction_work_items: tuple[tuple[str, int], ...]

    def candidates(self) -> list[dict[str, Any]]:
        return json.loads(self.candidates_json)

    def representatives(self) -> list[dict[str, Any]]:
        wanted = set(self.representative_ids)
        return [
            row for row in self.candidates() if row["candidate_id"] in wanted
        ]

    def construction_work(self) -> dict[str, int]:
        return dict(self.construction_work_items)


def prepare_candidate_bank(manifest: Any, expected_k: int) -> PreparedBank:
    """Verify the freeze, deduplicate models, and retain work over all K."""
    if not isinstance(manifest, dict):
        raise MechanismError("candidate bank: expected an object")
    _exact_keys(manifest, BANK_KEYS, "candidate bank")
    if manifest["schema"] != BANK_SCHEMA:
        raise MechanismError("candidate bank: unknown schema")
    panel = manifest["panel"]
    if panel not in PANELS:
        raise MechanismError(f"candidate bank.panel: unknown panel {panel!r}")
    p = _plain_int(manifest["p"], "candidate bank.p", 2)
    bank_id = _token(manifest["bank_id"], "candidate bank.bank_id")
    frozen_k = _plain_int(manifest["constant_k"], "candidate bank.constant_k", 1)
    expected_k = _plain_int(expected_k, "expected_k", 1)
    if frozen_k != expected_k:
        raise MechanismError(
            f"candidate bank: K changed over p ({frozen_k} != frozen {expected_k})"
        )
    candidates = _validate_candidates(manifest["candidates"], frozen_k)
    supplied_hash = manifest["candidate_bank_hash"]
    if not isinstance(supplied_hash, str) or HEX64.fullmatch(supplied_hash) is None:
        raise MechanismError("candidate bank.candidate_bank_hash: expected SHA-256")
    canonical_manifest = {
        "schema": BANK_SCHEMA,
        "panel": panel,
        "p": p,
        "bank_id": bank_id,
        "constant_k": frozen_k,
        "candidates": candidates,
        "candidate_bank_hash": supplied_hash,
    }
    if supplied_hash != _hash(_bank_payload(canonical_manifest)):
        raise MechanismError("candidate bank: hash mismatch after mutation")

    seen_classes = set()
    representative_ids = []
    total_work = {key: 0 for key in WORK_KEYS}
    for candidate in candidates:
        iso_class = candidate["q_isomorphism_class"]
        if iso_class not in seen_classes:
            seen_classes.add(iso_class)
            representative_ids.append(candidate["candidate_id"])
        for key, amount in candidate["construction_work"].items():
            total_work[key] += amount
    return PreparedBank(
        panel=panel,
        p=p,
        bank_id=bank_id,
        constant_k=frozen_k,
        candidate_bank_hash=supplied_hash,
        candidates_json=json.dumps(
            candidates,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ),
        representative_ids=tuple(representative_ids),
        duplicate_q_isomorphism_candidates=frozen_k - len(representative_ids),
        construction_work_items=tuple(sorted(total_work.items())),
    )


def prepare_panel_banks(
    manifests: Iterable[Mapping[str, Any]], expected_k: int
) -> tuple[PreparedBank, ...]:
    """Enforce one constant K across every p in one mechanism panel."""
    banks = tuple(
        prepare_candidate_bank(manifest, expected_k) for manifest in manifests
    )
    if not banks:
        raise MechanismError("panel banks: at least one bank is required")
    if len({bank.panel for bank in banks}) != 1:
        raise MechanismError("panel banks: mixed mechanism panels")
    identities = [(bank.p, bank.bank_id) for bank in banks]
    if len(set(identities)) != len(identities):
        raise MechanismError("panel banks: duplicate (p, bank_id)")
    return banks


def _selection_base(bank: PreparedBank, panel: str) -> dict[str, Any]:
    if bank.panel != panel:
        raise MechanismError(f"selector {panel}: received {bank.panel} bank")
    return {
        "schema": SELECTION_SCHEMA,
        "panel": panel,
        "candidate_bank_hash": bank.candidate_bank_hash,
        "constant_k": bank.constant_k,
        "q_isomorphism_unique": len(bank.representative_ids),
        "q_isomorphism_duplicates": bank.duplicate_q_isomorphism_candidates,
        "construction_work_all_proposals": bank.construction_work(),
        "mandatory_direct_source_baseline": "DIRECT_SOURCE_RELATION_TEST",
    }


def _hash_order(
    candidate: Mapping[str, Any], seed: str, label: str, bank_hash: str
) -> str:
    return _hash([seed, label, bank_hash, candidate["candidate_id"]])


def _deterministic_random(
    candidates: Sequence[Mapping[str, Any]],
    seed: str,
    label: str,
    bank_hash: str,
) -> str:
    if not candidates:
        raise MechanismError("selector: no Q-isomorphism representatives")
    return min(
        candidates,
        key=lambda row: (
            _hash_order(row, seed, label, bank_hash),
            row["candidate_id"],
        ),
    )["candidate_id"]


def _feature_number(
    candidate: Mapping[str, Any], name: str, context: str
) -> float:
    features = candidate["public_features"]
    if name not in features:
        raise MechanismError(f"{context}: missing public feature {name!r}")
    return _finite_number(features[name], f"{context}.{name}")


def _permuted_score_winner(
    candidates: Sequence[Mapping[str, Any]],
    scores: Mapping[str, float],
    seed: str,
    label: str,
    bank_hash: str,
    direction: str,
) -> tuple[str, str]:
    targets = sorted(
        candidates,
        key=lambda row: (
            _hash_order(row, seed, label, bank_hash),
            row["candidate_id"],
        ),
    )
    ordered_scores = sorted(scores.values())
    assignments = [
        {"candidate_id": target["candidate_id"], "score": ordered_scores[index]}
        for index, target in enumerate(targets)
    ]
    if direction == "min":
        winner = min(
            assignments, key=lambda row: (row["score"], row["candidate_id"])
        )
    elif direction == "max":
        winner = min(
            assignments, key=lambda row: (-row["score"], row["candidate_id"])
        )
    else:
        raise MechanismError(f"score direction: unknown value {direction!r}")
    return winner["candidate_id"], _hash(assignments)


def _permuted_stable_key_winner(
    candidates: Sequence[Mapping[str, Any]],
    scores: Mapping[str, tuple[int, str, str, str]],
    seed: str,
    label: str,
    bank_hash: str,
) -> tuple[str, str]:
    targets = sorted(
        candidates,
        key=lambda row: (
            _hash_order(row, seed, label, bank_hash),
            row["candidate_id"],
        ),
    )
    ordered_scores = sorted(scores.values())
    assignments = [
        {"candidate_id": target["candidate_id"], "score": list(ordered_scores[index])}
        for index, target in enumerate(targets)
    ]
    winner = min(
        assignments, key=lambda row: (tuple(row["score"]), row["candidate_id"])
    )
    return winner["candidate_id"], _hash(assignments)


def _select_discriminant_bank(
    bank: PreparedBank, panel: str, selection_seed: str
) -> dict[str, Any]:
    seed = _seed(selection_seed, f"{panel}.selection_seed")
    all_candidates = bank.candidates()
    _require_exact_features(
        all_candidates, M1_FEATURES if panel == "M1" else DISCRIMINANT_FEATURES, panel
    )
    representatives = set(bank.representative_ids)
    candidates = []
    rows = []
    ratio_scores = {}
    balanced = []
    for candidate in all_candidates:
        context = f"{panel}.{candidate['candidate_id']}"
        features = candidate["public_features"]
        if panel == "M1" and not isinstance(features["is_balanced"], bool):
            raise MechanismError(f"{context}.is_balanced: expected a boolean")
        raw_delta = _canonical_nonzero_integer_text(
            features["raw_delta"], f"{context}.raw_delta"
        )
        delta_min = _canonical_nonzero_integer_text(
            features["delta_min"], f"{context}.delta_min"
        )
        _positive_decimal_text(features["max_height"], f"{context}.max_height")
        candidate_hash = features["candidate_sha256"]
        if not isinstance(candidate_hash, str) or HEX64.fullmatch(candidate_hash) is None:
            raise MechanismError(f"{context}.candidate_sha256: invalid hash")
        invariant_hash = features["invariants_sha256"]
        ratio_key = _stable_key(
            features["stable_selection_key"],
            candidate_hash,
            f"{context}.stable_selection_key",
        )
        evidence = {
            name: features[name] for name in DISCRIMINANT_FEATURES - {"invariants_sha256"}
        }
        if invariant_hash != _hash(evidence):
            raise MechanismError(
                f"{context}.invariants_sha256: selection evidence hash mismatch"
            )
        if candidate["candidate_id"] not in representatives:
            continue
        candidates.append(candidate)
        if panel == "M1" and features["is_balanced"]:
            balanced.append(candidate["candidate_id"])
        ratio_scores[candidate["candidate_id"]] = ratio_key
        rows.append((candidate, abs(raw_delta), abs(delta_min), ratio_key))
    if not rows:
        raise MechanismError(f"{panel}: no Q-isomorphism representatives")
    if panel == "M1" and len(balanced) != 1:
        raise MechanismError("M1: expected exactly one balanced representative")
    selection_input_hash = _hash(
        {
            "panel": panel,
            "p": bank.p,
            "bank_id": bank.bank_id,
            "constant_k": bank.constant_k,
            "candidates": [
                {
                    "candidate_id": candidate["candidate_id"],
                    "q_isomorphism_class": candidate["q_isomorphism_class"],
                    "public_features": candidate["public_features"],
                }
                for candidate in all_candidates
            ],
        }
    )
    permuted, assignment_hash = _permuted_stable_key_winner(
        candidates,
        ratio_scores,
        seed,
        f"{panel}-permuted-normalized-delta",
        selection_input_hash,
    )
    result = _selection_base(bank, panel)
    result.update(
        {
            "selection_seed": seed,
            "selection_input_sha256": selection_input_hash,
            "selections": {
                "deterministic_random": _deterministic_random(
                    candidates, seed, f"{panel}-random", selection_input_hash
                ),
                "min_raw_delta": min(
                    rows, key=lambda row: (row[1], row[0]["candidate_id"])
                )[0]["candidate_id"],
                "min_delta_min": min(
                    rows, key=lambda row: (row[2], row[0]["candidate_id"])
                )[0]["candidate_id"],
                "min_log_abs_delta_min_over_max_height": min(
                    rows, key=lambda row: (row[3], row[0]["candidate_id"])
                )[0]["candidate_id"],
                "permuted_score_null": permuted,
            },
            "permuted_score_assignment_hash": assignment_hash,
            "normalized_score_source": (
                "hash-bound invariants_pari stable decimal selection key"
            ),
        }
    )
    if panel == "M1":
        result["selections"]["balanced"] = balanced[0]
    return result


def select_m1(bank: PreparedBank, selection_seed: str) -> dict[str, Any]:
    """M1 balanced, random, discriminant, normalized-height, and permutation arms."""
    return _select_discriminant_bank(bank, "M1", selection_seed)


def select_m4_candidates(
    bank: PreparedBank, selection_seed: str
) -> dict[str, Any]:
    """M4 uses the same public discriminant selectors before its map gate."""
    return _select_discriminant_bank(bank, "M4", selection_seed)


M2_RECORD_KEYS = {
    "arm",
    "auxiliary_primes",
    "crt_modulus",
    "quotient_compatible",
    "construction_work",
}


def validate_m2_arms(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Identify every local arm and quarantine the incompatible control."""
    if not isinstance(records, (list, tuple)):
        raise MechanismError("M2 records: expected a sequence")
    by_arm = {}
    for index, record in enumerate(records):
        context = f"M2.records[{index}]"
        if not isinstance(record, dict):
            raise MechanismError(f"{context}: expected an object")
        _exact_keys(record, M2_RECORD_KEYS, context)
        arm = record["arm"]
        if arm not in M2_LOCAL_ARMS or arm in by_arm:
            raise MechanismError(f"{context}.arm: unknown or duplicate arm {arm!r}")
        primes = record["auxiliary_primes"]
        if not isinstance(primes, list):
            raise MechanismError(f"{context}.auxiliary_primes: expected a list")
        primes = [
            _plain_int(value, f"{context}.auxiliary_primes", 2)
            for value in primes
        ]
        if primes != sorted(set(primes)):
            raise MechanismError(
                f"{context}.auxiliary_primes: must be strictly increasing"
            )
        if any(not _is_prime(value) for value in primes):
            raise MechanismError(
                f"{context}.auxiliary_primes: composite auxiliary modulus"
            )
        modulus = _plain_int(record["crt_modulus"], f"{context}.crt_modulus", 1)
        if modulus != math.prod(primes):
            raise MechanismError(
                f"{context}: CRT modulus does not equal auxiliary-prime product"
            )
        compatible = record["quotient_compatible"]
        if not isinstance(compatible, bool):
            raise MechanismError(
                f"{context}.quotient_compatible: expected a boolean"
            )
        by_arm[arm] = {
            "arm": arm,
            "auxiliary_primes": primes,
            "crt_modulus": modulus,
            "quotient_compatible": compatible,
            "construction_work": _validate_work(
                record["construction_work"], f"{context}.construction_work"
            ),
            "primary_eligible": arm in M2_PRIMARY_ARMS,
        }
    missing = sorted(set(M2_LOCAL_ARMS) - set(by_arm))
    if missing:
        raise MechanismError(f"M2 records: missing arms {missing}")
    for arm in ("A_none", "C_size_matched"):
        if by_arm[arm]["auxiliary_primes"] or by_arm[arm]["crt_modulus"] != 1:
            raise MechanismError(
                f"M2 {arm}: must have no auxiliary primes and modulus 1"
            )
    if by_arm["I_incompatible"]["quotient_compatible"]:
        raise MechanismError(
            "M2 I_incompatible: known-negative control must be incompatible"
        )
    for arm in set(M2_LOCAL_ARMS) - {"I_incompatible"}:
        if not by_arm[arm]["quotient_compatible"]:
            raise MechanismError(
                f"M2 {arm}: only I_incompatible may fail compatibility"
            )
    matched = ("B_reverse_mestre", "P_neutral_crt", "I_incompatible")
    signatures = {
        (tuple(by_arm[arm]["auxiliary_primes"]), by_arm[arm]["crt_modulus"])
        for arm in matched
    }
    if len(signatures) != 1:
        raise MechanismError(
            "M2 B/P/I arms must use identical primes and CRT modulus"
        )
    return {
        "panel": "M2",
        "disposition": "MECHANISM_ONLY",
        "arms": [by_arm[arm] for arm in M2_LOCAL_ARMS],
        "incompatible_primary_excluded": True,
        "mandatory_direct_source_baseline": "DIRECT_SOURCE_RELATION_TEST",
    }


M3_SPEC_KEYS = {
    "schema",
    "proxy_feature",
    "direction",
    "selection_seed",
    "selector_hash",
}


def freeze_m3_selector(
    proxy_feature: str, direction: str, selection_seed: str
) -> dict[str, Any]:
    """Freeze the named nonlinear proxy and its direction before outcomes."""
    feature = _token(proxy_feature, "M3.proxy_feature")
    _reject_outcome_features({feature: 0}, "M3.proxy_feature")
    if direction not in ("min", "max"):
        raise MechanismError("M3.direction: expected min or max")
    spec = {
        "schema": M3_SPEC_SCHEMA,
        "proxy_feature": feature,
        "direction": direction,
        "selection_seed": _seed(selection_seed, "M3.selection_seed"),
    }
    spec["selector_hash"] = _hash(spec)
    return spec


def _validate_m3_spec(spec: Any, expected_hash: str) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise MechanismError("M3 selector: expected an object")
    _exact_keys(spec, M3_SPEC_KEYS, "M3 selector")
    if spec["schema"] != M3_SPEC_SCHEMA:
        raise MechanismError("M3 selector: unknown schema")
    supplied = spec["selector_hash"]
    if (
        supplied != expected_hash
        or not isinstance(supplied, str)
        or HEX64.fullmatch(supplied) is None
    ):
        raise MechanismError("M3 selector: frozen hash mismatch")
    payload = {
        key: spec[key] for key in sorted(M3_SPEC_KEYS - {"selector_hash"})
    }
    if _hash(payload) != supplied:
        raise MechanismError("M3 selector: mutated after freeze")
    feature = _token(spec["proxy_feature"], "M3.proxy_feature")
    _reject_outcome_features({feature: 0}, "M3.proxy_feature")
    if spec["direction"] not in ("min", "max"):
        raise MechanismError("M3.direction: expected min or max")
    _seed(spec["selection_seed"], "M3.selection_seed")
    return spec


def select_m3(
    bank: PreparedBank,
    selector_spec: Mapping[str, Any],
    expected_selector_hash: str,
) -> dict[str, Any]:
    """Choose proxy, random, permuted-score, and balanced M3 arms."""
    if bank.panel != "M3":
        raise MechanismError(f"selector M3: received {bank.panel} bank")
    spec = _validate_m3_spec(dict(selector_spec), expected_selector_hash)
    candidates = bank.representatives()
    _require_exact_features(
        candidates, {spec["proxy_feature"], "is_balanced"}, "M3"
    )
    if not candidates:
        raise MechanismError("M3: no Q-isomorphism representatives")
    scores = {
        candidate["candidate_id"]: _feature_number(
            candidate, spec["proxy_feature"], f"M3.{candidate['candidate_id']}"
        )
        for candidate in candidates
    }
    balanced = [
        candidate["candidate_id"]
        for candidate in candidates
        if candidate["public_features"]["is_balanced"] is True
    ]
    invalid_balanced = [
        candidate["candidate_id"]
        for candidate in candidates
        if not isinstance(candidate["public_features"]["is_balanced"], bool)
    ]
    if invalid_balanced or len(balanced) != 1:
        raise MechanismError(
            "M3: is_balanced must be boolean with exactly one true representative"
        )
    if spec["direction"] == "min":
        proxy = min(scores, key=lambda identifier: (scores[identifier], identifier))
    else:
        proxy = min(scores, key=lambda identifier: (-scores[identifier], identifier))
    permuted, assignment_hash = _permuted_score_winner(
        candidates,
        scores,
        spec["selection_seed"],
        "M3-permuted-proxy",
        bank.candidate_bank_hash,
        spec["direction"],
    )
    result = _selection_base(bank, "M3")
    result.update(
        {
            "selector_hash": spec["selector_hash"],
            "proxy_feature": spec["proxy_feature"],
            "proxy_direction": spec["direction"],
            "selections": {
                "nonlinear_proxy": proxy,
                "deterministic_random": _deterministic_random(
                    candidates,
                    spec["selection_seed"],
                    "M3-random",
                    bank.candidate_bank_hash,
                ),
                "permuted_score_null": permuted,
                "balanced": balanced[0],
            },
            "permuted_score_assignment_hash": assignment_hash,
        }
    )
    return result


MODEL_KEYS = {"equation", "model_hash"}
MAP_KEYS = {"formula", "map_hash"}
M4_CERTIFICATE_KEYS = {
    "cubic_model",
    "jacobian_model",
    "cubic_to_jacobian_map",
    "good_reduction_certified",
    "origin_certificate",
    "selected_point_certificates",
}
M4_POINT_KEYS = {
    "point_id",
    "cubic_coordinates",
    "jacobian_coordinates",
    "image_verified",
    "source_replay_verified",
    "certificate_hash",
}


def _validate_hash(value: Any, context: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise MechanismError(f"{context}: expected lowercase SHA-256")
    return value


def _validate_model(value: Any, context: str) -> None:
    if not isinstance(value, dict):
        raise MechanismError(f"{context}: expected an explicit model object")
    _exact_keys(value, MODEL_KEYS, context)
    if not isinstance(value["equation"], str) or not value["equation"].strip():
        raise MechanismError(f"{context}.equation: expected a nonempty equation")
    _validate_hash(value["model_hash"], f"{context}.model_hash")


def _validate_map(value: Any, context: str) -> None:
    if not isinstance(value, dict):
        raise MechanismError(f"{context}: expected an explicit map object")
    _exact_keys(value, MAP_KEYS, context)
    if not isinstance(value["formula"], str) or not value["formula"].strip():
        raise MechanismError(f"{context}.formula: expected a nonempty formula")
    _validate_hash(value["map_hash"], f"{context}.map_hash")


def _point_ids(value: Sequence[str], context: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise MechanismError(f"{context}: expected at least one selected point id")
    identifiers = tuple(_token(item, context) for item in value)
    if len(set(identifiers)) != len(identifiers):
        raise MechanismError(f"{context}: duplicate selected point id")
    return identifiers


def _validate_coordinates(value: Any, context: str) -> None:
    if not isinstance(value, list) or not value:
        raise MechanismError(f"{context}: explicit coordinates required")
    _json_copy(value, context)


def _validate_m4_point(value: Any, context: str) -> str:
    if not isinstance(value, dict):
        raise MechanismError(f"{context}: expected a certificate object")
    _exact_keys(value, M4_POINT_KEYS, context)
    point_id = _token(value["point_id"], f"{context}.point_id")
    _validate_coordinates(value["cubic_coordinates"], f"{context}.cubic_coordinates")
    _validate_coordinates(
        value["jacobian_coordinates"], f"{context}.jacobian_coordinates"
    )
    if value["image_verified"] is not True:
        raise MechanismError(f"{context}: point image is not certified")
    if value["source_replay_verified"] is not True:
        raise MechanismError(f"{context}: source replay is not certified")
    _validate_hash(value["certificate_hash"], f"{context}.certificate_hash")
    return point_id


def _admission(panel: str, reasons: Sequence[str]) -> dict[str, Any]:
    return {
        "panel": panel,
        "disposition": "BLOCKED" if reasons else "MECHANISM_ONLY",
        "certificate_gate_passed": not reasons,
        "reasons": list(reasons),
    }


def admit_m4(certificate: Any, selected_point_ids: Sequence[str]) -> dict[str, Any]:
    """Block M4 unless the explicit origin and every point map/replay certify."""
    try:
        expected_ids = _point_ids(selected_point_ids, "M4.selected_point_ids")
        if not isinstance(certificate, dict):
            raise MechanismError("M4 certificate: missing certificate object")
        _exact_keys(certificate, M4_CERTIFICATE_KEYS, "M4 certificate")
        _validate_model(certificate["cubic_model"], "M4.cubic_model")
        _validate_model(certificate["jacobian_model"], "M4.jacobian_model")
        _validate_map(
            certificate["cubic_to_jacobian_map"], "M4.cubic_to_jacobian_map"
        )
        if certificate["good_reduction_certified"] is not True:
            raise MechanismError("M4: good reduction is not certified")
        origin_id = _validate_m4_point(
            certificate["origin_certificate"], "M4.origin_certificate"
        )
        if origin_id != "origin":
            raise MechanismError("M4.origin_certificate: point_id must be 'origin'")
        point_certificates = certificate["selected_point_certificates"]
        if not isinstance(point_certificates, list):
            raise MechanismError("M4.selected_point_certificates: expected a list")
        actual_ids = tuple(
            _validate_m4_point(value, f"M4.selected_point_certificates[{index}]")
            for index, value in enumerate(point_certificates)
        )
        if (
            len(set(actual_ids)) != len(actual_ids)
            or set(actual_ids) != set(expected_ids)
        ):
            raise MechanismError(
                "M4: certificates must cover every selected point exactly once"
            )
    except MechanismError as exc:
        return _admission("M4", [str(exc)])
    return _admission("M4", [])


M5_CERTIFICATE_KEYS = {
    "degree",
    "subgroup_order",
    "source_model",
    "neighbor_model",
    "phi",
    "dual_psi",
    "kernel_certificate",
    "subgroup_certificate",
    "point_certificates",
    "target_recovery_verified",
}
ISOGENY_MAP_KEYS = {"formula", "map_hash", "degree"}
KERNEL_KEYS = {
    "kernel_order",
    "intersection_order",
    "verified",
    "certificate_hash",
}
SUBGROUP_KEYS = {
    "source_order",
    "image_order",
    "verified",
    "certificate_hash",
}
M5_POINT_KEYS = {
    "point_id",
    "source_coordinates",
    "phi_image",
    "psi_phi_image",
    "ell_multiple",
    "composition_verified",
    "certificate_hash",
}


def _validate_isogeny_map(value: Any, context: str, degree: int) -> None:
    if not isinstance(value, dict):
        raise MechanismError(f"{context}: explicit map required")
    _exact_keys(value, ISOGENY_MAP_KEYS, context)
    if not isinstance(value["formula"], str) or not value["formula"].strip():
        raise MechanismError(f"{context}.formula: nonempty formula required")
    _validate_hash(value["map_hash"], f"{context}.map_hash")
    if value["degree"] != degree:
        raise MechanismError(f"{context}: map degree does not equal ell")


def _validate_m5_point(value: Any, context: str) -> str:
    if not isinstance(value, dict):
        raise MechanismError(f"{context}: expected a certificate object")
    _exact_keys(value, M5_POINT_KEYS, context)
    point_id = _token(value["point_id"], f"{context}.point_id")
    for field in (
        "source_coordinates",
        "phi_image",
        "psi_phi_image",
        "ell_multiple",
    ):
        _validate_coordinates(value[field], f"{context}.{field}")
    if value["composition_verified"] is not True:
        raise MechanismError(f"{context}: psi(phi(P))=[ell]P is not certified")
    if value["psi_phi_image"] != value["ell_multiple"]:
        raise MechanismError(f"{context}: psi(phi(P)) differs from [ell]P")
    _validate_hash(value["certificate_hash"], f"{context}.certificate_hash")
    return point_id


def admit_m5(
    certificate: Any,
    source_subgroup_order: int,
    selected_point_ids: Sequence[str],
    allowed_degrees: Sequence[int],
) -> dict[str, Any]:
    """Block M5 unless maps, subgroup, composition, and recovery certify."""
    try:
        expected_ids = _point_ids(selected_point_ids, "M5.selected_point_ids")
        expected_subgroup_order = _plain_int(
            source_subgroup_order, "M5.source_subgroup_order", 2
        )
        allowed = tuple(
            _plain_int(value, "M5.allowed_degrees", 2)
            for value in allowed_degrees
        )
        if not allowed or len(set(allowed)) != len(allowed):
            raise MechanismError(
                "M5.allowed_degrees: frozen distinct degrees required"
            )
        if not isinstance(certificate, dict):
            raise MechanismError("M5 certificate: missing certificate object")
        _exact_keys(certificate, M5_CERTIFICATE_KEYS, "M5 certificate")
        degree = _plain_int(certificate["degree"], "M5.degree", 2)
        subgroup_order = _plain_int(
            certificate["subgroup_order"], "M5.subgroup_order", 2
        )
        if subgroup_order != expected_subgroup_order:
            raise MechanismError(
                "M5: certificate subgroup order differs from the source subgroup"
            )
        if degree not in allowed:
            raise MechanismError(
                "M5.degree: not in the prospectively allowed set"
            )
        if math.gcd(degree, subgroup_order) != 1:
            raise MechanismError("M5: gcd(ell, q) must equal one")
        _validate_model(certificate["source_model"], "M5.source_model")
        _validate_model(certificate["neighbor_model"], "M5.neighbor_model")
        _validate_isogeny_map(certificate["phi"], "M5.phi", degree)
        _validate_isogeny_map(certificate["dual_psi"], "M5.dual_psi", degree)

        kernel = certificate["kernel_certificate"]
        if not isinstance(kernel, dict):
            raise MechanismError("M5.kernel_certificate: expected an object")
        _exact_keys(kernel, KERNEL_KEYS, "M5.kernel_certificate")
        if (
            kernel["kernel_order"] != degree
            or kernel["intersection_order"] != 1
            or kernel["verified"] is not True
        ):
            raise MechanismError(
                "M5: kernel/subgroup intersection is not certified trivial"
            )
        _validate_hash(
            kernel["certificate_hash"],
            "M5.kernel_certificate.certificate_hash",
        )

        subgroup = certificate["subgroup_certificate"]
        if not isinstance(subgroup, dict):
            raise MechanismError("M5.subgroup_certificate: expected an object")
        _exact_keys(subgroup, SUBGROUP_KEYS, "M5.subgroup_certificate")
        if (
            subgroup["source_order"] != subgroup_order
            or subgroup["image_order"] != subgroup_order
            or subgroup["verified"] is not True
        ):
            raise MechanismError(
                "M5: source subgroup preservation is not certified"
            )
        _validate_hash(
            subgroup["certificate_hash"],
            "M5.subgroup_certificate.certificate_hash",
        )

        point_certificates = certificate["point_certificates"]
        if not isinstance(point_certificates, list):
            raise MechanismError("M5.point_certificates: expected a list")
        actual_ids = tuple(
            _validate_m5_point(value, f"M5.point_certificates[{index}]")
            for index, value in enumerate(point_certificates)
        )
        if (
            len(set(actual_ids)) != len(actual_ids)
            or set(actual_ids) != set(expected_ids)
        ):
            raise MechanismError(
                "M5: composition certificates must cover every selected point exactly once"
            )
        if certificate["target_recovery_verified"] is not True:
            raise MechanismError("M5: target recovery is not certified")
    except MechanismError as exc:
        return _admission("M5", [str(exc)])
    return _admission("M5", [])


M6_PREDICTOR_KEYS = {
    "schema",
    "development_seeds",
    "feature_names",
    "weights",
    "intercept",
    "training_labels",
    "label_permutation_hash",
    "predictor_hash",
}


def _seed_set(value: Any, context: str) -> list[str]:
    if not isinstance(value, (list, tuple)) or not value:
        raise MechanismError(f"{context}: expected a nonempty seed sequence")
    seeds = [_seed(seed, context) for seed in value]
    if len(set(seeds)) != len(seeds):
        raise MechanismError(f"{context}: duplicate seed")
    return seeds


def freeze_m6_linear_predictor(
    development_seeds: Sequence[str],
    feature_names: Sequence[str],
    weights: Sequence[float],
    intercept: float,
    *,
    training_labels: str = "observed",
    label_permutation_hash: str | None = None,
) -> dict[str, Any]:
    """Freeze a transparent feature-only predictor for a later holdout."""
    development_seeds = _seed_set(
        development_seeds, "M6.development_seeds"
    )
    if not isinstance(feature_names, (list, tuple)) or not feature_names:
        raise MechanismError("M6.feature_names: expected a nonempty sequence")
    names = [_token(name, "M6.feature_names") for name in feature_names]
    if len(set(names)) != len(names):
        raise MechanismError("M6.feature_names: duplicate feature")
    _reject_outcome_features({name: 0 for name in names}, "M6.feature_names")
    if not isinstance(weights, (list, tuple)) or len(weights) != len(names):
        raise MechanismError("M6.weights: one weight per feature is required")
    frozen_weights = [
        _finite_number(value, f"M6.weights[{index}]")
        for index, value in enumerate(weights)
    ]
    if training_labels not in ("observed", "permuted"):
        raise MechanismError(
            "M6.training_labels: expected observed or permuted"
        )
    if training_labels == "observed":
        if label_permutation_hash is not None:
            raise MechanismError(
                "M6: observed-label predictor cannot carry a permutation hash"
            )
    else:
        _validate_hash(
            label_permutation_hash, "M6.label_permutation_hash"
        )
    predictor = {
        "schema": M6_PREDICTOR_SCHEMA,
        "development_seeds": development_seeds,
        "feature_names": names,
        "weights": frozen_weights,
        "intercept": _finite_number(intercept, "M6.intercept"),
        "training_labels": training_labels,
        "label_permutation_hash": label_permutation_hash,
    }
    predictor["predictor_hash"] = _hash(predictor)
    return predictor


def _validate_m6_predictor(
    predictor: Any, expected_hash: str
) -> dict[str, Any]:
    if not isinstance(predictor, dict):
        raise MechanismError("M6 predictor: expected an object")
    _exact_keys(predictor, M6_PREDICTOR_KEYS, "M6 predictor")
    if predictor["schema"] != M6_PREDICTOR_SCHEMA:
        raise MechanismError("M6 predictor: unknown schema")
    supplied = predictor["predictor_hash"]
    if (
        supplied != expected_hash
        or not isinstance(supplied, str)
        or HEX64.fullmatch(supplied) is None
    ):
        raise MechanismError("M6 predictor: frozen hash mismatch")
    payload = {
        key: predictor[key]
        for key in sorted(M6_PREDICTOR_KEYS - {"predictor_hash"})
    }
    if _hash(payload) != supplied:
        raise MechanismError("M6 predictor: mutated after freeze")
    rebuilt = freeze_m6_linear_predictor(
        predictor["development_seeds"],
        predictor["feature_names"],
        predictor["weights"],
        predictor["intercept"],
        training_labels=predictor["training_labels"],
        label_permutation_hash=predictor["label_permutation_hash"],
    )
    if rebuilt != predictor:
        raise MechanismError("M6 predictor: noncanonical representation")
    return predictor


def select_m6(
    bank: PreparedBank,
    predictor: Mapping[str, Any],
    expected_predictor_hash: str,
    permuted_predictor: Mapping[str, Any],
    expected_permuted_predictor_hash: str,
    holdout_seeds: Sequence[str],
) -> dict[str, Any]:
    """Apply a frozen development predictor to a disjoint-seed holdout bank."""
    if bank.panel != "M6":
        raise MechanismError(f"selector M6: received {bank.panel} bank")
    predictor = _validate_m6_predictor(
        dict(predictor), expected_predictor_hash
    )
    permuted_predictor = _validate_m6_predictor(
        dict(permuted_predictor), expected_permuted_predictor_hash
    )
    if predictor["training_labels"] != "observed":
        raise MechanismError("M6: primary predictor must use observed development labels")
    if permuted_predictor["training_labels"] != "permuted":
        raise MechanismError("M6: null predictor must use permuted development labels")
    if (
        predictor["development_seeds"]
        != permuted_predictor["development_seeds"]
        or predictor["feature_names"] != permuted_predictor["feature_names"]
    ):
        raise MechanismError(
            "M6: primary and permuted predictors must share development seeds and features"
        )
    holdout_seeds = _seed_set(holdout_seeds, "M6.holdout_seeds")
    if set(holdout_seeds) & set(predictor["development_seeds"]):
        raise MechanismError(
            "M6: development and holdout seeds must be disjoint"
        )
    selection_seed = _hash(["M6-holdout", holdout_seeds])
    candidates = bank.representatives()
    _require_exact_features(
        candidates, set(predictor["feature_names"]), "M6"
    )
    if not candidates:
        raise MechanismError("M6: no Q-isomorphism representatives")
    scores = {}
    permuted_scores = {}
    for candidate in candidates:
        score = float(predictor["intercept"])
        permuted_score = float(permuted_predictor["intercept"])
        for index, name in enumerate(predictor["feature_names"]):
            feature = _feature_number(
                candidate, name, f"M6.{candidate['candidate_id']}"
            )
            score += predictor["weights"][index] * feature
            permuted_score += permuted_predictor["weights"][index] * feature
        if not math.isfinite(score) or not math.isfinite(permuted_score):
            raise MechanismError(
                f"M6.{candidate['candidate_id']}: non-finite score"
            )
        scores[candidate["candidate_id"]] = score
        permuted_scores[candidate["candidate_id"]] = permuted_score
    selected = min(
        scores, key=lambda identifier: (-scores[identifier], identifier)
    )
    permuted = min(
        permuted_scores,
        key=lambda identifier: (-permuted_scores[identifier], identifier),
    )
    result = _selection_base(bank, "M6")
    result.update(
        {
            "development_seeds": predictor["development_seeds"],
            "holdout_seeds": holdout_seeds,
            "predictor_hash": predictor["predictor_hash"],
            "permuted_predictor_hash": permuted_predictor["predictor_hash"],
            "selections": {
                "frozen_predictor": selected,
                "deterministic_random": _deterministic_random(
                    candidates,
                    selection_seed,
                    "M6-random",
                    bank.candidate_bank_hash,
                ),
                "permuted_predictor": permuted,
                "direct_source_baseline": "DIRECT_SOURCE_RELATION_TEST",
            },
        }
    )
    return result


def validate_disposition(value: str) -> str:
    if value not in DISPOSITIONS:
        raise MechanismError(
            f"disposition: {value!r} is forbidden; mechanism panels never emit "
            "DEFEATED_IN_SCOPE"
        )
    return value


def panel_disposition(
    *,
    blocked_reasons: Sequence[str] = (),
    mechanism_signal: bool = False,
    replicated_useful_signal: bool = False,
) -> str:
    """Map external evidence flags to the only four mechanism dispositions."""
    if not isinstance(mechanism_signal, bool) or not isinstance(
        replicated_useful_signal, bool
    ):
        raise MechanismError(
            "panel disposition: evidence flags must be booleans"
        )
    if not isinstance(blocked_reasons, (list, tuple)) or any(
        not isinstance(reason, str) or not reason for reason in blocked_reasons
    ):
        raise MechanismError(
            "panel disposition: blocked reasons must be nonempty strings"
        )
    if blocked_reasons:
        return "BLOCKED"
    if replicated_useful_signal:
        return "REPLICATED_USEFUL_SIGNAL"
    if mechanism_signal:
        return "MECHANISM_ONLY"
    return "NULL_IN_SCOPE"


__all__ = [
    "BANK_SCHEMA",
    "DISPOSITIONS",
    "M2_LOCAL_ARMS",
    "MechanismError",
    "PreparedBank",
    "admit_m4",
    "admit_m5",
    "freeze_candidate_bank",
    "freeze_m3_selector",
    "freeze_m6_linear_predictor",
    "m1_features_from_invariants",
    "panel_disposition",
    "prepare_candidate_bank",
    "prepare_panel_banks",
    "select_m1",
    "select_m3",
    "select_m4_candidates",
    "select_m6",
    "validate_disposition",
    "validate_m2_arms",
]
