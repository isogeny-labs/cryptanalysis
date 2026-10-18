#!/usr/bin/env python3
"""Bounded fixed-workload HTTP evidence adapter; no general command endpoint."""
import argparse
import hashlib
import hmac
import json
import os
import resource
import signal
import subprocess
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STUDY = Path(__file__).resolve().parent
TOKEN = os.environ.get("IDEAS_HTTP_BEARER", "")
if len(TOKEN) < 32:
    raise SystemExit("IDEAS_HTTP_BEARER must bind a fresh nonce of at least 32 characters")

parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path, default=STUDY / "remote" / "run-0")
parser.add_argument("--port", type=int, default=8888)
args = parser.parse_args()
OUT = args.out.resolve()
if (OUT / "started.utc").exists() or (OUT / "http-adapter-started.json").exists():
    raise SystemExit("Refusing an existing evidence run")
OUT.mkdir(parents=True, exist_ok=True)
ARCHIVE = OUT.parent / (OUT.name + ".evidence.tar.gz")
STATE = {"done": False, "returncode": None, "archive_ready": False,
         "started_unix": time.time(), "workload_timeout_seconds": 4500,
         "setup_timeout_seconds": 600, "stage": "setup", "challenge_solution_claimed": False}
LOCK = threading.Lock()
CHILD = None
stopping = threading.Event()

def snapshot():
    with LOCK:
        return dict(STATE)

def save_state():
    data = snapshot()
    temp = OUT / "http-adapter-state.json.tmp"
    temp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(temp, OUT / "http-adapter-state.json")

def eligible(path):
    relative = path.relative_to(OUT)
    if any(part in ("cuda", "build", "__pycache__") for part in relative.parts):
        return False
    if path.is_symlink() or not path.is_file() or path.suffix == ".tmp":
        return False
    # Binary research records/checkpoints are retained; compiled ELF programs
    # are reproducible from the local pinned source package and are excluded.
    with path.open("rb") as source:
        if source.read(4) == b"\x7fELF":
            return False
    return True

def archive_evidence():
    files = [path for path in sorted(OUT.rglob("*")) if eligible(path)]
    manifest = OUT / "http-evidence-files.sha256"
    with manifest.open("w") as output:
        for path in files:
            if path == manifest:
                continue
            digest = hashlib.sha256()
            with path.open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            output.write(digest.hexdigest() + "  " + path.relative_to(OUT).as_posix() + "\n")
    if manifest not in files:
        files.append(manifest)
    temporary = ARCHIVE.with_suffix(ARCHIVE.suffix + ".tmp")
    with tarfile.open(temporary, "w:gz", compresslevel=2) as archive:
        for path in files:
            archive.add(path, arcname="remote/" + OUT.name + "/" + path.relative_to(OUT).as_posix(), recursive=False)
    os.replace(temporary, ARCHIVE)
    digest = hashlib.sha256()
    with ARCHIVE.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    with LOCK:
        STATE.update(archive_ready=True, archive_bytes=ARCHIVE.stat().st_size,
                     archive_sha256=digest.hexdigest())

def run_workload():
    global CHILD
    command = ["timeout", "--signal=TERM", "--kill-after=60", "4500",
               "bash", str(STUDY / "remote_launch.sh"), str(OUT)]
    (OUT / "http-adapter-command.json").write_text(json.dumps(command) + "\n")
    setup_script = """set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq build-essential python3-pip unzip time jq util-linux ca-certificates
command -v pip >/dev/null || ln -s /usr/bin/pip3 /usr/local/bin/pip
"""
    setup_command = ["timeout", "--signal=TERM", "--kill-after=30", "600", "bash", "-c", setup_script]
    (OUT / "setup.command.json").write_text(json.dumps(setup_command) + "\n")
    try:
        # The bearer belongs to the adapter; the scientific subprocess never
        # receives the nonce or the provider's injected API key.
        environment = {key: value for key, value in os.environ.items()
                       if key not in ("IDEAS_HTTP_BEARER", "RUNPOD_API_KEY")}
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        started = time.monotonic()
        with (OUT / "setup.stdout").open("wb") as stdout, (OUT / "setup.stderr").open("wb") as stderr:
            CHILD = subprocess.Popen(setup_command, cwd=STUDY, env=environment,
                                     stdout=stdout, stderr=stderr, start_new_session=True)
            setup_result = CHILD.wait()
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        (OUT / "setup.exit").write_text(str(setup_result) + "\n")
        (OUT / "setup.resources.json").write_text(json.dumps({
            "source": "Python standard-library resource.getrusage; GNU time may be absent before setup",
            "elapsed_seconds": time.monotonic() - started,
            "user_seconds": after.ru_utime - before.ru_utime,
            "system_seconds": after.ru_stime - before.ru_stime,
            "max_rss_kib": after.ru_maxrss, "exit_status": setup_result}) + "\n")
        with LOCK:
            STATE.update(setup_returncode=setup_result, stage="workflow" if setup_result == 0 else "evidence")
        save_state()
        if setup_result != 0:
            with LOCK:
                STATE.update(returncode=setup_result, workflow_returncode=None)
            return
        with (OUT / "http-workflow.stdout").open("wb") as stdout, (OUT / "http-workflow.stderr").open("wb") as stderr:
            CHILD = subprocess.Popen(command, cwd=STUDY, env=environment,
                                     stdout=stdout, stderr=stderr, start_new_session=True)
            result = CHILD.wait()
        with LOCK:
            STATE.update(returncode=result, workflow_returncode=result)
    except BaseException as error:
        with LOCK:
            STATE.update(returncode=127, adapter_error=type(error).__name__)
    finally:
        with LOCK:
            STATE.update(stage="evidence", workflow_finished_unix=time.time())
        save_state()
        try:
            archive_evidence()
        except BaseException as error:
            with LOCK:
                STATE["archive_error"] = type(error).__name__
        # The archived state intentionally precedes archive self-metadata.
        # Final digest/readiness live in authenticated /status and this file.
        with LOCK:
            STATE.update(done=True, stage="complete", finished_unix=time.time())
        save_state()

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        pass  # Never log request headers, URLs or bearer material.

    def respond(self, code, content, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        supplied = self.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied, "Bearer " + TOKEN):
            self.respond(401, b'{"error":"unauthorized"}\n')
            return
        if self.path == "/status":
            self.respond(200, (json.dumps(snapshot()) + "\n").encode())
        elif self.path == "/evidence.tar.gz":
            state = snapshot()
            if not state.get("archive_ready"):
                self.respond(409, b'{"error":"evidence_not_ready"}\n')
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Length", str(ARCHIVE.stat().st_size))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-SHA256", state["archive_sha256"])
            self.end_headers()
            with ARCHIVE.open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    self.wfile.write(block)
        else:
            self.respond(404, b'{"error":"not_found"}\n')

def on_stop(_signal, _frame):
    stopping.set()
    child = CHILD
    if child is not None and child.poll() is None:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

signal.signal(signal.SIGTERM, on_stop)
signal.signal(signal.SIGINT, on_stop)
server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
server.timeout = 1
server.daemon_threads = True
(OUT / "http-adapter-started.json").write_text(json.dumps({
    "port": args.port, "fixed_workload": "remote_launch.sh", "authentication": "ephemeral_bearer",
    "arbitrary_execution": False, "tcp_forwarding": False}) + "\n")
save_state()
worker = threading.Thread(target=run_workload, daemon=False)
worker.start()
while not stopping.is_set() or worker.is_alive():
    server.handle_request()
server.server_close()
worker.join(timeout=65)
