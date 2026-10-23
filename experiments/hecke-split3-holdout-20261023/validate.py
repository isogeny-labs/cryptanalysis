"""Pure-Python validation of the frozen holdout and corrected cycle rule."""
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def class_number(disc):
    total = 0
    for a in range(1, isqrt((-disc) // 3) + 2):
        for b in range(-a, a + 1):
            n = b*b - disc
            if n % (4*a):
                continue
            c = n // (4*a)
            if a > c or (b < 0 and (abs(b) == a or a == c)):
                continue
            if gcd(gcd(a, abs(b)), c) == 1:
                total += 1
    return total


def main():
    search, selected = read("search_protocol.json"), read("selection.json")
    protocol = read("producer_protocol.json")
    gate, data, audit = (read(name) for name in
                         ("fiber_gate_result.json", "data/exp11_class_walk_D431_f6.json", "audit.json"))
    structure, degree3, cycles, combined = (read(name) for name in
                                              ("floor_structure.json", "degree3_diagnostic.json",
                                               "cycle_model.json", "combined.json"))
    assert selected["protocol_sha256"] == sha("search_protocol.json")
    assert selected["status"] == "FROZEN_HOLDOUT_SELECTED"
    assert selected["chosen"] == {"d": 431, "h1": 21, "h3": 42,
                                   "norm2_order_f3": 14, "p": 12343,
                                   "predicted_signed_cycles": 6, "u_abs": 184, "v": 92}
    assert protocol["selection_sha256"] == sha("selection.json")
    for name, digest in protocol["source_sha256"].items():
        assert sha(name) == digest, name
    assert 184**2 - 4*12343 == -431*6**2
    assert all(12343 % q for q in range(2, isqrt(12343) + 1))
    class_numbers = {str(f): class_number(-431*f*f) for f in (1, 2, 3, 6)}
    assert class_numbers == {"1": 21, "2": 21, "3": 42, "6": 42}
    assert gate["status"] == "PASS_UNIFORM_TWO_SHEET_GATE"
    assert {f: s["class_number"] for f, s in gate["strata"].items()} == class_numbers
    assert audit["status"] == "VERIFIED_D431_F6_MATRIX"
    assert audit["producer_sha256"] == sha("data/exp11_class_walk_D431_f6.json")
    assert (data["class_size"], data["relations"], data["rank"]) == (252, 210, 168)
    assert protocol["predictions"]["floor_kernel_rank"] == 6
    assert audit["ranks"]["2+3"] == {"full_QQ": 168, "nonfloor_QQ": 158}
    assert structure["status"] == "VERIFIED_SIX_SIGNED_DEGREE2_FLOOR_DIRECTIONS"
    assert degree3["status"] == "VERIFIED_FOUR_DEGREE3_FLOOR_DIRECTIONS"
    assert cycles["status"] == "VERIFIED_TWO_CLASS_NORM3_CYCLE_RULE"
    assert cycles["cases"]["D215"]["cycle_lengths"] == [14, 14]
    assert cycles["cases"]["D431"]["cycle_lengths"] == [21, 21]
    assert combined["status"] == "PASS_TEN_FLOOR_DIRECTIONS_SPAN_KERNEL"
    assert combined["frozen_rank_prediction"] == 6 and combined["floor_kernel_dimension"] == 10
    check = (HERE / "formal/cycle-kernel-check.txt").read_text()
    assert "CycleKernel.period_three" in check and "CycleKernel.cycle14_trivial" in check
    assert "sorryAx" not in check
    result = {"status": "PASS_SPLIT3_HOLDOUT_REPLAY_WITH_FALSIFIED_FORECAST",
              "search_protocol_sha256": sha("search_protocol.json"),
              "producer_protocol_sha256": sha("producer_protocol.json"),
              "data_sha256": sha("data/exp11_class_walk_D431_f6.json"),
              "audit_sha256": sha("audit.json"),
              "cycle_model_sha256": sha("cycle_model.json"),
              "combined_sha256": sha("combined.json"),
              "lean_check_sha256": sha("formal/cycle-kernel-check.txt"),
              "class_numbers": class_numbers,
              "frozen_floor_rank": 6, "observed_floor_rank": 10,
              "degree2_directions": 6, "degree3_directions": 4,
              "candidate_id": None, "timing_claim": None}
    (HERE / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
