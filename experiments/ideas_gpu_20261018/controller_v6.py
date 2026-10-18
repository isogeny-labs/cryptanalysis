#!/usr/bin/env python3
"""Resource-equivalent native-compatible GPU alternatives, with price gate."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import controller_v5
controller = controller_v5.controller
podtool = controller.podtool
api = podtool.api
def equivalent_capacity(method, url, body=None, timeout=60):
    if method == "POST" and url == podtool.REST + "/pods":
        body = dict(body)
        body["gpuTypeIds"] = [
            "NVIDIA RTX PRO 6000 Blackwell Server Edition",
            "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
            "NVIDIA GeForce RTX 5090", "NVIDIA A100-SXM4-80GB",
            "NVIDIA A100 80GB PCIe", "NVIDIA H100 PCIe"]
        body["allowedCudaVersions"] = ["13.0", "12.9", "12.8", "12.7", "12.6"]
        return controller_v5.api(method, url, {
            **body, "cloudType": "COMMUNITY",
            "dockerEntrypoint": ["/bin/bash", "-c"],
            "dockerStartCmd": [controller_v5.controller_v4.START],
            "env": {**body["env"], "POD_MAX_SECONDS": "6000"}}, timeout)
    return api(method, url, body, timeout)
podtool.api = equivalent_capacity
if __name__ == "__main__":
    controller.main()
