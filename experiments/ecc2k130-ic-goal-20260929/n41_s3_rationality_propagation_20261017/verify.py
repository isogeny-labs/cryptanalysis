"""Read-only receipt audit of the direct-leaf public S3 experiment."""
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def check_query(pname, rname, outname, errname, runner):
    p = read(D / pname)
    r = read(D / rname)
    assert sha(D / pname) == r["query_protocol_sha256"]
    assert sha(D / runner) == p["runner_sha256"]
    for name, digest in p["sources"].items():
        assert sha(D / name) == digest, name
    assert sha(Path(p["solver_path"])) == p["solver_sha256"]
    assert r["command"] == [p["solver_path"], *p["solver_flags"], str(D / "public.xcnf")]
    assert sha(D / outname) == r["stdout_sha256"]
    assert sha(D / errname) == r["stderr_sha256"]
    assert (D / errname).read_text() == ""
    assert not r["monitor_degraded"]
    assert r["sampled_peak_combined_rss_bytes"] < p["rss_cap_bytes"]
    assert r["wall_ns"] <= (p["parent_wall_cap_s"] + 2) * 10**9
    lines = (D / outname).read_text(errors="replace").splitlines()
    assert "Reading file" in "\n".join(lines)
    assert any("Parsing time:" in line for line in lines)
    restarts = sum(line.startswith("c rst ") for line in lines)
    assert restarts > 0
    assert r["terminal_lines"] == [line for line in lines if line.startswith("s ")]
    if r["status"] == "BOUNDED_UNKNOWN":
        assert r["stop_reason"] == "PARENT_WALL_CAP" and r["exit_code"] == -15
        assert not r["terminal_lines"]
    elif r["status"] == "SAT_PENDING_REPLAY":
        assert "s SATISFIABLE" in r["terminal_lines"]
        assert r["stop_reason"] is None and r["exit_code"] == 0
    else:
        raise AssertionError((r["status"], r["terminal_lines"]))
    return {"status": r["status"], "wall_ns": r["wall_ns"],
            "peak_combined_rss_bytes": r["sampled_peak_combined_rss_bytes"],
            "logged_restarts": restarts}


def main():
    p = read(D / "protocol.json")
    b = read(D / "build_result.json")
    ap = read(D / "audit_protocol.json")
    ar = read(D / "leaf_audit_result.json")
    assert p["schema"] == 1 and p["candidate_id"] is None
    assert sha(D / "freeze.py") == p["producer_sha256"]
    assert sha(D / "circuit.py") == p["circuit_sha256"]
    assert sha(D / "build.py") == p["builder_sha256"]
    assert sha(D / "sage_runtime_info.json") == p["runtime_info_sha256"]
    assert sha(D / "protocol.json") == b["protocol_sha256"]
    for name, digest in p["source_sha256"].items():
        assert sha(ROOT / name) == digest, name
    assert sha(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json") == p["geometry_sha256"]
    assert sha(ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json") == p["relation_sha256"]
    assert b["status"] == "PASS_PUBLIC_S3_RATIONALITY_FORMULA_BUILD"
    assert b["assignment_check"] == {"clauses": 52243, "native_xor_rows": 2975}
    assert (b["and_gates"], b["variables"], b["ordinary_clauses"], b["native_xor_rows"]) == (
        16851, 20283, 52243, 2975)
    assert b["leaf_and_checkpoints"] == [287 * (i + 1) for i in range(6)]
    spec = importlib.util.spec_from_file_location("direct_leaf_readback", D / "circuit.py")
    direct = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(direct)
    machine, wires = direct.build(b["target_reciprocal"])
    code_wires = {wire for slot in wires["codes"] for wire in slot}
    assert len(code_wires) == 42
    assert machine.and_count == b["and_gates"]
    assert not any(len((tokens := clause.split())) == 2 and
                   abs(int(tokens[0])) in code_wires
                   for clause in machine.clauses)
    assert sha(D / "public.xcnf") == b["formula_sha256"]
    dependencies = read(D / "dependency_manifest.json")
    assert dependencies["scope"].startswith("postrun source readback")
    assert sha(D / "dependency_manifest.py") == dependencies["producer_sha256"]
    assert sha(D / "public.xcnf") == dependencies["public_formula_sha256"]
    assert sha(D / "build_result.json") == dependencies["build_result_sha256"]
    assert sha(D / "query_protocol_v2.json") == dependencies["query_protocol_v2_sha256"]
    assert sha(D / "query_v2_result.json") == dependencies["query_v2_result_sha256"]
    for name, digest in dependencies["goal_sources"].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in dependencies["experiment_sources"].items():
        assert sha(ROOT.parent / name) == digest, name
    for name, digest in dependencies["local_sources"].items():
        assert sha(D / name) == digest, name
    dependencies_v2 = read(D / "dependency_manifest_v2.json")
    assert dependencies_v2["schema"] == 2
    assert sha(D / "dependency_manifest_v2.py") == dependencies_v2["producer_v2_sha256"]
    assert sha(D / "dependency_manifest.json") == dependencies_v2["supersedes_manifest_sha256"]
    assert len(dependencies_v2["workspace_sources"]) == 3
    for name, digest in dependencies_v2["workspace_sources"].items():
        assert sha(D.parents[2] / name) == digest, name
    with tempfile.TemporaryDirectory(prefix="n41-direct-leaf-rebuild-") as temp:
        rebuilt = Path(temp) / "public.xcnf"
        machine.write(rebuilt)
        assert sha(rebuilt) == b["formula_sha256"]
    with (D / "public.xcnf").open() as formula:
        header = formula.readline().split()
        assert header == ["p", "cnf", "20283", "55218"]
        ordinary = xors = 0
        for line in formula:
            if line.startswith("c"):
                continue
            assert line.split()[-1] == "0"
            if line.startswith("x"):
                xors += 1
            else:
                ordinary += 1
    assert (ordinary, xors) == (52243, 2975)
    assert sha(D / "audit_leaf_sage.py") == ap["auditor_sha256"]
    assert sha(D / "sage_runtime_info.json") == ap["runtime_info_sha256"]
    assert sha(D / "public.xcnf") == ap["formula_sha256"]
    assert sha(D / "audit_protocol.json") == ar["audit_protocol_sha256"]
    for name, digest in ap["sources"].items():
        assert sha(ROOT / name) == digest, name
    assert ar["status"] == "PASS_INDEPENDENT_S3_LEAF_SUPPORT"
    assert (ar["curve_states_replayed"], ar["code_slot_quadratics"],
            ar["distinct_expected_roots_across_code_slots"]) == (960, 240, 480)
    assert ar["roots_per_quadratic"] == 2
    assert ar["field_modulus_irreducible"] and ar["leading_coefficient_nonzero"]
    assert (D / "lean_build.exit").read_text().strip() == "0"
    assert (D / "lean_build.stderr").read_text() == ""
    assert "does not depend on any axioms" in (D / "lean_build.stdout").read_text()
    assert not any(token in (D / "RationalityPropagation.lean").read_text()
                   for token in ("sorry", "admit", "sorryAx"))
    for version, kind in ((1, "PRODUCER_FAILURE_INPUT_MODEL"),
                          (2, "PRODUCER_FAILURE_HALFTRACE_ASSERTION")):
        stem = f"n131_v{version}"
        failure = read(D / (stem + "_failure.json"))
        assert failure["status"] == kind
        assert (D / (stem + ".exit")).read_text().strip() == "1"
        assert "AssertionError" in (D / (stem + ".stderr")).read_text()
        assert sha(D / (stem + ".stdout")) == failure["stdout_sha256"]
        assert sha(D / (stem + ".stderr")) == failure["stderr_sha256"]
        script = "n131_leaf_projection_sage.py" if version == 1 else "n131_leaf_projection_v2_sage.py"
        protocol = ("n131_leaf_projection_protocol.json" if version == 1
                    else "n131_leaf_projection_protocol_v2.json")
        assert sha(D / script) == failure["source_sha256"]
        assert sha(D / protocol) == failure["protocol_sha256"]
    n131_p = read(D / "n131_leaf_projection_protocol_v3.json")
    n131_r = read(D / "n131_leaf_projection_v3_result.json")
    assert n131_p["schema"] == 3
    assert sha(D / "freeze_n131_leaf_v3.py") == n131_p["producer_v3_sha256"]
    assert sha(D / "n131_leaf_projection_v3_sage.py") == n131_p["runner_sha256"]
    assert sha(D / "n131_leaf_projection_protocol_v2.json") == n131_p["supersedes_protocol_sha256"]
    assert sha(D / "n131_v2_failure.json") == n131_p["failed_v2_receipt_sha256"]
    assert sha(D / "n131_v1_failure.json") == n131_p["failed_v1_receipt_sha256"]
    assert sha(D / "sage_runtime_info.json") == n131_p["runtime_info_sha256"]
    for name, digest in n131_p["sources"].items():
        assert sha(ROOT / name) == digest, name
    assert sha(D / "n131_leaf_projection_protocol_v3.json") == n131_r["protocol_sha256"]
    assert n131_r["status"] == "PASS_N131_W23_DIRECT_LEAF_PROJECTION"
    assert (n131_r["product_map_rank"], n131_r["predicted_direct_leaf_and_gates_per_slot"],
            n131_r["sample_edges"], n131_r["independent_signed_pair_sums"]) == (
                22, 2882, 8, 32)
    assert not n131_r["product_one_in_span"]
    sf_fail = read(D / "small_field_v1_failure.json")
    assert sf_fail["status"] == "PRODUCER_FAILURE_FIELD_API"
    assert (D / "small_field_v1.exit").read_text().strip() == "1"
    assert "fetch_int" in (D / "small_field_v1.stderr").read_text()
    assert sha(D / "small_field_protocol.json") == sf_fail["protocol_sha256"]
    assert sha(D / "small_field_s3_sage.py") == sf_fail["source_sha256"]
    assert sha(D / "small_field_v1.stdout") == sf_fail["stdout_sha256"]
    assert sha(D / "small_field_v1.stderr") == sf_fail["stderr_sha256"]
    sfp = read(D / "small_field_protocol_v2.json")
    sfr = read(D / "small_field_v2_result.json")
    assert sfp["schema"] == 2
    assert sha(D / "freeze_small_field_v2.py") == sfp["producer_v2_sha256"]
    assert sha(D / "small_field_s3_v2_sage.py") == sfp["runner_sha256"]
    assert sha(D / "small_field_protocol.json") == sfp["supersedes_protocol_sha256"]
    assert sha(D / "small_field_v1_failure.json") == sfp["failed_v1_receipt_sha256"]
    assert sha(D / "sage_runtime_info.json") == sfp["runtime_info_sha256"]
    assert sha(D / "small_field_protocol_v2.json") == sfr["protocol_sha256"]
    assert sfr["status"] == "PASS_EXHAUSTIVE_SMALL_FIELD_S3_RATIONALITY"
    assert [(x["field_degree"], x["s3_zeros_with_rational_parent"],
             x["rational_children_checked"]) for x in sfr["panels"]] == [
                 (5, 840, 840), (7, 6384, 6384)]
    q1 = check_query("query_protocol.json", "query_result.json", "solver.stdout",
                     "solver.stderr", "run_public.py")
    p2 = read(D / "query_protocol_v2.json")
    assert p2["schema"] == 2
    assert sha(D / "freeze_query_v2.py") == p2["producer_v2_sha256"]
    assert sha(D / "query_protocol.json") == p2["supersedes_protocol_sha256"]
    assert sha(D / "query_result.json") == p2["pilot_result_sha256"]
    q2 = check_query("query_protocol_v2.json", "query_v2_result.json",
                     "solver_v2.stdout", "solver_v2.stderr", "run_public_v2.py")
    audit = {"status": "PASS_PUBLIC_DIRECT_LEAF_RECEIPTS",
             "formula_sha256": b["formula_sha256"],
             "and_gates": b["and_gates"],
             "independent_leaf_states": ar["curve_states_replayed"],
             "n131_leaf_projection": n131_r["status"],
             "small_field_s3_zeros_checked": [840, 6384],
             "explicit_code_units": 0,
             "public_query_185": q1,
             "public_query_550": q2}
    (D / "verification.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
