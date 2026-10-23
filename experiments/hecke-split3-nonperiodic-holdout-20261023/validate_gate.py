"""Replay the frozen D551 selection and the independent X0(11) fiber gate."""
import hashlib
import json
from math import isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def main():
    selection, protocol, gate = (read(name) for name in
        ("selection.json", "producer_protocol.json", "fiber_gate_result.json"))
    assert selection["protocol_sha256"] == sha("selection_protocol.json")
    assert selection["chosen"] == {"d":551,"h1":26,"h2":26,"h3":52,
        "norm2_order_f3":26,"norm3_order_f2":26,
        "degree2_directions_predicted":4,"degree3_directions_predicted":0,
        "floor_rank_predicted":4,"v":88,"p":12703,"u_abs":176}
    assert protocol["status"] == "FROZEN_BEFORE_GATE_AND_PRODUCER"
    assert protocol["selection_sha256"] == sha("selection.json")
    assert all(sha(name) == digest for name,digest in protocol["source_sha256"].items())
    assert gate["script_sha256"] == sha("fiber_gate.py")
    assert gate["status"] == "FAIL_UNIFORM_TWO_SHEET_GATE"
    assert (gate["dk"],gate["f"],gate["p"],gate["u"]) == (-551,6,12703,176)
    assert all(12703 % q for q in range(2,isqrt(12703)+1))
    assert 176**2-4*12703 == -551*6**2
    assert len(gate["exceptions"]) == 156
    expected={"1":26,"2":26,"3":52,"6":52}
    for f,stratum in gate["strata"].items():
        assert stratum == {"class_number":expected[f],
            "rational_j_count":expected[f],"rational_point_count":0,
            "points_per_j":{"0":expected[f]}}
    assert all(x["rational_point_count"]==0 and x["trace_abs"]==176
               for x in gate["exceptions"])
    residue = (176*176-4*12703) % 11
    squares = {x*x%11 for x in range(11)}
    assert residue == 8 and residue not in squares
    result={"status":"PASS_FROZEN_GATE_FAILURE_REPLAY",
        "selection_protocol_sha256":sha("selection_protocol.json"),
        "producer_protocol_sha256":sha("producer_protocol.json"),
        "gate_sha256":sha("fiber_gate_result.json"),
        "frobenius_discriminant_mod_11":residue,
        "squares_mod_11":sorted(squares),
        "rational_class_j_count":156,
        "rational_x0_11_points":0,
        "candidate_id":None,"timing_claim":None,
        "matrix_status":"NOT_RUN_AFTER_FAILED_ELIGIBILITY_GATE"}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
