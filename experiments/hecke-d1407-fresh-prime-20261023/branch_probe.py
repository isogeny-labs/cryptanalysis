"""Check both x=16 sheets outside the selected class walk."""
import json
from pathlib import Path
import sys

from sage.all import EllipticCurve_from_j

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
import hecke11 as H


def main():
    funcs, jfun = H.build([2, 3])
    rd = H.Reduced(20407, funcs, jfun, [2, 3])
    regular = rd.E(rd.Fp(16), rd.Fp(60))
    cusp = rd.E(rd.Fp(16), rd.Fp(-61))
    value = rd.j(regular)
    assert value == rd.Fp(-121)
    assert rd.j(cusp) is None
    fiber = rd.points_with_j(value)
    assert regular in fiber and cusp not in fiber
    model = EllipticCurve_from_j(value)
    trace = int(model.trace_of_frobenius())
    conductor = int(model.endomorphism_order().conductor())
    result = {
        "status": "PASS_FRESH_PRIME_REGULAR_BRANCH",
        "p": 20407,
        "regular_point": str(regular),
        "cusp_point": str(cusp),
        "regular_j": int(value),
        "regular_fiber": [str(q) for q in fiber],
        "regular_j_trace": trace,
        "regular_j_conductor": conductor,
        "selected_class_trace_abs": 176,
        "branch_in_selected_class": abs(trace) == 176 and 6 % conductor == 0,
    }
    (HERE / "branch_probe.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
