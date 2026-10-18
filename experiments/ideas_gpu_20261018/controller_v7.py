#!/usr/bin/env python3
"""Direct final request avoids obsolete nested-provider rewrites."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import controller
import controller_v4
podtool = controller.podtool
# Imported adapters modify the shared module; use the original API directly.
raw_api = controller_v4.controller_v3.controller_v2.api
original_ssh = controller_v4.controller_v3.ssh_args
def private_ssh(pod):
    args = original_ssh(pod)
    return [args[0], "-F", "/tmp/ideas-ssh-config", *args[1:]]
podtool.ssh_args = private_ssh
START = controller_v4.START.replace("-o UsePAM=no", "-o UsePAM=yes -o KbdInteractiveAuthentication=no")
def final_request(method, url, body=None, timeout=60):
    if method == "POST" and url == podtool.REST + "/pods":
        body = dict(body)
        body.update(cloudType="COMMUNITY", dockerEntrypoint=["/bin/bash", "-c"],
                    dockerStartCmd=[START],
                    allowedCudaVersions=["13.0", "12.9", "12.8", "12.7", "12.6"],
                    gpuTypeIds=["NVIDIA RTX PRO 6000 Blackwell Server Edition",
                                "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
                                "NVIDIA GeForce RTX 5090", "NVIDIA A100-SXM4-80GB",
                                "NVIDIA A100 80GB PCIe", "NVIDIA H100 PCIe"])
        body["env"] = {**body["env"], "POD_MAX_SECONDS": "6000"}
    return raw_api(method, url, body, timeout)
podtool.api = final_request
if __name__ == "__main__":
    controller.main()
