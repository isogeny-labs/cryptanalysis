#!/usr/bin/env python3
"""One fixed public measurement on a newly owned high-memory pod."""
import hashlib
import json
import os
import secrets
import sys
import shlex
import subprocess
import tarfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
import controller

STUDY = Path(__file__).resolve().parent
TOOL = controller.podtool
MODE = sys.argv[1] if len(sys.argv) == 2 else ""
if MODE not in ("cpu", "gpu"):
    raise SystemExit("choose cpu or gpu")
NAME = "ideas-20261018-" + MODE + "-split-v2"
GPUS = ["NVIDIA GeForce RTX 5090", "NVIDIA GeForce RTX 4090",
        "NVIDIA RTX A6000", "NVIDIA RTX 6000 Ada Generation",
        "NVIDIA RTX PRO 6000 Blackwell Server Edition",
        "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
        "NVIDIA A100-SXM4-80GB", "NVIDIA A100 80GB PCIe"]


def main():
    if TOOL.find(NAME):
        raise SystemExit("Existing dedicated name: refusing replacement")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=STUDY, text=True).strip()
    packet = STUDY / "remote-payload-v5.tar.gz"
    digest = hashlib.sha256(packet.read_bytes()).hexdigest()
    source_url = "https://raw.githubusercontent.com/aburan28/cryptanalysis/" + commit + "/experiments/ideas_gpu_20261018/" + packet.name
    with urllib.request.urlopen(urllib.request.Request(source_url, headers={"User-Agent": "cryptanalysis-research/1.0"}), timeout=30) as response:
        if hashlib.sha256(response.read()).hexdigest() != digest:
            raise SystemExit("Unauthenticated public payload check failed")
    token = secrets.token_urlsafe(48)
    keyfile = Path("/tmp/ideas-split-v2-" + MODE + "-http-token")
    fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(token)
    startup = "\n".join([
        "set -eu", "mkdir -p /root/cryptanalysis", "cd /root/cryptanalysis",
        "curl --fail --location --retry 3 --output /tmp/ideas-payload.tar.gz " + shlex.quote(source_url),
        "printf '%s  %s\\n' " + shlex.quote(digest) + " /tmp/ideas-payload.tar.gz | sha256sum -c -",
        "tar -xzf /tmp/ideas-payload.tar.gz",
        ("exec python3 experiments/ideas_gpu_20261018/remote_http_cpu_v3.py" if MODE == "cpu" else "exec python3 experiments/ideas_gpu_20261018/remote_http_gpu_v3.py --out /root/cryptanalysis/experiments/ideas_gpu_20261018/remote/run-gpu-v3"), ""])
    outcome = {"schema": "ideas-split-outcome/v1", "mode": MODE, "source_commit": commit,
               "payload_sha256": digest, "started_unix": time.time(), "pod_id": None,
               "workflow_returncode": None, "results_fetched": False,
               "deleted": False, "absence_verified": False}
    deleted = threading.Event()
    owned = None
    try:
        for requested_ram in ([256] if MODE == "cpu" else [32]):
            body = {"name": NAME, "cloudType": "COMMUNITY", "computeType": "GPU",
                    "imageName": "runpod/base:1.0.2-ubuntu2404", "containerDiskInGb": 40,
                    "volumeInGb": 0, "ports": ["8888/http"],
                    "dockerEntrypoint": ["/bin/bash", "-c"], "dockerStartCmd": [startup],
                    "env": {"IDEAS_HTTP_BEARER": token}, "gpuTypeIds": GPUS,
                    "gpuTypePriority": "custom", "gpuCount": 1,
                    "minVCPUPerGPU": 16, "minRAMPerGPU": requested_ram,
                    "allowedCudaVersions": ["13.0"]}
            if MODE == "cpu":
                for key in ("gpuTypeIds", "gpuTypePriority", "gpuCount", "minVCPUPerGPU", "minRAMPerGPU", "allowedCudaVersions"):
                    body.pop(key, None)
                body.update(computeType="CPU", cloudType="SECURE", cpuFlavorIds=["cpu3m", "cpu5m"],
                            cpuFlavorPriority="custom", vcpuCount=32)
            try:
                pod = TOOL.api("POST", TOOL.REST + "/pods", body)
                owned = pod["id"]
                outcome["pod_id"] = owned
                outcome["requested_provider_ram_gb"] = requested_ram
                outcome["provider_resources"] = controller.summary(pod)
                break
            except SystemExit as error:
                outcome.setdefault("allocation_refusals", []).append({"ram_gb": requested_ram, "error": str(error)})
                # Ambiguous creation may still have allocated a resource.
                found = TOOL.find(NAME)
                if found:
                    owned = found["id"]
                    outcome["pod_id"] = owned
                    raise RuntimeError("Allocation response ambiguous; delete and retain evidence")
        if not owned:
            raise RuntimeError("No matching requested capacity; no pod allocated")
        if pod.get("costPerHr") is None or int(pod.get("vcpuCount") or 0) < 16 or float(pod.get("costPerHr") or 0) > (2.10 if MODE == "cpu" else 1.80) or int(pod.get("memoryInGb") or 0) < (192 if MODE == "cpu" else 32):
            raise RuntimeError("Provider price or resource guard refused allocated pod")

        def watchdog():
            if not deleted.wait(2700 if MODE == "cpu" else 3600):
                TOOL.api("DELETE", TOOL.REST + "/pods/" + owned)
                outcome["absolute_watchdog_deleted"] = True
        threading.Thread(target=watchdog, daemon=True).start()
        (STUDY / ("active-split-v2-" + MODE + "-pod.json")).write_text(json.dumps({"id": owned, "name": NAME, "started_unix": time.time(), "maximum_seconds": 2700 if MODE == "cpu" else 3600}) + "\n")
        print(json.dumps({"allocated": controller.summary(pod), "maximum_hours": 0.75 if MODE == "cpu" else 1.0}), flush=True)
        base = "https://" + owned + "-8888.proxy.runpod.net"

        def request(path, timeout=30):
            return urllib.request.urlopen(urllib.request.Request(base + path, headers={
                "User-Agent": "cryptanalysis-research/1.0", "Authorization": "Bearer " + token}), timeout=timeout)

        deadline = time.monotonic() + (2250 if MODE == "cpu" else 3000)
        notice = 0.0
        while time.monotonic() < deadline:
            try:
                with request("/status") as response:
                    status = json.load(response)
                (STUDY / ("http-job-status-" + MODE + "-v3.json")).write_text(json.dumps(status, indent=2) + "\n")
                if time.monotonic() - notice > 45:
                    print(json.dumps({"pod_id": owned, "job": status}), flush=True)
                    notice = time.monotonic()
                if status.get("done") and status.get("archive_error"):
                    raise RuntimeError("Archive creation failed: " + status["archive_error"])
                if status.get("done") and status.get("archive_ready"):
                    outcome["workflow_returncode"] = status["returncode"]
                    break
            except (urllib.error.URLError, TimeoutError, ValueError) as error:
                if time.monotonic() - notice > 45:
                    print(json.dumps({"pod_id": owned, "readiness": type(error).__name__}), flush=True)
                    notice = time.monotonic()
            time.sleep(10)
        else:
            raise RuntimeError("Fixed-job deadline exceeded")
        archive = STUDY / ("remote-" + MODE + "-v3.evidence.tar.gz")
        with request("/evidence.tar.gz", 180) as response, archive.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        outcome["evidence_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        if outcome["evidence_sha256"] != status["archive_sha256"]:
            raise RuntimeError("Retrieved evidence hash mismatch")
        with tarfile.open(archive) as tar:
            tar.extractall(STUDY, filter="data")
        outcome["results_fetched"] = True
        outcome["scientific_started"] = (STUDY / ("remote/run-" + MODE + "-v3/started.utc")).is_file()
    except BaseException as error:
        outcome["controller_error"] = str(error)
        raise
    finally:
        if owned:
            try:
                TOOL.api("DELETE", TOOL.REST + "/pods/" + owned)
                outcome["deleted"] = True
                for _ in range(6):
                    if not any(p.get("id") == owned and p.get("desiredStatus") != "TERMINATED" for p in TOOL.pods()):
                        outcome["absence_verified"] = True
                        deleted.set()
                        break
                    time.sleep(5)
            except BaseException as error:
                outcome["cleanup_error"] = str(error)
        outcome["finished_unix"] = time.time()
        (STUDY / ("resource-outcome-" + MODE + "-v3.json")).write_text(json.dumps(outcome, indent=2) + "\n")
        print(json.dumps({k: outcome[k] for k in ("pod_id", "workflow_returncode", "results_fetched", "deleted", "absence_verified")}), flush=True)


if __name__ == "__main__":
    main()
