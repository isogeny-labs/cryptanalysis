#!/usr/bin/env python3
"""Thin orchestration over the repository RunPod helper; never save credentials."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "cloud"))
import runpod_pod as podtool

NAME = "ideas-20261018-ic-gpu"


def summary(pod):
    return {k: pod.get(k) for k in ("id", "name", "desiredStatus", "costPerHr",
            "vcpuCount", "memoryInGb", "publicIp", "portMappings", "imageName", "gpu")}


def main():
    mode = sys.argv[1]
    if mode == "up":
        if podtool.find(NAME):
            raise SystemExit("Dedicated name already exists; inspect instead of replacing")
        original = podtool.pod_body

        def constrained(args, keys, extra_env=None):
            body = original(args, keys, extra_env)
            body["allowedCudaVersions"] = ["13.3"]
            return body

        podtool.pod_body = constrained
        args = podtool.parse(["up", NAME, "--gpu",
            "NVIDIA RTX PRO 6000 Blackwell Server Edition", "--min-vcpu", "16",
            "--min-ram", "96", "--max-hours", "2", "--wait", "300", "--disk", "80"])
        try:
            pod = podtool.create(args)
            if float(pod.get("costPerHr") or 0) > 3.0:
                raise RuntimeError("New pod exceeds $3/hour guard; deleting")
            if int(pod.get("memoryInGb") or 0) < 96:
                raise RuntimeError("New pod has less than required 96GiB RAM; deleting")
            print(json.dumps({"status":"ready", "maximum_hours":2,
                              "pod":summary(pod)}),flush=True)
        except BaseException:
            pod = podtool.find(NAME)
            if pod:
                podtool.api("DELETE", f"{podtool.REST}/pods/{pod['id']}")
                print(json.dumps({"status":"creation_failed_and_deleted","id":pod['id']}),flush=True)
            raise
    elif mode == "status":
        pod = podtool.find(NAME)
        print(json.dumps({"pod": summary(pod) if pod else None}))
    elif mode == "down":
        pod = podtool.find(NAME)
        if pod:
            podtool.api("DELETE", f"{podtool.REST}/pods/{pod['id']}")
            print(json.dumps({"deleted":pod['id'],"name":NAME}))
        else:
            print(json.dumps({"status":"already_absent","name":NAME}))
    else:
        raise SystemExit("mode must be up/status/down")


if __name__ == "__main__":
    main()
