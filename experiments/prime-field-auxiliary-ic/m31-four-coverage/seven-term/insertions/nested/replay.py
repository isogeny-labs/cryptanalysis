"""Replay the nested insertion schedule against the full-census reference CSV."""
import csv
import hashlib
import io
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
COMMIT = "95a72bb298f6aa80df983992cc7916339ec42a25"
PREFIX = "experiments/prime-field-auxiliary-ic/"


def archived(path):
    return subprocess.check_output(["git", "show", f"{COMMIT}:{PREFIX}{path}"], cwd=HERE)


def replay(binary):
    def counts(labels):
        # The reference CSV was generated with the full census in both orders.
        data = "".join(f"{x}\n" for x in reversed(labels))
        return tuple(int(subprocess.check_output([binary, mode], input=data, text=True))
                     for mode in ("simple-five", "overlap-3-4"))

    coords = archived("m31-basis-mask/coordinates.txt")
    if hashlib.sha256(coords).hexdigest() != "e7ddb831369de7724ca977022707d844512ccfe0191cb2c5daf5a22ad84a6203":
        raise ValueError("Frozen basis mismatch")
    outer = archived("m31-four-coverage/seven-term/insertions/counts.csv")
    outside = {int(row["x"]) for row in csv.DictReader(io.StringIO(outer.decode()))}
    core = [int(x) for x in coords.splitlines() if int(x) not in outside]
    if (len(core), len(outside)) != (74, 121):
        raise ValueError("Core partition mismatch")
    base, pending = core[:32], core[32:]
    rank, _ = counts(base)
    if rank != 1:
        raise ValueError("Expected one initial five-term class")
    proof = [(HERE / "Round.lean").read_text()]
    gains = []
    with (HERE / "rounds.csv").open() as stream:
        reference = csv.reader(stream)
        next(reference)
        while pending:
            five, overlap = counts(base)
            hits = []
            checks = []
            for x in pending:
                extended, observed = counts(base + [x])
                passed = extended > five or observed > overlap + 40 * five
                row = [len(base), five, overlap, x, extended, observed, int(passed)]
                if row != list(map(int, next(reference))):
                    raise ValueError(f"Mismatch for coordinate {x} at base size {len(base)}")
                if passed:
                    hits.append(x)
                checks.append(f"({extended}, {observed})")
            panel = f"panel{len(base)}"
            proof.append(f"def {panel} : List (Nat × Nat) := [{', '.join(checks)}]")
            predicate = f"fun v => decide (v.1 > {five} ∨ v.2 > {overlap} + 40 * {five})"
            proof.append(f"example : ({panel}.filter ({predicate})).length = {len(hits)} := by decide +kernel")
            gains.append(len(hits))
            rank += len(hits)
            # A stalled round admits the first pending coordinate for zero rank credit.
            added = hits or pending[:1]
            base.extend(added)
            pending = [x for x in pending if x not in added]
        if next(reference, None) is not None or rank != 41:
            raise ValueError("Incomplete nested replay")
    proof.append("example : 121 + 1 + " + " + ".join(map(str, gains)) + " = 162 := by decide")
    proof.append(f"""
example {{K I : Type*}} [Field K] (space : Submodule K (I → K)) [FiniteDimensional K space]
    (old : Fin {rank} → I → K) (pivot : Fin {len(outside)} → I)
    (indep : LinearIndependent K old) (inside : ∀ i, old i ∈ space)
    (prior : ∀ i j, old i (pivot j) = 0)
    (witness : ∀ i, ∃ v ∈ space, v (pivot i) ≠ 0 ∧ ∀ j, i ≠ j → v (pivot j) = 0) :
    162 ≤ Module.finrank K space :=
  M31Round.space_lower_bound old pivot space indep inside prior witness
""")
    subprocess.run(["lean", "-DwarningAsError=true", "--stdin"], input="\n".join(proof), text=True, check=True)
    print("Verified the nested census, round pass counts, and conditional combined bound of 162.")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "census.cpp"
        binary = Path(directory) / "census"
        source.write_bytes(archived("m31-four-coverage/census.cpp"))
        subprocess.run(["c++", "-std=c++17", "-O3", str(source), "-o", str(binary)], check=True)
        replay(binary)
