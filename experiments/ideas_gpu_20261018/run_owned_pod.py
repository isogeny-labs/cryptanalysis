#!/usr/bin/env python3
"""Ship the frozen native package, retain results, delete only our own pod."""
import json
import shlex
import subprocess
import sys
import tarfile
import time
from pathlib import Path
import controller_v3

control = controller_v3.controller
podtool = control.podtool
STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[1]
REMOTE_ROOT = "/root/cryptanalysis"
REMOTE_STUDY = REMOTE_ROOT + "/experiments/ideas_gpu_20261018"
REMOTE_OUT = REMOTE_STUDY + "/remote/run-0"
EXPECTED_ID = "qy31gqnna1aasz"


def run_ssh(pod, script, **kwargs):
    return subprocess.run([*podtool.ssh_args(pod), "bash -c " + shlex.quote(script)], **kwargs)


def fetch(pod):
    archive = STUDY / "remote-results.tar.gz"
    with archive.open("wb") as output:
        result = run_ssh(pod, "tar -czf - -C " + shlex.quote(REMOTE_STUDY) + " remote/run-0",
                         stdout=output, stderr=subprocess.PIPE, timeout=180)
    (STUDY / "fetch.stderr").write_bytes(result.stderr)
    if result.returncode:
        return False
    with tarfile.open(archive) as tar:
        tar.extractall(STUDY, filter="data")
    return (STUDY / "remote/run-0/started.utc").is_file()


def main():
    pod = podtool.need(control.NAME)
    if pod["id"] != EXPECTED_ID:
        raise SystemExit("Refusing to run or delete a pod other than the recorded replacement")
    outcome = {"pod":control.summary(pod),"started_unix":time.time(),
               "workflow_returncode":None,"results_fetched":False,"deleted":False}
    try:
        with (STUDY / "setup.stdout").open("wb") as out, (STUDY / "setup.stderr").open("wb") as err:
            setup = run_ssh(pod, """set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq build-essential python3-pip unzip time jq util-linux ca-certificates
command -v pip >/dev/null || ln -s /usr/bin/pip3 /usr/local/bin/pip
mkdir -p /root/cryptanalysis
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
if test -n "${RUNPOD_API_KEY:-}"; then printf 'pod-scoped-stop-key-present\\n'; else printf 'pod-scoped-stop-key-absent\\n'; fi
""", stdout=out, stderr=err, timeout=600)
        if setup.returncode:
            raise RuntimeError("Remote prerequisite installation failed; see preserved setup logs")
        payload = STUDY / "payload.tar.gz"
        with tarfile.open(payload,"w:gz") as tar:
            for path in sorted(STUDY.rglob("*")):
                relative=path.relative_to(STUDY)
                if not path.is_file() or any(p in relative.parts for p in ("__pycache__","remote","local_checks","reports")):
                    continue
                if len(relative.parts)==1 and (path.name in ("payload.tar.gz","remote-results.tar.gz")
                        or path.suffix in (".stdout", ".stderr") or path.name.startswith("provision")):
                    continue
                tar.add(path,arcname="experiments/ideas_gpu_20261018/"+relative.as_posix(),recursive=False)
        with payload.open("rb") as source, (STUDY / "ship.stdout").open("wb") as out, (STUDY / "ship.stderr").open("wb") as err:
            shipped=run_ssh(pod,"tar -xzf - -C /root/cryptanalysis",stdin=source,stdout=out,stderr=err,timeout=180)
        if shipped.returncode:
            raise RuntimeError("Payload transfer failed")
        command = "timeout --signal=TERM --kill-after=60 4500 bash " + shlex.quote(REMOTE_STUDY+"/remote_launch.sh") + " " + shlex.quote(REMOTE_OUT)
        with (STUDY / "remote-workflow.stdout").open("wb") as out, (STUDY / "remote-workflow.stderr").open("wb") as err:
            result=run_ssh(pod,command,stdout=out,stderr=err,timeout=4620)
        outcome["workflow_returncode"]=result.returncode
    except BaseException as error:
        outcome["controller_error"]=str(error)
        raise
    finally:
        try:
            for _ in range(2):
                if fetch(pod):
                    outcome["results_fetched"]=True
                    break
        except BaseException as error:
            outcome["fetch_error"]=str(error)
        try:
            podtool.api("DELETE",f"{podtool.REST}/pods/{EXPECTED_ID}")
            outcome["deleted"]=True
        except BaseException as error:
            outcome["deletion_error"]=str(error)
        outcome["finished_unix"]=time.time()
        (STUDY/"resource-outcome.json").write_text(json.dumps(outcome,indent=2)+"\n")
        print(json.dumps({k:outcome[k] for k in ("workflow_returncode","results_fetched","deleted")}),flush=True)


if __name__=="__main__":
    main()
