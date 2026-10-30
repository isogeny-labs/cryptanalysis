"""Exact signed-pattern count conditioned on the frozen order-five residues."""
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
raw = (ROOT / INPUTS["parent_class_receipt"]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == INPUTS["parent_class_sha256"]
parent = json.loads(raw)
case = next(c for c in parent["cases"] if c["p"] == INPUTS["p"])
residues = case["projection_residues"]
assert len(residues) == 40 and case["projection_counts"] == {"0":20,"1":20,"2":0,"3":0,"4":0}
kernel_size = case["curve_order"] // 5


def main():
    rows = []
    for support in range(1, INPUTS["support_max"] + 1):
        trials = eligible = 0
        for inds in itertools.combinations(range(len(residues)), support):
            for rest in itertools.product(INPUTS["coefficient_order"], repeat=support-1):
                signs = (1,) + rest
                trials += 1
                eligible += sum(residues[i]*s for i,s in zip(inds,signs)) % 5 == 0
        expectation = Fraction(eligible, kernel_size)
        assert eligible == INPUTS["projection_eligible_counts"][str(support)]
        assert str(expectation) == INPUTS["projection_uniform_coset_means"][str(support)]
        rows.append({"support": support, "trials": trials,
                     "projection_eligible": eligible,
                     "uniform_coset_mean_exact": str(expectation)})
    out = {"schema":"hecke-d79-p26237-projection-null-v1", "status":"PASS",
           "parent_class_sha256": INPUTS["parent_class_sha256"],
           "kernel_size": kernel_size, "rows": rows}
    (HERE / "projection-null.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status":out["status"],"rows":rows},sort_keys=True))


if __name__ == "__main__":
    main()
