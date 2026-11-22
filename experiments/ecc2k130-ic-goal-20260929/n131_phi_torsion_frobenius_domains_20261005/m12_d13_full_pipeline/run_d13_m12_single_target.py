#!/usr/bin/env python3
"""Full single-target ECC2K-130 IC run for d13/m12.

The runner is drain-gated behind the existing R3, d10, and public-Q diagnostic
controllers. It uses one supplied public Q, builds reusable factor logs from
known-scalar preparation relations, and times only the later target-dependent
query through independently replayed scalar recovery.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parents[1]
ROOT = GOAL.parents[1]
SOURCE_RUN = GOAL / "n131_w2_m15_official_single_target_4g_r3_20261004"
D10 = GOAL / "n131_phi_torsion_frobenius_domains_20261005" / "m15_d10_static"
DOMAIN = D10.parent
PROBE = DOMAIN / "d13_m12_probe"
STATIC = DOMAIN / "m12_d13_static"
M16 = DOMAIN / "m16_static"
CODEGEN = ROOT / "ecc2k130" / "codegen"
RUNNER_HELPER = D10 / "run_d10_m15_single_target.py"
PIPELINE = HERE / "sparse_seed_d13_m12_pipeline.py"
MATRIX_ADAPTER = HERE / "flint_relation_rank.py"
MATRIX_SOURCE = HERE / "flint_relation_rank.cpp"
MATRIX_SOLVER = HERE / "flint_relation_rank"
MANIFEST = HERE / "d13_m12_candidate_manifest_v1.json"
PROTOCOL = HERE / "d13_m12_single_target_protocol_v1.json"
WORKLOAD = SOURCE_RUN / "workload.json"
CURVE_RECORD = SOURCE_RUN / "field_curve_record.json"
BRIDGE = SOURCE_RUN / "bridge_audit.json"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLINT_LIBRARY = Path("/opt/homebrew/opt/flint/lib/libflint.23.0.dylib")
GMP_LIBRARY = Path("/opt/homebrew/opt/gmp/lib/libgmp.10.dylib")

for directory in (CODEGEN, SOURCE_RUN, M16, D10, PROBE, STATIC, HERE):
    sys.path.insert(0, str(directory))

import run_d10_m15_single_target as common  # shared, source-hashed primitives
import sparse_seed_d13_m12_pipeline as pipeline
from flint_relation_rank import run_rank_solver

common.GOAL = GOAL
common.ROOT = ROOT
common.SOURCE_RUN = SOURCE_RUN
common.CODEGEN = CODEGEN
common.M16_DIR = M16
common.HERE = HERE
common.pipeline = pipeline
common.gate = pipeline.gate
common.decoder = pipeline.decoder
common.WORKLOAD = WORKLOAD
common.CURVE_RECORD = CURVE_RECORD
common.BRIDGE = BRIDGE
common.SOLVER = SOLVER
common.LEAVES = 12
common.MAX_MODELS_PER_RELATION = 4
common.MAX_PRECOMPUTE_ATTEMPTS = 8192
common.PRECOMPUTE_QUERY_SECONDS = 600.0
common.ONLINE_QUERY_SECONDS = 604800.0
common.RSS_LIMIT_BYTES = 4 * 1024**3
CONFLICT_LIMIT = 1_000_000_000_000
common.CONFLICT_LIMIT = CONFLICT_LIMIT


def validate_d13_target_formula_counts(stats, roots, phi_masks, expected):
    """Bind every generated d13/m12 formula to the audited circuit shape."""
    return (
        len(phi_masks) == 4 and
        len(roots) == (common.LEAVES - 1) * pipeline.N == expected["roots"] and
        expected["records"] == expected["clauses"] + expected["native_xors"] and
        stats == {"vars": expected["variables"],
                  "clauses": expected["clauses"],
                  "xors": expected["native_xors"]}
    )


# The shared d10 helper checks four endpoint masks as if they were chain roots.
# Replace only that gate for this d13 candidate; retain its exact count checks.
common.validate_target_formula_counts = validate_d13_target_formula_counts

WIDTH = 4134
SURPLUS_RELATIONS_BEFORE_RANK_CHECK = 256
RANK_RETRY_RELATION_INCREMENT = 256
MAX_MODELS_PER_RELATION = 4
MAX_PRECOMPUTE_ATTEMPTS = 8192
PRECOMPUTE_QUERY_SECONDS = 600.0
ONLINE_QUERY_SECONDS = 604800.0
RSS_LIMIT_BYTES = 4 * 1024**3
CMS_MATRIX_ROWS = 10000
CMS_MATRIX_COLS = 15000
CMS_NUM_MATRICES = 10
MAX_ARCHIVED_SOLVER_ARTIFACT_BYTES = 4 * 1024**3
ARCHIVED_SOLVER_ARTIFACT_BYTES = 0
STAGE_CODES = {
    "point_decomposition": "PDP12sat",
    "relation_collection": "RCdirect",
    "relation_linear_algebra": "LAgauss",
    "target_descent": "TDdirect",
    "isogeny": "ISO0",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    os.replace(temporary, path)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def source_hashes():
    files = {
        "runner": Path(__file__),
        "d10_shared_runner_primitives": RUNNER_HELPER,
        "d13_pipeline_adapter": PIPELINE,
        "flint_rank_adapter": MATRIX_ADAPTER,
        "flint_rank_solver_source": MATRIX_SOURCE,
        "flint_rank_solver_binary": MATRIX_SOLVER,
        "formula_gate": M16 / "phi_frobenius_sat_gate_m16_sparse_seed_v1.py",
        "decoder": M16 / "q1358_exact_model_decoder_m16.py",
        "codegen_e2e": CODEGEN / "indexcalc_e2e.py",
        "codegen_field": CODEGEN / "field.py",
        "codegen_curves": CODEGEN / "curves.py",
        "codegen_cnf": CODEGEN / "cnf.py",
        "codegen_ir": CODEGEN / "ir.py",
        "codegen_decomp": CODEGEN / "decomp.py",
        "cryptominisat": SOLVER,
        "flint_library": FLINT_LIBRARY,
        "gmp_library": GMP_LIBRARY,
    }
    return {name: sha(path) for name, path in files.items()}


def evidence_hashes():
    files = {
        "geometry": STATIC / "d13_exact_geometry_v1.json",
        "geometry_builder": STATIC / "audit_d13_geometry.py",
        "extension_screen": STATIC / "screen_d13_extension.py",
        "formula_receipt": PROBE / "d13_m12_formula_and_planted_control_v1.json",
        "formula_file": PROBE / "official_q_phi_fiber_d13_m12_v1.xcnf",
        "formula_builder": PROBE / "build_d13_m12_formula.py",
        "planted_witness": PROBE / "d13_planted_witness_v1.json",
        "planted_witness_builder": PROBE / "export_d13_planted_witness.py",
        "full_base_audit": PROBE / "sage_d13_full_base_audit_v1.json",
        "full_base_audit_builder": PROBE / "sage_audit_d13_full_base.py",
        "planted_relation_audit": PROBE / "sage_d13_planted_relation_audit_v1.json",
        "planted_relation_audit_builder": PROBE / "sage_replay_d13_planted_relation.py",
        "adapter_formula_equivalence": HERE / "adapter_formula_equivalence_v1.json",
        "adapter_formula_check_builder": HERE / "check_d13_adapter_formula.py",
        "candidate_runtime_info": HERE / "sage_runtime_info_d13_candidate.json",
        "fullwidth_matrix_control": HERE / "flint_relation_rank_fullwidth_v2.json",
        "fullwidth_matrix_provenance":
            HERE / "flint_relation_rank_fullwidth_provenance_v2.json",
        "fullwidth_matrix_provenance_builder":
            HERE / "record_flint_fullwidth_provenance_v2.py",
        "small_matrix_control": HERE / "flint_relation_rank_test_v2.json",
        "artifact_archive_budget_control": HERE / "test_d13_archive_budget.py",
        "candidate_freezer": HERE / "freeze_d13_m12_candidate.py",
        "candidate_continuation_controller":
            HERE / "continue_d13_m12_full_candidate.py",
        "independent_single_target_auditor":
            HERE / "audit_d13_m12_single_target.py",
        "curve_record": CURVE_RECORD,
        "workload": WORKLOAD,
        "bridge_audit": BRIDGE,
    }
    return {name: sha(path) for name, path in files.items()}


def candidate_identity(manifest):
    core = manifest["candidate_record"]
    identity = digest(core)
    if manifest.get("stage_codes") != STAGE_CODES:
        raise ValueError("candidate stage-code labels do not match its method record")
    expected_id = (
        "IC1N131Ckb1fb%d%s%s%s%s%sh%s" % (
            core["factor_base"]["actual_usable_points_before_sign_frobenius_folding"],
            STAGE_CODES["point_decomposition"],
            STAGE_CODES["relation_collection"],
            STAGE_CODES["relation_linear_algebra"],
            STAGE_CODES["target_descent"],
            STAGE_CODES["isogeny"], identity[:12]))
    if (manifest.get("candidate_identity_sha256") != identity or
            manifest.get("candidate_id") != expected_id):
        raise ValueError("d13/m12 candidate identity digest or stage label mismatch")
    return identity, expected_id


def inspect_d10_gate(workload):
    protocol = json.loads((D10 / "d10_m15_single_target_protocol_v1.json").read_text())
    run_id = "%sW%sR%d" % (protocol["candidate_id"], protocol["workload_id"],
                            protocol["run_control"]["run_number"])
    run_dir = D10 / "single_target_runs" / run_id
    result_path = run_dir / "result.json"
    if not result_path.is_file():
        state_path = D10 / "continuation" / "state.json"
        state = json.loads(state_path.read_text()) if state_path.is_file() else {}
        return "WAIT_FOR_D10_TERMINAL", {"state": state.get("status"),
                                          "run_id": run_id}
    result = json.loads(result_path.read_text())
    if (result.get("run_id") != run_id or
            result.get("candidate_id") != protocol["candidate_id"] or
            result.get("curve_id") != workload["curve_id"] or
            result.get("workload_id") != workload["workload_id"] or
            result.get("target_count") != 1 or result.get("batch") is not False):
        return "WAIT_FOR_D10_TERMINAL", {"run_id": run_id,
                                          "reason": "result is not fully bound"}
    if result.get("status", "").startswith("RUNNING"):
        return "WAIT_FOR_D10_TERMINAL", {"run_id": run_id,
                                          "result_status": result.get("status")}
    if result.get("target_discrete_log_recovered") is True:
        audit_path = run_dir / "independent_sage_audit.json"
        if not audit_path.is_file():
            return "WAIT_FOR_D10_AUDIT", {"run_id": run_id}
        audit = json.loads(audit_path.read_text())
        if (audit.get("status") == "PASS_VERIFIED_SINGLE_TARGET_DLP" and
                audit.get("scalar_replay_passed") is True and
                audit.get("batch") is False):
            return "STOP_D10_DLP_VERIFIED", {"run_id": run_id,
                                             "result": str(result_path),
                                             "audit": str(audit_path)}
        return "STOP_D10_DLP_AUDIT_FAILED", {"run_id": run_id,
                                              "audit": str(audit_path)}
    return "READY", {"run_id": run_id, "result": str(result_path),
                     "result_status": result.get("status")}


def inspect_d13_probe_gate():
    path = PROBE / "continuation" / "state.json"
    if not path.is_file():
        return "WAIT_FOR_D13_PROBE", {"reason": "missing diagnostic state"}
    state = json.loads(path.read_text())
    status = state.get("status")
    if status in ("VERIFIED_ORDINARY_RELATION", "TERMINAL_NO_VERIFIED_RELATION"):
        return "READY", {"state": str(path), "status": status,
                          "run_dir": state.get("run_dir")}
    if status in ("INDEPENDENT_AUDIT_FAILURE", "PROBE_PRODUCER_FAILURE",
                  "PROBE_MISSING_RUN_RECEIPT", "PROBE_MISSING_RESULT",
                  "PROBE_INVALID_RUN_DIRECTORY"):
        return "STOP_D13_PROBE_FAILURE", {"state": str(path),
                                           "status": status}
    return "WAIT_FOR_D13_PROBE", {"state": str(path), "status": status}


def preflight():
    required = [MANIFEST, PROTOCOL, WORKLOAD, CURVE_RECORD, BRIDGE, SOLVER,
                FLINT_LIBRARY, GMP_LIBRARY, MATRIX_SOLVER, MATRIX_SOURCE,
                MATRIX_ADAPTER, PIPELINE,
                STATIC / "d13_exact_geometry_v1.json",
                PROBE / "d13_m12_formula_and_planted_control_v1.json",
                PROBE / "official_q_phi_fiber_d13_m12_v1.xcnf",
                PROBE / "d13_planted_witness_v1.json",
                PROBE / "sage_d13_full_base_audit_v1.json",
                PROBE / "sage_d13_planted_relation_audit_v1.json",
                HERE / "adapter_formula_equivalence_v1.json",
                HERE / "sage_runtime_info_d13_candidate.json"]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)

    manifest = json.loads(MANIFEST.read_text())
    protocol = json.loads(PROTOCOL.read_text())
    workload = json.loads(WORKLOAD.read_text())
    curve_record = json.loads(CURVE_RECORD.read_text())
    bridge = json.loads(BRIDGE.read_text())
    geometry = json.loads((STATIC / "d13_exact_geometry_v1.json").read_text())
    formula = json.loads((PROBE / "d13_m12_formula_and_planted_control_v1.json").read_text())
    witness = json.loads((PROBE / "d13_planted_witness_v1.json").read_text())
    base_audit = json.loads((PROBE / "sage_d13_full_base_audit_v1.json").read_text())
    planted_audit = json.loads((PROBE / "sage_d13_planted_relation_audit_v1.json").read_text())
    equivalence = json.loads((HERE / "adapter_formula_equivalence_v1.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info_d13_candidate.json").read_text())

    identity, candidate_id = candidate_identity(manifest)
    core = manifest["candidate_record"]
    if (protocol.get("candidate_id") != candidate_id or
            protocol.get("candidate_identity_sha256") != identity or
            protocol.get("candidate_manifest_sha256") != sha(MANIFEST) or
            protocol.get("target_count") != 1 or protocol.get("batch") is not False or
            workload.get("target_count") != 1 or len(workload.get("targets", [])) != 1 or
            protocol.get("workload_id") != workload.get("workload_id") or
            protocol.get("curve_id") != workload.get("curve_id") or
            protocol.get("workload_sha256") != sha(WORKLOAD) or
            protocol.get("curve_record_sha256") != sha(CURVE_RECORD) or
            protocol.get("bridge_sha256") != sha(BRIDGE)):
        raise ValueError("candidate protocol does not bind the frozen single target")

    curve_core = {key: value for key, value in curve_record["curve"].items()
                  if key != "curve_id"}
    workload_core = {key: value for key, value in workload.items()
                     if key not in ("workload_id", "workload_sha256")}
    if (digest({"field": curve_record["field"], "curve": curve_core}) !=
            curve_record["curve_sha256"] or
            digest(workload_core) != workload["workload_sha256"] or
            bridge.get("status") != "PASS" or
            bridge.get("official_target_onb_coordinates") != workload["targets"][0]):
        raise ValueError("curve, workload, or ONB bridge audit changed")

    factor_base = core["factor_base"]
    geometry_fb = geometry["factor_base"]
    if (geometry.get("status") != "PASS" or geometry.get("target_count") != 1 or
            geometry.get("curve_id") != workload["curve_id"] or
            geometry.get("workload_id") != workload["workload_id"] or
            factor_base.get("nominal_subspace_dimension_or_bound") != 13 or
            factor_base.get("ordered_basis_coordinate_masks_hex") !=
            geometry["domain"]["basis_coordinate_masks_hex"] or
            factor_base.get("actual_usable_points_before_sign_frobenius_folding") !=
            geometry_fb["actual_distinct_nonidentity_subgroup_points_before_sign_frobenius_folding"] or
            factor_base.get("effective_relation_matrix_columns") !=
            geometry_fb["folded_frobenius_columns"] or
            factor_base.get("enumerated_point_set_sha256") !=
            geometry_fb["enumerated_signed_subgroup_point_set_sha256"]):
        raise ValueError("full d13 geometry does not match the candidate factor base")

    formula_path = PROBE / "official_q_phi_fiber_d13_m12_v1.xcnf"
    formula_template = M16 / "phi_frobenius_sat_gate_m16_sparse_seed_v1.py"
    if (formula.get("status") != "PASS" or formula.get("target_count") != 1 or
            formula.get("summand_count") != 12 or
            formula.get("subspace_dimension") != 13 or
            formula.get("source_sha256") != sha(PROBE / "build_d13_m12_formula.py") or
            formula.get("formula_file", {}).get("sha256") != sha(formula_path) or
            formula.get("inputs_sha256", {}).get("formula_template") != sha(formula_template)):
        raise ValueError("frozen d13 formula receipt is stale")
    if (base_audit.get("status") != "PASS" or
            base_audit.get("target_count") != 1 or
            base_audit.get("workload_id") != workload["workload_id"] or
            base_audit.get("curve_id") != workload["curve_id"] or
            base_audit.get("folded_columns") != factor_base["effective_relation_matrix_columns"] or
            base_audit.get("actual_usable_points_before_folding") !=
            factor_base["actual_usable_points_before_sign_frobenius_folding"] or
            base_audit.get("source_sha256") != sha(PROBE / "sage_audit_d13_full_base.py")):
        raise ValueError("independent Sage d13 full-base audit is stale or failed")
    if (witness.get("status") != "PASS" or witness.get("target_count") != 1 or
            witness.get("summand_count") != 12 or
            planted_audit.get("status") != "PASS" or
            planted_audit.get("exact_leaf_point_checks") != 12 or
            planted_audit.get("exact_partial_phi_chain_checks") != 10 or
            planted_audit.get("target_fiber_endpoint_checks") != 4):
        raise ValueError("d13 planted correctness controls failed")
    if (equivalence.get("status") != "PASS" or
            equivalence.get("candidate_id") is not None or
            equivalence.get("run_id") is not None or
            equivalence.get("target_count") != 1 or equivalence.get("batch") is not False or
            equivalence.get("emitted_formula_sha256") != formula["formula_file"]["sha256"] or
            equivalence.get("emitted_formula_bytes") != formula["formula_file"]["bytes"]):
        raise ValueError("runtime d13 formula equivalence evidence failed")
    if (runtime.get("status") != "verified" or
            runtime.get("manifest_sha256") !=
            sha(ROOT / "experiments/sage-binary-arithmetic/runtime-current.json")):
        raise ValueError("checked Sage runtime manifest is stale")

    current_sources = source_hashes()
    current_evidence = evidence_hashes()
    if (protocol.get("source_sha256") != current_sources or
            manifest.get("provenance", {}).get("source_sha256") != current_sources or
            core.get("implementation", {}).get("component_sha256") != current_sources or
            protocol.get("evidence_sha256") != current_evidence or
            manifest.get("provenance", {}).get("evidence_sha256") != current_evidence or
            protocol.get("runtime_info_sha256") != current_evidence["candidate_runtime_info"]):
        raise ValueError("candidate code or its evidence changed after freeze")

    run_control = protocol.get("run_control", {})
    envelope = protocol.get("resource_envelope", {})
    if (run_control.get("precomputation_attempt_cap") != MAX_PRECOMPUTE_ATTEMPTS or
            run_control.get("precomputation_query_seconds") != PRECOMPUTE_QUERY_SECONDS or
            run_control.get("online_query_seconds") != ONLINE_QUERY_SECONDS or
            run_control.get("models_per_relation_target") != MAX_MODELS_PER_RELATION or
            run_control.get("max_conflicts_per_query") != CONFLICT_LIMIT or
            run_control.get("surplus_relations_before_rank_check") !=
            SURPLUS_RELATIONS_BEFORE_RANK_CHECK or
            run_control.get("rank_retry_relation_increment") !=
            RANK_RETRY_RELATION_INCREMENT or
            run_control.get("max_archived_solver_artifact_bytes") !=
            MAX_ARCHIVED_SOLVER_ARTIFACT_BYTES or
            envelope.get("combined_sage_and_solver_rss_limit_bytes") != RSS_LIMIT_BYTES or
            envelope.get("solver_threads") != 1 or
            envelope.get("cms_max_matrix_rows") != CMS_MATRIX_ROWS or
            envelope.get("cms_max_matrix_columns") != CMS_MATRIX_COLS or
            envelope.get("cms_max_matrices") != CMS_NUM_MATRICES):
        raise ValueError("frozen d13 run limits changed")
    if protocol.get("solver_sha256") != sha(SOLVER):
        raise ValueError("CryptoMiniSat binary changed after candidate freeze")

    r3_status, r3_process, r3_result = common.r3_terminal_gate()
    d10_status, d10_detail = inspect_d10_gate(workload)
    probe_status, probe_detail = inspect_d13_probe_gate()
    status = (r3_status if r3_status != "READY" else
              d10_status if d10_status != "READY" else
              probe_status)
    if status == "READY":
        run_id = "%sW%sR%d" % (candidate_id, protocol["workload_id"],
                               run_control["run_number"])
        if (HERE / "single_target_runs" / run_id).exists():
            raise FileExistsError("preserve the existing d13 single-target run")
    receipt = {
        "kind": "ecc2k130_n131_d13_m12_single_target_preflight_v1",
        "status": status,
        "candidate_id": candidate_id,
        "curve_id": workload["curve_id"],
        "workload_id": workload["workload_id"],
        "target_count": 1,
        "batch": False,
        "solver_launched": False,
        "r3_status": r3_status,
        "r3_process_state": r3_process,
        "r3_result_path": str(r3_result),
        "d10_gate": {"status": d10_status, **d10_detail},
        "d13_first_relation_gate": {"status": probe_status, **probe_detail},
        "source_sha256": current_sources,
        "evidence_sha256": current_evidence,
        "target_count_for_online_metric": 1,
        "resource_envelope": envelope,
    }
    return receipt, manifest, protocol, workload, curve_record


def sparse_row(row):
    return [[column, int(value)] for column, value in enumerate(row) if value]


def compact_query_details(details):
    details = dict(details)
    # The canonical sparse rows are already written once to the relation file;
    # do not duplicate them in every in-memory query receipt.
    details.pop("accepted_dense_rows", None)
    details.pop("accepted_sparse_rows", None)
    return details


def archive_solver_artifacts(directory):
    global ARCHIVED_SOLVER_ARTIFACT_BYTES
    archived = []
    for path in sorted(Path(directory).rglob("*")):
        if not path.is_file() or path.name.endswith(".gz"):
            continue
        if not (path.suffix == ".xcnf" or path.name.endswith(".stdout.txt") or
                path.name.endswith(".stderr.txt")):
            continue
        raw_sha = sha(path)
        raw_bytes = path.stat().st_size
        output = path.with_name(path.name + ".gz")
        temporary = output.with_name(output.name + ".partial")
        if ARCHIVED_SOLVER_ARTIFACT_BYTES < MAX_ARCHIVED_SOLVER_ARTIFACT_BYTES:
            with path.open("rb") as source, temporary.open("wb") as target:
                with gzip.GzipFile(filename="", mode="wb", fileobj=target,
                                   mtime=0) as zipped:
                    shutil.copyfileobj(source, zipped)
            compressed_bytes = temporary.stat().st_size
        else:
            compressed_bytes = MAX_ARCHIVED_SOLVER_ARTIFACT_BYTES + 1

        if (ARCHIVED_SOLVER_ARTIFACT_BYTES + compressed_bytes <=
                MAX_ARCHIVED_SOLVER_ARTIFACT_BYTES):
            os.replace(temporary, output)
            ARCHIVED_SOLVER_ARTIFACT_BYTES += compressed_bytes
            archived.append({"path": str(output),
                             "stored": True,
                             "retention": "gzip_within_frozen_run_budget",
                             "compressed_bytes": compressed_bytes,
                             "uncompressed_bytes": raw_bytes,
                             "uncompressed_sha256": raw_sha,
                             "compressed_sha256": sha(output)})
        else:
            temporary.unlink(missing_ok=True)
            archived.append({"path": None,
                             "stored": False,
                             "retention": "hash_only_frozen_run_budget_exhausted",
                             "compressed_bytes": None,
                             "uncompressed_bytes": raw_bytes,
                             "uncompressed_sha256": raw_sha,
                             "compressed_sha256": None})
        path.unlink()
    return archived


def rank_by_query(rank_receipt, attempts):
    gains = {}
    after = {}
    for item in rank_receipt.get("rank_trace", []):
        query = int(item["query_index"])
        gains[query] = gains.get(query, 0) + int(item["rank_increment"])
        after[query] = int(item["rank_after"])
    last_rank = 0
    result = []
    for attempt in attempts:
        query = int(attempt["relation_index"])
        before = last_rank
        last_rank = after.get(query, last_rank)
        gain = gains.get(query, 0)
        result.append({"query_index": query, "rank_before": before,
                       "rank_increment": gain, "rank_after": last_rank,
                       "verified_relation_count": attempt["verified_relation_count"],
                       "query_wall_ns": attempt["query_details"]["query_wall_ns"],
                       "cost_per_useful_rank_ns": (
                           attempt["query_details"]["query_wall_ns"] / gain
                           if gain else None)})
    return result


def verify_factor_logs(curve, generator, representatives, logs, order):
    if len(logs) != len(representatives) or len(logs) != WIDTH:
        raise ValueError("FLINT solver returned an incomplete factor-log vector")
    started = time.perf_counter_ns()
    for column, (log_value, representative) in enumerate(zip(logs, representatives)):
        if not 0 <= int(log_value) < order or curve.mul(generator, int(log_value)) != representative:
            raise ValueError("independent factor-log curve replay failed at column %d" % column)
    return time.perf_counter_ns() - started


def enforce_matrix_worker_memory(rank_receipt):
    parent_peak = int(common.parent_peak_rss())
    worker_peak = int(rank_receipt.get("process_peak_rss_bytes", 0))
    conservative_combined_peak = parent_peak + worker_peak
    rank_receipt["parent_process_peak_rss_bytes"] = parent_peak
    rank_receipt["conservative_combined_peak_rss_bytes"] = conservative_combined_peak
    rank_receipt["rss_gate_passed"] = conservative_combined_peak <= RSS_LIMIT_BYTES
    if not rank_receipt["rss_gate_passed"]:
        raise MemoryError(
            "parent plus FLINT worker peak RSS exceeds the frozen 4-GiB envelope")
    return conservative_combined_peak


def accumulate_matrix_stage_costs(totals, rank_receipt):
    totals["input_serialization_ns"] += int(
        rank_receipt.get("input_serialization_ns", 0))
    totals["input_parse_ns"] += int(rank_receipt.get("input_parse_ns", 0))
    totals["matrix_build_ns"] += int(rank_receipt.get("matrix_build_ns", 0))
    totals["relation_linear_algebra_ns"] += int(
        rank_receipt.get("elimination_ns", 0))
    totals["equation_replay_ns"] += int(
        rank_receipt.get("relation_replay_ns", 0))


def run_one_target(args):
    preflight_receipt, manifest, protocol, workload, curve_data = preflight()
    if preflight_receipt["status"] != "READY" or args.preflight_only:
        receipt_path = HERE / "single_target_preflights" / (
            "d13_m12_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
        atomic_json(receipt_path, preflight_receipt)
        print(json.dumps({"status": preflight_receipt["status"],
                          "preflight": str(receipt_path), "solver_launched": False},
                         sort_keys=True))
        return 0

    run_control = protocol["run_control"]
    run_id = "%sW%sR%d" % (protocol["candidate_id"], protocol["workload_id"],
                            run_control["run_number"])
    run_dir = HERE / "single_target_runs" / run_id
    if run_dir.exists():
        raise FileExistsError("refusing to overwrite a d13 single-target run")
    run_dir.mkdir(parents=True)
    runtime_output = subprocess.run([str(ROOT / "sage"), "--runtime-info"],
                                    capture_output=True, text=True, check=True).stdout
    (run_dir / "sage_runtime_info.json").write_text(runtime_output)
    started = {**preflight_receipt, "status": "RUNNING_FACTOR_BASE_SETUP",
               "run_id": run_id, "started_utc": utc_now()}
    atomic_json(run_dir / "started.json", started)

    setup_start = time.perf_counter_ns()
    context, target, base_receipt, setup_operations = common.build_context(
        curve_data, workload, manifest)
    setup_wall_ns = time.perf_counter_ns() - setup_start
    setup_peak_rss_bytes = int(common.parent_peak_rss())
    if setup_peak_rss_bytes > RSS_LIMIT_BYTES:
        raise MemoryError("factor-base setup exceeded the frozen 4-GiB RSS envelope")
    base_summary = {key: value for key, value in base_receipt.items()
                    if key not in ("entries", "selector_codes")}
    atomic_json(run_dir / "factor_base_receipt.json", base_summary)
    (onb, curve, order, eigenvalue, generator, basis_masks, representatives, lookup,
     key_to_column, valid_codes, official_q, fiber_coordinates) = context
    formula_receipt = json.loads(
        (PROBE / "d13_m12_formula_and_planted_control_v1.json").read_text())

    relation_records = []
    attempt_records = []
    relation_file = run_dir / "precomputed_relations.jsonl"
    attempt_file = run_dir / "precomputation_attempts.jsonl"
    rank_checks = run_dir / "matrix_checks"
    rank_checks.mkdir()
    precompute_start_ns = time.perf_counter_ns()
    random_source = random.Random(run_control["precomputation_seed"])
    rank_receipt = None
    next_rank_check = (WIDTH + SURPLUS_RELATIONS_BEFORE_RANK_CHECK)
    last_rank_checked_relation_count = 0
    matrix_worker_wall_ns = 0
    matrix_stage_costs_ns = {
        "input_serialization_ns": 0,
        "input_parse_ns": 0,
        "matrix_build_ns": 0,
        "relation_linear_algebra_ns": 0,
        "equation_replay_ns": 0,
    }
    matrix_rank = 0
    matrix_combined_peak_rss_bytes = setup_peak_rss_bytes
    atomic_json(run_dir / "precompute_progress.json", {
        "status": "RUNNING", "rank": 0, "rank_target": WIDTH,
        "verified_relations": 0, "attempts_completed": 0,
        "target_count": 1, "batch": False,
    })

    for relation_index in range(1, MAX_PRECOMPUTE_ATTEMPTS + 1):
        scalar = random_source.randrange(1, order)
        generation_start = time.perf_counter_ns()
        precompute_target = curve.mul(generator, scalar)
        generation_ns = time.perf_counter_ns() - generation_start
        if precompute_target is None:
            raise AssertionError("nonzero precomputation scalar generated identity")
        query_dir = run_dir / "precomputation" / ("target_%05d" % relation_index)
        query_dir.mkdir(parents=True)
        rows, details = common.solve_relation(
            context, precompute_target, scalar, query_dir,
            int(run_control["precomputation_solver_seed"]) + relation_index * 16,
            formula_receipt, MAX_MODELS_PER_RELATION)
        compact = compact_query_details(details)
        archive = archive_solver_artifacts(query_dir)
        query_relation_records = []
        for relation_in_query, row in enumerate(rows):
            terms = sparse_row(row)
            record = {
                "query_index": relation_index,
                "relation_in_query_index": relation_in_query,
                "rhs": 4 * scalar % order,
                "terms": terms,
                "term_count": len(terms),
                "row_sha256": digest([terms, 4 * scalar % order]),
                "target_scalar_known_to_precomputation": True,
            }
            relation_records.append(record)
            query_relation_records.append(record)
            with relation_file.open("a", encoding="ascii") as stream:
                stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        attempt = {
            "relation_index": relation_index,
            "status": "verified_relation" if rows else compact["status"],
            "target_count": 1,
            "batch": False,
            "known_scalar_target_fixture": True,
            "target_scalar": str(scalar),
            "target_generation_ns": generation_ns,
            "verified_relation_count": len(rows),
            "independent_rank_gain": None,
            "query_details": compact,
            "archived_solver_artifacts": archive,
            "completed_utc": utc_now(),
        }
        attempt_records.append(attempt)
        with attempt_file.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(attempt, sort_keys=True) + "\n")

        if len(relation_records) >= next_rank_check:
            check_index = len(list(rank_checks.glob("rank_check_*.json"))) + 1
            rank_receipt = run_rank_solver(
                WIDTH, relation_records,
                rank_checks / ("rank_check_%03d.tsv" % check_index),
                rank_checks / ("rank_check_%03d.json" % check_index))
            matrix_worker_wall_ns += int(rank_receipt["worker_wall_ns"])
            accumulate_matrix_stage_costs(matrix_stage_costs_ns, rank_receipt)
            matrix_combined_peak_rss_bytes = max(
                matrix_combined_peak_rss_bytes,
                enforce_matrix_worker_memory(rank_receipt))
            last_rank_checked_relation_count = len(relation_records)
            matrix_rank = int(rank_receipt["final_rank"])
            if rank_receipt.get("status") == "PASS" and \
                    rank_receipt.get("full_column_rank") is True and \
                    rank_receipt.get("all_relation_equations_replayed") is True:
                logs = [int(value) for value in rank_receipt["log_values"]]
                log_replay_ns = verify_factor_logs(
                    curve, generator, representatives, logs, order)
                break
            next_rank_check = (len(relation_records) +
                               RANK_RETRY_RELATION_INCREMENT)

        atomic_json(run_dir / "precompute_progress.json", {
            "status": "RUNNING", "rank": matrix_rank,
            "rank_target": WIDTH, "verified_relations": len(relation_records),
            "attempts_completed": relation_index,
            "next_rank_check_at_relation_count": next_rank_check,
            "target_count": 1, "batch": False,
        })

    precompute_wall_ns = time.perf_counter_ns() - precompute_start_ns
    if len(relation_records) > last_rank_checked_relation_count:
        check_index = len(list(rank_checks.glob("rank_check_*.json"))) + 1
        rank_receipt = run_rank_solver(
            WIDTH, relation_records,
            rank_checks / ("rank_check_%03d.tsv" % check_index),
            rank_checks / ("rank_check_%03d.json" % check_index))
        matrix_worker_wall_ns += int(rank_receipt["worker_wall_ns"])
        accumulate_matrix_stage_costs(matrix_stage_costs_ns, rank_receipt)
        matrix_combined_peak_rss_bytes = max(
            matrix_combined_peak_rss_bytes,
            enforce_matrix_worker_memory(rank_receipt))
        last_rank_checked_relation_count = len(relation_records)
        matrix_rank = int(rank_receipt["final_rank"])
        if rank_receipt.get("status") == "PASS":
            logs = [int(value) for value in rank_receipt["log_values"]]
            log_replay_ns = verify_factor_logs(
                curve, generator, representatives, logs, order)

    if rank_receipt is None or rank_receipt.get("status") != "PASS":
        trace = rank_receipt.get("rank_trace", []) if rank_receipt else []
        rank_summary = rank_by_query(rank_receipt or {}, attempt_records)
        atomic_json(run_dir / "precomputation_rank_by_query.json", {
            "kind": "ecc2k130_d13_m12_rank_trace_v1",
            "status": "INCOMPLETE", "target_count": 1, "batch": False,
            "final_rank": matrix_rank, "rank_target": WIDTH,
            "verified_relations": len(relation_records),
            "rank_by_query": rank_summary,
            "rank_trace_rows": len(trace),
        })
        result = {
            "kind": "ecc2k130_sparse_seed_d13_m12_single_target_result",
            "status": "PRECOMPUTATION_INCOMPLETE",
            "candidate_id": protocol["candidate_id"], "run_id": run_id,
            "curve_id": workload["curve_id"],
            "workload_id": workload["workload_id"],
            "target_count": 1, "batch": False,
            "target_discrete_log_recovered": False,
            "precomputation_attempt_count": len(attempt_records),
            "precomputation_verified_relations": len(relation_records),
            "precomputation_rank": matrix_rank,
            "precomputation_rank_target": WIDTH,
            "precomputation_wall_ns": precompute_wall_ns,
            "matrix_worker_wall_ns": matrix_worker_wall_ns,
            "matrix_stage_costs_ns": matrix_stage_costs_ns,
            "last_matrix_rank_check": rank_receipt,
            "setup_wall_ns_excluded": setup_wall_ns,
            "setup_peak_rss_bytes": setup_peak_rss_bytes,
            "conservative_combined_peak_rss_bytes": matrix_combined_peak_rss_bytes,
            "resource_limit_enforced": True,
            "factor_base_point_count": len(lookup),
            "factor_base_folded_columns": len(representatives),
            "solver_artifact_archive_bytes_used": ARCHIVED_SOLVER_ARTIFACT_BYTES,
            "solver_artifact_archive_budget_bytes":
                MAX_ARCHIVED_SOLVER_ARTIFACT_BYTES,
            "rho_online_ms": None, "online_speedup": None,
        }
        atomic_json(run_dir / "result.json", result)
        atomic_json(run_dir / "precompute_progress.json", {
            "status": "ATTEMPT_LIMIT_REACHED", "rank": matrix_rank,
            "rank_target": WIDTH, "verified_relations": len(relation_records),
            "attempts_completed": len(attempt_records),
            "target_count": 1, "batch": False,
        })
        print(json.dumps({"status": result["status"], "run_id": run_id,
                          "target_count": 1, "rank": matrix_rank,
                          "rank_target": WIDTH}, sort_keys=True))
        return 2

    rank_summary = rank_by_query(rank_receipt, attempt_records)
    atomic_json(run_dir / "precomputation_rank_by_query.json", {
        "kind": "ecc2k130_d13_m12_rank_trace_v1",
        "status": "PASS", "target_count": 1, "batch": False,
        "final_rank": WIDTH, "rank_target": WIDTH,
        "verified_relations": len(relation_records),
        "rank_by_query": rank_summary,
        "rank_trace": rank_receipt["rank_trace"],
        "matrix_solver_sha256": sha(MATRIX_SOLVER),
        "matrix_solver_source_sha256": sha(MATRIX_SOURCE),
    })
    atomic_json(run_dir / "precomputed_logs.json", {
        "curve_id": workload["curve_id"],
        "candidate_id": protocol["candidate_id"],
        "matrix_rank": WIDTH,
        "logs": [str(value) for value in logs],
        "representatives": [[str(onb.toCoords(point[0])),
                             str(onb.toCoords(point[1]))]
                            for point in representatives],
        "all_logs_independently_verified": True,
        "relation_matrix_receipt": str(rank_checks / ("rank_check_%03d.json" %
            len(list(rank_checks.glob("rank_check_*.json"))))),
        "relation_file_sha256": sha(relation_file),
        "rank_by_query_sha256": sha(run_dir / "precomputation_rank_by_query.json"),
    })
    atomic_json(run_dir / "precompute_progress.json", {
        "status": "LOGS_READY", "rank": WIDTH, "rank_target": WIDTH,
        "verified_relations": len(relation_records),
        "attempts_completed": len(attempt_records),
        "precomputation_wall_ns": precompute_wall_ns,
        "matrix_worker_wall_ns": matrix_worker_wall_ns,
        "matrix_stage_costs_ns": matrix_stage_costs_ns,
        "factor_log_curve_replay_ns": log_replay_ns,
        "target_count": 1, "batch": False,
    })

    query_dir = run_dir / "online_target"
    query_dir.mkdir()
    online_start_utc = utc_now()
    online_start_ns = time.perf_counter_ns()
    rows, target_details = common.solve_relation(
        context, target, None, query_dir,
        int(run_control["online_solver_seed"]), formula_receipt, 1)
    compact_target_details = compact_query_details(target_details)
    online_relation_rows_dense = [
        [int(value) for value in row]
        for row in target_details.get("accepted_dense_rows", [])]
    if ([list(map(int, row)) for row in rows] != online_relation_rows_dense or
            any(len(row) != WIDTH for row in online_relation_rows_dense)):
        raise AssertionError("online accepted relation rows do not match decoded rows")
    descent_start_ns = time.perf_counter_ns()
    recovered = None
    if rows:
        inverse_four = pow(4, -1, order)
        recovered = (sum(coefficient * log_value
                         for coefficient, log_value in zip(rows[0], logs)) *
                     inverse_four) % order
    descent_ns = time.perf_counter_ns() - descent_start_ns
    recovery_start_ns = time.perf_counter_ns()
    verified = recovered is not None and curve.mul(generator, recovered) == target
    recovery_ns = time.perf_counter_ns() - recovery_start_ns
    online_stop_ns = time.perf_counter_ns()
    online_stop_utc = utc_now()
    raw_online_ns = online_stop_ns - online_start_ns
    artifact_archive_start_ns = time.perf_counter_ns()
    online_archive_error = None
    try:
        online_archives = archive_solver_artifacts(query_dir)
    except Exception as error:
        online_archives = []
        online_archive_error = {
            "type": type(error).__name__,
            "message": str(error),
        }
    artifact_archive_ns = time.perf_counter_ns() - artifact_archive_start_ns
    online_ns = raw_online_ns - compact_target_details[
        "solver_startup_and_input_load_ns_excluded"]
    phase_ns = {
        "T_target_query": online_ns - compact_target_details["solver_wall_ns"] -
            compact_target_details["relation_check_ns"] - descent_ns - recovery_ns,
        "T_target_PDP": compact_target_details["solver_wall_ns"],
        "T_target_relation_check": compact_target_details["relation_check_ns"],
        "T_target_descent": descent_ns,
        "T_target_recovery_check": recovery_ns,
    }
    if min(phase_ns.values()) < 0 or sum(phase_ns.values()) != online_ns:
        raise AssertionError("exclusive d13 single-target phase accounting failed")
    result = {
        "kind": "ecc2k130_sparse_seed_d13_m12_single_target_result",
        "status": ("verified_single_target_dlp" if verified else
                   "TARGET_RECOVERY_UNVERIFIED" if rows else compact_target_details["status"]),
        "candidate_id": protocol["candidate_id"], "run_id": run_id,
        "curve_id": workload["curve_id"],
        "workload_id": workload["workload_id"],
        "target_count": 1, "batch": False,
        "target_sha256": digest(workload["targets"][0]),
        "target_discrete_log_recovered": bool(verified),
        "recovered_scalar": str(recovered) if verified else None,
        "target_relation_verified": bool(rows),
        "setup_wall_ns_excluded": setup_wall_ns,
        "setup_peak_rss_bytes": setup_peak_rss_bytes,
        "setup_operation_record": setup_operations,
        "factor_base_point_count": len(lookup),
        "factor_base_folded_columns": len(representatives),
        "factor_base_point_set_sha256": base_receipt["enumerated_point_set_sha256"],
        "precomputation": {
            "rank": WIDTH, "attempt_count": len(attempt_records),
            "verified_relation_count": len(relation_records),
            "rank_trace_path": str(run_dir / "precomputation_rank_by_query.json"),
            "relation_file": str(relation_file),
            "wall_ns": precompute_wall_ns,
            "matrix_solver_wall_ns": matrix_worker_wall_ns,
            "matrix_stage_costs_ns": matrix_stage_costs_ns,
            "factor_log_curve_replay_ns": log_replay_ns,
            "factor_base_logs_verified": True,
            "excluded_from_online_metric": True,
            "solver_artifact_archive_bytes_used": ARCHIVED_SOLVER_ARTIFACT_BYTES,
            "solver_artifact_archive_budget_bytes":
                MAX_ARCHIVED_SOLVER_ARTIFACT_BYTES,
        },
        "primary_target_online_wall_ns": online_ns,
        "primary_target_online_wall_ms": online_ns / 1_000_000,
        "primary_target_raw_wall_including_excluded_solver_startup_ns": raw_online_ns,
        "online_interval": {
            "start_utc": online_start_utc,
            "start_event": "immediately before target-specific cofactor-fiber encoding and d13/m12 formula construction after verified reusable factor-base logs are ready",
            "stop_utc": online_stop_utc,
            "stop_event": "after exact row recovery, factor-log dot product, inverse-four adjustment, and scalar replay against the one supplied public Q",
            "wall_accounting": "raw start-to-stop wall less explicitly recorded CryptoMiniSat process launch and XCNF input parsing; formula serialization remains charged",
            "excluded_solver_startup_and_input_load_ns": compact_target_details[
                "solver_startup_and_input_load_ns_excluded"],
            "included_stages": ["target_cofactor_fiber", "target_formula_build",
                                "target_PDP", "target_relation_lift_and_check",
                                "target_descent", "scalar_replay"],
            "excluded_diagnostic_work": ["SAT artifact archiving"],
        },
        "online_artifact_archival_wall_ns_excluded": artifact_archive_ns,
        "online_artifact_archival_status": (
            "PASS" if online_archive_error is None else "FAILED_DIAGNOSTIC_ONLY"),
        "online_artifact_archival_error": online_archive_error,
        "exclusive_online_phases": phase_ns,
        "target_query_details": compact_target_details,
        "archived_online_solver_artifacts": online_archives,
        "online_verified_relation_rows_dense": online_relation_rows_dense,
        "online_relation_rows_sha256": digest(online_relation_rows_dense),
        "combined_process_rss_limit_bytes": RSS_LIMIT_BYTES,
        "resource_limit_enforced": True,
        "conservative_combined_peak_rss_bytes": matrix_combined_peak_rss_bytes,
        "solver_artifact_archive_bytes_used": ARCHIVED_SOLVER_ARTIFACT_BYTES,
        "solver_artifact_archive_budget_bytes":
            MAX_ARCHIVED_SOLVER_ARTIFACT_BYTES,
        "rho_online_ms": None,
        "online_speedup": None,
        "claim_boundary": "single-target IC DLP and online accounting only; a same-public-Q rho run and isolated-host receipt are separate requirements for any speedup claim",
    }
    atomic_json(run_dir / "result.json", result)
    print(json.dumps({"status": result["status"], "run_id": run_id,
                      "target_count": 1,
                      "primary_target_online_wall_ms": result["primary_target_online_wall_ms"],
                      "rho_online_ms": None, "online_speedup": None,
                      "result": str(run_dir / "result.json")}, sort_keys=True))
    return 0 if verified else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    try:
        return run_one_target(args)
    except BaseException as failure:
        try:
            protocol = json.loads(PROTOCOL.read_text())
            workload = json.loads(WORKLOAD.read_text())
            run_id = "%sW%sR%d" % (
                protocol["candidate_id"], protocol["workload_id"],
                protocol["run_control"]["run_number"])
            run_dir = HERE / "single_target_runs" / run_id
            if run_dir.is_dir() and not (run_dir / "result.json").exists():
                failed = {
                    "kind": "ecc2k130_sparse_seed_d13_m12_single_target_result",
                    "status": "PRODUCER_FAILURE",
                    "candidate_id": protocol["candidate_id"], "run_id": run_id,
                    "curve_id": workload["curve_id"],
                    "workload_id": workload["workload_id"],
                    "target_count": 1, "batch": False,
                    "target_discrete_log_recovered": False,
                    "error_type": type(failure).__name__, "error": str(failure),
                    "rho_online_ms": None, "online_speedup": None,
                }
                atomic_json(run_dir / "failure.json", failed)
                atomic_json(run_dir / "result.json", failed)
        except Exception:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
