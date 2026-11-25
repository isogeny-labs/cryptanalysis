"""Paired fresh-process census comparison including both launches and all output."""
import csv
from pathlib import Path
import resource
import subprocess
import sys
from time import perf_counter_ns

here = Path(__file__).resolve().parent
build = Path(sys.argv[1]).resolve()
expected = {89:(here.parent/"phases.csv").read_bytes(),211:(here/"phases.csv").read_bytes()}

def cpu():
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime+r.ru_stime

writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","bound","pairs_wall_ns","complete_wall_ns","pairs_cpu_s","complete_cpu_s"))
for block in range(8):
    for n in ((89,211) if block % 2 == 0 else (211,89)):
        c0 = cpu()
        t0 = perf_counter_ns()
        pairs = subprocess.check_output([build/f"pairs{n}"])
        t1 = perf_counter_ns()
        c1 = cpu()
        result = subprocess.check_output([build/f"masks{n}"],input=pairs)
        t2 = perf_counter_ns()
        c2 = cpu()
        if result != expected[n]:
            raise ValueError(f"phase output mismatch at {n}")
        writer.writerow((block,n,t1-t0,t2-t0,c1-c0,c2-c0))
