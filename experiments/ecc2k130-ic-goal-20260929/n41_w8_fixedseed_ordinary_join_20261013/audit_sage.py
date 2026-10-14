"""Independent Sage reconstruction of the ordinary seven-pair relation."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n41_w8_fixed_sum_table_20261009" / "audit.py"
GEO = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
BASE = ROOT / "n41_lowpower_w8_s6" / "basis8.json"
PUBLIC = ROOT / "n41_adjacent_pairpair" / "public_target.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    for name, digest in protocol["source_sha256"].items():
        assert sha(Path(name)) == digest, name
    spec = importlib.util.spec_from_file_location("prior_sage_group_audit", OLD)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    curve, elem, integer = old.sage_curve()
    basis = json.loads(BASE.read_text())["basis_halftrace_by_unique_rotation"][0]
    geometry = json.loads(GEO.read_text())
    public = json.loads(PUBLIC.read_text())
    rows = old.first_rows()
    hit_lines = [x for x in (HERE / "join.stdout").read_text().splitlines() if x.startswith("HIT ")]
    assert len(hit_lines) == 1
    hit = hit_lines[0].split()
    assert hit[1] == "0" and len(hit) == 12
    ids = list(map(int, hit[2:9]))
    assert all(0 <= value < 160 for value in ids)
    raw_sum = curve(0)
    leaves = []
    columns = []
    pair_checks = []
    for slot, sid in enumerate(ids):
        state = geometry["blocks"][slot]["states"][sid]
        a, b, total = old.replay_state(curve, elem, integer, basis, rows,
                                       geometry["rotations"][slot], state)
        raw_sum += total
        leaves.extend((a, b))
        columns.extend(state["columns"])
        pair_checks.append({"slot": slot, "state_id": sid,
                            "masks": [state["a"], state["b"]],
                            "folded_columns": state["columns"],
                            "raw_pair_sum": state["raw_sum"]})
    assert len(set(columns)) == 14
    assert len(set((integer(x[0]), integer(x[1])) for x in leaves)) == 14
    Q = curve(elem(public["target_q"][0]), elem(public["target_q"][1]))
    expected_raw = curve(elem(protocol["raw_target"][0]), elem(protocol["raw_target"][1]))
    assert raw_sum == expected_raw and 4*raw_sum == Q
    assert R*Q == curve(0) and raw_sum == (inverse_mod(4,R))*Q
    result = {"status": "PASS_INDEPENDENT_SAGE_ORDINARY_N41_SEVEN_PAIR_RELATION",
              "candidate_id": None, "curve_id": geometry["curve_id"],
              "public_target": list(public["target_q"]),
              "raw_target": [integer(raw_sum[0]), integer(raw_sum[1])],
              "states": pair_checks, "distinct_folded_columns": len(set(columns)),
              "group_replay_pass": True, "raw_sum_pass": True,
              "query_protocol_sha256": sha(HERE / "query_protocol.json"),
              "query_result_sha256": sha(HERE / "query_result.json"),
              "audit_protocol_sha256": sha(HERE / "audit_protocol.json")}
    with (HERE / "audit_result.json").open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True); out.write("\n")
    print(result["status"], ids, flush=True)


if __name__ == "__main__":
    from sage.all import inverse_mod
    main()
