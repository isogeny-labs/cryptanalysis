#!/usr/bin/env python3
"""Tiny token-guarded control server for a RunPod GPU pod (no SSH needed).

PUT /bundle   upload a tar.xz; it is unpacked to /work/bundle and
              bash /work/bundle/research/clmad_audit_20261110/pod/run.sh starts
GET /status   JSON: state, exit code, log tail
GET /log      the run log
GET /results  /work/results.tar.xz
"""
import hashlib
import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ["TOKEN"]
WORK = "/work"
STATE = {"state": "idle", "exit": None, "bundle_sha256": None}
LOCK = threading.Lock()
RUN = os.environ.get("RUN_SCRIPT", "research/clmad_audit_20261110/pod/run.sh")


def _watch(proc):
    rc = proc.wait()
    with LOCK:
        STATE["state"] = "done"
        STATE["exit"] = rc


class H(BaseHTTPRequestHandler):
    def _ok(self, body, ctype="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        if self.headers.get("X-Token") != TOKEN:
            self.send_response(403)
            self.end_headers()
            return False
        return True

    def log_message(self, *a):
        pass

    def do_GET(self):
        if not self._auth():
            return
        if self.path == "/status":
            tail = ""
            try:
                with open(f"{WORK}/run.log", "rb") as f:
                    f.seek(0, 2)
                    f.seek(max(0, f.tell() - 1500))
                    tail = f.read().decode("utf-8", "replace")
            except OSError:
                pass
            with LOCK:
                d = dict(STATE)
            d["tail"] = tail
            self._ok(json.dumps(d).encode())
        elif self.path == "/log":
            try:
                self._ok(open(f"{WORK}/run.log", "rb").read(), "text/plain")
            except OSError:
                self.send_response(404)
                self.end_headers()
        elif self.path == "/results":
            try:
                self._ok(open(f"{WORK}/results.tar.xz", "rb").read(), "application/octet-stream")
            except OSError:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if not self._auth():
            return
        if self.path != "/bundle":
            self.send_response(404)
            self.end_headers()
            return
        n = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(n)
        sha = hashlib.sha256(data).hexdigest()
        with LOCK:
            if STATE["state"] != "idle":
                self.send_response(409)
                self.end_headers()
                return
            STATE["state"] = "running"
            STATE["bundle_sha256"] = sha
        os.makedirs(f"{WORK}/bundle", exist_ok=True)
        with open(f"{WORK}/bundle.tar.xz", "wb") as f:
            f.write(data)
        with open(f"{WORK}/bundle.sha256", "w") as f:
            f.write(sha + "\n")
        subprocess.run(["tar", "-xJf", f"{WORK}/bundle.tar.xz", "-C", f"{WORK}/bundle"], check=False)
        log = open(f"{WORK}/run.log", "ab")
        proc = subprocess.Popen(["bash", f"{WORK}/bundle/{RUN}"], stdout=log, stderr=subprocess.STDOUT,
                                cwd=f"{WORK}/bundle")
        threading.Thread(target=_watch, args=(proc,), daemon=True).start()
        self._ok(json.dumps({"ok": True, "sha256": sha}).encode())


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", 8888), H).serve_forever()
