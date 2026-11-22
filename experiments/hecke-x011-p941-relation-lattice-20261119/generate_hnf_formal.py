"""Generate Lean arithmetic checks of the digest-bound p941 Hermite basis."""
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
raw = (HERE / "result.json").read_bytes()
result = json.loads(raw)
post = json.loads((HERE / "post-run.json").read_text())
assert hashlib.sha256(raw).hexdigest() == post["producer_result_sha256"]
basis_raw = (HERE / "hnf-basis.json").read_bytes()
assert hashlib.sha256(basis_raw).hexdigest() == result["hnf_basis_sha256"]
basis = json.loads(basis_raw)
assert len(basis) == 112 and all(len(row) == 112 for row in basis)
entries = [(i, j, int(v)) for i, row in enumerate(basis) for j, v in enumerate(row) if v]
diagonal = [int(basis[i][i]) for i in range(112)]
assert len(entries) == 461 and all(i <= j for i, j, _ in entries)
assert math.prod(diagonal) == result["lattice_index"] == 900
lines = [
    "-- Generated from the digest-bound Hermite basis by generate_hnf_formal.py.",
    "set_option maxRecDepth 100000", "set_option maxHeartbeats 0",
    "namespace X011P941Lattice", "structure Entry where",
    "  row : Nat", "  col : Nat", "  value : Int",
    "def nonzeroEntries : List Entry := [",
]
for k, (i, j, v) in enumerate(entries):
    lines.append(f"  {{ row := {i}, col := {j}, value := {v} }}" + ("," if k < len(entries)-1 else ""))
lines += [
    "]", "def diagonal : List Int := [",
    "  " + ", ".join(map(str, diagonal)) + "]",
    "theorem nonzero_entry_count : nonzeroEntries.length = 461 := by decide",
    "theorem upper_triangular_entries :",
    "    nonzeroEntries.all (fun e => e.row ≤ e.col) = true := by decide",
    "theorem diagonal_product : diagonal.foldl (· * ·) 1 = 900 := by decide",
    "#print axioms X011P941Lattice.nonzero_entry_count",
    "#print axioms X011P941Lattice.upper_triangular_entries",
    "#print axioms X011P941Lattice.diagonal_product",
    "end X011P941Lattice", "",
]
(HERE / "formal" / "HNFIndex.lean").write_text("\n".join(lines))
