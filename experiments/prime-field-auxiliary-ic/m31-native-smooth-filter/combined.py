"""Charge all setup from the original Python layer through the native filter."""
from pathlib import Path
import runpy
import csv
import sys
from time import perf_counter_ns,process_time_ns

here=Path(__file__).resolve().parent
g=runpy.run_path(str(here/"replay.py"))
prev,ns,fixture=g["prev"],g["ns"],g["fixture"]
writer=csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","arm","wall_ns","cpu_ns"))
for block in range(24):
    for arm in (("anchor","native") if block%2==0 else ("native","anchor")):
        if arm=="anchor":
            ns["_layer_walk"]=prev["ref"]["reference"]
            ns["_append_reciprocals"],ns["_check_sibling_fiber"]=prev["old_inv"],prev["old_check"]
            f=lambda:fixture["run"]("lift_trial")
        else:
            ns["_layer_walk"]=prev["ref"]["native"]
            ns["_append_reciprocals"],ns["_check_sibling_fiber"]=prev["reciprocals"],prev["fiber"]
            f=g["candidate"]
        wall,cpu=perf_counter_ns(),process_time_ns()
        pts=f()
        ct,wt=process_time_ns()-cpu,perf_counter_ns()-wall
        assert pts==fixture["reference"]
        writer.writerow((block,arm,wt,ct))
