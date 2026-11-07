#!/usr/bin/env python3
"""Turn a frozen manifest_<family>.json into the GitHub Actions run manifest
(PROTOCOL-AMENDMENT-1.md). Only paths, the pinned CPU, the cgroup and the
allocation identity change; cases, panels, expected fields and result,
repetitions and the measurement boundary stay as frozen.

    gh_manifest.py FROZEN OUT --workdir W --bindir B --cpu N --instance-id ID --receipt R"""
import argparse
import json
import os
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("frozen")
ap.add_argument("out")
for a in ("--workdir", "--bindir", "--instance-id", "--receipt"):
    ap.add_argument(a, required=True)
ap.add_argument("--cpu", type=int, required=True)
a = ap.parse_args()
here = Path(__file__).resolve().parent
lines = Path("/proc/self/cgroup").read_text().splitlines()
v2 = [l.split(":", 2)[2] for l in lines if l.startswith("0::")]
cgroup = "/sys/fs/cgroup" + (v2[0] if v2 and v2[0] != "/" else "")
if not os.path.isdir(cgroup):
    cgroup = "/sys/fs/cgroup"
m = json.load(open(a.frozen))
m["workdir"] = a.workdir
m["isolation"].update(cpus=str(a.cpu), execution_cpu=a.cpu, mem_nodes="0", cgroup=cgroup,
                      allocation={"provider": "github_actions", "instance_id": a.instance_id, "receipt": a.receipt})
m["artifacts"] = [a.receipt] + [str(here / Path(p).name) for p in m["artifacts"][1:]]
for case in m["cases"]:
    for arm in ("reference", "candidate"):
        case[arm] = [str(Path(a.bindir) / Path(case[arm][0]).name), str(here / Path(case[arm][1]).name), case[arm][2]]
json.dump(m, open(a.out, "w"), indent=1)
print(json.dumps({"cgroup": cgroup, "cpu": a.cpu}))
