#!/usr/bin/env python3
"""Fail-closed outcome analysis for the prospective Xedni rank-decay panel.

This program consumes *analysis rows*, not raw rank-tool transcripts.  A future
runner must preserve those transcripts and normalize each complete factorial
configuration into the exact ``xedni-rank-decay-analysis-row/v1`` schema
validated below.  No natural data are bundled with this module.

The signed rate convention is ``q(p) = kappa * p**beta``.  Thus the historical
``1/p`` model has ``beta = -1`` and meaningfully slower decay requires a lower
simultaneous confidence bound greater than ``-0.8``.

Production ``DEFEATED_IN_SCOPE`` is additionally hard-blocked until two open
obligations have executable implementations: rigorous minimization over mixed
per-prime unresolved allocations, and binding every row to frozen rosters plus
raw rank/relation evidence.  Non-CLI test-only switches exercise downstream
Boolean logic without weakening that production boundary.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable

from prime_manifest import is_prime_u32


ROW_SCHEMA = "xedni-rank-decay-analysis-row/v1"
RESULT_SCHEMA = "xedni-rank-decay-analysis/v1"
ROBUSTNESS_SCHEMA = "xedni-rank-decay-robustness/v1"
BIT_SIZES = (16, 18, 20, 22, 24, 26, 28, 30, 32)
INFERENCE_STAGES = ("discovery", "replication")
STAGES = ("controls", "calibration", "sentinel") + INFERENCE_STAGES
PANELS = ("primary", "M1", "M2", "M3", "M4", "M5", "M6")
CURVE_FAMILIES = ("generic", "j0")
LOCAL_ARMS = (
    "A_none",
    "B_reverse_mestre",
    "P_neutral_crt",
    "C_size_matched",
    "I_incompatible",
    "B_reverse_mestre_plus1",
    "B_reverse_mestre_plus2",
    "pairwise_coprime_canary",
)
ROW_STATUSES = (
    "ranked",
    "local_rejected",
    "construction_rejected",
    "certificate_failed",
)
TOOL_STATUSES = ("certified", "timeout", "error", "unavailable")
CERT_STATES = ("CERT_YES", "CERT_NO", "UNKNOWN")
RELATION_CLASSES = (
    "none",
    "line",
    "torsion",
    "parallelogram",
    "nontrivial",
    "unknown",
)
RANK_CLASSES = ("CERT_LT", "CERT_GE", "UNKNOWN")
SAFE_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+/-]{0,127}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")

ROW_KEYS = {
    "schema",
    "trial_id",
    "master_seed",
    "stage",
    "panel",
    "arm",
    "p",
    "bits",
    "curve_family",
    "lift_strategy",
    "local_arm",
    "r",
    "index",
    "planned_trials",
    "source_id",
    "curve_id",
    "isomorphism_class_id",
    "lift_digest",
    "status",
    "rank",
    "outcome",
    "work",
}
TOOL_KEYS = {"status", "version", "lower", "upper", "exact", "wall_ns"}
RANK_KEYS = {"pari", "magma"}
OUTCOME_KEYS = {
    "selected_dependence",
    "relation_class",
    "rational_relation_replay",
    "relation_certificate_sha256",
    "relation_proof_verified",
    "target_coefficient_invertible",
    "scalar_replay",
    "source_replay_sha256",
    "source_replay_proof_verified",
    "useful_recovery",
}
WORK_KEYS = {
    "complete",
    "source_generation_candidates",
    "local_construction_candidates",
    "lift_candidates",
    "rejected_candidates",
    "duplicate_candidates",
    "public_group_operations",
    "rank_calls",
    "cpu_seconds",
    "peak_rss_bytes",
    "retained_bytes",
}
WORK_INTEGER_KEYS = WORK_KEYS - {"complete", "cpu_seconds"}
ROBUSTNESS_METHODS = ("binomial_cloglog", "cluster_robust_cloglog")
CLUSTER_METHODS = ("cluster_bootstrap_cloglog",)
ROBUSTNESS_KEYS = {
    "schema",
    "artifact_id",
    "input_rowset_sha256",
    "protocol_sha256",
    "sensitivity_implementation_sha256",
    "freeze_manifest_sha256",
    "familywise_alpha",
    "simultaneous_hypotheses",
    "binomial_model",
    "cluster_method",
    "cluster_keys",
    "cluster_replicates",
    "minimum_cluster_replicates",
    "cluster_seed",
    "useful_event_min_bits",
    "complete",
    "profiles",
}
ROBUST_PROFILE_KEYS = {
    "series",
    "method",
    "endpoint",
    "denominator",
    "unresolved_allocation",
    "signed_beta_lower",
}
FREEZE_ANALYSIS_KEYS = {
    "familywise_alpha",
    "simultaneous_hypotheses",
    "endpoints",
    "denominators",
    "unresolved_allocations",
    "methods",
    "cluster_method",
    "cluster_keys",
    "cluster_replicates",
    "cluster_seed",
    "useful_event_min_bits",
}


class AnalysisError(ValueError):
    """Input is malformed, semantically inconsistent, or incomplete."""


def _exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise AnalysisError(f"{context}: key mismatch; missing={missing}, extra={extra}")


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nonnegative_int(value: Any, context: str) -> int:
    if not _is_plain_int(value) or value < 0:
        raise AnalysisError(f"{context}: expected a nonnegative integer")
    return value


def _boolean(value: Any, context: str) -> bool:
    if not isinstance(value, bool):
        raise AnalysisError(f"{context}: expected a boolean")
    return value


def _token(value: Any, context: str) -> str:
    if not isinstance(value, str) or SAFE_TOKEN.fullmatch(value) is None:
        raise AnalysisError(f"{context}: invalid or empty token")
    return value


def _enum(value: Any, choices: tuple[str, ...], context: str) -> str:
    if value not in choices:
        raise AnalysisError(f"{context}: unknown value {value!r}")
    return value


def _validate_tool(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AnalysisError(f"{context}: expected an object")
    _exact_keys(value, TOOL_KEYS, context)
    status = _enum(value["status"], TOOL_STATUSES, f"{context}.status")
    _token(value["version"], f"{context}.version")
    exact = _boolean(value["exact"], f"{context}.exact")
    _nonnegative_int(value["wall_ns"], f"{context}.wall_ns")
    lower, upper = value["lower"], value["upper"]
    if status == "certified":
        lower = _nonnegative_int(lower, f"{context}.lower")
        upper = _nonnegative_int(upper, f"{context}.upper")
        if lower > upper:
            raise AnalysisError(f"{context}: lower bound exceeds upper bound")
        if exact != (lower == upper):
            raise AnalysisError(
                f"{context}: exact must be true exactly when lower equals upper"
            )
    else:
        if lower is not None or upper is not None or exact:
            raise AnalysisError(
                f"{context}: uncertified result must have null bounds and exact=false"
            )
    return value


def _validate_outcome(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AnalysisError(f"{context}: expected an object")
    _exact_keys(value, OUTCOME_KEYS, context)
    dependent = _enum(
        value["selected_dependence"], CERT_STATES, f"{context}.selected_dependence"
    )
    relation_class = _enum(
        value["relation_class"], RELATION_CLASSES, f"{context}.relation_class"
    )
    relation_replay = _enum(
        value["rational_relation_replay"],
        CERT_STATES,
        f"{context}.rational_relation_replay",
    )
    relation_proof = _boolean(
        value["relation_proof_verified"], f"{context}.relation_proof_verified"
    )
    invertible = _enum(
        value["target_coefficient_invertible"],
        CERT_STATES,
        f"{context}.target_coefficient_invertible",
    )
    replay = _enum(
        value["scalar_replay"], CERT_STATES, f"{context}.scalar_replay"
    )
    source_proof = _boolean(
        value["source_replay_proof_verified"],
        f"{context}.source_replay_proof_verified",
    )
    useful = _enum(
        value["useful_recovery"], CERT_STATES, f"{context}.useful_recovery"
    )
    if dependent == "CERT_NO" and relation_class != "none":
        raise AnalysisError(f"{context}: certified independence requires relation=none")
    if dependent == "UNKNOWN" and relation_class != "unknown":
        raise AnalysisError(f"{context}: unresolved dependence requires relation=unknown")
    if dependent == "CERT_YES" and relation_class in ("none", "unknown"):
        raise AnalysisError(
            f"{context}: certified dependence requires a certified relation class"
        )
    if dependent == "CERT_YES" and relation_replay != "CERT_YES":
        raise AnalysisError(
            f"{context}: certified dependence requires exact rational relation replay"
        )
    if relation_replay == "CERT_YES" and dependent != "CERT_YES":
        raise AnalysisError(
            f"{context}: successful relation replay must certify dependence"
        )
    if relation_proof != (relation_replay == "CERT_YES"):
        raise AnalysisError(
            f"{context}: relation proof flag must match successful exact replay"
        )
    if invertible != "UNKNOWN" and dependent != "CERT_YES":
        raise AnalysisError(
            f"{context}: target-coefficient status requires a certified relation"
        )
    if replay != "UNKNOWN" and dependent != "CERT_YES":
        raise AnalysisError(f"{context}: replay status requires a certified relation")
    if replay == "CERT_YES" and invertible != "CERT_YES":
        raise AnalysisError(
            f"{context}: successful scalar replay requires an invertible coefficient"
        )
    if source_proof != (replay == "CERT_YES"):
        raise AnalysisError(
            f"{context}: source replay proof flag must match successful scalar replay"
        )
    for digest_key, state in (
        ("relation_certificate_sha256", relation_replay),
        ("source_replay_sha256", replay),
    ):
        digest = value[digest_key]
        if state == "UNKNOWN":
            if digest is not None:
                raise AnalysisError(
                    f"{context}.{digest_key}: unresolved replay requires null digest"
                )
        elif not isinstance(digest, str) or HEX64.fullmatch(digest) is None:
            raise AnalysisError(
                f"{context}.{digest_key}: certified replay status requires SHA-256"
            )
    components = (
        dependent,
        relation_replay,
        "CERT_YES" if relation_class not in ("none", "unknown") else (
            "CERT_NO" if relation_class == "none" else "UNKNOWN"
        ),
        invertible,
        replay,
    )
    if all(component == "CERT_YES" for component in components):
        expected_useful = "CERT_YES"
    elif any(component == "CERT_NO" for component in components):
        expected_useful = "CERT_NO"
    else:
        expected_useful = "UNKNOWN"
    if useful != expected_useful:
        raise AnalysisError(
            f"{context}: useful recovery must be the three-state conjunction of "
            "dependence, relation, invertibility, and scalar replay"
        )
    return value


def _validate_work(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AnalysisError(f"{context}: expected an object")
    _exact_keys(value, WORK_KEYS, context)
    _boolean(value["complete"], f"{context}.complete")
    for key in WORK_INTEGER_KEYS:
        _nonnegative_int(value[key], f"{context}.{key}")
    cpu = value["cpu_seconds"]
    if isinstance(cpu, bool) or not isinstance(cpu, (int, float)):
        raise AnalysisError(f"{context}.cpu_seconds: expected a finite nonnegative number")
    if not math.isfinite(float(cpu)) or cpu < 0:
        raise AnalysisError(f"{context}.cpu_seconds: expected a finite nonnegative number")
    return value


def validate_row(value: Any, line_number: int | None = None) -> dict[str, Any]:
    context = f"line {line_number}" if line_number is not None else "row"
    if not isinstance(value, dict):
        raise AnalysisError(f"{context}: expected a JSON object")
    _exact_keys(value, ROW_KEYS, context)
    if value["schema"] != ROW_SCHEMA:
        raise AnalysisError(f"{context}.schema: unknown schema {value['schema']!r}")
    for key in (
        "trial_id",
        "master_seed",
        "arm",
        "lift_strategy",
        "source_id",
        "curve_id",
        "isomorphism_class_id",
    ):
        _token(value[key], f"{context}.{key}")
    _enum(value["stage"], STAGES, f"{context}.stage")
    _enum(value["panel"], PANELS, f"{context}.panel")
    _enum(value["curve_family"], CURVE_FAMILIES, f"{context}.curve_family")
    _enum(value["local_arm"], LOCAL_ARMS, f"{context}.local_arm")
    status = _enum(value["status"], ROW_STATUSES, f"{context}.status")
    prime = _nonnegative_int(value["p"], f"{context}.p")
    bits = _nonnegative_int(value["bits"], f"{context}.bits")
    if prime >= 2**32 or not is_prime_u32(prime):
        raise AnalysisError(f"{context}.p: expected a certified prime below 2^32")
    if bits != prime.bit_length():
        raise AnalysisError(f"{context}: bits does not equal p.bit_length()")
    if value["stage"] != "controls" and bits not in BIT_SIZES:
        raise AnalysisError(f"{context}.bits: not in the frozen natural bit roster")
    r = _nonnegative_int(value["r"], f"{context}.r")
    if not 2 <= r <= 9:
        raise AnalysisError(f"{context}.r: expected 2 <= r <= 9")
    index = _nonnegative_int(value["index"], f"{context}.index")
    planned = _nonnegative_int(value["planned_trials"], f"{context}.planned_trials")
    if planned == 0 or index >= planned:
        raise AnalysisError(f"{context}: index lies outside planned_trials")
    if not isinstance(value["lift_digest"], str) or HEX64.fullmatch(
        value["lift_digest"]
    ) is None:
        raise AnalysisError(f"{context}.lift_digest: expected lowercase SHA-256")
    _validate_work(value["work"], f"{context}.work")
    if status == "ranked":
        if not isinstance(value["rank"], dict):
            raise AnalysisError(f"{context}.rank: expected an object")
        _exact_keys(value["rank"], RANK_KEYS, f"{context}.rank")
        _validate_tool(value["rank"]["pari"], f"{context}.rank.pari")
        _validate_tool(value["rank"]["magma"], f"{context}.rank.magma")
        _validate_outcome(value["outcome"], f"{context}.outcome")
    elif value["rank"] is not None or value["outcome"] is not None:
        raise AnalysisError(
            f"{context}: non-ranked status must have rank=null and outcome=null"
        )
    return value


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise AnalysisError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> None:
    raise AnalysisError(f"non-finite JSON number {value!r} is not allowed")


def _strict_json_loads(raw: str, context: str) -> Any:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise AnalysisError(f"{context}: invalid JSON: {exc}") from exc


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                raise AnalysisError(f"line {line_number}: blank lines are not allowed")
            value = _strict_json_loads(raw, f"line {line_number}")
            rows.append(validate_row(value, line_number))
    return rows


def _tool_side(tool: dict[str, Any], r: int) -> str | None:
    if tool["status"] != "certified":
        return None
    if tool["upper"] < r:
        return "CERT_LT"
    if tool["lower"] >= r:
        return "CERT_GE"
    return None


def classify_rank(row: dict[str, Any]) -> dict[str, Any]:
    """Classify from certified intervals only; never coerce a straddling bound."""
    if row["status"] != "ranked":
        raise AnalysisError("rank classification requested for a non-ranked row")
    tools = [row["rank"]["pari"], row["rank"]["magma"]]
    certified = [tool for tool in tools if tool["status"] == "certified"]
    conflict = False
    if certified:
        combined_lower = max(tool["lower"] for tool in certified)
        combined_upper = min(tool["upper"] for tool in certified)
        conflict = combined_lower > combined_upper
    sides = [_tool_side(tool, row["r"]) for tool in tools]
    nonnull_sides = {side for side in sides if side is not None}
    pari_certified = tools[0]["status"] == "certified"
    if conflict or len(nonnull_sides) > 1:
        rank_class = "UNKNOWN"
    elif sides[0] == "CERT_GE":
        # Ordinary PARI CERT_GE rows are not routed to Magma.
        rank_class = "CERT_GE"
    elif sides[0] == "CERT_LT" and sides[1] == "CERT_LT":
        # Apparent low-rank events require independent Magma confirmation.
        rank_class = "CERT_LT"
    elif pari_certified and sides[0] is None and sides[1] is not None:
        # A certified PARI interval straddles r; a compatible Magma interval
        # can resolve the side.  Missing/timed-out PARI cannot use this route.
        rank_class = sides[1]
    else:
        rank_class = "UNKNOWN"
    double_certified = (
        sides[0] is not None and sides[0] == sides[1] == rank_class
    )
    return {
        "rank_class": rank_class,
        "tool_sides": {"pari": sides[0], "magma": sides[1]},
        "double_certified": double_certified,
        "event_confirmed": rank_class == "CERT_LT",
        "conflict": conflict or len(nonnull_sides) > 1,
    }


def is_doubly_certified_nontrivial_useful(row: dict[str, Any]) -> bool:
    """Require exact rational-relation and exact source-scalar replay."""
    if row["status"] != "ranked":
        return False
    outcome = row["outcome"]
    return (
        outcome["selected_dependence"] == "CERT_YES"
        and outcome["relation_class"] == "nontrivial"
        and outcome["rational_relation_replay"] == "CERT_YES"
        and outcome["relation_proof_verified"]
        and isinstance(outcome["relation_certificate_sha256"], str)
        and outcome["target_coefficient_invertible"] == "CERT_YES"
        and outcome["scalar_replay"] == "CERT_YES"
        and outcome["source_replay_proof_verified"]
        and isinstance(outcome["source_replay_sha256"], str)
        and outcome["useful_recovery"] == "CERT_YES"
    )


def classify_useful_endpoint(row: dict[str, Any]) -> str:
    """Classify the exact nontrivial useful-recovery endpoint.

    Recovery censoring is separate from curve-rank censoring.  In particular,
    ``rank(E(Q)) >= r`` neither proves nor refutes dependence of the selected
    points; an exact selected-point relation can exist on a higher-rank curve.
    """
    if row["status"] in ("local_rejected", "construction_rejected"):
        return "CERT_NO"
    if row["status"] == "certificate_failed":
        return "UNKNOWN"
    if is_doubly_certified_nontrivial_useful(row):
        return "CERT_YES"
    # Replaying a false, trivial, or noninvertible supplied candidate does not
    # prove that no other useful relation exists.  Until an exhaustive
    # relation-lattice/independence certificate is implemented, every ranked
    # non-success remains censored rather than becoming a negative endpoint.
    return "UNKNOWN"


def _full_cell_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["stage"],
        row["panel"],
        row["arm"],
        row["p"],
        row["bits"],
        row["curve_family"],
        row["lift_strategy"],
        row["local_arm"],
        row["r"],
    )


def _series_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["stage"],
        row["panel"],
        row["arm"],
        row["curve_family"],
        row["lift_strategy"],
        row["local_arm"],
        row["r"],
    )


def _pair_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["panel"],
        row["arm"],
        row["curve_family"],
        row["lift_strategy"],
        row["local_arm"],
        row["r"],
    )


def _key_object(key: tuple[Any, ...], fields: tuple[str, ...]) -> dict[str, Any]:
    return dict(zip(fields, key, strict=True))


FULL_CELL_FIELDS = (
    "stage",
    "panel",
    "arm",
    "p",
    "bits",
    "curve_family",
    "lift_strategy",
    "local_arm",
    "r",
)
SERIES_FIELDS = (
    "stage",
    "panel",
    "arm",
    "curve_family",
    "lift_strategy",
    "local_arm",
    "r",
)
PAIR_FIELDS = (
    "panel",
    "arm",
    "curve_family",
    "lift_strategy",
    "local_arm",
    "r",
)


def _fraction(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def _sum_work(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    result: dict[str, Any] = {
        key: sum(row["work"][key] for row in rows) for key in WORK_INTEGER_KEYS
    }
    result["cpu_seconds"] = sum(float(row["work"]["cpu_seconds"]) for row in rows)
    result["all_complete"] = all(row["work"]["complete"] for row in rows)
    return result


def _validate_rosters(rows: list[dict[str, Any]]) -> None:
    trial_ids: set[str] = set()
    factorial_keys: set[tuple[Any, ...]] = set()
    rosters: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["trial_id"] in trial_ids:
            raise AnalysisError(f"duplicate trial_id {row['trial_id']!r}")
        trial_ids.add(row["trial_id"])
        key = _full_cell_key(row) + (row["index"],)
        if key in factorial_keys:
            raise AnalysisError(f"duplicate full factorial row {key!r}")
        factorial_keys.add(key)
        rosters[_full_cell_key(row)].append(row)
    for key, group in rosters.items():
        planned_values = {row["planned_trials"] for row in group}
        if len(planned_values) != 1:
            raise AnalysisError(f"cell {key!r}: inconsistent planned_trials")
        planned = next(iter(planned_values))
        indices = {row["index"] for row in group}
        expected = set(range(planned))
        if indices != expected:
            missing = sorted(expected - indices)
            extra = sorted(indices - expected)
            raise AnalysisError(
                f"cell {key!r}: incomplete roster; missing={missing}, extra={extra}"
            )


def aggregate_cells(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _validate_rosters(rows)
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_full_cell_key(row)].append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        group = grouped[key]
        statuses = Counter(row["status"] for row in group)
        ranked = [row for row in group if row["status"] == "ranked"]
        classes = [classify_rank(row) for row in ranked]
        counts = Counter(item["rank_class"] for item in classes)
        a_count = counts["CERT_LT"]
        g_count = counts["CERT_GE"]
        u_count = counts["UNKNOWN"]
        n_count = len(ranked)
        useful = sum(is_doubly_certified_nontrivial_useful(row) for row in ranked)
        trivial_useful = sum(
            row["outcome"]["useful_recovery"] == "CERT_YES"
            and row["outcome"]["relation_class"]
            in ("line", "torsion", "parallelogram")
            for row in ranked
        )
        useful_endpoint_counts = Counter(
            classify_useful_endpoint(row) for row in group
        )
        dependence_counts = Counter(
            row["outcome"]["selected_dependence"] for row in ranked
        )

        curve_classes: dict[str, set[str]] = defaultdict(set)
        for row, classification in zip(ranked, classes, strict=True):
            curve_classes[row["isomorphism_class_id"]].add(
                classification["rank_class"]
            )
        curve_counts = Counter()
        for iso_id, observed in curve_classes.items():
            if "CERT_LT" in observed and "CERT_GE" in observed:
                raise AnalysisError(
                    f"cell {key!r}: isomorphism class {iso_id!r} has contradictory "
                    "certified rank classifications"
                )
            if "CERT_LT" in observed:
                curve_counts["CERT_LT"] += 1
            elif "CERT_GE" in observed:
                curve_counts["CERT_GE"] += 1
            else:
                curve_counts["UNKNOWN"] += 1
        curve_n = sum(curve_counts.values())

        output.append(
            {
                "cell": _key_object(key, FULL_CELL_FIELDS),
                "proposals": len(group),
                "status_counts": {name: statuses[name] for name in ROW_STATUSES},
                "configuration_weighted": {
                    "A": a_count,
                    "G": g_count,
                    "U": u_count,
                    "N": n_count,
                    "q_min": _fraction(a_count, n_count),
                    "q_max": _fraction(a_count + u_count, n_count),
                    "q_min_per_proposal": _fraction(a_count, len(group)),
                    "q_max_per_proposal": _fraction(
                        a_count + u_count, len(group)
                    ),
                },
                "distinct_q_isomorphism_curve_weighted": {
                    "A": curve_counts["CERT_LT"],
                    "G": curve_counts["CERT_GE"],
                    "U": curve_counts["UNKNOWN"],
                    "N": curve_n,
                    "q_min": _fraction(curve_counts["CERT_LT"], curve_n),
                    "q_max": _fraction(
                        curve_counts["CERT_LT"] + curve_counts["UNKNOWN"],
                        curve_n,
                    ),
                },
                "doubly_certified_nontrivial_useful_recoveries": useful,
                "trivial_useful_recoveries": trivial_useful,
                "useful_recovery_endpoint": {
                    "A": useful_endpoint_counts["CERT_YES"],
                    "G": useful_endpoint_counts["CERT_NO"],
                    "U": useful_endpoint_counts["UNKNOWN"],
                    "N": len(group),
                    "q_min_per_proposal": _fraction(
                        useful_endpoint_counts["CERT_YES"], len(group)
                    ),
                    "q_max_per_proposal": _fraction(
                        useful_endpoint_counts["CERT_YES"]
                        + useful_endpoint_counts["UNKNOWN"],
                        len(group),
                    ),
                },
                "selected_point_dependence_endpoint": {
                    "status": "DESCRIPTIVE_ONLY_SLOPE_NOT_PREREGISTERED",
                    "A": dependence_counts["CERT_YES"],
                    "G": dependence_counts["CERT_NO"],
                    "U": dependence_counts["UNKNOWN"],
                    "N": len(ranked),
                    "q_min": _fraction(
                        dependence_counts["CERT_YES"], len(ranked)
                    ),
                    "q_max": _fraction(
                        dependence_counts["CERT_YES"]
                        + dependence_counts["UNKNOWN"],
                        len(ranked),
                    ),
                    "q_min_per_proposal": _fraction(
                        dependence_counts["CERT_YES"], len(group)
                    ),
                    "q_max_per_proposal": _fraction(
                        dependence_counts["CERT_YES"]
                        + dependence_counts["UNKNOWN"],
                        len(group),
                    ),
                },
                "rank_tool_conflicts": sum(item["conflict"] for item in classes),
                "work": _sum_work(group),
            }
        )
    return output


def _logsumexp(values: list[float]) -> float:
    maximum = max(values)
    return maximum + math.log(sum(math.exp(value - maximum) for value in values))


def _profile_terms(entries: list[tuple[int, int, int]], beta: float) -> tuple[float, float]:
    # entries are (p, exposure, successes), with positive exposure.
    xs = [math.log(p) for p, _, _ in entries]
    log_terms = [math.log(exposure) + beta * x for x, (_, exposure, _) in zip(xs, entries)]
    log_total = _logsumexp(log_terms)
    weights = [math.exp(value - log_total) for value in log_terms]
    successes = sum(count for _, _, count in entries)
    event_x = sum(count * x for x, (_, _, count) in zip(xs, entries))
    mean_x = sum(weight * x for weight, x in zip(weights, xs))
    log_likelihood = sum(
        count * (math.log(exposure) + beta * x - log_total)
        for x, (_, exposure, count) in zip(xs, entries)
    )
    derivative = event_x - successes * mean_x
    return log_likelihood, derivative


def _bisect_derivative(
    entries: list[tuple[int, int, int]], low: float, high: float
) -> float:
    for _ in range(160):
        middle = (low + high) / 2
        _, derivative = _profile_terms(entries, middle)
        if derivative > 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def _profile_mle(entries: list[tuple[int, int, int]]) -> float:
    low, high = -1.0, 1.0
    for _ in range(200):
        if _profile_terms(entries, low)[1] > 0:
            break
        low *= 2
    else:
        raise AnalysisError("failed to bracket the negative side of the profile MLE")
    for _ in range(200):
        if _profile_terms(entries, high)[1] < 0:
            break
        high *= 2
    else:
        raise AnalysisError("failed to bracket the positive side of the profile MLE")
    return _bisect_derivative(entries, low, high)


def _weighted_log_prime_mean(
    entries: list[tuple[int, int, int]], beta: float
) -> float:
    xs = [math.log(prime) for prime, _, _ in entries]
    terms = [
        math.log(exposure) + beta * x
        for x, (_, exposure, _) in zip(xs, entries, strict=True)
    ]
    normalizer = _logsumexp(terms)
    return sum(
        math.exp(term - normalizer) * x
        for term, x in zip(terms, xs, strict=True)
    )


def _invert_weighted_mean(
    entries: list[tuple[int, int, int]], target: float
) -> float:
    low, high = -1.0, 1.0
    for _ in range(200):
        if _weighted_log_prime_mean(entries, low) <= target:
            break
        low *= 2
    else:
        raise AnalysisError("failed to bracket a conservative lower slope bound")
    for _ in range(200):
        if _weighted_log_prime_mean(entries, high) >= target:
            break
        high *= 2
    else:
        raise AnalysisError("failed to bracket a conservative upper slope bound")
    for _ in range(160):
        middle = (low + high) / 2
        if _weighted_log_prime_mean(entries, middle) >= target:
            high = middle
        else:
            low = middle
    return (low + high) / 2


def poisson_profile(
    entries: Iterable[tuple[int, int, int]],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
) -> dict[str, Any]:
    """Conditional/profile Poisson slope with a conservative simultaneous CI.

    Profiling the intercept is equivalent to conditioning on the total event
    count.  Given total S, event locations have weights proportional to
    ``N_i * p_i**beta``.  The signed MLE is the profile-Poisson slope.  The
    reported interval inverts Hoeffding's finite-sample bound for the mean
    event location and applies Bonferroni to both tails of every prospectively
    counted profile.  It is conservative conditional on the total event count.
    """
    entries = sorted(entries)
    if not 0 < familywise_alpha < 1:
        raise AnalysisError("familywise_alpha must lie strictly between 0 and 1")
    if not _is_plain_int(simultaneous_hypotheses) or simultaneous_hypotheses <= 0:
        raise AnalysisError("simultaneous_hypotheses must be a positive integer")
    normalized: list[tuple[int, int, int]] = []
    for prime, exposure, successes in entries:
        if not (_is_plain_int(prime) and prime > 1):
            raise AnalysisError("profile prime must be an integer greater than one")
        if not (_is_plain_int(exposure) and exposure > 0):
            raise AnalysisError("profile exposure must be a positive integer")
        if not (_is_plain_int(successes) and 0 <= successes <= exposure):
            raise AnalysisError("profile successes must lie in [0, exposure]")
        normalized.append((prime, exposure, successes))
    total_events = sum(item[2] for item in normalized)
    distinct_primes = len({item[0] for item in normalized})
    base = {
        "model": "S_p ~ Poisson(N_p * exp(alpha) * p^beta)",
        "signed_beta_convention": "1/p corresponds to beta=-1",
        "entries": [
            {"p": prime, "exposure": exposure, "successes": successes}
            for prime, exposure, successes in normalized
        ],
        "total_events": total_events,
        "familywise_alpha": familywise_alpha,
        "simultaneous_hypotheses": simultaneous_hypotheses,
        "interval_method": (
            "Bonferroni two-sided conditional Hoeffding inversion "
            "(finite-sample conservative)"
        ),
    }
    if total_events == 0 or distinct_primes < 2:
        return {
            **base,
            "identifiable": False,
            "reason": "requires at least one event and two distinct primes",
            "beta_hat": None,
            "confidence_interval": {"lower": None, "upper": None},
        }
    xs = [math.log(item[0]) for item in normalized]
    event_mean = sum(
        item[2] * x for item, x in zip(normalized, xs, strict=True)
    ) / total_events
    min_x, max_x = min(xs), max(xs)
    event_primes = {prime for prime, _, count in normalized if count}
    if event_primes == {min(item[0] for item in normalized)}:
        beta_hat: float | str = "-inf"
        profile_log_likelihood = None
    elif event_primes == {max(item[0] for item in normalized)}:
        beta_hat = "+inf"
        profile_log_likelihood = None
    else:
        beta_hat = _profile_mle(normalized)
        profile_log_likelihood, _ = _profile_terms(normalized, beta_hat)

    tail_alpha = familywise_alpha / (2 * simultaneous_hypotheses)
    radius = (max_x - min_x) * math.sqrt(
        math.log(1 / tail_alpha) / (2 * total_events)
    )
    lower_target = event_mean - radius
    upper_target = event_mean + radius
    if lower_target <= min_x:
        lower = "-inf"
    else:
        lower = _invert_weighted_mean(normalized, lower_target)
    if upper_target >= max_x:
        upper = "+inf"
    else:
        upper = _invert_weighted_mean(normalized, upper_target)
    return {
        **base,
        "identifiable": True,
        "reason": None,
        "beta_hat": beta_hat,
        "confidence_interval": {"lower": lower, "upper": upper},
        "per_tail_alpha": tail_alpha,
        "hoeffding_log_prime_mean_radius": radius,
        "observed_event_log_prime_mean": event_mean,
        "profile_log_likelihood_at_finite_hat": profile_log_likelihood,
    }


def _profile_inputs(
    rows: list[dict[str, Any]],
    endpoint: str,
    denominator: str,
    unresolved_allocation: str,
) -> list[tuple[int, int, int]]:
    by_prime: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_prime[row["p"]].append(row)
    entries: list[tuple[int, int, int]] = []
    for prime in sorted(by_prime):
        group = by_prime[prime]
        ranked = [row for row in group if row["status"] == "ranked"]
        if denominator == "admitted":
            exposure = len(ranked)
        elif denominator == "proposed":
            exposure = len(group)
        else:
            raise AssertionError(denominator)
        if not exposure:
            continue
        if endpoint == "rank_lt_r":
            classifications = [classify_rank(row) for row in ranked]
            successes = sum(item["rank_class"] == "CERT_LT" for item in classifications)
            unknown = sum(
                item["rank_class"] == "UNKNOWN" for item in classifications
            )
            if denominator == "proposed":
                unknown += sum(row["status"] == "certificate_failed" for row in group)
        elif endpoint == "nontrivial_useful_recovery":
            endpoint_rows = ranked if denominator == "admitted" else group
            endpoint_classes = [
                classify_useful_endpoint(row) for row in endpoint_rows
            ]
            successes = sum(item == "CERT_YES" for item in endpoint_classes)
            unknown = sum(item == "UNKNOWN" for item in endpoint_classes)
        else:
            raise AssertionError(endpoint)
        if unresolved_allocation == "all_success":
            successes += unknown
        elif unresolved_allocation != "all_failure":
            raise AssertionError(unresolved_allocation)
        if successes > exposure:
            raise AnalysisError(
                f"p={prime}: unresolved allocation produces successes > exposure"
            )
        entries.append((prime, exposure, successes))
    return entries


def build_profiles(
    rows: list[dict[str, Any]],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    useful_event_min_bits: int | None,
) -> list[dict[str, Any]]:
    series: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["stage"] in INFERENCE_STAGES:
            series[_series_key(row)].append(row)
    requested_profile_count = len(series) * 2 * 2 * 2
    if requested_profile_count and simultaneous_hypotheses < requested_profile_count:
        raise AnalysisError(
            "simultaneous_hypotheses is smaller than the number of reported "
            f"profiles ({simultaneous_hypotheses} < {requested_profile_count})"
        )
    profiles: list[dict[str, Any]] = []
    for key in sorted(series):
        tail_rows = [
            row
            for row in series[key]
            if useful_event_min_bits is None
            or row["bits"] >= useful_event_min_bits
        ]
        for endpoint in ("rank_lt_r", "nontrivial_useful_recovery"):
            for denominator in ("admitted", "proposed"):
                for allocation in ("all_failure", "all_success"):
                    fit = poisson_profile(
                        _profile_inputs(
                            tail_rows, endpoint, denominator, allocation
                        ),
                        familywise_alpha=familywise_alpha,
                        simultaneous_hypotheses=simultaneous_hypotheses,
                    )
                    profiles.append(
                        {
                            "series": _key_object(key, SERIES_FIELDS),
                            "endpoint": endpoint,
                            "denominator": denominator,
                            "unresolved_allocation": allocation,
                            "useful_event_min_bits": useful_event_min_bits,
                            "fit": fit,
                        }
                    )
    return profiles


def rowset_sha256(rows: list[dict[str, Any]]) -> str:
    """Digest a validated row set independently of JSONL line ordering."""
    ordered = sorted(rows, key=lambda row: row["trial_id"])
    payload = json.dumps(
        ordered,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def protocol_sha256() -> str:
    return hashlib.sha256(
        Path(__file__).with_name("PROTOCOL.md").read_bytes()
    ).hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    value = _strict_json_loads(path.read_text(encoding="utf-8"), str(path))
    if not isinstance(value, dict):
        raise AnalysisError(f"{path}: expected a JSON object")
    return value


def freeze_object_sha256(value: dict[str, Any]) -> str:
    """Canonical digest used only for an explicitly injected trusted object."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _trusted_freeze(
    injected: dict[str, Any] | None,
) -> tuple[dict[str, Any], str]:
    if injected is not None:
        if not isinstance(injected, dict):
            raise AnalysisError("injected trusted freeze must be an object")
        return injected, freeze_object_sha256(injected)
    freeze_path = Path(__file__).with_name("FREEZE.json")
    if not freeze_path.is_file():
        raise AnalysisError(
            "robustness artifact: trusted FREEZE.json is absent; production "
            "analysis cannot accept a digest override"
        )
    return read_json_object(freeze_path), hashlib.sha256(
        freeze_path.read_bytes()
    ).hexdigest()


def validate_freeze_analysis(
    freeze: dict[str, Any],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    cluster_method: str,
    cluster_replicates: int,
    cluster_seed: str,
) -> None:
    analysis = freeze.get("analysis")
    if not isinstance(analysis, dict):
        raise AnalysisError("trusted freeze: missing analysis object")
    missing = FREEZE_ANALYSIS_KEYS - set(analysis)
    if missing:
        raise AnalysisError(
            f"trusted freeze.analysis: missing frozen fields {sorted(missing)}"
        )
    frozen_alpha = analysis["familywise_alpha"]
    if (
        isinstance(frozen_alpha, bool)
        or not isinstance(frozen_alpha, (int, float))
        or not math.isfinite(float(frozen_alpha))
        or float(frozen_alpha) != float(familywise_alpha)
    ):
        raise AnalysisError("trusted freeze: familywise_alpha mismatch")
    if analysis["simultaneous_hypotheses"] != simultaneous_hypotheses:
        raise AnalysisError("trusted freeze: simultaneous_hypotheses mismatch")
    exact_lists = {
        "endpoints": ["rank_lt_r", "nontrivial_useful_recovery"],
        "denominators": ["admitted", "proposed"],
        "unresolved_allocations": ["all_failure", "all_success"],
        "methods": [
            "conditional_poisson",
            "binomial_cloglog",
            "cluster_robust_cloglog",
        ],
        "cluster_keys": ["bits", "p", "source_id", "curve_id"],
    }
    for key, expected in exact_lists.items():
        if analysis[key] != expected:
            raise AnalysisError(f"trusted freeze: {key} mismatch")
    if analysis["cluster_method"] != cluster_method:
        raise AnalysisError("trusted freeze: cluster_method mismatch")
    if analysis["cluster_replicates"] != cluster_replicates:
        raise AnalysisError("trusted freeze: cluster_replicates mismatch")
    if analysis["cluster_seed"] != cluster_seed:
        raise AnalysisError("trusted freeze: cluster_seed mismatch")
    useful_event_min_bits = analysis["useful_event_min_bits"]
    if (
        not _is_plain_int(useful_event_min_bits)
        or useful_event_min_bits not in BIT_SIZES
    ):
        raise AnalysisError(
            "trusted freeze: useful_event_min_bits must be a frozen bit size"
        )


def validate_robustness_artifact(
    value: Any,
    rows: list[dict[str, Any]],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    trusted_freeze: dict[str, Any] | None,
    test_only_allow_small_bootstrap: bool,
) -> dict[str, Any]:
    """Validate a separately frozen binomial/cluster sensitivity artifact.

    The analyzer does not silently substitute its conditional Poisson model
    for the preregistered binomial-cloglog and cluster checks.  The external
    artifact is bound to the exact row set and protocol by SHA-256 and must
    contain every required series/allocation/denominator contrast twice: once
    for binomial cloglog and once for a named cluster-robust sensitivity.
    """
    if not isinstance(value, dict):
        raise AnalysisError("robustness artifact: expected an object")
    _exact_keys(value, ROBUSTNESS_KEYS, "robustness artifact")
    if value["schema"] != ROBUSTNESS_SCHEMA:
        raise AnalysisError("robustness artifact: unknown schema")
    _token(value["artifact_id"], "robustness artifact.artifact_id")
    for key in (
        "input_rowset_sha256",
        "protocol_sha256",
        "sensitivity_implementation_sha256",
        "freeze_manifest_sha256",
    ):
        if not isinstance(value[key], str) or HEX64.fullmatch(value[key]) is None:
            raise AnalysisError(f"robustness artifact.{key}: expected lowercase SHA-256")
    if value["input_rowset_sha256"] != rowset_sha256(rows):
        raise AnalysisError("robustness artifact: input row-set digest mismatch")
    if value["protocol_sha256"] != protocol_sha256():
        raise AnalysisError("robustness artifact: protocol digest mismatch")
    sensitivity_path = Path(__file__).with_name("sensitivity.py")
    if not sensitivity_path.is_file():
        raise AnalysisError("robustness artifact: verified sensitivity.py is absent")
    actual_implementation_sha256 = hashlib.sha256(
        sensitivity_path.read_bytes()
    ).hexdigest()
    if value["sensitivity_implementation_sha256"] != actual_implementation_sha256:
        raise AnalysisError(
            "robustness artifact: sensitivity implementation digest mismatch"
        )
    trusted_freeze_object, trusted_freeze_sha256 = _trusted_freeze(trusted_freeze)
    if value["freeze_manifest_sha256"] != trusted_freeze_sha256:
        raise AnalysisError("robustness artifact: freeze manifest digest mismatch")
    artifact_alpha = value["familywise_alpha"]
    if (
        isinstance(artifact_alpha, bool)
        or not isinstance(artifact_alpha, (int, float))
        or not math.isfinite(float(artifact_alpha))
        or float(artifact_alpha) != float(familywise_alpha)
    ):
        raise AnalysisError("robustness artifact: familywise_alpha mismatch")
    if value["simultaneous_hypotheses"] != simultaneous_hypotheses:
        raise AnalysisError(
            "robustness artifact: simultaneous_hypotheses mismatch"
        )
    if value["binomial_model"] != (
        "S~Binomial(N,q); cloglog(q)=alpha+beta*log(p)"
    ):
        raise AnalysisError("robustness artifact: binomial model mismatch")
    cluster_method = _enum(
        value["cluster_method"], CLUSTER_METHODS, "robustness artifact.cluster_method"
    )
    if value["cluster_keys"] != ["bits", "p", "source_id", "curve_id"]:
        raise AnalysisError(
            "robustness artifact: cluster_keys must be bits/p/source_id/curve_id"
        )
    replicates = _nonnegative_int(
        value["cluster_replicates"], "robustness artifact.cluster_replicates"
    )
    if cluster_method == "cluster_bootstrap_cloglog" and replicates == 0:
        raise AnalysisError("robustness artifact: bootstrap requires replicates")
    minimum_replicates = math.ceil(
        2 * simultaneous_hypotheses / familywise_alpha
    )
    if value["minimum_cluster_replicates"] != minimum_replicates:
        raise AnalysisError(
            "robustness artifact: minimum bootstrap replicate calculation mismatch"
        )
    if replicates < minimum_replicates and not test_only_allow_small_bootstrap:
        raise AnalysisError(
            "robustness artifact: inadequate Bonferroni-tail resolution; "
            f"need at least {minimum_replicates} cluster replicates"
        )
    cluster_seed = _token(
        value["cluster_seed"], "robustness artifact.cluster_seed"
    )
    useful_event_min_bits = _nonnegative_int(
        value["useful_event_min_bits"],
        "robustness artifact.useful_event_min_bits",
    )
    if useful_event_min_bits not in BIT_SIZES:
        raise AnalysisError(
            "robustness artifact: useful_event_min_bits is not frozen bit size"
        )
    validate_freeze_analysis(
        trusted_freeze_object,
        familywise_alpha=familywise_alpha,
        simultaneous_hypotheses=simultaneous_hypotheses,
        cluster_method=cluster_method,
        cluster_replicates=replicates,
        cluster_seed=cluster_seed,
    )
    if (
        trusted_freeze_object["analysis"]["useful_event_min_bits"]
        != useful_event_min_bits
    ):
        raise AnalysisError(
            "robustness artifact: useful_event_min_bits disagrees with freeze"
        )
    if not _boolean(value["complete"], "robustness artifact.complete"):
        raise AnalysisError("robustness artifact: complete must be true")
    if not isinstance(value["profiles"], list):
        raise AnalysisError("robustness artifact.profiles: expected an array")

    series = {
        _series_key(row) for row in rows if row["stage"] in INFERENCE_STAGES
    }
    expected = {
        (key, method, endpoint, denominator, allocation)
        for key in series
        for method in ROBUSTNESS_METHODS
        for endpoint in ("rank_lt_r", "nontrivial_useful_recovery")
        for denominator in ("admitted", "proposed")
        for allocation in ("all_failure", "all_success")
    }
    observed: set[tuple[Any, ...]] = set()
    for index, profile in enumerate(value["profiles"]):
        context = f"robustness artifact.profiles[{index}]"
        if not isinstance(profile, dict):
            raise AnalysisError(f"{context}: expected an object")
        _exact_keys(profile, ROBUST_PROFILE_KEYS, context)
        series_object = profile["series"]
        if not isinstance(series_object, dict):
            raise AnalysisError(f"{context}.series: expected an object")
        _exact_keys(series_object, set(SERIES_FIELDS), f"{context}.series")
        series_key = tuple(series_object[field] for field in SERIES_FIELDS)
        method = _enum(profile["method"], ROBUSTNESS_METHODS, f"{context}.method")
        endpoint = _enum(
            profile["endpoint"],
            ("rank_lt_r", "nontrivial_useful_recovery"),
            f"{context}.endpoint",
        )
        denominator = _enum(
            profile["denominator"], ("admitted", "proposed"), f"{context}.denominator"
        )
        allocation = _enum(
            profile["unresolved_allocation"],
            ("all_failure", "all_success"),
            f"{context}.unresolved_allocation",
        )
        lower = profile["signed_beta_lower"]
        if lower != "-inf" and (
            isinstance(lower, bool)
            or not isinstance(lower, (int, float))
            or not math.isfinite(float(lower))
        ):
            raise AnalysisError(
                f"{context}.signed_beta_lower: expected finite number or '-inf'"
            )
        key = (series_key, method, endpoint, denominator, allocation)
        if key in observed:
            raise AnalysisError(f"{context}: duplicate robustness profile")
        observed.add(key)
    if observed != expected:
        missing = len(expected - observed)
        extra = len(observed - expected)
        raise AnalysisError(
            "robustness artifact: incomplete or foreign profile roster; "
            f"missing={missing}, extra={extra}"
        )
    import sensitivity

    recomputed_profiles = sensitivity.compute_profiles(
        rows,
        familywise_alpha=familywise_alpha,
        simultaneous_hypotheses=simultaneous_hypotheses,
        cluster_method=cluster_method,
        cluster_replicates=replicates,
        cluster_seed=cluster_seed,
        useful_event_min_bits=useful_event_min_bits,
    )
    if value["profiles"] != recomputed_profiles:
        raise AnalysisError(
            "robustness artifact: reported bounds differ from executable recomputation"
        )
    return value


def _has_three_adjacent_event_sizes(
    rows: list[dict[str, Any]], useful_event_min_bits: int
) -> bool:
    event_bits = {
        row["bits"] for row in rows if is_doubly_certified_nontrivial_useful(row)
    }
    longest = current = 0
    for bits in (value for value in BIT_SIZES if value >= useful_event_min_bits):
        if bits in event_bits:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest >= 3


def _fresh_replication(discovery: list[dict[str, Any]], replication: list[dict[str, Any]]) -> bool:
    fields = (
        "master_seed",
        "p",
        "source_id",
        "curve_id",
        "isomorphism_class_id",
        "lift_digest",
    )
    return all(
        {row[field] for row in discovery}.isdisjoint(
            {row[field] for row in replication}
        )
        for field in fields
    )


def evaluate_decision(
    rows: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    robustness_artifact: dict[str, Any] | None,
    provenance_verified: bool,
    interval_allocation_verified: bool,
    relation_inventory_verified: bool,
    useful_event_min_bits: int | None,
) -> dict[str, Any]:
    profile_index: dict[tuple[Any, ...], dict[str, Any]] = {}
    for profile in profiles:
        series = tuple(profile["series"][field] for field in SERIES_FIELDS)
        profile_index[
            (
                series,
                profile["endpoint"],
                profile["denominator"],
                profile["unresolved_allocation"],
            )
        ] = profile["fit"]
    robustness_index: dict[tuple[Any, ...], float | str] = {}
    if robustness_artifact is not None:
        for profile in robustness_artifact["profiles"]:
            series = tuple(
                profile["series"][field] for field in SERIES_FIELDS
            )
            robustness_index[
                (
                    series,
                    profile["method"],
                    profile["endpoint"],
                    profile["denominator"],
                    profile["unresolved_allocation"],
                )
            ] = profile["signed_beta_lower"]
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["stage"] in INFERENCE_STAGES:
            grouped[_pair_key(row)].append(row)
    candidates: list[dict[str, Any]] = []
    for key in sorted(grouped):
        group = grouped[key]
        reasons: list[str] = []
        if key[0] != "primary":
            reasons.append("mechanism panels cannot classify DEFEATED_IN_SCOPE")
        if key[4] in ("C_size_matched", "I_incompatible"):
            reasons.append("diagnostic local arm is excluded from the primary estimand")
        if robustness_artifact is None:
            reasons.append(
                "frozen binomial-cloglog and cluster-robust sensitivity artifact is absent"
            )
        if not provenance_verified:
            reasons.append(
                "frozen roster/prime/stage-seed and raw adapter/relation-certificate "
                "provenance is not executable-verified"
            )
        if not interval_allocation_verified:
            reasons.append(
                "rigorous worst-case mixed per-prime unresolved allocation is not "
                "implemented for all required slope models"
            )
        if not relation_inventory_verified:
            reasons.append(
                "complete proposed-relation inventory, coexistence classes, proof "
                "digests, and deterministic any-useful rule are not verified"
            )
        if useful_event_min_bits is None:
            reasons.append("frozen useful_event_min_bits is unavailable")
        discovery = [row for row in group if row["stage"] == "discovery"]
        replication = [row for row in group if row["stage"] == "replication"]
        if not discovery or not replication:
            reasons.append("both discovery and replication rows are required")
        total_useful_all_bits = sum(
            is_doubly_certified_nontrivial_useful(row) for row in group
        )
        total_useful = sum(
            is_doubly_certified_nontrivial_useful(row)
            and useful_event_min_bits is not None
            and row["bits"] >= useful_event_min_bits
            for row in group
        )
        if total_useful < 30:
            reasons.append(
                "fewer than 30 doubly certified nontrivial useful recoveries "
                "at or above the frozen bit cutoff (combined stages)"
            )
        stage_useful_counts: dict[str, int] = {}
        for stage_name, stage_rows in (
            ("discovery", discovery),
            ("replication", replication),
        ):
            stage_useful_counts[stage_name] = sum(
                is_doubly_certified_nontrivial_useful(row)
                and useful_event_min_bits is not None
                and row["bits"] >= useful_event_min_bits
                for row in stage_rows
            )
            if (
                stage_rows
                and useful_event_min_bits is not None
                and not _has_three_adjacent_event_sizes(
                    stage_rows, useful_event_min_bits
                )
            ):
                reasons.append(
                    f"{stage_name} lacks useful events at three adjacent frozen "
                    "sizes at or above the cutoff"
                )
        fresh = bool(discovery and replication) and _fresh_replication(
            discovery, replication
        )
        if discovery and replication and not fresh:
            reasons.append("replication does not use disjoint seeds/primes/sources/lifts")
        work_complete = all(row["work"]["complete"] for row in group)
        if not work_complete:
            reasons.append("complete work accounting is false on at least one row")
        if any(row["status"] == "certificate_failed" for row in group):
            reasons.append("certificate failure is present")
        ranked = [row for row in group if row["status"] == "ranked"]
        rank_evidence = [classify_rank(row) for row in ranked]
        if any(item["conflict"] for item in rank_evidence):
            reasons.append("rank tools have a contradictory certified interval")
        nontrivial_useful_outcomes = [
            row
            for row in ranked
            if row["outcome"]["useful_recovery"] == "CERT_YES"
            and row["outcome"]["relation_class"] == "nontrivial"
            and useful_event_min_bits is not None
            and row["bits"] >= useful_event_min_bits
        ]
        trivial_useful = sum(
            row["outcome"]["useful_recovery"] == "CERT_YES"
            and row["outcome"]["relation_class"]
            in ("line", "torsion", "parallelogram")
            and useful_event_min_bits is not None
            and row["bits"] >= useful_event_min_bits
            for row in ranked
        )
        if len(nontrivial_useful_outcomes) <= trivial_useful:
            reasons.append("useful outcomes are dominated by trivial relation classes")

        slope_checks: list[dict[str, Any]] = []
        for stage_name in INFERENCE_STAGES:
            series_key = (stage_name,) + key
            for endpoint in ("rank_lt_r", "nontrivial_useful_recovery"):
                for denominator in ("admitted", "proposed"):
                    for allocation in ("all_failure", "all_success"):
                        fit = profile_index.get(
                            (series_key, endpoint, denominator, allocation)
                        )
                        lower = (
                            None
                            if fit is None
                            else fit["confidence_interval"]["lower"]
                        )
                        passed = (
                            isinstance(lower, (int, float))
                            and not isinstance(lower, bool)
                            and lower > -0.8
                        )
                        slope_checks.append(
                            {
                                "stage": stage_name,
                                "endpoint": endpoint,
                                "model": "conditional_poisson",
                                "denominator": denominator,
                                "unresolved_allocation": allocation,
                                "simultaneous_lower_beta": lower,
                                "passed": passed,
                            }
                        )
                        if not passed:
                            reasons.append(
                                f"{stage_name}/{endpoint}/conditional_poisson/"
                                f"{denominator}/{allocation} does not have "
                                "simultaneous lower beta > -0.8"
                            )
                        for method in ROBUSTNESS_METHODS:
                            robust_lower = robustness_index.get(
                                (
                                    series_key,
                                    method,
                                    endpoint,
                                    denominator,
                                    allocation,
                                )
                            )
                            robust_passed = (
                                isinstance(robust_lower, (int, float))
                                and not isinstance(robust_lower, bool)
                                and robust_lower > -0.8
                            )
                            slope_checks.append(
                                {
                                    "stage": stage_name,
                                    "endpoint": endpoint,
                                    "model": method,
                                    "denominator": denominator,
                                    "unresolved_allocation": allocation,
                                    "simultaneous_lower_beta": robust_lower,
                                    "passed": robust_passed,
                                }
                            )
                            if not robust_passed:
                                reasons.append(
                                    f"{stage_name}/{endpoint}/{method}/"
                                    f"{denominator}/{allocation} does not have "
                                    "simultaneous lower beta > -0.8"
                                )
        candidates.append(
            {
                "factor_cell": _key_object(key, PAIR_FIELDS),
                "passed": not reasons,
                "reasons": sorted(set(reasons)),
                "doubly_certified_nontrivial_useful_recoveries": total_useful,
                "doubly_certified_useful_recoveries_all_bits": total_useful_all_bits,
                "useful_event_min_bits": useful_event_min_bits,
                "qualifying_useful_recoveries_by_stage": stage_useful_counts,
                "fresh_replication": fresh,
                "complete_work": work_complete,
                "slope_checks": slope_checks,
            }
        )
    passed = [candidate for candidate in candidates if candidate["passed"]]
    return {
        "classification": "DEFEATED_IN_SCOPE" if passed else "NOT_DEFEATED_IN_SCOPE",
        "defeated_in_scope": bool(passed),
        "rule": {
            "minimum_doubly_certified_nontrivial_useful_recoveries": 30,
            "minimum_useful_recoveries_scope": "combined discovery and replication",
            "useful_event_min_bits": useful_event_min_bits,
            "minimum_adjacent_sizes_per_stage": 3,
            "signed_beta_simultaneous_lower_threshold": -0.8,
            "required_stages": list(INFERENCE_STAGES),
            "required_unresolved_allocations": ["all_failure", "all_success"],
            "required_denominators": ["admitted", "proposed"],
            "required_models": [
                "conditional_poisson",
                "binomial_cloglog",
                "cluster_robust_cloglog",
            ],
            "requires_magma_confirmation_for_pari_cert_lt": True,
            "curve_rank_and_selected_recovery_are_separate_co_primary_endpoints": True,
            "requires_complete_work": True,
            "requires_executable_frozen_and_raw_provenance_binding": True,
            "requires_rigorous_mixed_per_prime_unresolved_optimization": True,
            "requires_complete_relation_proposal_and_coexistence_inventory": True,
        },
        "passing_factor_cells": [candidate["factor_cell"] for candidate in passed],
        "factor_cells": candidates,
        "no_natural_data": not any(
            row["stage"] in INFERENCE_STAGES for row in rows
        ),
        "provenance_verified": provenance_verified,
        "interval_allocation_verified": interval_allocation_verified,
        "relation_inventory_verified": relation_inventory_verified,
    }


def analyze(
    rows: list[dict[str, Any]],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    robustness_artifact: dict[str, Any] | None = None,
    trusted_freeze: dict[str, Any] | None = None,
    test_only_allow_small_bootstrap: bool = False,
    test_only_provenance_verified: bool = False,
    test_only_interval_allocation_verified: bool = False,
    test_only_relation_inventory_verified: bool = False,
) -> dict[str, Any]:
    validated = [validate_row(row) for row in rows]
    cells = aggregate_cells(validated)
    inference_series = {
        _series_key(row)
        for row in validated
        if row["stage"] in INFERENCE_STAGES
    }
    joint_profile_count = len(inference_series) * 2 * 2 * 2 * 3
    if joint_profile_count and simultaneous_hypotheses < joint_profile_count:
        raise AnalysisError(
            "simultaneous_hypotheses is smaller than the joint Poisson, "
            "binomial-cloglog, and cluster-robust profile roster "
            f"({simultaneous_hypotheses} < {joint_profile_count})"
        )
    useful_event_min_bits = None
    if robustness_artifact is not None:
        freeze_object, _ = _trusted_freeze(trusted_freeze)
        analysis_freeze = freeze_object.get("analysis")
        if isinstance(analysis_freeze, dict):
            candidate_min_bits = analysis_freeze.get("useful_event_min_bits")
            if _is_plain_int(candidate_min_bits):
                useful_event_min_bits = candidate_min_bits
    profiles = build_profiles(
        validated,
        familywise_alpha=familywise_alpha,
        simultaneous_hypotheses=simultaneous_hypotheses,
        useful_event_min_bits=useful_event_min_bits,
    )
    validated_robustness = (
        None
        if robustness_artifact is None
        else validate_robustness_artifact(
            robustness_artifact,
            validated,
            familywise_alpha=familywise_alpha,
            simultaneous_hypotheses=simultaneous_hypotheses,
            trusted_freeze=trusted_freeze,
            test_only_allow_small_bootstrap=test_only_allow_small_bootstrap,
        )
    )
    decision = evaluate_decision(
        validated,
        profiles,
        validated_robustness,
        test_only_provenance_verified,
        test_only_interval_allocation_verified,
        test_only_relation_inventory_verified,
        useful_event_min_bits,
    )
    test_only_overrides = {
        "small_bootstrap": test_only_allow_small_bootstrap,
        "provenance_verified": test_only_provenance_verified,
        "interval_allocation_verified": test_only_interval_allocation_verified,
        "relation_inventory_verified": test_only_relation_inventory_verified,
    }
    if any(test_only_overrides.values()):
        # The private switches exist only to exercise downstream Boolean logic
        # on synthetic fixtures.  They must never emit the literal production
        # verdict or leave a candidate marked as production-passing.
        synthetic_passing = list(decision["passing_factor_cells"])
        for candidate in decision["factor_cells"]:
            candidate["synthetic_would_pass_if_verified"] = candidate["passed"]
            candidate["passed"] = False
            candidate["reasons"] = sorted(
                set(candidate["reasons"])
                | {"test-only overrides cannot authorize a production verdict"}
            )
        decision["synthetic_would_pass_if_verified"] = bool(synthetic_passing)
        decision["synthetic_passing_factor_cells"] = synthetic_passing
        decision["classification"] = "NOT_DEFEATED_IN_SCOPE"
        decision["defeated_in_scope"] = False
        decision["passing_factor_cells"] = []
    else:
        decision["synthetic_would_pass_if_verified"] = None
        decision["synthetic_passing_factor_cells"] = []

    return {
        "schema": RESULT_SCHEMA,
        "input_rows": len(validated),
        "familywise_alpha": familywise_alpha,
        "simultaneous_hypotheses": simultaneous_hypotheses,
        "signed_beta_convention": "q(p)=kappa*p^beta; 1/p is beta=-1",
        "cells": cells,
        "profiles": profiles,
        "robustness_artifact": {
            "supplied": validated_robustness is not None,
            "schema": (
                None if validated_robustness is None else validated_robustness["schema"]
            ),
            "artifact_id": (
                None
                if validated_robustness is None
                else validated_robustness["artifact_id"]
            ),
            "input_rowset_sha256": rowset_sha256(validated),
            "protocol_sha256": protocol_sha256(),
        },
        "provenance_gate": {
            "status": (
                "TEST_ONLY_OVERRIDE"
                if test_only_provenance_verified
                else "BLOCKED_NO_FREEZE_BOUND_ROW_MANIFEST"
            ),
            "production_verified": False,
            "required_binding": (
                "FREEZE roster + PRIMES + stage seed + raw PARI/Magma transcripts "
                "+ relation/recovery certificate digests"
            ),
        },
        "decision": decision,
        "test_only_overrides_active": test_only_overrides,
    }


def render_json(value: Any) -> str:
    return json.dumps(
        value, indent=2, sort_keys=True, separators=(",", ": "), allow_nan=False
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="strict analysis-row JSONL")
    parser.add_argument("output", type=Path, help="analysis JSON")
    parser.add_argument(
        "--familywise-alpha", type=float, default=0.05, help="default: 0.05"
    )
    parser.add_argument(
        "--simultaneous-hypotheses",
        type=int,
        required=True,
        help="prospectively frozen Bonferroni hypothesis count",
    )
    parser.add_argument(
        "--robustness",
        type=Path,
        help=(
            "separately frozen binomial-cloglog and cluster sensitivity JSON; "
            "without it the decision fails closed"
        ),
    )
    args = parser.parse_args()
    try:
        result = analyze(
            read_jsonl(args.input),
            familywise_alpha=args.familywise_alpha,
            simultaneous_hypotheses=args.simultaneous_hypotheses,
            robustness_artifact=(
                None if args.robustness is None else read_json_object(args.robustness)
            ),
        )
    except (AnalysisError, OSError) as exc:
        parser.error(str(exc))
    args.output.write_text(render_json(result), encoding="utf-8")


if __name__ == "__main__":
    main()
