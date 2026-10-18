"""Replay the frozen N131 W33 resultant artifact and solver receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def sources_match(protocol):
    for name, expected in protocol["sources"].items():
        path = Path(name)
        if not path.is_absolute():
            path = WORKSPACE / path
        assert digest(path) == expected, name


def main():
    export = read("export_protocol.json")
    sources_match(export)
    coeff = read("coefficients.json")
    assert coeff["protocol_sha256"] == digest(HERE / "export_protocol.json")
    assert coeff["status"] == "PASS_N131_W33_FREECODE_RESULTANT_EXPORT"
    assert (coeff["field_degree"], coeff["source_width"],
            coeff["free_code_bits"], coeff["source_product_rank"]) == (131, 33, 32, 32)
    assert coeff["rotations"] == [0, 18] and len(coeff["rows"]) == 2
    assert all(len(row["terms"]) == 13 for row in coeff["rows"])
    assert [check["code"] for check in coeff["positive_source_checks"]] == [3, 16722]

    build = read("build_protocol.json")
    sources_match(build)
    counts = {"and_gates": 15225, "variables": 21194,
              "clauses": 46073, "xor_rows": 5643,
              "generic_mul_calls": 1, "sparse_mul_calls": 4,
              "sparse_pair_products": 6240, "linear_squares": 4}
    for index, formula in enumerate(("positive.xcnf", "public.xcnf")):
        row = read(f"build_{index}_result.json")
        assert row["status"] == "PASS_N131_W33_FREECODE_RESULTANT_CIRCUIT"
        assert row["protocol_sha256"] == digest(HERE / "build_protocol.json")
        assert row["counts"] == counts and row["target_index"] == index
        assert row["formula_sha256"] == digest(HERE / formula)
        assert row["formula_bytes"] == (HERE / formula).stat().st_size
        assert row["target_point"] == coeff["rows"][index]["point"]
        if index == 0:
            assert row["positive_assignment_check"] == {
                "clauses": counts["clauses"], "native_xor_rows": counts["xor_rows"]}
        else:
            assert row["positive_assignment_check"] is None

    pin = read("pin_build_protocol.json")
    sources_match(pin)
    pinned = read("pin_build_result.json")
    assert pinned["status"] == "PASS_N131_W33_PIN_FIRST_FORMULA"
    assert pinned["protocol_sha256"] == digest(HERE / "pin_build_protocol.json")
    assert pinned["formula_sha256"] == digest(HERE / "positive_pin_first.xcnf")
    assert pinned["formula_bytes"] == (HERE / "positive_pin_first.xcnf").stat().st_size
    assert (pinned["known_first_code"], pinned["pinned_input_variables"],
            pinned["second_code_bits_free"], pinned["inverse_witness_bits_free"]) == (3, 32, 32, 262)

    for protocol_name, result_name, stem, cap in (
            ("solver_protocol.json", "solver_0_result.json", "solver_0", 600),
            ("pin_query_protocol.json", "pin_query_result.json", "pin_solver", 300)):
        protocol = read(protocol_name)
        sources_match(protocol)
        result = read(result_name)
        assert result["protocol_sha256"] == digest(HERE / protocol_name)
        assert result["status"] == "BOUNDED_UNKNOWN"
        assert result["stop_reason"] == "WALL_CAP"
        assert result["solver_terminal_sat"] is False
        assert result["solver_terminal_unsat"] is False
        assert cap <= result["wall_seconds"] < cap + 2
        assert 0 < result["sampled_peak_combined_rss_bytes"] < protocol["rss_cap_bytes"]
        assert result["solver_stdout_sha256"] == digest(HERE / (stem + ".stdout"))
        assert result["solver_stderr_sha256"] == digest(HERE / (stem + ".stderr"))
    assert not (HERE / "solver_1_result.json").exists()
    print(json.dumps({"status": "PASS_FROZEN_RECEIPT_REPLAY",
                      "positive_solver": "BOUNDED_UNKNOWN_600S",
                      "pin_first_solver": "BOUNDED_UNKNOWN_300S",
                      "public_solver": "GATED_NOT_RUN"}, sort_keys=True))


if __name__ == "__main__":
    main()
