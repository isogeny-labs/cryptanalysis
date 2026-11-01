#!/usr/bin/env python3
"""Authenticated, GET-only result adapter for one Runpod batch command.

The controller starts this module only after checking out the exact public
source commit. The service exposes status and fixed, hash-bound result chunks;
it has no command, upload, filesystem, or directory-listing endpoint. The
Runpod API key and service bearer are removed from the scientific child.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import signal
import subprocess
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


STATUS_SCHEMA = "runpod.http-batch.status/v1"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
JOB_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,120}\Z")
CHUNK_PATH = re.compile(r"/v1/result/([0-9]{6})\Z")
SECRET_ENV_NAMES = {
    "RUNPOD_API_KEY", "RUNPOD_BATCH_TOKEN", "RUNPOD_SSH_PRIVATE_KEY",
    "RUNPOD_SSH_KEY", "GITHUB_TOKEN", "CURSOR_API_KEY", "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "ARTIFACTS_AWS_ACCESS_KEY_ID",
    "ARTIFACTS_AWS_SECRET_ACCESS_KEY",
}
MAX_ARCHIVE_MEMBERS = 100_000
MAX_MANIFEST_BYTES = 16 << 20
MAX_METADATA_BYTES = 64 << 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def decode_text(name: str, maximum: int) -> str:
    encoded = os.environ.pop(name, "")
    if not encoded or len(encoded) > maximum * 2:
        raise ValueError(f"invalid {name} envelope")
    try:
        data = base64.b64decode(encoded, validate=True)
        text = data.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError(f"invalid {name} encoding") from error
    if not text or len(data) > maximum or "\x00" in text:
        raise ValueError(f"invalid {name} contents")
    return text


def safe_relative(name: str) -> bool:
    path = PurePosixPath(name)
    return (bool(name) and name != "." and path.as_posix() == name
            and not path.is_absolute() and ".." not in path.parts
            and ".git" not in path.parts and "\n" not in name and "\x00" not in name)


def read_config(repo: Path) -> dict:
    token = os.environ.pop("RUNPOD_BATCH_TOKEN", "")
    if len(token) < 43:
        raise ValueError("RUNPOD_BATCH_TOKEN must carry at least 256 random bits")
    job_id = os.environ.pop("RUNPOD_BATCH_JOB_ID", "")
    commit = os.environ.pop("RUNPOD_BATCH_SOURCE_COMMIT", "")
    tree = os.environ.pop("RUNPOD_BATCH_SOURCE_TREE", "")
    source_archive = os.environ.pop("RUNPOD_BATCH_SOURCE_ARCHIVE_SHA256", "")
    command_sha = os.environ.pop("RUNPOD_BATCH_COMMAND_SHA256", "")
    if (not JOB_ID.fullmatch(job_id) or not COMMIT.fullmatch(commit)
            or not re.fullmatch(r"[0-9a-f]{40,64}", tree)
            or not SHA256.fullmatch(source_archive)):
        raise ValueError("invalid source/job identity")
    command = decode_text("RUNPOD_BATCH_COMMAND_B64", 1 << 20)
    bootstrap = decode_text("RUNPOD_BATCH_BOOTSTRAP_B64", 1 << 20)
    if (hashlib.sha256(command.encode()).hexdigest() != command_sha
            or not SHA256.fullmatch(command_sha)):
        raise ValueError("command digest mismatch")
    outputs = json.loads(decode_text("RUNPOD_BATCH_OUTPUTS_B64", 1 << 20))
    if (not isinstance(outputs, list) or not outputs or len(set(outputs)) != len(outputs)
            or any(not isinstance(path, str) or not safe_relative(path)
                   or path.startswith(".runpod-batch") or path.startswith("-")
                   for path in outputs)):
        raise ValueError("invalid output paths")
    timeout = int(os.environ.pop("RUNPOD_BATCH_TIMEOUT_SECONDS", "0"))
    chunk_bytes = int(os.environ.pop("RUNPOD_BATCH_CHUNK_BYTES", "0"))
    max_result = int(os.environ.pop("RUNPOD_BATCH_MAX_RESULT_BYTES", "0"))
    if timeout < 1 or not 1 << 20 <= chunk_bytes <= 16 << 20 or max_result < 1:
        raise ValueError("invalid timeout/result limits")
    actual_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    actual_tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=repo,
        capture_output=True, text=True, check=True
    ).stdout.strip()
    if (actual_commit, actual_tree) != (commit, tree):
        raise ValueError("checked-out source identity mismatch")
    return {
        "token": token, "job_id": job_id, "commit": commit, "tree": tree,
        "source_archive_sha256": source_archive,
        "command": command, "command_sha256": command_sha, "bootstrap": bootstrap,
        "outputs": outputs, "timeout": timeout, "chunk_bytes": chunk_bytes,
        "max_result_bytes": max_result,
    }


def scrubbed_environment() -> dict[str, str]:
    """Environment for scientific code; provider and transport secrets never cross."""
    return {
        key: value for key, value in os.environ.items()
        if key not in SECRET_ENV_NAMES and not key.startswith("RUNPOD_BATCH_")
        and not key.startswith("ARTIFACTS_AWS_")
    }


def hardware() -> dict:
    try:
        query = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,uuid,driver_version,compute_cap,memory.total",
             "--format=csv,noheader,nounits"], capture_output=True, text=True,
            check=False, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        query = None
    gpus = []
    if query is not None and query.returncode == 0:
        for line in query.stdout.splitlines():
            fields = [part.strip() for part in line.split(",")]
            if len(fields) == 5:
                gpus.append(dict(zip(
                    ("name", "uuid", "driver", "compute_capability", "memory_mib"), fields)))
    try:
        nvcc = subprocess.run(
            ["bash", "-lc", "command -v nvcc >/dev/null && nvcc --version || true"],
            capture_output=True, text=True, check=False, timeout=15).stdout[-2000:]
    except (OSError, subprocess.TimeoutExpired):
        nvcc = ""
    return {"pod_id": os.environ.get("RUNPOD_POD_ID"), "gpus": gpus, "nvcc": nvcc}


class HashingReader:
    def __init__(self, source):
        self.source = source
        self.digest = hashlib.sha256()

    def read(self, size=-1):
        data = self.source.read(size)
        self.digest.update(data)
        return data


def clean_tar_info(member: tarfile.TarInfo) -> tarfile.TarInfo:
    info = tarfile.TarInfo(member.name)
    info.size = member.size
    info.mode = (member.mode & 0o700) or 0o600
    info.mtime = int(member.mtime or time.time())
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def add_path(archive: tarfile.TarFile, path: Path, name: str) -> tuple[str, int]:
    info = tarfile.TarInfo(name)
    info.size = path.stat().st_size
    info.mode = (path.stat().st_mode & 0o700) or 0o600
    info.mtime = int(path.stat().st_mtime)
    info.uid = info.gid = 0
    with path.open("rb") as source:
        reader = HashingReader(source)
        archive.addfile(info, reader)
    return reader.digest.hexdigest(), info.size


def build_result_archive(job_dir: Path, destination: Path, source: dict, maximum: int) -> dict:
    """Repack job_runner outputs with its log/status and an exact file manifest."""
    inner = job_dir / "out.tar.gz"
    if not inner.exists():
        with tarfile.open(inner, "w:gz"):
            pass
    source_path = job_dir / "source.json"
    atomic_json(source_path, source)
    job_status = job_dir / "status.json"
    if not job_status.exists():
        atomic_json(job_status, {"returncode": source["returncode"], "status_missing": True})
    job_log = job_dir / "log.txt"
    if not job_log.exists():
        job_log.write_text("job runner produced no log\n")

    temp = destination.with_name(destination.name + ".tmp")
    manifest: list[tuple[str, str]] = []
    total = 0
    seen: set[str] = set()
    with tarfile.open(temp, "x:gz", compresslevel=2) as output, tarfile.open(inner, "r:gz") as inputs:
        input_members = inputs.getmembers()
        if len(input_members) > MAX_ARCHIVE_MEMBERS:
            raise ValueError("job output archive contains too many members")
        for member in sorted(input_members, key=lambda item: item.name):
            if (member.name in seen or not member.isfile() or not safe_relative(member.name)
                    or member.name.startswith(".runpod-batch/")):
                raise ValueError("unsafe or duplicate job output archive member")
            seen.add(member.name)
            total += member.size
            if total > maximum:
                raise ValueError("job outputs exceed configured uncompressed limit")
            source_file = inputs.extractfile(member)
            if source_file is None:
                raise ValueError("unreadable job output archive member")
            reader = HashingReader(source_file)
            output.addfile(clean_tar_info(member), reader)
            manifest.append((reader.digest.hexdigest(), member.name))
        for path, name in (
            (job_log, ".runpod-batch/log.txt"),
            (job_status, ".runpod-batch/job-status.json"),
            (source_path, ".runpod-batch/source.json"),
        ):
            size = path.stat().st_size
            if size > MAX_METADATA_BYTES or total + size > maximum:
                raise ValueError("job evidence exceeds configured size limit")
            digest, size = add_path(output, path, name)
            total += size
            manifest.append((digest, name))
        manifest_bytes = "".join(
            f"{digest}  {name}\n" for digest, name in manifest).encode()
        if len(manifest_bytes) > MAX_MANIFEST_BYTES or total + len(manifest_bytes) > maximum:
            raise ValueError("job evidence manifest exceeds configured size limit")
        info = tarfile.TarInfo(".runpod-batch/files.sha256")
        info.size = len(manifest_bytes)
        info.mode = 0o600
        info.mtime = int(time.time())
        output.addfile(info, io.BytesIO(manifest_bytes))
    os.replace(temp, destination)
    return {
        "sha256": sha256_file(destination), "bytes": destination.stat().st_size,
        "uncompressed_bytes": total + len(manifest_bytes),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "files": len(manifest) + 1,
    }


def chunk_manifest(path: Path, chunk_bytes: int) -> list[dict]:
    chunks = []
    with path.open("rb") as source:
        index = offset = 0
        while data := source.read(chunk_bytes):
            chunks.append({
                "index": index, "path": f"/v1/result/{index:06d}", "offset": offset,
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            })
            index += 1
            offset += len(data)
    return chunks


class State:
    def __init__(self, path: Path, initial: dict):
        self.path = path
        self.lock = threading.Lock()
        self.value = initial
        atomic_json(path, initial)

    def snapshot(self) -> dict:
        with self.lock:
            return json.loads(json.dumps(self.value))

    def update(self, **values) -> None:
        with self.lock:
            self.value.update(values)
            atomic_json(self.path, self.value)


def run_job(repo: Path, job_dir: Path, result: Path, config: dict,
            state: State, child_holder: dict) -> None:
    environment = scrubbed_environment()
    payload = config["bootstrap"] + "\n" + config["command"]
    timed_command = " ".join(shlex.quote(part) for part in (
        "timeout", "--signal=TERM", "--kill-after=30", str(config["timeout"]),
        "bash", "-c", payload))
    environment.update({
        "JOB_ID": config["job_id"], "JOB_DIR": str(job_dir),
        "JOB_WORKDIR": str(repo),
        "JOB_CMD": timed_command,
        "JOB_OUTS": "\n".join(config["outputs"]), "JOB_CHANGED": "0",
        "SHARD_INDEX": "0", "SHARD_COUNT": "1",
    })
    command = ["bash", str(repo / "cloud" / "job_runner.sh")]
    started = time.time()
    state.update(stage="running", command_started_unix=started)
    returncode = 125
    error_type = None
    try:
        child = subprocess.Popen(command, cwd=repo, env=environment, start_new_session=True)
        child_holder["process"] = child
        returncode = child.wait()
    except BaseException as error:  # retain infrastructure failures, then archive
        error_type = type(error).__name__
    finally:
        child_holder.pop("process", None)
    timed_out = returncode in (124, 137)
    source = {
        "schema": STATUS_SCHEMA, "job_id": config["job_id"],
        "source_commit": config["commit"], "source_tree": config["tree"],
        "source_archive_sha256": config["source_archive_sha256"],
        "command_sha256": config["command_sha256"], "returncode": returncode,
        "timed_out": timed_out,
    }
    try:
        archive = build_result_archive(job_dir, result, source, config["max_result_bytes"])
        chunks = chunk_manifest(result, config["chunk_bytes"])
        state.update(
            stage="complete", done=True, returncode=returncode, timed_out=timed_out,
            worker_error_type=error_type, archive_ready=True, archive=archive,
            chunks=chunks, finished_unix=time.time())
    except BaseException as error:
        state.update(
            stage="archive_failed", done=True, returncode=returncode,
            timed_out=timed_out, worker_error_type=error_type, archive_ready=False,
            archive_error_type=type(error).__name__, finished_unix=time.time())


def handler_class(state: State, result: Path, token: str):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args):
            pass

        def send_bytes(self, code: int, data: bytes,
                       content_type="application/json", digest=None):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            if digest:
                self.send_header("X-Content-SHA256", digest)
            self.end_headers()
            self.wfile.write(data)

        def authorized(self) -> bool:
            supplied = self.headers.get("Authorization", "")
            return hmac.compare_digest(supplied, "Bearer " + token)

        def do_GET(self):
            if not self.authorized():
                self.send_bytes(401, b'{"error":"unauthorized"}\n')
                return
            if self.path == "/v1/status":
                data = (json.dumps(state.snapshot(), sort_keys=True,
                                   allow_nan=False) + "\n").encode()
                self.send_bytes(200, data)
                return
            match = CHUNK_PATH.fullmatch(self.path)
            snapshot = state.snapshot()
            if not match:
                self.send_bytes(404, b'{"error":"not_found"}\n')
                return
            if not snapshot.get("archive_ready"):
                self.send_bytes(409, b'{"error":"result_not_ready"}\n')
                return
            index = int(match.group(1))
            chunks = snapshot.get("chunks", [])
            if index >= len(chunks) or chunks[index].get("path") != self.path:
                self.send_bytes(404, b'{"error":"not_found"}\n')
                return
            chunk = chunks[index]
            with result.open("rb") as source:
                source.seek(chunk["offset"])
                data = source.read(chunk["bytes"])
            if (len(data) != chunk["bytes"]
                    or hashlib.sha256(data).hexdigest() != chunk["sha256"]):
                self.send_bytes(500, b'{"error":"result_changed"}\n')
                return
            self.send_bytes(200, data, "application/octet-stream", chunk["sha256"])

        def do_POST(self):
            self.send_bytes(405, b'{"error":"method_not_allowed"}\n')

        do_PUT = do_POST
        do_DELETE = do_POST
        do_PATCH = do_POST

    return Handler


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    if not repo.is_dir() or not 1 <= args.port <= 65535:
        raise SystemExit("invalid repository or port")
    config = read_config(repo)
    token = config.pop("token")
    for name in SECRET_ENV_NAMES:
        os.environ.pop(name, None)
    job_dir = Path("/root/runpod-http-batch") / config["job_id"]
    job_dir.mkdir(parents=True, exist_ok=False)
    result = job_dir / "result.tar.gz"
    initial = {
        "schema": STATUS_SCHEMA, "job_id": config["job_id"], "stage": "starting",
        "done": False, "archive_ready": False, "source_commit": config["commit"],
        "source_tree": config["tree"], "command_sha256": config["command_sha256"],
        "source_archive_sha256": config["source_archive_sha256"],
        "hardware": hardware(), "started_unix": time.time(),
    }
    state = State(job_dir / "adapter-status.json", initial)
    child_holder: dict = {}
    stopping = threading.Event()

    def stop(_signal, _frame):
        stopping.set()
        child = child_holder.get("process")
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), handler_class(state, result, token))
    server.timeout = 1
    server.daemon_threads = True
    worker = threading.Thread(
        target=run_job, args=(repo, job_dir, result, config, state, child_holder),
        daemon=False)
    worker.start()
    while not stopping.is_set():
        server.handle_request()
    server.server_close()
    worker.join(timeout=35)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
