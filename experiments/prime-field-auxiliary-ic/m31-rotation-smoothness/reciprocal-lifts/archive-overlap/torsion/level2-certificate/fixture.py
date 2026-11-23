"""Bind the eight pairs in Threshold.lean to the pinned public manifest."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

here = Path(__file__).resolve().parent
revision = "efb9330c1ee7e30743b7674f686cccb49f1cb25e"
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
raw = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=here)
assert hashlib.sha256(raw).hexdigest() == "a5fd508b6deacd2e2036a790946d7700929a822caf92e1fed699e6a7657fb9ca"
fixture = json.loads(raw)
p = fixture["public"]["p"]
first, second = fixture["auxiliary"]["maps"][:2]
assert first == {"r": 0, "A": 0, "B": 1} and second == {"r": 2, "A": 6, "B": 8}
shifted = {(x + pow(x, -1, p) - 2) % p for x in fixture["structured_roots"]}
pairs = sorted((u,v) for u in shifted if u < (v := 8 * pow(u,-1,p) % p))
assert {x for pair in pairs for x in pair} == shifted and len(pairs) == 8
source = (here / "Threshold.lean").read_text()
rows = re.findall(r"^  \| (\d+) => \((\d+), (\d+)\)$", source, re.M)
assert [(int(i), (int(u),int(v))) for i,u,v in rows] == list(enumerate(pairs))
print("Pinned fixture reproduces all eight indexed sibling pairs.")
