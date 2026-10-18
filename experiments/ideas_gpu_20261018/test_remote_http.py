"""Synthetic end-to-end infrastructure gates; no scientific workload runs."""
import hashlib
import io
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="ideas-http-adapter-test-") as directory:
    root = Path(directory)
    shutil.copyfile(HERE / "remote_http.py", root / "remote_http.py")
    (root / "remote_launch.sh").write_text('''#!/bin/bash
set -eu
out=$1
test -z "${IDEAS_HTTP_BEARER:-}"
test -z "${RUNPOD_API_KEY:-}"
mkdir -p "$out/cuda" "$out/build"
printf 'excluded' > "$out/cuda/toolchain"
printf 'excluded' > "$out/build/object"
printf '\\177ELFexcluded' > "$out/executable"
printf 'fixture-record' > "$out/challenge.32"
printf '{"fixture":true}\\n' > "$out/result.json"
sleep 0.3
''')
    token = "synthetic-only-token-for-infrastructure-test-20261018"
    (root / "bin").mkdir()
    (root / "bin/timeout").write_text('''#!/bin/bash
if [[ "$2" == --kill-after=30 ]]; then exit 0; fi
exec /usr/bin/timeout "$@"
''')
    (root / "bin/timeout").chmod(0o755)
    env = dict(os.environ, IDEAS_HTTP_BEARER=token,
               RUNPOD_API_KEY="synthetic-provider-key-not-a-credential",
               PATH=str(root / "bin") + ":" + os.environ.get("PATH", "/usr/bin:/bin"))
    with socket.socket() as reserve:
        reserve.bind(("127.0.0.1", 0))
        port = reserve.getsockname()[1]
    child = subprocess.Popen([sys.executable, str(root / "remote_http.py"),
                              "--port", str(port)], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def get(path, auth=None):
        headers = {} if auth is None else {"Authorization": "Bearer " + auth}
        return opener.open(urllib.request.Request(f"http://127.0.0.1:{port}" + path, headers=headers), timeout=3)
    checks = []
    try:
        for _ in range(50):
            if (root / "remote/run-0/http-adapter-started.json").exists():
                break
            time.sleep(0.05)
        for auth in (None, "incorrect-synthetic-token"):
            try:
                get("/status", auth)
                raise AssertionError("missing/incorrect bearer was accepted")
            except urllib.error.HTTPError as error:
                assert error.code == 401
        checks.append("missing_and_wrong_bearers_rejected")
        try:
            get("/arbitrary-path", token)
            raise AssertionError("arbitrary route accepted")
        except urllib.error.HTTPError as error:
            assert error.code == 404
        checks.append("arbitrary_route_rejected")
        state = None
        for _ in range(100):
            with get("/status", token) as response:
                state = json.load(response)
            if state["archive_ready"]:
                break
            time.sleep(0.05)
        assert state["done"] and state["returncode"] == 0 and state["archive_ready"]
        checks.append("fixed_child_completed_without_inherited_credentials")
        with get("/evidence.tar.gz", token) as response:
            archive_bytes = response.read()
            assert response.headers["X-Content-SHA256"] == state["archive_sha256"]
        assert hashlib.sha256(archive_bytes).hexdigest() == state["archive_sha256"]
        checks.append("authenticated_archive_digest_matches")
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            members = archive.getnames()
            assert "remote/run-0/challenge.32" in members
            assert all("/cuda/" not in path and "/build/" not in path and not path.endswith("/executable") for path in members)
            checks.append("records_kept_toolchain_build_elf_excluded")
            for member in archive.getmembers():
                payload = archive.extractfile(member).read()
                assert token.encode() not in payload
                assert b"synthetic-provider-key-not-a-credential" not in payload
            checks.append("no_bearer_or_provider_key_in_archive")
            manifest = archive.extractfile("remote/run-0/http-evidence-files.sha256").read().decode()
            for line in manifest.splitlines():
                digest, path = line.split("  ", 1)
                assert hashlib.sha256(archive.extractfile("remote/run-0/" + path).read()).hexdigest() == digest
            checks.append("all_archived_file_manifest_hashes_match")
    finally:
        child.send_signal(signal.SIGTERM)
        stdout, stderr = child.communicate(timeout=10)
        assert token.encode() not in stdout + stderr
    checks.append("server_stops_and_does_not_log_bearer")
    print(json.dumps({"status": "passed", "synthetic_infrastructure_checks": checks,
                      "scientific_workloads_executed": 0, "provider_api_calls": 0}))
