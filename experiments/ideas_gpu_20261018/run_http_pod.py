#!/usr/bin/env python3
"""Run one fixed published job through the documented pod HTTP proxy."""
import hashlib
import json
import os
import secrets
import shlex
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path
import controller

STUDY = Path(__file__).resolve().parent
POD_ID = "uf7o6868cpoxi7"
TOKEN_PATH = Path("/tmp/ideas-runpod-http-token")
BASE = "https://" + POD_ID + "-8888.proxy.runpod.net"


def main():
    tool = controller.podtool
    pod = tool.need(controller.NAME)
    if pod["id"] != POD_ID:
        raise SystemExit("Ownership check failed; refusing mutation")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=STUDY, text=True).strip()
    payload = STUDY / "remote-payload-v1.tar.gz"
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    resume = sys.argv[1:] == ["--resume"]
    if resume:
        token = TOKEN_PATH.read_text()
    else:
        token = secrets.token_urlsafe(48)
        fd = os.open(TOKEN_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as output:
            output.write(token)
    url = "https://raw.githubusercontent.com/aburan28/cryptanalysis/" + commit + "/experiments/ideas_gpu_20261018/remote-payload-v1.tar.gz"
    startup = "\n".join([
        "set -eu", "mkdir -p /root/cryptanalysis", "cd /root/cryptanalysis",
        "curl --fail --location --retry 3 --output /tmp/ideas-payload.tar.gz " + shlex.quote(url),
        "printf '%s  %s\\n' " + shlex.quote(digest) + " /tmp/ideas-payload.tar.gz | sha256sum -c -",
        "tar -xzf /tmp/ideas-payload.tar.gz",
        "exec python3 experiments/ideas_gpu_20261018/remote_http.py", ""])
    outcome = {"pod_id": POD_ID, "transport": "documented HTTP proxy", "source_commit": commit,
               "payload_sha256": digest, "started_unix": time.time(), "workflow_returncode": None,
               "results_fetched": False, "deleted": False, "absence_verified": False,
               "resumed_existing_job": resume}

    def request(path, timeout=30):
        return urllib.request.urlopen(urllib.request.Request(BASE + path,
            headers={"Authorization": "Bearer " + token,
                     "User-Agent": "cryptanalysis-research/1.0"}), timeout=timeout)

    try:
        if not resume:
            tool.api("PATCH", tool.REST + "/pods/" + POD_ID, {
                "ports": ["22/tcp", "8888/http"],
                "dockerEntrypoint": ["/bin/bash", "-c"], "dockerStartCmd": [startup],
                "env": {**pod.get("env", {}), "IDEAS_HTTP_BEARER": token}})
        deadline = time.monotonic() + 5100
        last_notice = 0.0
        while time.monotonic() < deadline:
            try:
                with request("/status") as response:
                    status = json.load(response)
                (STUDY / "http-job-status.json").write_text(json.dumps(status, indent=2) + "\n")
                if time.monotonic() - last_notice > 45:
                    print(json.dumps({"pod_id": POD_ID, "job": status}), flush=True)
                    last_notice = time.monotonic()
                if status.get("done") and status.get("archive_error"):
                    raise RuntimeError("Remote archive failed: " + status["archive_error"])
                if status.get("done") and status.get("archive_ready"):
                    outcome["workflow_returncode"] = status.get("returncode")
                    break
            except (urllib.error.URLError, TimeoutError, ValueError) as error:
                if time.monotonic() - last_notice > 45:
                    print(json.dumps({"pod_id": POD_ID, "http_readiness": type(error).__name__}), flush=True)
                    last_notice = time.monotonic()
            time.sleep(10)
        else:
            raise RuntimeError("HTTP job deadline exceeded")
        archive = STUDY / "remote-results.tar.gz"
        with request("/evidence.tar.gz", timeout=180) as response, archive.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        outcome["evidence_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        if outcome["evidence_sha256"] != status.get("archive_sha256"):
            raise RuntimeError("Retrieved evidence digest differs from authenticated status")
        with tarfile.open(archive) as tar:
            tar.extractall(STUDY, filter="data")
        outcome["results_fetched"] = (STUDY / "remote/run-0/started.utc").is_file()
    except BaseException as error:
        outcome["controller_error"] = str(error)
        raise
    finally:
        try:
            tool.api("DELETE", tool.REST + "/pods/" + POD_ID)
            outcome["deleted"] = True
            for _ in range(6):
                if not any(p.get("id") == POD_ID and p.get("desiredStatus") != "TERMINATED" for p in tool.pods()):
                    outcome["absence_verified"] = True
                    break
                time.sleep(5)
        except BaseException as error:
            outcome["cleanup_error"] = str(error)
        outcome["finished_unix"] = time.time()
        (STUDY / "resource-outcome.json").write_text(json.dumps(outcome, indent=2) + "\n")
        print(json.dumps({k: outcome[k] for k in ("workflow_returncode", "results_fetched", "deleted", "absence_verified")}), flush=True)


if __name__ == "__main__":
    main()
