"""Read-only independent audit of the incremental first-code experiment."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent
PRIOR = D.parent / "n41_public_code_cube_20261017"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_model(formula_path, model, wires, code):
    assert set(model) <= {"0", "1"}
    assignment = [int(bit) == 0 for bit in model]  # CMSat: 0=true, 1=false.
    assert len(assignment) == 31533
    assert all(assignment[wire - 1] == bool(code >> j & 1)
               for j, wire in enumerate(wires))
    ordinary = xors = 0
    with formula_path.open() as source:
        for raw in source:
            if raw[0] in "cp":
                continue
            is_xor = raw[0] == "x"
            literals = [int(x) for x in raw[1 if is_xor else 0:].split()]
            assert literals[-1] == 0
            literals.pop()
            values = [assignment[abs(x) - 1] == (x > 0) for x in literals]
            if is_xor:
                assert sum(values) % 2 == 1
                xors += 1
            else:
                assert any(values)
                ordinary += 1
    assert (ordinary, xors) == (82957, 3689)
    return {"ordinary_clauses": ordinary, "xor_rows": xors}


def main():
    p = read(D / "protocol_v2.json")
    r = read(D / "run_protocol_v2.json")
    result = read(D / "full_v2_result.json")
    pilot_p = read(D / "protocol.json")
    pilot_r = read(D / "run_protocol.json")
    pilot = read(D / "pilot_result.json")
    assert p["schema"] == 2 and r["schema"] == 2
    assert p["candidate_id"] is None
    assert sha(D / "protocol_v2.json") == r["protocol_sha256"] == result["protocol_sha256"]
    assert sha(D / "run_protocol_v2.json") == result["run_protocol_sha256"]
    assert sha(D / "run_v2.py") == r["runner_sha256"]
    assert sha(D / "sage_runtime_info.json") == r["runtime_info_sha256"]
    assert sha(D / "incremental.cpp") == p["source_sha256"]
    assert sha(D / "incremental") == p["binary_sha256"]
    assert sha(D / "codes.tsv") == p["codes_sha256"]
    assert sha(Path(p["formula_path"])) == p["formula_sha256"]
    assert sha(Path(p["lib_path"])) == p["lib_sha256"]
    assert sha(Path("/opt/homebrew/include/cryptominisat5/cryptominisat_c.h")) == p["header_sha256"]
    assert sha(D / "freeze.py") == p["producer_sha256"]
    assert (D / "compile.exit").read_text().strip() == "0"
    assert sha(D / "pilot_result.json") == p["pilot_result_sha256"]
    assert sha(D / "protocol.json") == p["supersedes_protocol_sha256"]
    assert sha(D / "protocol.json") == pilot_r["protocol_sha256"] == pilot["protocol_sha256"]
    assert sha(D / "run_protocol.json") == pilot["run_protocol_sha256"]
    assert sha(D / "run.py") == pilot_r["runner_sha256"]
    assert pilot["status"] == "PILOT_CENSORED" and pilot["exit_code"] == 0
    assert pilot["code_lines"] == [line for line in (D / "pilot.stdout").read_text().splitlines()
                                    if line.startswith("CODE ")]
    assert pilot["code_lines"][0].split()[1:3] == ["2", "UNKNOWN"]
    assert read(PRIOR / "witness_result.json")["formula_sha256"] == p["formula_sha256"]
    assert read(PRIOR / "witness_result.json")["first_code"] == 6
    assert read(PRIOR / "witness_result.json")["status"] == "PASS_PUBLIC_WITNESS_ASSIGNMENT"

    tokens = (D / "codes.tsv").read_text().splitlines()
    header = tokens.pop(0).split()
    assert header[:2] == ["W", "7"]
    wires = [int(x) for x in header[2:]]
    assert len(wires) == 7 and len(set(wires)) == 7
    assert wires == read(PRIOR / "wires.json")["code_wires"]
    codes = [int(line.split()[1]) for line in tokens]
    assert all(line.split()[0] == "C" for line in tokens)
    assert codes == p["allowed_codes"] and len(codes) == len(set(codes)) == 40
    assert p["allowed_codes"] == read(PRIOR / "protocol.json")["allowed_codes"]
    assert sha(PRIOR / "protocol.json") == p["prior_cube_protocol_sha256"]
    assert sha(PRIOR / "campaign_result.json") == p["prior_cube_result_sha256"]

    out = D / "full_v2.stdout"
    err = D / "full_v2.stderr"
    assert sha(out) == result["stdout_sha256"]
    assert sha(err) == result["stderr_sha256"]
    assert err.read_text() == ""
    assert not result["monitor_degraded"]
    assert result["sampled_peak_combined_rss_bytes"] < p["rss_cap_bytes"]
    assert result["wall_s"] <= p["parent_cap_s"] + 2
    assert result["command"] == [str(D / "incremental"), p["formula_path"],
                                  str(D / "codes.tsv"), "40", str(p["per_call_cpu_cap_s"])]
    lines = out.read_text().splitlines()
    assert len(result["load_lines"]) == 1
    assert result["load_lines"] == [x for x in lines if x.startswith("LOADED ")]
    assert result["load_lines"][0].split()[1:4] == ["31533", "82957", "3689"]
    rows = [x.split() for x in lines if x.startswith("CODE ")]
    assert result["code_lines"] == [x for x in lines if x.startswith("CODE ")]
    assert [int(row[1]) for row in rows] == codes[:len(rows)]
    assert all(row[0] == "CODE" and row[2] in {"SAT", "UNSAT", "UNKNOWN"}
               and int(row[4]) == i and float(row[3]) > 0
               for i, row in enumerate(rows, 1))
    assert len(rows) <= 40
    sat = [row for row in rows if row[2] == "SAT"]
    models = [x[6:] for x in lines if x.startswith("MODEL ")]
    assert len(models) == result["model_line_count"]
    if sat:
        assert len(sat) == len(models) == 1 and rows[-1] == sat[0]
        assert result["exit_code"] == 0 and result["stop_reason"] is None
        checked = check_model(Path(p["formula_path"]), models[0], wires, int(sat[0][1]))
        status = "PASS_EXACT_FORMULA_MODEL"
    else:
        assert not models
        if len(rows) == 40:
            assert result["status"] == "ALL_CUBES_BOUNDED_OR_UNCERTIFIED"
            assert result["exit_code"] == 0 and result["stop_reason"] is None
        else:
            assert result["status"] == "BOUNDED_UNKNOWN"
            assert result["stop_reason"] == "PARENT_WALL_CAP"
            assert result["exit_code"] == -15
        checked = None
        status = "PASS_BOUNDED_ASSUMPTION_AUDIT"
    audit = {"status": status, "completed_codes": len(rows),
             "sat_codes": [int(row[1]) for row in sat],
             "unknown_codes": [int(row[1]) for row in rows if row[2] == "UNKNOWN"],
             "uncertified_unsat_codes": [int(row[1]) for row in rows if row[2] == "UNSAT"],
             "sum_solver_call_wall_s": sum(float(row[3]) for row in rows),
             "formula_assignment_check": checked,
             "retrospective_satisfiable_code": 6,
             "retrospective_code_status": next(row[2] for row in rows if row[1] == "6")}
    (D / "verification.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
