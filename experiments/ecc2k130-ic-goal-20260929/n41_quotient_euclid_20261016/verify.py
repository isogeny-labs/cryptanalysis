"""Replay the quotient gate against the frozen explicit finite-code oracle."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    receipt = json.loads((HERE / "receipt.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    oracle_path = ROOT / "n41_implicit_span_norm_20261016/oracle_result.json"
    oracle = json.loads(oracle_path.read_text())
    inputs = {
        "source": HERE / "run.cpp", "ring": HERE / "quotient.hpp",
        "helpers": HERE / "oracle_helpers.hpp", "binary": HERE / "run",
        "parent": HERE / "parent.py",
        "tensor": ROOT / "n41_target_chart_symbolic_tensor_20261014/coefficients.bin",
        "codes": ROOT / "n41_triproduct_tensor_20261014/codes.txt",
        "source_roots": ROOT / "n41_native_rootproduct_span_20261014/input.txt",
        "oracle": oracle_path,
    }
    assert {key: sha(path) for key, path in inputs.items()} == protocol["sources"]
    assert sha(HERE / "protocol.json") == receipt["protocol_sha256"]
    assert sha(HERE / "result.json") == receipt["result_sha256"]
    assert sha(oracle_path) == protocol["sources"]["oracle"]
    assert receipt["status"] == "EXIT_0"
    assert receipt["peak_polled_rss_bytes"] <= protocol["memory_cap_bytes"]
    assert receipt["wall_ns"] <= protocol["wall_cap_seconds"] * 10**9
    comparisons = []
    for panel, explicit in zip(result["panels"], oracle["panels"]):
        assert panel["panel"] == explicit["panel"]
        assert panel["chart"] == explicit["chart"]
        for gate, exact in zip(panel["ranks"], explicit["ranks"]):
            assert gate["rank"] == exact["rank"]
            kept = set(gate["suspect_second_codes"])
            roots = set(exact["zero_second_codes"])
            assert roots <= kept
            comparisons.append({"panel": panel["panel"], "rank": gate["rank"],
                                "exact_roots": sorted(roots),
                                "gate_kept": sorted(kept),
                                "false_positive_count": len(kept - roots),
                                "gate_ns": gate["gate_ns"],
                                "reduce_ns": gate["reduce_ns"]})
    assert len(comparisons) == 4
    record = {"status": "PASS_FROZEN_EXPLICIT_ORACLE_REPLAY",
              "comparisons": comparisons,
              "gate_result_sha256": sha(HERE / "result.json"),
              "oracle_sha256": sha(oracle_path),
              "verifier_sha256": sha(HERE / "verify.py")}
    (HERE / "verification.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(record["status"])


if __name__ == "__main__":
    main()
