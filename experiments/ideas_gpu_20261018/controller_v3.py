#!/usr/bin/env python3
"""Use a private ownership-correct copy of the unchanged system SSH policy."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import controller_v2
controller = controller_v2.controller
ssh_args = controller.podtool.ssh_args
def private_config_args(pod):
    args = ssh_args(pod)
    return [args[0],"-F","/tmp/ideas-ssh-config",*args[1:]]
controller.podtool.ssh_args = private_config_args
api = controller.podtool.api
def remaining_lifetime(method,url,body=None,timeout=60):
    if method == "POST" and url == controller.podtool.REST + "/pods":
        body = dict(body)
        body["env"] = {**body["env"], "POD_MAX_SECONDS":"6840"}
    return api(method,url,body,timeout)
controller.podtool.api = remaining_lifetime
if __name__ == "__main__":
    controller.main()
