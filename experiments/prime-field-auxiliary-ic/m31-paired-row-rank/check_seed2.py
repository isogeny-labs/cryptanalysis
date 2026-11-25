"""Replay the frozen auxiliary seed-2 column witness with Lean 4.28.0."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLOB = "8a88f0454152910b4a73d9ad1157c4779b2aa10a"

# Zero-based row positions outside the witness. Lean checks the complement
# directly, so replay does not require the peeling algorithm that found it.
EXCLUDED = [
    2,3,4,6,7,9,13,17,21,24,25,27,28,34,39,41,42,44,46,50,59,74,76,80,
    81,86,87,88,91,94,97,98,100,102,103,107,108,112,114,117,120,130,133,
    136,140,142,145,147,153,154,155,164,165,173,175,176,178,182,191,197,
    204,210,212,213,216,224,227,233,238,244,245,253,254,257,261,262,263,
    270,274,276,279,282,294,296,298,299,302,303,306,308,311,316,318,320,
    321,324,325,330,332,336,340,341,345,347,349,350,352,353,354,356,358,
    359,360,365,368,374,377,378,380,382,384,391,393,394,397,401,403,404,
    407,410,412,418,419,420,422,426,430,431,452,456,459,
]

def main():
    log = subprocess.check_output(["git", "cat-file", "blob", BLOB], cwd=ROOT, text=True)
    rows = [json.loads(line)["codes"] for line in log.splitlines()]
    if any(type(c) is not int or not 0 <= c < 1000 for row in rows for c in row):
        raise ValueError("Expected signed codes for 500 columns")
    source = f"""
import Std
set_option maxRecDepth 100000
set_option maxHeartbeats 0
def rows : List (List Nat) := {rows}
def excluded : List Nat := {EXCLUDED}
def witness := (rows.zipIdx.filter (fun x => !excluded.contains x.2)).map Prod.fst
def columns := witness.flatten.foldl (init := ([] : List Nat)) (fun seen c => seen.insert (c / 2))
def coefficient (r : List Nat) (col : Nat) : Int :=
  (r.count (2 * col) : Int) - (r.count (2 * col + 1) : Int)
example : rows.length = 465 ∧ witness.length = 324 ∧ columns.length = 324 ∧
    columns.contains 49 ∧ columns.contains 96 ∧
    witness.all (fun r => coefficient r 49 == coefficient r 96) ∧
    witness.any (fun r => coefficient r 49 != 0) := by native_decide
"""
    subprocess.run(["lean", "+leanprover/lean4:v4.28.0", "--stdin"], input=source,
                   text=True, check=True)
    print(f"Lean verified the 324-row witness from Git blob {BLOB}.")

if __name__ == "__main__":
    main()
