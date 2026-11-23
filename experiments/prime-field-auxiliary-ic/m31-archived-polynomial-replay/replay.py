"""Run with Python 3.13, python-flint 0.9.0, sympy and system FLINT 3.6.0."""
from array import array
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter

here = Path(__file__).resolve().parent
rev = "7901d6529"
snapshot = "experiments/prime-field-auxiliary-ic/snapshot"
panel = "algebraic/structure_results/field31_s15"
def read(path):
    return subprocess.check_output(["git", "show", f"{rev}:{snapshot}/{path}"], cwd=here)

def words(values):
    return array("Q", map(int, values)).tobytes()

assert sys.byteorder == "little" and array("L").itemsize == 8
manifest = json.loads(read(f"{panel}/models.json"))
rows = sorted((r for r in json.loads(read(f"{panel}/runs.json")) if r["encoding"] == "chain"),
              key=lambda r:r["seed"])
assert [r["seed"] for r in rows] == list(range(16))
with tempfile.TemporaryDirectory() as temp:
    tmp = Path(temp)
    for name in ("prepare.py", "algebraic/resultant_solver.py"):
        (tmp/Path(name).name).write_bytes(read(name))
    sys.path.insert(0,str(tmp))
    from prepare import chain
    from resultant_solver import prepare, chain_resultant
    flags = subprocess.check_output(["pkg-config","--cflags","--libs","flint"],text=True).split()
    binary = tmp/"intersection"
    subprocess.run(["cc","-O3","-Wall","-Wextra","-Werror",str(here/"intersection.c"),
                    *flags,"-o",str(binary)],check=True)
    model = prepare(manifest["curve"],auxiliary=manifest["auxiliary"])
    coeffs = words(model.polynomial)
    assert hashlib.sha256(coeffs).hexdigest() == manifest["structured_membership_sha256"]
    roots = manifest["structured_roots"]
    data = bytearray(words(roots) + coeffs)
    setup = []
    for row in rows:
        times = {}
        for limit in ((0,len(roots)) if row["seed"]%2==0 else (len(roots),0)):
            start = perf_counter()
            aux, xs = chain(manifest["curve"]["p"],15,root_limit=limit)
            times[limit] = perf_counter()-start
            assert xs == roots[:limit] and aux["maps"] == manifest["auxiliary"]["maps"]
        setup.append(times)
        polynomial = chain_resultant(model,row["target"])
        raw = words(polynomial)
        assert len(raw)==8*65537 and hashlib.sha256(raw).hexdigest()==row["resultant_sha256"]
        data.extend(words([row["gcd_degree"]])+raw)
    output = subprocess.check_output([binary],input=data).decode()
    writer = csv.writer(sys.stdout,lineterminator="\n")
    writer.writerow(["seed","common_roots","gcd_s","tree_s","evaluation_s","map_only_s","full_roots_s"])
    for line in csv.reader(io.StringIO(output)):
        times=setup[int(line[0])]
        writer.writerow([*line,times[0],times[len(roots)]])
