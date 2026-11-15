#!/usr/bin/env python3
"""Provision one RunPod GPU pod, run the clmad audit bundle on it, fetch the
results, delete the pod.  Standard library only; RUNPOD_API_KEY from the
environment; the key is never written to disk.

  run_runpod.py --arm cuda13.4.3 --image nvidia/cuda:13.4.3-devel-ubuntu24.04 \
      --bundle bundle.tar.xz --out results/cuda13.4.3 [--gpu "NVIDIA GeForce RTX 5090" ...]
"""
import argparse
import base64
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request

API = "https://rest.runpod.io/v1"
KEY = os.environ.get("RUNPOD_API_KEY")
HERE = os.path.dirname(os.path.abspath(__file__))
# Cloudflare in front of the API answers 403/1010 to urllib's default agent.
UA = "clmad-audit/1 (+https://github.com/isogeny-labs/cryptanalysis)"


def api(method, path, body=None, timeout=60):
    req = urllib.request.Request(API + path, method=method,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                                          "User-Agent": UA})
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
        raw = r.read()
        return r.status, (json.loads(raw) if raw else None)


def proxy(pod_id, path, token, method="GET", data=None, timeout=60):
    url = f"https://{pod_id}-8888.proxy.runpod.net{path}"
    req = urllib.request.Request(url, method=method, data=data, headers={"X-Token": token, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def sanitized(pod):
    pod = dict(pod)
    pod.pop("env", None)
    pod.pop("dockerStartCmd", None)
    pod.pop("dockerEntrypoint", None)
    return pod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--gpu", action="append", default=None)
    ap.add_argument("--cloud", default="SECURE")
    ap.add_argument("--disk-gb", type=int, default=30)
    ap.add_argument("--boot-timeout", type=int, default=900)
    ap.add_argument("--run-timeout", type=int, default=3600)
    ap.add_argument("--keep", action="store_true", help="do not delete the pod at the end")
    ap.add_argument("--run-script", default="research/clmad_audit_20261110/pod/run.sh",
                    help="script inside the bundle that the pod runs")
    a = ap.parse_args()
    if not KEY:
        print("RUNPOD_API_KEY missing", file=sys.stderr)
        return 2
    gpus = a.gpu or ["NVIDIA GeForce RTX 5090", "NVIDIA RTX PRO 6000 Blackwell Server Edition",
                     "NVIDIA RTX PRO 6000 Blackwell Workstation Edition"]
    os.makedirs(a.out, exist_ok=True)
    token = secrets.token_urlsafe(24)
    server_b64 = base64.b64encode(open(os.path.join(HERE, "..", "pod", "server.py"), "rb").read()).decode()
    start = ("apt-get update -qq >/tmp/apt.log 2>&1; DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "
             "python3 xz-utils make g++ >>/tmp/apt.log 2>&1; mkdir -p /work; "
             f"echo {server_b64} | base64 -d > /work/server.py; exec python3 /work/server.py")
    body = {
        "name": f"clmad-audit-{a.arm}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "imageName": a.image,
        "cloudType": a.cloud,
        "computeType": "GPU",
        "gpuTypeIds": gpus,
        "gpuTypePriority": "availability",
        "gpuCount": 1,
        "containerDiskInGb": a.disk_gb,
        "volumeInGb": 0,
        "ports": ["8888/http"],
        "env": {"TOKEN": token, "RUN_SCRIPT": a.run_script},
        "dockerEntrypoint": [],
        "dockerStartCmd": ["bash", "-c", start],
        "interruptible": False,
    }
    t0 = time.time()
    try:
        st, pod = api("POST", "/pods", body)
    except urllib.error.HTTPError as e:
        print("create failed", e.code, e.read().decode()[:800], file=sys.stderr)
        return 3
    pod_id = pod["id"]
    print(f"pod {pod_id} created ({a.arm}, {a.cloud}); cost/hr {pod.get('costPerHr')}", flush=True)
    log = {"arm": a.arm, "image": a.image, "pod_id": pod_id, "created": pod, "events": []}

    def ev(msg):
        log["events"].append({"t": round(time.time() - t0, 1), "msg": msg})
        print(f"[{time.time() - t0:7.1f}s] {msg}", flush=True)

    rc = 1
    try:
        # boot: wait for the control server
        deadline = time.time() + a.boot_timeout
        ready = False
        while time.time() < deadline:
            try:
                st, p = api("GET", f"/pods/{pod_id}")
                log["last_pod"] = sanitized(p)
                if p.get("desiredStatus") not in (None, "RUNNING", "CREATED"):
                    ev(f"pod status {p.get('desiredStatus')}")
            except Exception as e:  # noqa: BLE001
                ev(f"pod poll error {e}")
            try:
                s, b = proxy(pod_id, "/status", token, timeout=20)
                if s == 200:
                    ready = True
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(15)
        if not ready:
            ev("control server never came up")
            return 4
        ev("control server up")
        data = open(a.bundle, "rb").read()
        s, b = proxy(pod_id, "/bundle", token, method="PUT", data=data, timeout=300)
        ev(f"bundle uploaded: {b.decode()[:200]}")
        deadline = time.time() + a.run_timeout
        last = ""
        while time.time() < deadline:
            time.sleep(30)
            try:
                s, b = proxy(pod_id, "/status", token, timeout=30)
                d = json.loads(b)
            except Exception as e:  # noqa: BLE001
                ev(f"status poll error {e}")
                continue
            tail = d.get("tail", "").strip().splitlines()
            if tail and tail[-1] != last:
                last = tail[-1]
                ev(f"pod: {last[:160]}")
            if d.get("state") == "done":
                ev(f"run finished, exit {d.get('exit')}")
                log["run_exit"] = d.get("exit")
                log["bundle_sha256_on_pod"] = d.get("bundle_sha256")
                break
        else:
            ev("run timed out")
        try:
            s, b = proxy(pod_id, "/log", token, timeout=60)
            open(os.path.join(a.out, "run.log"), "wb").write(b)
        except Exception as e:  # noqa: BLE001
            ev(f"log fetch failed {e}")
        try:
            s, b = proxy(pod_id, "/results", token, timeout=300)
            open(os.path.join(a.out, "results.tar.xz"), "wb").write(b)
            ev(f"results fetched: {len(b)} bytes")
            rc = 0
        except Exception as e:  # noqa: BLE001
            ev(f"results fetch failed {e}")
        try:
            st, p = api("GET", f"/pods/{pod_id}")
            log["final_pod"] = sanitized(p)
        except Exception:  # noqa: BLE001
            pass
    finally:
        if not a.keep:
            for i in range(5):
                try:
                    api("DELETE", f"/pods/{pod_id}")
                    ev("pod deleted")
                    break
                except Exception as e:  # noqa: BLE001
                    ev(f"delete attempt {i} failed {e}")
                    time.sleep(10)
        log["wall_s"] = round(time.time() - t0, 1)
        with open(os.path.join(a.out, "allocation.json"), "w") as f:
            json.dump(log, f, indent=1, default=str)
    return rc


if __name__ == "__main__":
    sys.exit(main())
