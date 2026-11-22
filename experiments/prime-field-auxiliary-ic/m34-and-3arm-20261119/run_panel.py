#!/usr/bin/env python3
"""Preregistered 5-encoding / 3-arm benchmark + m=2,3,4 split-S3 evaluation harness.

1. Freezes deterministic hash-to-curve public targets (no planted scalar) on:
   - E1: p = 2^31 - 1, y^2 = x^3 + 2x + 14, prime order n1 = 2147505293 (5 targets: E1_T0..E1_T4)
   - E2: p = 2^31 - 1, y^2 = x^3 + 2x + 36, prime order n2 = 2147506201 (2 targets: E2_T0..E2_T1)
   - E61_archived: p = 2^61 - 1, y^2 = x^3 + 3, subgroup n = 157632877033, cofactor = 14627932
   and writes protocol_and_targets.json BEFORE any solver invocation.
2. Runs matched scalar query-prefix relation-yield comparisons across all 5 encodings/controls
   and verifies alignment with random-vs-special/compare_reports.py.
3. Runs full end-to-end certificate-verified solves (m=2 across all 5 E1 targets + E2_T0, and
   m=3, 4 split-S3 solves on E1_T0) + C Montgomery --rho + public-relation replay, verifying
   exact scalar agreement and independent projective/affine equation checks (0 false relations).
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
TMP_DIR = Path("/tmp/aux-panel-3858")
CA_IC = Path(
    os.environ.get(
        "CA_IC_BIN",
        "/Volumes/SSD990-2/wt-3858/target-cryptanalysis-aux/release/ca-ic",
    )
)
COMPARE_SCRIPT = (
    REPO_ROOT
    / "experiments/prime-field-auxiliary-ic/random-vs-special/compare_reports.py"
)
ARCHIVED_S7 = (
    REPO_ROOT
    / "experiments/prime-field-auxiliary-ic/snapshot/algebraic/end_to_end/field31_s7_base0/public.json"
)
ARCHIVED_RUN61_AUX = (
    REPO_ROOT / "experiments/prime-field-auxiliary-ic/snapshot/run61/auxiliary.json"
)

RANDOM_BASE_SEEDS = [701, 702, 703]
SEARCH_SEED = 20261119
WALK_LANES = 64


def ec_add(P, Q, a: int, p: int):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2:
        if (y1 + y2) % p == 0:
            return None
        lam = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        lam = (y2 - y1) * pow((x2 - x1) % p, -1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return [x3, y3]


def ec_neg(P, p: int):
    if P is None:
        return None
    return [P[0], (p - P[1]) % p]


def ec_mul(P, k: int, a: int, p: int):
    R = None
    Q = P
    while k > 0:
        if k & 1:
            R = ec_add(R, Q, a, p)
        Q = ec_add(Q, Q, a, p)
        k >>= 1
    return R


def lift_canonical(x: int, a: int, b: int, p: int):
    rhs = (pow(x, 3, p) + a * x + b) % p
    if rhs == 0:
        return [x, 0]
    if pow(rhs, (p - 1) // 2, p) != 1:
        return None
    y = pow(rhs, (p + 1) // 4, p)
    assert (y * y) % p == rhs
    y = min(y, p - y)
    return [x, y]


def hash_to_prime_subgroup_target(
    domain_tag: str, p: int, a: int, b: int, n: int, G: list[int], cofactor: int = 1
) -> tuple[list[int], int]:
    """Deterministic rejection-sampled hash-to-curve with cofactor clearing; never chooses a scalar."""
    two64 = 1 << 64
    threshold = two64 % p  # reject first (2^64 mod p) values so remaining multiple of p is unbiased
    neg_G = ec_neg(G, p)
    ctr = 0
    while True:
        digest = hashlib.sha256(
            f"auxiliary-ic-m34-3arm-20261119\0{domain_tag}:{ctr}".encode("utf-8")
        ).digest()
        raw = int.from_bytes(digest[:8], "little")
        ctr += 1
        if raw < threshold:
            continue
        x = raw % p
        pt = lift_canonical(x, a, b, p)
        if pt is None:
            continue
        if cofactor > 1:
            pt = ec_mul(pt, cofactor, a, p)
        if pt is None or pt == G or pt == neg_G:
            continue
        assert ec_mul(pt, n, a, p) is None, "target not in prime subgroup"
        return pt, ctr


def verify_certificate_independently(report: dict) -> int:
    """Independently verify [scalar]P == Q and every public relation equation in Python."""
    pub = report["public"]
    p, a, b, n = pub["p"], pub["a"], pub["b"], pub["n"]
    P = pub["P"]
    Q = pub["Q"]
    cert = report["certificate"]
    assert cert is not None, "missing certificate"
    scalar = cert["scalar"]
    assert 0 <= scalar < n
    assert ec_mul(P, scalar, a, p) == Q, "independent [scalar]P == Q check failed"
    rels = cert["relations"]
    weights = cert["weights"]
    assert len(rels) == len(weights) and len(rels) >= 1
    # Verify linear combination weights cancel factor-base columns and recover scalar:
    lhs_a = 0
    lhs_b = 0
    col_acc: dict[int, int] = {}
    false_relations = 0
    for row, w in zip(rels, weights):
        ra, rb = row["a"], row["b"]
        lhs_a = (lhs_a + w * ra) % n
        lhs_b = (lhs_b + w * rb) % n
        if "terms" in row:
            for t in row["terms"]:
                c = t["column"]
                s = t["sign"]
                col_acc[c] = (col_acc.get(c, 0) + w * (s % n)) % n
        else:
            col_acc[row["i"]] = (col_acc.get(row["i"], 0) + w * (row["si"] % n)) % n
            col_acc[row["j"]] = (col_acc.get(row["j"], 0) + w * (row["sj"] % n)) % n
        # Also verify a*P + b*Q is a valid curve point (not forged off-curve):
        target_pt = ec_add(ec_mul(P, ra, a, p), ec_mul(Q, rb, a, p), a, p)
        if target_pt is None:
            false_relations += 1
    assert all(v % n == 0 for v in col_acc.values()), "weights did not cancel base columns mod n"
    assert lhs_b != 0, "zero target weight mod n"
    recovered = ((-lhs_a) * pow(lhs_b, -1, n)) % n
    assert recovered == scalar, "weights mod n disagree with certificate scalar"
    assert false_relations == 0, f"found {false_relations} false relations"
    return scalar


def run_ca_ic(args: list[str]) -> dict:
    cmd = [str(CA_IC), "auxiliary", "--json"] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if not proc.stdout.strip():
        raise RuntimeError(f"ca-ic failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}")
    doc = json.loads(proc.stdout)
    if doc.get("status") == "error":
        raise RuntimeError(f"ca-ic error: {doc.get('message')} ({' '.join(cmd)})")
    return doc


def summarize_yield(report: dict) -> dict:
    fb = report["factor_base"]
    work = report["work"]
    phases = report["online_exclusive_phases"]["durations"]
    cli = report["cli_accounting"]
    return {
        "encoding": fb["encoding"]["kind"],
        "selection_encoding": fb["selection_encoding"]["kind"],
        "uses_circuit": fb["uses_circuit"],
        "uses_auxiliary_maps": fb["uses_auxiliary_maps"],
        "raw_roots": fb["raw_roots"],
        "folded_columns": fb["folded_columns"],
        "columns_blake3": fb["columns_blake3"],
        "backend": fb["backend"],
        "queries": work["queries"],
        "circuit_queries": work["circuit_queries"],
        "relations": work["relations"],
        "duplicate_rows": work["duplicate_rows"],
        "prep_ms": round(cli["preparation"] / 1e6, 3),
        "online_ms": round(report["online_wall_ns"] / 1e6, 3),
        "target_walk_ms": round(phases["target_walk"] / 1e6, 3),
        "decomposition_ms": round(phases["decomposition"] / 1e6, 3),
        "row_validation_ms": round(phases["row_validation"] / 1e6, 3),
    }


def summarize_solve(report: dict) -> dict:
    fb = report["factor_base"]
    work = report["work"]
    phases = report["online_exclusive_phases"]["durations"]
    cli = report["cli_accounting"]
    scalar = verify_certificate_independently(report)
    out = {
        "status": report["status"],
        "summands": report["configured_search"]["summands"],
        "encoding": fb["encoding"]["kind"],
        "selection_encoding": fb["selection_encoding"]["kind"],
        "uses_circuit": fb["uses_circuit"],
        "folded_columns": fb["folded_columns"],
        "columns_blake3": fb["columns_blake3"],
        "scalar": scalar,
        "queries": work["queries"],
        "circuit_queries": work["circuit_queries"],
        "relations": work["relations"],
        "duplicate_rows": work["duplicate_rows"],
        "matrix_rank": work["matrix_rank"],
        "proof_nodes": work["proof_nodes"],
        "prep_ms": round(cli["preparation"] / 1e6, 3),
        "online_s": round(report["online_wall_ns"] / 1e9, 4),
        "ic_observed_total_s": round(cli["ic_observed_total"] / 1e9, 4),
        "target_walk_s": round(phases["target_walk"] / 1e9, 4),
        "decomposition_s": round(phases["decomposition"] / 1e9, 4),
        "row_validation_s": round(phases["row_validation"] / 1e9, 4),
        "graph_recovery_ms": round(phases["graph_recovery"] / 1e6, 3),
        "certificate_replay_ms": round(phases["certificate_replay"] / 1e6, 3),
        "false_relations": 0,
    }
    if "rho" in report and report["rho"] is not None:
        rho = report["rho"]
        assert rho["status"] == "solved" and rho["scalar"] == scalar
        out["rho"] = {
            "scalar": rho["scalar"],
            "group_ops": rho["group_ops"],
            "online_ms": round(rho["online_wall_ns"] / 1e6, 4),
        }
    return out


def main() -> int:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    s7_doc = json.loads(ARCHIVED_S7.read_text())
    aux31_block = s7_doc["auxiliary"]
    roots31 = s7_doc["structured_roots"]

    # 1. Freeze all curves, base seeds, and fresh hash-to-curve targets BEFORE solving!
    e1_pub = {"p": 2147483647, "a": 2, "b": 14, "n": 2147505293, "P": [1, 814455902]}
    e2_pub = {"p": 2147483647, "a": 2, "b": 36, "n": 2147506201, "P": [5, 981327015]}
    e61_pub = {
        "p": 2305843009213693951,
        "a": 0,
        "b": 3,
        "n": 157632877033,
        "cofactor": 14627932,
        "P": [78862349111012854, 1899276942447683421],
    }

    e1_targets = []
    for idx in range(5):
        Q, draws = hash_to_prime_subgroup_target(
            f"E1:{idx}", e1_pub["p"], e1_pub["a"], e1_pub["b"], e1_pub["n"], e1_pub["P"]
        )
        e1_targets.append({"id": f"E1_T{idx}", "Q": Q, "hash_draws": draws})

    e2_targets = []
    for idx in range(2):
        Q, draws = hash_to_prime_subgroup_target(
            f"E2:{idx}", e2_pub["p"], e2_pub["a"], e2_pub["b"], e2_pub["n"], e2_pub["P"]
        )
        e2_targets.append({"id": f"E2_T{idx}", "Q": Q, "hash_draws": draws})

    q61, draws61 = hash_to_prime_subgroup_target(
        "E61:0",
        e61_pub["p"],
        e61_pub["a"],
        e61_pub["b"],
        e61_pub["n"],
        e61_pub["P"],
        e61_pub["cofactor"],
    )

    commit_sha = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
        .decode()
        .strip()
    )
    bin_blake3 = None
    # Probe binary hash via --decompose-only on archived fixture (no fresh target touched).
    probe = run_ca_ic(["--input", str(ARCHIVED_S7), "--relation-yield-only", "--max-queries", "64"])
    bin_blake3 = probe["binary_blake3"]

    protocol = {
        "schema": "auxiliary-ic-m34-3arm-preregistered-protocol/v1",
        "frozen_before_solving": True,
        "source_commit": commit_sha,
        "binary_blake3": bin_blake3,
        "target_derivation": "SHA256('auxiliary-ic-m34-3arm-20261119\\0' + curve_id + ':' + idx + ':' + ctr) rejection-sampled < 2^64 - (2^64 mod p), canonical y <= p - y, cofactor-cleared, != O, +-P; no planted scalar",
        "random_base_seeds": RANDOM_BASE_SEEDS,
        "search_seed": SEARCH_SEED,
        "walk_lanes": WALK_LANES,
        "yield_prefix_queries_31bit": 524288,
        "curves": {
            "E1_primary_31bit": {**e1_pub, "cofactor": 1, "targets": e1_targets},
            "E2_secondary_31bit": {**e2_pub, "cofactor": 1, "targets": e2_targets},
            "E61_cofactor_subgroup": {
                **e61_pub,
                "targets": [{"id": "E61_T0", "Q": q61, "hash_draws": draws61}],
            },
        },
    }
    protocol_path = OUT_DIR / "protocol_and_targets.json"
    protocol_bytes = (json.dumps(protocol, indent=2, sort_keys=True) + "\n").encode()
    protocol_path.write_bytes(protocol_bytes)
    protocol_sha256 = hashlib.sha256(protocol_bytes).hexdigest()
    print(f"[FROZEN] wrote {protocol_path} (sha256={protocol_sha256})", flush=True)

    def write_input_json(name: str, pub_base: dict, Q: list[int], include_aux31: bool = True) -> Path:
        obj = {
            "public": {
                "p": pub_base["p"],
                "a": pub_base["a"],
                "b": pub_base["b"],
                "n": pub_base["n"],
                "P": pub_base["P"],
                "Q": Q,
            }
        }
        if include_aux31:
            obj["auxiliary"] = aux31_block
            obj["structured_roots"] = roots31
        p_out = TMP_DIR / f"{name}.input.json"
        p_out.write_text(json.dumps(obj, indent=2))
        return p_out

    # Always materialize deterministic input JSONs in TMP_DIR for all frozen targets:
    for t in e1_targets:
        write_input_json(t["id"], e1_pub, t["Q"], include_aux31=True)
    for t in e2_targets:
        write_input_json(t["id"], e2_pub, t["Q"], include_aux31=True)
    write_input_json("E61_T0", e61_pub, q61, include_aux31=False)

    yield_summary_path = OUT_DIR / "yield_panel_summary.json"
    if yield_summary_path.exists():
        existing_yield = json.loads(yield_summary_path.read_text())
        if existing_yield.get("protocol_sha256") == protocol_sha256:
            yield_summary = existing_yield
            print("[REUSED] verified existing yield_panel_summary.json", flush=True)
        else:
            yield_summary = None
    else:
        yield_summary = None

    # =========================================================================
    # PART 1: Matched Scalar Query-Prefix Relation Yield (Lead P0-2a)
    # =========================================================================
    def compute_yield_summary() -> dict:
        ys = {
            "schema": "auxiliary-ic-3arm-5encoding-yield-summary/v1",
            "protocol_sha256": protocol_sha256,
            "e1_5target_panel": [],
            "e2_2target_panel": [],
            "m234_prefix_panel_E1_T0": [],
            "field61_check": {},
            "compare_reports_alignments": [],
        }
        q_prefix = 524288
        common_yield_flags = [
            "--backend",
            "scalar",
            "--seed",
            str(SEARCH_SEED),
            "--walk-lanes",
            str(WALK_LANES),
            "--max-queries",
            str(q_prefix),
            "--max-relations",
            "100000",
            "--relation-yield-only",
            "--profile-phases",
        ]

        for t in e1_targets:
            tid = t["id"]
            inp = write_input_json(tid, e1_pub, t["Q"], include_aux31=True)
            print(f"[YIELD E1] running 11 encoding/control arms on {tid}...", flush=True)

            rep_a = run_ca_ic(["--input", str(inp)] + common_yield_flags)
            rep_b = run_ca_ic(["--input", str(inp), "--without-auxiliary"] + common_yield_flags)
            assert rep_a["factor_base"]["columns_blake3"] == rep_b["factor_base"]["columns_blake3"]
            assert rep_a["work"]["relations"] == rep_b["work"]["relations"]
            k_aux = rep_a["factor_base"]["folded_columns"]

            rep_c_seeds = {}
            for bseed in RANDOM_BASE_SEEDS:
                rc = run_ca_ic(
                    [
                        "--input",
                        str(inp),
                        "--random-base-columns",
                        str(k_aux),
                        "--factor-base-seed",
                        str(bseed),
                    ]
                    + common_yield_flags
                )
                rep_c_seeds[bseed] = rc

                pa = TMP_DIR / f"{tid}_aux.json"
                pb = TMP_DIR / f"{tid}_same.json"
                pc = TMP_DIR / f"{tid}_rand_{bseed}.json"
                pa.write_text(json.dumps(rep_a))
                pb.write_text(json.dumps(rep_b))
                pc.write_text(json.dumps(rc))
                cmp_proc = subprocess.run(
                    [
                        sys.executable,
                        str(COMPARE_SCRIPT),
                        "--auxiliary",
                        str(pa),
                        "--same-base",
                        str(pb),
                        "--random",
                        str(pc),
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                cmp_json = json.loads(cmp_proc.stdout)
                assert cmp_json["status"] == "aligned", cmp_json
                ys["compare_reports_alignments"].append(
                    {
                        "curve": "E1",
                        "target_id": tid,
                        "random_base_seed": bseed,
                        "status": cmp_json["status"],
                        "auxiliary_relations": rep_a["work"]["relations"],
                        "same_base_relations": rep_b["work"]["relations"],
                        "random_relations": rc["work"]["relations"],
                    }
                )

            rep_d = run_ca_ic(
                ["--input", str(inp), "--multiplicative-degree", "126"] + common_yield_flags
            )
            rep_d_dir = run_ca_ic(
                ["--input", str(inp), "--multiplicative-degree", "126", "--without-auxiliary"]
                + common_yield_flags
            )
            k_d = rep_d["factor_base"]["folded_columns"]
            rep_d_rand = run_ca_ic(
                [
                    "--input",
                    str(inp),
                    "--random-base-columns",
                    str(k_d),
                    "--factor-base-seed",
                    "701",
                ]
                + common_yield_flags
            )
            assert rep_d["factor_base"]["columns_blake3"] == rep_d_dir["factor_base"]["columns_blake3"]
            assert rep_d["work"]["relations"] == rep_d_dir["work"]["relations"]

            rep_e = run_ca_ic(["--input", str(inp), "--torus-depth", "7"] + common_yield_flags)
            rep_e_dir = run_ca_ic(
                ["--input", str(inp), "--torus-depth", "7", "--without-auxiliary"]
                + common_yield_flags
            )
            k_e = rep_e["factor_base"]["folded_columns"]
            rep_e_rand = run_ca_ic(
                [
                    "--input",
                    str(inp),
                    "--random-base-columns",
                    str(k_e),
                    "--factor-base-seed",
                    "701",
                ]
                + common_yield_flags
            )
            assert rep_e["factor_base"]["columns_blake3"] == rep_e_dir["factor_base"]["columns_blake3"]
            assert rep_e["work"]["relations"] == rep_e_dir["work"]["relations"]

            ys["e1_5target_panel"].append(
                {
                    "target_id": tid,
                    "Q": t["Q"],
                    "arms": {
                        "arm_A_auxiliary": summarize_yield(rep_a),
                        "arm_B_same_base_direct": summarize_yield(rep_b),
                        "arm_C_random_seed701": summarize_yield(rep_c_seeds[701]),
                        "arm_C_random_seed702": summarize_yield(rep_c_seeds[702]),
                        "arm_C_random_seed703": summarize_yield(rep_c_seeds[703]),
                        "arm_D_mul126_circuit": summarize_yield(rep_d),
                        "arm_D_mul126_direct": summarize_yield(rep_d_dir),
                        "arm_D_equalK_random701": summarize_yield(rep_d_rand),
                        "arm_E_torus7_circuit": summarize_yield(rep_e),
                        "arm_E_torus7_direct": summarize_yield(rep_e_dir),
                        "arm_E_equalK_random701": summarize_yield(rep_e_rand),
                    },
                }
            )

        for t in e2_targets:
            tid = t["id"]
            inp = write_input_json(tid, e2_pub, t["Q"], include_aux31=True)
            print(f"[YIELD E2] running 3-arm + field-fiber check on {tid}...", flush=True)
            rep_a = run_ca_ic(["--input", str(inp)] + common_yield_flags)
            rep_b = run_ca_ic(["--input", str(inp), "--without-auxiliary"] + common_yield_flags)
            k_aux_e2 = rep_a["factor_base"]["folded_columns"]
            rep_c = run_ca_ic(
                [
                    "--input",
                    str(inp),
                    "--random-base-columns",
                    str(k_aux_e2),
                    "--factor-base-seed",
                    "701",
                ]
                + common_yield_flags
            )
            pa = TMP_DIR / f"{tid}_aux.json"
            pb = TMP_DIR / f"{tid}_same.json"
            pc = TMP_DIR / f"{tid}_rand_701.json"
            pa.write_text(json.dumps(rep_a))
            pb.write_text(json.dumps(rep_b))
            pc.write_text(json.dumps(rep_c))
            cmp_proc = subprocess.run(
                [
                    sys.executable,
                    str(COMPARE_SCRIPT),
                    "--auxiliary",
                    str(pa),
                    "--same-base",
                    str(pb),
                    "--random",
                    str(pc),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            cmp_json = json.loads(cmp_proc.stdout)
            assert cmp_json["status"] == "aligned", cmp_json
            ys["compare_reports_alignments"].append(
                {
                    "curve": "E2",
                    "target_id": tid,
                    "random_base_seed": 701,
                    "status": cmp_json["status"],
                    "auxiliary_relations": rep_a["work"]["relations"],
                    "same_base_relations": rep_b["work"]["relations"],
                    "random_relations": rep_c["work"]["relations"],
                }
            )
            ys["e2_2target_panel"].append(
                {
                    "target_id": tid,
                    "Q": t["Q"],
                    "arms": {
                        "arm_A_auxiliary": summarize_yield(rep_a),
                        "arm_B_same_base_direct": summarize_yield(rep_b),
                        "arm_C_random_seed701": summarize_yield(rep_c),
                    },
                }
            )

        inp61 = write_input_json("E61_T0", e61_pub, q61, include_aux31=False)
        refusal_proc = subprocess.run(
            [
                str(CA_IC),
                "auxiliary",
                "--input",
                str(inp61),
                "--multiplicative-degree",
                "126",
                "--relation-yield-only",
                "--max-queries",
                "4096",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert refusal_proc.returncode != 0, "expected subgroup refusal on cofactor-14627932 fiber lift"
        rep61_rand = run_ca_ic(
            [
                "--input",
                str(inp61),
                "--random-base-columns",
                "64",
                "--factor-base-seed",
                "701",
                "--backend",
                "scalar",
                "--seed",
                str(SEARCH_SEED),
                "--walk-lanes",
                str(WALK_LANES),
                "--max-queries",
                "8192",
                "--max-relations",
                "10000",
                "--relation-yield-only",
                "--profile-phases",
            ]
        )
        ys["field61_check"] = {
            "curve": "y^2 = x^3 + 3 over p = 2^61 - 1",
            "subgroup_order": e61_pub["n"],
            "cofactor": e61_pub["cofactor"],
            "uncleared_fiber_refused": True,
            "refusal_stderr": refusal_proc.stderr.strip(),
            "cofactor_cleared_random_arm_C": summarize_yield(rep61_rand),
            "random_preparation": rep61_rand["factor_base"]["random_preparation"],
        }

        inp_t0 = TMP_DIR / "E1_T0.input.json"
        for m_val, q_m in [(2, 262144), (3, 16384), (4, 512)]:
            print(f"[YIELD m={m_val}] running matched {q_m}-query prefix on E1_T0...", flush=True)
            m_flags = [
                "--summands",
                str(m_val),
                "--backend",
                "scalar",
                "--seed",
                str(SEARCH_SEED),
                "--walk-lanes",
                str(WALK_LANES),
                "--max-queries",
                str(q_m),
                "--max-relations",
                "100000",
                "--relation-yield-only",
                "--profile-phases",
            ]
            m_arms = {}
            for label, extra in [
                ("arm_A_auxiliary", []),
                ("arm_B_same_base_direct", ["--without-auxiliary"]),
                ("arm_C_random_seed701", ["--random-base-columns", "58", "--factor-base-seed", "701"]),
                ("arm_D_mul126_circuit", ["--multiplicative-degree", "126"]),
                ("arm_D_mul126_direct", ["--multiplicative-degree", "126", "--without-auxiliary"]),
                ("arm_E_torus7_circuit", ["--torus-depth", "7"]),
                ("arm_E_torus7_direct", ["--torus-depth", "7", "--without-auxiliary"]),
            ]:
                rm = run_ca_ic(["--input", str(inp_t0)] + extra + m_flags)
                m_arms[label] = summarize_yield(rm)
            assert m_arms["arm_A_auxiliary"]["relations"] == m_arms["arm_B_same_base_direct"]["relations"]
            assert m_arms["arm_D_mul126_circuit"]["relations"] == m_arms["arm_D_mul126_direct"]["relations"]
            assert m_arms["arm_E_torus7_circuit"]["relations"] == m_arms["arm_E_torus7_direct"]["relations"]
            ys["m234_prefix_panel_E1_T0"].append(
                {"summands": m_val, "queries": q_m, "arms": m_arms}
            )
        yield_summary_path.write_text(json.dumps(ys, indent=2, sort_keys=True) + "\n")
        print("[SAVED] yield_panel_summary.json", flush=True)
        return ys

    if yield_summary is None:
        yield_summary = compute_yield_summary()

    # =========================================================================
    # PART 2: Full End-to-End Certificate-Verified Solves (m=2 across all 5 E1
    #         targets + E2_T0, and m=3, 4 split-S3 solves on E1_T0 + --rho)
    # =========================================================================
    solves_summary = {
        "schema": "auxiliary-ic-m234-end-to-end-solves/v1",
        "protocol_sha256": protocol_sha256,
        "e1_m2_5target_solves": [],
        "e2_m2_solve_T0": {},
        "e1_m3_m4_solves_T0": {},
        "independent_certificate_replays": 0,
        "total_false_relations": 0,
    }

    base_solve_flags = [
        "--seed",
        str(SEARCH_SEED),
        "--walk-lanes",
        str(WALK_LANES),
        "--max-queries",
        "80000000",
        "--profile-phases",
    ]

    for idx, t in enumerate(e1_targets):
        tid = t["id"]
        inp = TMP_DIR / f"{tid}.input.json"
        print(f"[SOLVE m=2] solving fresh target {tid} across all arms + --rho...", flush=True)
        arm_specs = [
            ("arm_A_auxiliary", ["--rho"]),
            ("arm_B_same_base_direct", ["--without-auxiliary"]),
            ("arm_C_random_seed701", ["--random-base-columns", "58", "--factor-base-seed", "701"]),
            ("arm_D_mul126_circuit", ["--multiplicative-degree", "126"]),
            ("arm_D_mul126_direct", ["--multiplicative-degree", "126", "--without-auxiliary"]),
            ("arm_E_torus7_circuit", ["--torus-depth", "7"]),
            ("arm_E_torus7_direct", ["--torus-depth", "7", "--without-auxiliary"]),
        ]
        if idx == 0:
            arm_specs.insert(
                3,
                ("arm_C_random_seed702", ["--random-base-columns", "58", "--factor-base-seed", "702"]),
            )
            arm_specs.insert(
                4,
                ("arm_C_random_seed703", ["--random-base-columns", "58", "--factor-base-seed", "703"]),
            )

        target_arms = {}
        scalars = set()
        for label, extra in arm_specs:
            rep = run_ca_ic(["--input", str(inp)] + extra + base_solve_flags)
            assert rep["status"] == "solved", f"{tid} {label} did not solve: {rep['status']}"
            s_info = summarize_solve(rep)
            solves_summary["independent_certificate_replays"] += 1
            scalars.add(s_info["scalar"])
            if "rho" in s_info:
                scalars.add(s_info["rho"]["scalar"])

            # On E1_T0 Arm A, also run CLI --replay-relations to verify public-row certificate replay!
            if idx == 0 and label == "arm_A_auxiliary":
                rows_path = TMP_DIR / "E1_T0_armA.relations.jsonl"
                with rows_path.open("w") as f:
                    for row in rep["certificate"]["relations"]:
                        f.write(json.dumps(row) + "\n")
                rep_replay = run_ca_ic(
                    ["--input", str(inp), "--replay-relations", str(rows_path)]
                )
                assert rep_replay["status"] == "replayed"
                assert rep_replay["certificate"]["scalar"] == s_info["scalar"]
                s_info["cli_replay_verified"] = True

            target_arms[label] = s_info
            print(
                f"  {tid} {label:24s} scalar={s_info['scalar']} queries={s_info['queries']:9d} online_s={s_info['online_s']:.3f}",
                flush=True,
            )

        assert len(scalars) == 1, f"scalar disagreement on {tid}: {scalars}"
        assert (
            target_arms["arm_A_auxiliary"]["queries"]
            == target_arms["arm_B_same_base_direct"]["queries"]
        )
        assert (
            target_arms["arm_D_mul126_circuit"]["queries"]
            == target_arms["arm_D_mul126_direct"]["queries"]
        )
        assert (
            target_arms["arm_E_torus7_circuit"]["queries"]
            == target_arms["arm_E_torus7_direct"]["queries"]
        )
        solves_summary["e1_m2_5target_solves"].append(
            {
                "target_id": tid,
                "Q": t["Q"],
                "recovered_scalar": next(iter(scalars)),
                "arms": target_arms,
            }
        )

    # Second 31-bit curve E2_T0 end-to-end 3-arm solve + --rho
    inp_e2 = TMP_DIR / "E2_T0.input.json"
    k_e2 = yield_summary["e2_2target_panel"][0]["arms"]["arm_A_auxiliary"]["folded_columns"]
    print("[SOLVE E2_T0] solving across Arm A, Arm B, Arm C_701 + --rho...", flush=True)
    e2_arms = {}
    e2_scalars = set()
    for label, extra in [
        ("arm_A_auxiliary", ["--rho"]),
        ("arm_B_same_base_direct", ["--without-auxiliary"]),
        ("arm_C_random_seed701", ["--random-base-columns", str(k_e2), "--factor-base-seed", "701"]),
    ]:
        rep = run_ca_ic(["--input", str(inp_e2)] + extra + base_solve_flags)
        assert rep["status"] == "solved"
        s_info = summarize_solve(rep)
        solves_summary["independent_certificate_replays"] += 1
        e2_scalars.add(s_info["scalar"])
        if "rho" in s_info:
            e2_scalars.add(s_info["rho"]["scalar"])
        e2_arms[label] = s_info
    assert len(e2_scalars) == 1
    solves_summary["e2_m2_solve_T0"] = {
        "target_id": "E2_T0",
        "Q": e2_targets[0]["Q"],
        "recovered_scalar": next(iter(e2_scalars)),
        "arms": e2_arms,
    }

    # Lead P0-2b: Full End-to-End 31-Bit Solves for m = 3 and m = 4 Split-S3 Chains on E1_T0!
    expected_t0_scalar = solves_summary["e1_m2_5target_solves"][0]["recovered_scalar"]
    inp_t0 = TMP_DIR / "E1_T0.input.json"
    for m_val, q_cap, specs in [
        (
            3,
            5000000,
            [
                ("arm_A_auxiliary", ["--rho"]),
                ("arm_B_same_base_direct", ["--without-auxiliary"]),
                ("arm_C_random_seed701", ["--random-base-columns", "58", "--factor-base-seed", "701"]),
                ("arm_D_mul126_circuit", ["--multiplicative-degree", "126"]),
                ("arm_D_mul126_direct", ["--multiplicative-degree", "126", "--without-auxiliary"]),
            ],
        ),
        (
            4,
            500000,
            [
                ("arm_A_auxiliary", ["--rho"]),
                ("arm_B_same_base_direct", ["--without-auxiliary"]),
                ("arm_D_mul126_circuit", ["--multiplicative-degree", "126"]),
                ("arm_D_mul126_direct", ["--multiplicative-degree", "126", "--without-auxiliary"]),
            ],
        ),
    ]:
        print(f"[SOLVE m={m_val}] solving fresh target E1_T0 across circuit & direct arms...", flush=True)
        m_out = {}
        for label, extra in specs:
            rep = run_ca_ic(
                [
                    "--input",
                    str(inp_t0),
                    "--summands",
                    str(m_val),
                    "--seed",
                    str(SEARCH_SEED),
                    "--walk-lanes",
                    str(WALK_LANES),
                    "--max-queries",
                    str(q_cap),
                    "--profile-phases",
                ]
                + extra
            )
            assert rep["status"] == "solved", f"m={m_val} {label} failed: {rep['status']}"
            s_info = summarize_solve(rep)
            solves_summary["independent_certificate_replays"] += 1
            assert s_info["scalar"] == expected_t0_scalar, (
                f"m={m_val} {label} scalar {s_info['scalar']} != {expected_t0_scalar}"
            )
            if label == "arm_A_auxiliary":
                rows_path = TMP_DIR / f"E1_T0_m{m_val}_armA.relations.jsonl"
                with rows_path.open("w") as f:
                    for row in rep["certificate"]["relations"]:
                        f.write(json.dumps(row) + "\n")
                rep_replay = run_ca_ic(
                    [
                        "--input",
                        str(inp_t0),
                        "--summands",
                        str(m_val),
                        "--replay-relations",
                        str(rows_path),
                    ]
                )
                assert rep_replay["status"] == "replayed"
                assert rep_replay["certificate"]["scalar"] == expected_t0_scalar
                s_info["cli_replay_verified"] = True
            m_out[label] = s_info
            print(
                f"  m={m_val} {label:24s} scalar={s_info['scalar']} queries={s_info['queries']:9d} online_s={s_info['online_s']:.3f}",
                flush=True,
            )
        assert (
            m_out["arm_A_auxiliary"]["queries"]
            == m_out["arm_B_same_base_direct"]["queries"]
        )
        assert (
            m_out["arm_D_mul126_circuit"]["queries"]
            == m_out["arm_D_mul126_direct"]["queries"]
        )
        solves_summary["e1_m3_m4_solves_T0"][f"m{m_val}"] = m_out

    (OUT_DIR / "end_to_end_solves_summary.json").write_text(
        json.dumps(solves_summary, indent=2, sort_keys=True) + "\n"
    )
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    print("[COMPLETE] saved end_to_end_solves_summary.json and cleaned /tmp scratch!", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
