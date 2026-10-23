#!/usr/bin/env python3
"""Turn a frozen manifest_<family>.json into the pod's run manifest: only paths, the
pinned CPU, the cgroup and the allocation identity change; cases, panels, expected
fields, expected result, repetitions and the measurement boundary stay as frozen.

    pod_manifest.py FROZEN OUT CPU CGROUP INSTANCE_ID RECEIPT"""
import json
import sys

frozen, out, cpu, cgroup, instance, receipt = sys.argv[1:7]
m = json.load(open(frozen))
root = "/root/wt"


def local(path):
    return f"{root}/{path.rsplit('/', 1)[1]}"


m["workdir"] = root
m["isolation"].update(cpus=cpu, execution_cpu=int(cpu), mem_nodes="0", cgroup=cgroup,
                      allocation={"provider": "runpod", "instance_id": instance, "receipt": receipt})
m["artifacts"] = [receipt] + [local(a) for a in m["artifacts"][1:]]
for case in m["cases"]:
    for arm in ("reference", "candidate"):
        case[arm] = [local(case[arm][0]), local(case[arm][1]), case[arm][2]]
json.dump(m, open(out, "w"), indent=1)
