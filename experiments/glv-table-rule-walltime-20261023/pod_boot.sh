#!/bin/bash
# Runs once on the rented Runpod CPU pod (POD_BOOT_B64 in its environment); no SSH is used.
#  1. serves /root/out on port 8000 and accepts one PUT /payload whose sha256 equals
#     $PAYLOAD_SHA256, fixed in the pod's environment when the pod was created;
#  2. writes the allocation receipt from the pod's own Runpod identity (no API key in it);
#  3. runs scripts/isolated_bench.py `run` (Tier 1) on both frozen manifests, pinned to
#     the last CPU the pod exposes, then publishes the result tree and DONE.
set -u
mkdir -p /root/wt /root/out
exec >>/root/out/boot.log 2>&1
echo "boot $(date -u +%FT%TZ) pod=${RUNPOD_POD_ID:-?}"
cat >/root/srv.py <<'EOF'
import hashlib, http.server, os
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory="/root/out", **k)
    def do_PUT(self):
        target = "/root/wt/payload.tgz"
        if self.path != "/payload" or os.path.exists(target):
            self.send_response(403); self.end_headers(); return
        data = self.rfile.read(int(self.headers["Content-Length"]))
        if hashlib.sha256(data).hexdigest() != os.environ["PAYLOAD_SHA256"]:
            self.send_response(400); self.end_headers(); return
        with open(target + ".part", "wb") as fh:
            fh.write(data)
        os.rename(target + ".part", target)
        self.send_response(201); self.end_headers()
http.server.ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
EOF
python3 /root/srv.py >>/root/out/srv.log 2>&1 &
until [ -f /root/wt/payload.tgz ]; do sleep 5; done
cd /root/wt && tar -xzf payload.tgz && echo "payload unpacked: $(ls | tr '\n' ' ')"
python3 - <<'EOF'
import json, os
env = {k: v for k, v in os.environ.items() if k.startswith("RUNPOD_") and not any(s in k for s in ("KEY", "TOKEN", "SECRET"))}
receipt = {"provider": "runpod", "instance_id": os.environ["RUNPOD_POD_ID"], "pod_environment": env,
           "note": "written on the pod from its own RUNPOD_* identity variables; API keys excluded"}
json.dump(receipt, open("/root/wt/allocation.json", "w"), indent=1, sort_keys=True)
EOF
CPU=$(python3 -c "import os; print(max(os.sched_getaffinity(0)))")
CG=$(python3 -c "
p = open('/proc/self/cgroup').read().splitlines()
v2 = [l.split(':', 2)[2] for l in p if l.startswith('0::')]
print('/sys/fs/cgroup' + (v2[0] if v2 and v2[0] != '/' else ''))")
echo "execution cpu $CPU cgroup $CG"
python3 /root/wt/isolated_bench.py probe-host >/root/out/probe-host.json 2>&1
for fam in j1728 j0; do
  python3 /root/wt/pod_manifest.py /root/wt/manifest_$fam.json /root/wt/pod_manifest_$fam.json "$CPU" "$CG" "${RUNPOD_POD_ID}" /root/wt/allocation.json
  python3 /root/wt/isolated_bench.py --queue-root /root/wt/q probe /root/wt/pod_manifest_$fam.json >/root/out/probe_$fam.json 2>&1
  echo "run $fam $(date -u +%T)"
  python3 /root/wt/isolated_bench.py --queue-root /root/wt/q run /root/wt/pod_manifest_$fam.json >/root/out/run_$fam.json 2>&1
  echo "run $fam exit $? $(date -u +%T)"
done
cp /root/wt/allocation.json /root/wt/pod_manifest_*.json /root/out/
tar -C /root/wt -czf /root/out/results.tgz q
date -u +%FT%TZ >/root/out/DONE
echo "done"
