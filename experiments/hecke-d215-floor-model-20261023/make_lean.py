"""Generate concrete Lean vectors from the sealed integer floor certificates."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMAL = HERE / "formal"


def main():
    raw = (HERE / "floor_structure.json").read_bytes()
    receipt = json.loads(raw)
    assert receipt["status"] == "VERIFIED_FOUR_SIGNED_FLOOR_DIRECTIONS"
    certs = receipt["certificates"]
    assert len(certs) == 4
    base = (FORMAL / "FloorKernelBase.lean").read_text()
    lines = [base.rstrip(), "", "namespace FloorKernel", "",
             "/-! The four concrete 168-column floor vectors, generated from floor_structure.json. -/", ""]
    witnesses = []
    for i, cert in enumerate(certs):
        support = sorted(((int(k), int(v)) for k, v in cert["floor_vector"].items()))
        assert len(support) == 14 and all(0 <= k < 168 and v in (-1, 1) for k, v in support)
        witnesses.append(support[0][0])
        lines.append(f"public def cert{i} (j : Fin 168) : ℚ :=")
        for k, value in support:
            lines.append(f"  if j.val = {k} then {value} else")
        lines.extend(["  0", ""])
    args = " ".join(f"cert{i}" for i in range(4))
    wargs = " ".join(f"⟨{k}, by decide⟩" for k in witnesses)
    proof = "(by norm_num [cert0, cert1, cert2, cert3])"
    lines.extend([
        "public theorem concrete_certificates_independent",
        "    (a0 a1 a2 a3 : ℚ)",
        "    (hcomb : ∀ x : Fin 168,",
        "      a0 * cert0 x + a1 * cert1 x + a2 * cert2 x + a3 * cert3 x = 0) :",
        "    a0 = 0 ∧ a1 = 0 ∧ a2 = 0 ∧ a3 = 0 := by",
        f"  exact separating_coordinates {args}",
        f"    {wargs}",
    ])
    for _ in range(16):
        lines.append(f"    {proof}")
    lines.extend(["    a0 a1 a2 a3 hcomb", "", "end FloorKernel", "",
                  "#print axioms FloorKernel.concrete_certificates_independent", ""])
    output = FORMAL / "FloorKernel.lean"
    output.write_text("\n".join(lines))
    receipt_out = {"status": "GENERATED_CONCRETE_FLOOR_VECTORS",
                   "floor_structure_sha256": hashlib.sha256(raw).hexdigest(),
                   "base_sha256": hashlib.sha256((FORMAL / "FloorKernelBase.lean").read_bytes()).hexdigest(),
                   "generated_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                   "witness_columns": witnesses,
                   "generator_sha256": hashlib.sha256((HERE / "make_lean.py").read_bytes()).hexdigest()}
    (FORMAL / "generation.json").write_text(json.dumps(receipt_out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt_out, sort_keys=True))


if __name__ == "__main__":
    main()
