"""Split the 821 exact Lean equalities into independently checked modules."""

import ast
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
source = (HERE / "QuadraticRank.lean").read_text()


def declaration(name):
    match = re.search(r"^def " + name + r" : Array Nat := #\[(.+)\]$", source, re.M)
    assert match, name
    return ast.literal_eval("[" + match.group(1) + "]")


chunks = []
for name in ("X", "Inverse"):
    rows = declaration("rows" + name)
    witnesses = declaration("witnesses" + name)
    assert len(rows) == len(witnesses) == 821
    for number in range(math.ceil(821 / 32)):
        start = number * 32
        count = min(32, 821 - start)
        filename = f"QuadraticChunk_{name}_{number:02d}.lean"
        text = f'''import Std
set_option maxRecDepth 4096
set_option maxHeartbeats 0

namespace QuadraticChunk{name}{number:02d}

def rows : Array Nat := #[{', '.join(map(str, rows))}]
def witnesses : Array Nat := #[{', '.join(map(str, witnesses))}]
def xorSelected (mask : Nat) : Nat :=
  (List.range rows.size).foldl
    (fun acc index => if mask.testBit index then Nat.xor acc rows[index]! else acc) 0

theorem certificate : ∀ bit : Fin {count},
    xorSelected witnesses[bit.val + {start}]! = 2 ^ (bit.val + {start}) := by decide

#print axioms QuadraticChunk{name}{number:02d}.certificate

end QuadraticChunk{name}{number:02d}
'''
        with (HERE / filename).open("x") as stream:
            stream.write(text)
        chunks.append({"name": filename, "coordinate": name,
                       "start": start, "count": count,
                       "sha256": hashlib.sha256(text.encode()).hexdigest()})

assert sum(row["count"] for row in chunks) == 1642
output = {"status": "FROZEN_N41_QUADRATIC_LEAN_CHUNK_PLAN", "candidate_id": None,
          "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
          "chunks": chunks}
with (HERE / "chunk_plan.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], len(chunks))
