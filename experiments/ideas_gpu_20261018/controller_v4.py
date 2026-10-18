#!/usr/bin/env python3
"""Explicit SSH bootstrap; preserve prior readiness failures unchanged."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import controller_v3
controller = controller_v3.controller
podtool = controller.podtool
original_parse = podtool.parse
def longer_readiness(argv):
    args = original_parse(argv)
    if hasattr(args, "wait"):
        args.wait = 600
    return args
podtool.parse = longer_readiness
api = podtool.api
START = r'''set -eu
mkdir -p /run/sshd /root/.ssh
chmod 700 /root/.ssh
printf '%s\n' "$PUBLIC_KEY" > /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
ssh-keygen -A
( sleep "$POD_MAX_SECONDS"
  kill -TERM 1
) >/tmp/ideas-lifetime.log 2>&1 &
exec /usr/sbin/sshd -D -e -o PermitRootLogin=prohibit-password -o PasswordAuthentication=no -o UsePAM=no
'''
def explicit_ssh(method, url, body=None, timeout=60):
    if method == "POST" and url == podtool.REST + "/pods":
        body = dict(body)
        body["dockerEntrypoint"] = ["/bin/bash", "-c"]
        body["dockerStartCmd"] = [START]
        body["env"] = {**body["env"], "POD_MAX_SECONDS": "6000"}
    return api(method, url, body, timeout)
podtool.api = explicit_ssh
if __name__ == "__main__":
    controller.main()
