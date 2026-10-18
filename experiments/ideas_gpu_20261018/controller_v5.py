#!/usr/bin/env python3
"""Use available community capacity under the same resource/price gates."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import controller_v4
controller = controller_v4.controller
podtool = controller.podtool
# Bypass only v3's older lifetime rewrite; keep v2's supported CUDA label.
api = controller_v4.controller_v3.api
def available_capacity(method, url, body=None, timeout=60):
    if method == "POST" and url == podtool.REST + "/pods":
        body = dict(body)
        body["cloudType"] = "COMMUNITY"
        body["dockerEntrypoint"] = ["/bin/bash", "-c"]
        body["dockerStartCmd"] = [controller_v4.START]
        body["env"] = {**body["env"], "POD_MAX_SECONDS": "6000"}
    return api(method, url, body, timeout)
podtool.api = available_capacity
if __name__ == "__main__":
    controller.main()
