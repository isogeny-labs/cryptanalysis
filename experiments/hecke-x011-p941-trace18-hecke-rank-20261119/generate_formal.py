"""Generate exact finite-field root-count certificates for both Hecke degrees."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
raw = (HERE / "result.json").read_bytes()
result = json.loads(raw)
post = json.loads((HERE / "post-run.json").read_text())
audit = json.loads((HERE / "audit.json").read_text())
assert audit["status"] == "PASS"
assert hashlib.sha256(raw).hexdigest() == post["producer_result_sha256"] == audit["result_sha256"]

for ell, name in [(2, "Degree2Roots"), (3, "Degree3Roots")]:
    rows = result["source_records"][str(ell)]
    assert len(rows) == 112 and [r["source"] for r in rows] == list(range(112))
    counts = [r["rational_root_count"] for r in rows]
    if ell == 2:
        assert counts.count(1) == 56 and counts.count(3) == 56
    else:
        assert counts == [2]*112
    fields = [f"c{k}" for k in range(ell+2)]
    lines = [
        "-- Generated from digest-bound result and independent audit by generate_formal.py.",
        "set_option maxRecDepth 100000", "set_option maxHeartbeats 0",
        f"namespace X011P941{name}", f"structure Polynomial where",
    ]
    lines += [f"  {field} : Nat" for field in fields]
    lines.append("def polynomials : List Polynomial := [")
    for i, r in enumerate(rows):
        coeff = r["polynomial"]
        assert len(coeff) == ell+2
        body = ", ".join(f"{field} := {value}" for field, value in zip(fields, coeff))
        lines.append("  { " + body + " }" + ("," if i < 111 else ""))
    lines += ["]", "def rootCount (q : Polynomial) : Nat :=",
              "  ((List.range 941).filter fun x =>",
              "    (" + " + ".join(f"q.c{k}" + ("*x"*k) for k in range(ell+2)) + ") % 941 == 0).length",
              "theorem exact_root_counts : polynomials.map rootCount = [",
              "  " + ", ".join(map(str, counts)) + "] := by decide"]
    if ell == 2:
        lines += ["theorem root_count_histogram :",
                  "    ((polynomials.map rootCount).filter (· == 1)).length = 56 ∧",
                  "    ((polynomials.map rootCount).filter (· == 3)).length = 56 := by",
                  "  rw [exact_root_counts]", "  decide"]
    else:
        lines += ["theorem all_have_two_roots :",
                  "    (polynomials.map rootCount).all (· == 2) = true := by",
                  "  rw [exact_root_counts]", "  decide"]
    lines += [f"#print axioms X011P941{name}.exact_root_counts",
              f"#print axioms X011P941{name}." + ("root_count_histogram" if ell == 2 else "all_have_two_roots"),
              f"end X011P941{name}", ""]
    (HERE / "formal" / f"{name}.lean").write_text("\n".join(lines))
