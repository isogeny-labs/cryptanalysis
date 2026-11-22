"""Generate a Lean arithmetic check of the audited Hermite basis diagonal."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
raw = (HERE / "result.json").read_bytes()
result = json.loads(raw)
audit = json.loads((HERE / "audit.json").read_text())
assert audit["status"] == "PASS"
assert hashlib.sha256(raw).hexdigest() == audit["result_sha256"]
basis_raw = (HERE / "hnf-basis.json").read_bytes()
assert hashlib.sha256(basis_raw).hexdigest() == result["hnf_basis_sha256"]
basis = json.loads(basis_raw)
assert len(basis) == 84 and all(len(row) == 84 for row in basis)
entries = [(i, j, int(v)) for i, row in enumerate(basis) for j, v in enumerate(row) if v]
diagonal = [int(basis[i][i]) for i in range(84)]
assert all(i <= j for i, j, _ in entries)
assert len(entries) == 281
assert __import__("math").prod(diagonal) == result["lattice_index"] == 1020
lines = [
    "-- Generated from the digest-bound Hermite basis by generate_hnf_formal.py.",
    "set_option maxRecDepth 100000", "set_option maxHeartbeats 0",
    "namespace X011RelationLattice", "structure Entry where",
    "  row : Nat", "  col : Nat", "  value : Int",
    "def nonzeroEntries : List Entry := [",
]
for k, (i, j, v) in enumerate(entries):
    lines.append(f"  {{ row := {i}, col := {j}, value := {v} }}" + ("," if k < len(entries)-1 else ""))
lines += [
    "]", "def diagonal : List Int := [",
    "  " + ", ".join(map(str, diagonal)) + "]",
    "theorem nonzero_entry_count : nonzeroEntries.length = 281 := by decide",
    "theorem upper_triangular_entries :",
    "    nonzeroEntries.all (fun e => e.row ≤ e.col) = true := by decide",
    "theorem diagonal_product : diagonal.foldl (· * ·) 1 = 1020 := by decide",
    "#print axioms X011RelationLattice.nonzero_entry_count",
    "#print axioms X011RelationLattice.upper_triangular_entries",
    "#print axioms X011RelationLattice.diagonal_product",
    "end X011RelationLattice", "",
]
(HERE / "formal" / "HNFIndex.lean").write_text("\n".join(lines))
