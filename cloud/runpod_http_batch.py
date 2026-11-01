#!/usr/bin/env python3
"""Run one exact public commit on a new Runpod pod without outbound SSH.

The pod checks out a publicly reachable ref at an exact commit, verifies its
Git tree and archive SHA-256, runs one command under a timeout, and serves only
authenticated status and hash-bound result chunks through Runpod's HTTPS
proxy. The controller verifies and extracts declared outputs, then deletes the
exact pod ID returned by its create request in ``finally``.

``--dry-run`` performs no provider or public-origin request. A real run refuses
to allocate until ``--source-ref`` advertises ``--source-commit`` on the fixed
public origin. No AWS or SSH credential is sent to the pod.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import http.client
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import runpod_pod  # noqa: E402


SCHEMA = "runpod.http-batch.receipt/v1"
STATUS_SCHEMA = "runpod.http-batch.status/v1"
PUBLIC_ORIGIN = "https://github.com/isogeny-labs/cryptanalysis.git"
V2 = "https://api.runpod.io/v2"
HTTP_PORT = 8888
CHUNK_BYTES = 4 << 20
MAX_STATUS_BYTES = 4 << 20
MAX_ARCHIVE_MEMBERS = 100_000
MAX_PROVIDER_BYTES = 16 << 20
MAX_MANIFEST_BYTES = 16 << 20
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
POD_ID = re.compile(r"[A-Za-z0-9_-]{3,100}\Z")
NAME_PREFIX = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,42}\Z")
SOURCE_REF = re.compile(r"refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]{0,180}\Z")
REMOTE_BOOT = r"""set -Eeuo pipefail
umask 077
export DEBIAN_FRONTEND=noninteractive
missing=0
for tool in ca-certificates git python3 sha256sum tar timeout; do
  if [[ $tool = ca-certificates ]]; then
    [[ -e /etc/ssl/certs/ca-certificates.crt ]] || missing=1
  else
    command -v "$tool" >/dev/null 2>&1 || missing=1
  fi
done
if (( missing )); then
  apt-get update -qq
  apt-get install -y -qq ca-certificates coreutils git gzip python3 tar
fi
root=/root/runpod-http-source
checkout=$root/repo
mkdir "$root"
git init -q "$checkout"
git -C "$checkout" remote add origin "$RUNPOD_BATCH_SOURCE_URL"
git -C "$checkout" fetch -q --depth=1 origin "$RUNPOD_BATCH_SOURCE_REF"
actual=$(git -C "$checkout" rev-parse FETCH_HEAD)
[[ $actual = "$RUNPOD_BATCH_SOURCE_COMMIT" ]]
git -C "$checkout" checkout -q --detach "$actual"
actual_tree=$(git -C "$checkout" rev-parse HEAD^{tree})
[[ $actual_tree = "$RUNPOD_BATCH_SOURCE_TREE" ]]
actual_archive=$(git -C "$checkout" archive --format=tar HEAD | sha256sum | cut -d' ' -f1)
[[ $actual_archive = "$RUNPOD_BATCH_SOURCE_ARCHIVE_SHA256" ]]
exec python3 "$checkout/cloud/runpod_http_batch_server.py" --repo "$checkout" --port "$RUNPOD_BATCH_PORT"
"""


class BatchError(RuntimeError):
    pass


class ProviderError(BatchError):
    def __init__(self, message, status=None):
        self.status = status
        super().__init__(message)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_error(error: BaseException, hidden=()) -> str:
    text = str(error)
    values = list(hidden)
    for name in (
        "RUNPOD_API_KEY", "RUNPOD_SSH_PRIVATE_KEY", "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN", "ARTIFACTS_AWS_SECRET_ACCESS_KEY",
    ):
        value = os.environ.get(name)
        if value:
            values.append(value)
    for value in values:
        if value:
            text = text.replace(value, "<redacted>")
    return text[:1600]


def write_once(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    fd, temporary = tempfile.mkstemp(prefix=".runpod-http-batch-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    if result.returncode:
        raise BatchError(f"git {' '.join(args[:2])} failed")
    return result.stdout.strip()


def archive_sha256(repo: Path, commit: str) -> str:
    process = subprocess.Popen(
        ["git", "archive", "--format=tar", commit], cwd=repo, stdout=subprocess.PIPE)
    digest = hashlib.sha256()
    assert process.stdout is not None
    for block in iter(lambda: process.stdout.read(1 << 20), b""):
        digest.update(block)
    if process.wait() != 0:
        raise BatchError("git archive failed")
    return digest.hexdigest()


def validate_source_ref(ref: str) -> str:
    if (not SOURCE_REF.fullmatch(ref) or ".." in ref.split("/") or "//" in ref
            or ref.endswith(".lock")):
        raise BatchError("--source-ref must be one safe exact refs/heads/... name")
    return ref


def source_identity(repo: Path, commit: str, ref: str, public_check: bool) -> dict:
    if not COMMIT.fullmatch(commit):
        raise BatchError("--source-commit must be exactly 40 lowercase hex characters")
    validate_source_ref(ref)
    actual = git_output(repo, "rev-parse", f"{commit}^{{commit}}")
    if actual != commit:
        raise BatchError("source commit is not the requested local commit")
    tree = git_output(repo, "rev-parse", f"{commit}^{{tree}}")
    if not re.fullmatch(r"[0-9a-f]{40,64}", tree):
        raise BatchError("invalid Git tree identity")
    identity = {
        "origin": PUBLIC_ORIGIN, "ref": ref, "commit": commit, "tree": tree,
        "archive_sha256": archive_sha256(repo, commit),
        "public_ref_checked": False,
    }
    if public_check:
        environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith("GIT_CONFIG_") and key not in {
                "GIT_ASKPASS", "SSH_ASKPASS", "GITHUB_TOKEN", "GH_TOKEN",
            }
        }
        environment.update({
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "/bin/false", "SSH_ASKPASS": "/bin/false",
            "GCM_INTERACTIVE": "never",
        })
        with tempfile.TemporaryDirectory(prefix="runpod-public-ref-") as directory:
            result = subprocess.run(
                ["git", "-c", "credential.helper=", "-c", "core.askPass=/bin/false",
                 "-c", "http.extraHeader=", "-c",
                 "http.https://github.com/.extraHeader=", "ls-remote", "--exit-code",
                 PUBLIC_ORIGIN, ref],
                cwd=directory, env=environment, capture_output=True, text=True,
                check=False, timeout=60)
        rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
        if result.returncode or rows != [[commit, ref]]:
            raise BatchError("public origin does not advertise source ref at exact commit")
        identity["public_ref_checked"] = True
        identity["public_checked_at"] = utc_now()
    return identity


def validate_outputs(outputs: list[str]) -> list[str]:
    if not outputs:
        raise BatchError("at least one --out path is required")
    normalized = []
    for raw in outputs:
        name = raw.rstrip("/")
        path = PurePosixPath(name)
        if (not name or name == "." or path.as_posix() != name or name.startswith("-")
                or path.is_absolute() or ".." in path.parts
                or ".git" in path.parts
                or name.startswith(".runpod-batch") or "\x00" in name or "\n" in name):
            raise BatchError(f"unsafe output path: {raw!r}")
        normalized.append(path.as_posix())
    if len(set(normalized)) != len(normalized):
        raise BatchError("duplicate --out path")
    return normalized


def unique_name(prefix: str, nonce: str) -> str:
    if not NAME_PREFIX.fullmatch(prefix) or not re.fullmatch(r"[0-9a-f]{12}", nonce):
        raise BatchError("unsafe pod name prefix or nonce")
    return f"{prefix}-{nonce}"


def proxy_base(pod_id: str, port=HTTP_PORT) -> str:
    if not POD_ID.fullmatch(pod_id) or not 1 <= port <= 65535:
        raise BatchError("invalid pod ID or HTTP port")
    return f"https://{pod_id}-{port}.proxy.runpod.net"


def build_body(args, name: str, token: str, source: dict,
               command: str, outputs: list[str]) -> dict:
    if len(token) < 43:
        raise BatchError("HTTP bearer must carry at least 256 random bits")
    command_sha = hashlib.sha256(command.encode()).hexdigest()
    bootstrap = runpod_pod.BOOTSTRAP.replace(
        "cd /root/cryptanalysis", 'cd "$JOB_WORKDIR"')
    if bootstrap == runpod_pod.BOOTSTRAP:
        raise BatchError("runpod bootstrap no longer has its expected checkout path")
    job_id = name
    environment = {
        "POD_BOOT_B64": b64(REMOTE_BOOT),
        "RUNPOD_BATCH_TOKEN": token,
        "RUNPOD_BATCH_OWNERSHIP_ID": hashlib.sha256(token.encode()).hexdigest(),
        "RUNPOD_BATCH_JOB_ID": job_id,
        "RUNPOD_BATCH_SOURCE_URL": PUBLIC_ORIGIN,
        "RUNPOD_BATCH_SOURCE_REF": source["ref"],
        "RUNPOD_BATCH_SOURCE_COMMIT": source["commit"],
        "RUNPOD_BATCH_SOURCE_TREE": source["tree"],
        "RUNPOD_BATCH_SOURCE_ARCHIVE_SHA256": source["archive_sha256"],
        "RUNPOD_BATCH_COMMAND_B64": b64(command),
        "RUNPOD_BATCH_COMMAND_SHA256": command_sha,
        "RUNPOD_BATCH_BOOTSTRAP_B64": b64(bootstrap),
        "RUNPOD_BATCH_OUTPUTS_B64": b64(json.dumps(outputs, separators=(",", ":"))),
        "RUNPOD_BATCH_TIMEOUT_SECONDS": str(args.timeout),
        "RUNPOD_BATCH_CHUNK_BYTES": str(CHUNK_BYTES),
        "RUNPOD_BATCH_MAX_RESULT_BYTES": str(args.max_result_mib << 20),
        "RUNPOD_BATCH_PORT": str(HTTP_PORT),
    }
    body = runpod_pod.pod_body(args, "", environment)
    body["name"] = name
    body["ports"] = [f"{HTTP_PORT}/http"]
    body["env"].pop("PUBLIC_KEY", None)
    body["env"].pop("SHIP_PREFETCH", None)
    forbidden = {key for key in body["env"] if key.startswith("AWS_") or key.startswith("ARTIFACTS_AWS_")}
    if forbidden or "22/tcp" in body["ports"]:
        raise BatchError("batch body contains forbidden cloud credentials or SSH exposure")
    return body


def request_summary(body: dict) -> dict:
    return {
        "name": body["name"], "cloudType": body["cloudType"],
        "computeType": body["computeType"], "imageName": body["imageName"],
        "containerDiskInGb": body["containerDiskInGb"], "ports": body["ports"],
        "gpuTypeIds": body.get("gpuTypeIds"), "gpuCount": body.get("gpuCount"),
        "minVCPUPerGPU": body.get("minVCPUPerGPU"),
        "minRAMPerGPU": body.get("minRAMPerGPU"),
        "environment_keys": sorted(body["env"]),
        "startup_sha256": hashlib.sha256(body["dockerStartCmd"][0].encode()).hexdigest(),
        "secrets_redacted": True,
    }


class RunpodClient:
    """Pinned, no-redirect adapter for the repository's Runpod REST endpoints."""
    def __init__(self, key=None):
        self._key = (key if key is not None else os.environ.get("RUNPOD_API_KEY", "")).strip()
        if not self._key:
            raise BatchError("RUNPOD_API_KEY is required for a real batch run")
        self._opener = urllib.request.build_opener(NoRedirect())

    def call(self, method, url, body=None):
        parsed = urllib.parse.urlsplit(url)
        allowed = (runpod_pod.REST + "/", V2 + "/")
        if (method not in {"GET", "POST", "DELETE"} or not url.startswith(allowed)
                or parsed.scheme != "https" or parsed.username is not None
                or parsed.password is not None or parsed.fragment or ".." in parsed.path):
            raise ProviderError("refusing provider request outside pinned HTTPS endpoints")
        request = urllib.request.Request(
            url, method=method,
            data=None if body is None else json.dumps(
                body, allow_nan=False, separators=(",", ":")).encode(),
            headers={"Authorization": "Bearer " + self._key,
                     "Content-Type": "application/json", "Accept": "application/json",
                     "User-Agent": "cryptanalysis-runpod-http-batch/1.0"})
        try:
            with self._opener.open(request, timeout=60) as response:
                raw = response.read(MAX_PROVIDER_BYTES + 1)
                status = response.status
        except urllib.error.HTTPError as error:
            raw = error.read(16385)
            detail = "request refused"
            if len(raw) <= 16384:
                try:
                    problem = json.loads(raw)
                    if isinstance(problem, dict):
                        candidate = problem.get("detail") or problem.get("title")
                        if isinstance(candidate, str):
                            detail = safe_error(candidate, (self._key,))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    pass
            raise ProviderError(f"provider HTTP {error.code}: {detail}", error.code) from None
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise ProviderError("provider request transport failure") from error
        if len(raw) > MAX_PROVIDER_BYTES:
            raise ProviderError("provider response exceeds size limit", status)
        if status == 204 or not raw.strip():
            return None
        try:
            return json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProviderError("provider returned invalid JSON", status) from error

    def list_pods(self):
        value = self.call("GET", f"{runpod_pod.REST}/pods")
        return value if isinstance(value, list) else value.get("pods", [])

    def named(self, name):
        return [pod for pod in self.list_pods()
                if pod.get("name") == name and pod.get("desiredStatus") != "TERMINATED"]

    def create(self, body):
        return self.call("POST", f"{runpod_pod.REST}/pods", body)

    def get_v2(self, pod_id):
        return self.call("GET", f"{V2}/pods/{pod_id}")

    def delete(self, pod_id):
        return self.call("DELETE", f"{runpod_pod.REST}/pods/{pod_id}")


def pod_identifier(pod: dict) -> str:
    value = pod.get("id")
    if not isinstance(value, str) or not POD_ID.fullmatch(value):
        raise BatchError("provider returned an invalid pod ID")
    return value


def marker_matches(pod: dict, name: str, ownership_id: str) -> bool:
    return (pod.get("name") == name
            and (pod.get("env") or {}).get("RUNPOD_BATCH_OWNERSHIP_ID") == ownership_id)


def reconcile_ambiguous(client, name: str, ownership_id: str, seconds: int,
                        sleep=time.sleep):
    deadline = time.monotonic() + seconds
    while True:
        matches = [pod for pod in client.named(name)
                   if marker_matches(pod, name, ownership_id)]
        if len(matches) > 1:
            raise BatchError("multiple exact-name marker-bound pods after ambiguous create")
        if matches:
            return matches[0]
        if time.monotonic() >= deadline:
            return None
        sleep(min(5, max(0, deadline - time.monotonic())))


def provider_summary(pod: dict) -> dict:
    return {key: pod.get(key) for key in (
        "id", "name", "status", "gpu", "cost", "cloud", "image", "cudaVersion",
        "dataCenterId", "createdAt", "startedAt")}


def guard_provider(pod: dict, expected_id: str, name: str, args) -> dict:
    gpu = pod.get("gpu") or {}
    allowed = args.gpu or runpod_pod.DEFAULT_GPUS
    cost = pod.get("cost")
    cuda = pod.get("cudaVersion")
    if (pod_identifier(pod) != expected_id or pod.get("name") != name
            or pod.get("status") != "RUNNING" or pod.get("cloud") != args.cloud
            or pod.get("image") != (args.image or runpod_pod.GPU_IMAGE)
            or gpu.get("id") not in allowed or gpu.get("count") != args.gpu_count
            or not isinstance(gpu.get("vcpuCount"), (int, float))
            or isinstance(gpu.get("vcpuCount"), bool)
            or gpu["vcpuCount"] < args.min_vcpu
            or not isinstance(gpu.get("memory"), (int, float))
            or isinstance(gpu.get("memory"), bool)
            or gpu["memory"] < args.min_ram
            or not isinstance(cost, (int, float)) or isinstance(cost, bool)
            or not math.isfinite(cost) or not 0 < cost <= args.max_price
            or not isinstance(cuda, str) or not re.fullmatch(r"[0-9]+\.[0-9]+", cuda)
            or f"{HTTP_PORT}/http" not in (pod.get("ports") or [])):
        raise BatchError("allocated pod identity/GPU/CUDA/price/HTTP guard failed")
    return provider_summary(pod)


def wait_provider(client, pod_id: str, name: str, args, sleep=time.sleep) -> dict:
    deadline = time.monotonic() + args.wait
    last = None
    while time.monotonic() < deadline:
        try:
            last = client.get_v2(pod_id)
            if last.get("status") == "RUNNING":
                return guard_provider(last, pod_id, name, args)
            if last.get("status") in ("ERROR", "EXITED", "TERMINATED"):
                raise BatchError(f"pod entered terminal state {last.get('status')}")
        except ProviderError as error:
            if error.status not in (404, 429, 500, 502, 503, 504):
                raise
        sleep(min(5, max(0, deadline - time.monotonic())))
    raise BatchError(f"pod did not become RUNNING within {args.wait} seconds")


def monitor_provider(client, pod_id: str, name: str, args) -> None:
    try:
        pod = client.get_v2(pod_id)
    except ProviderError as error:
        if error.status in (429, 500, 502, 503, 504):
            return
        raise
    status = pod.get("status")
    if status != "RUNNING":
        raise BatchError(f"pod left RUNNING state during result polling: {status}")
    guard_provider(pod, pod_id, name, args)


def validate_status(status: dict, expected: dict) -> dict:
    if not isinstance(status, dict):
        raise BatchError("remote status identity binding failed")
    hardware = status.get("hardware") or {}
    remote_gpus = hardware.get("gpus")
    if (status.get("schema") != STATUS_SCHEMA
            or status.get("job_id") != expected["job_id"]
            or status.get("source_commit") != expected["commit"]
            or status.get("source_tree") != expected["tree"]
            or status.get("source_archive_sha256") != expected["archive_sha256"]
            or status.get("command_sha256") != expected["command_sha256"]
            or hardware.get("pod_id") != expected["pod_id"]
            or not isinstance(remote_gpus, list)
            or len(remote_gpus) != expected["gpu_count"]
            or any(not isinstance(gpu, dict)
                   or gpu.get("name") != expected["gpu_id"] for gpu in remote_gpus)):
        raise BatchError("remote status identity binding failed")
    if status.get("done") is not True or status.get("archive_ready") is not True:
        raise BatchError("remote terminal status has no result archive")
    returncode = status.get("returncode")
    archive = status.get("archive")
    chunks = status.get("chunks")
    if type(returncode) is not int or not isinstance(archive, dict) or not isinstance(chunks, list):
        raise BatchError("remote terminal status has invalid result metadata")
    if (not SHA256.fullmatch(str(archive.get("sha256", "")))
            or type(archive.get("bytes")) is not int or archive["bytes"] < 1
            or archive["bytes"] > expected["max_result_bytes"]):
        raise BatchError("remote archive identity is invalid")
    offset = total = 0
    for index, chunk in enumerate(chunks):
        if (not isinstance(chunk, dict) or chunk.get("index") != index
                or chunk.get("path") != f"/v1/result/{index:06d}"
                or chunk.get("offset") != offset or type(chunk.get("bytes")) is not int
                or not 0 < chunk["bytes"] <= CHUNK_BYTES
                or not SHA256.fullmatch(str(chunk.get("sha256", "")))):
            raise BatchError("remote chunk manifest is invalid")
        offset += chunk["bytes"]
        total += chunk["bytes"]
    if not chunks or total != archive["bytes"]:
        raise BatchError("remote chunk coverage does not equal archive size")
    return status


class HttpTransport:
    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())

    def open(self, base: str, path: str, token: str, timeout: int):
        if not path.startswith("/v1/") or ".." in path:
            raise BatchError("refusing non-protocol HTTP path")
        request = urllib.request.Request(
            base + path,
            headers={"Authorization": "Bearer " + token,
                     "User-Agent": "cryptanalysis-runpod-http-batch/1.0"})
        return self.opener.open(request, timeout=timeout)

    def wait_status(self, base: str, token: str, expected: dict,
                    deadline: float, sleep=time.sleep, provider_monitor=None) -> dict:
        while time.monotonic() < deadline:
            if provider_monitor is not None:
                provider_monitor()
            try:
                with self.open(base, "/v1/status", token, 20) as response:
                    raw = response.read(MAX_STATUS_BYTES + 1)
                if len(raw) > MAX_STATUS_BYTES:
                    raise BatchError("result status exceeds size limit")
                status = json.loads(raw)
                if status.get("done") is True:
                    return validate_status(status, expected)
            except urllib.error.HTTPError as error:
                if error.code in (401, 403):
                    raise BatchError("result service rejected its bearer") from None
                if error.code not in (404, 409, 429, 502, 503, 504):
                    raise BatchError(f"result service HTTP {error.code}") from None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                pass
            sleep(min(5, max(0, deadline - time.monotonic())))
        raise BatchError("result status polling deadline exceeded")

    def download(self, base: str, token: str, status: dict, destination: Path) -> None:
        if destination.exists():
            raise FileExistsError(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(destination.parent).free < status["archive"]["bytes"] + (64 << 20):
            raise BatchError("insufficient local disk for result archive")
        fd, temporary_name = tempfile.mkstemp(
            prefix=".runpod-http-result-", dir=destination.parent)
        overall = hashlib.sha256()
        total = 0
        try:
            with os.fdopen(fd, "wb") as output:
                for chunk in status["chunks"]:
                    data = header = content_length = None
                    for attempt in range(4):
                        try:
                            with self.open(base, chunk["path"], token, 90) as response:
                                data = response.read(chunk["bytes"] + 1)
                                header = response.headers.get("X-Content-SHA256")
                                content_length = response.headers.get("Content-Length")
                            break
                        except urllib.error.HTTPError as error:
                            if error.code not in (409, 429, 500, 502, 503, 504) or attempt == 3:
                                raise BatchError(
                                    f"result chunk HTTP {error.code}") from None
                        except (urllib.error.URLError, TimeoutError, OSError,
                                http.client.IncompleteRead) as error:
                            if attempt == 3:
                                raise BatchError("result chunk transport retries exhausted") from error
                        time.sleep(min(2 ** attempt, 5))
                    assert isinstance(data, bytes)
                    if (len(data) != chunk["bytes"] or header != chunk["sha256"]
                            or content_length != str(chunk["bytes"])
                            or hashlib.sha256(data).hexdigest() != chunk["sha256"]):
                        raise BatchError("downloaded result chunk failed size/hash binding")
                    output.write(data)
                    overall.update(data)
                    total += len(data)
                output.flush()
                os.fsync(output.fileno())
            archive = status["archive"]
            if total != archive["bytes"] or overall.hexdigest() != archive["sha256"]:
                raise BatchError("reassembled result archive failed size/hash binding")
            os.link(temporary_name, destination)
            os.chmod(destination, 0o600)
        finally:
            os.unlink(temporary_name)


def allowed_output(name: str, outputs: list[str]) -> bool:
    path = PurePosixPath(name)
    return any(path == PurePosixPath(root) or PurePosixPath(root) in path.parents
               for root in outputs)


def extract_verified(archive_path: Path, outputs: list[str], repo: Path,
                     metadata_dir: Path, maximum: int) -> list[dict]:
    if metadata_dir.exists():
        raise FileExistsError(metadata_dir)
    metadata_names = {
        ".runpod-batch/log.txt", ".runpod-batch/job-status.json",
        ".runpod-batch/source.json", ".runpod-batch/files.sha256",
    }
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise BatchError("result archive contains too many members")
        seen = set()
        total = 0
        by_name = {}
        for member in members:
            path = PurePosixPath(member.name)
            if (member.name in seen or path.as_posix() != member.name
                    or not member.isfile() or path.is_absolute()
                    or ".." in path.parts or ".git" in path.parts):
                raise BatchError("unsafe or duplicate result archive member")
            seen.add(member.name)
            by_name[member.name] = member
            total += member.size
            if total > maximum:
                raise BatchError("result archive exceeds uncompressed limit")
            if member.name not in metadata_names and not allowed_output(member.name, outputs):
                raise BatchError("result archive contains an undeclared output")
        manifest_member = by_name.get(".runpod-batch/files.sha256")
        if manifest_member is None or manifest_member.size > MAX_MANIFEST_BYTES:
            raise BatchError("result archive lacks its file manifest")
        manifest_stream = archive.extractfile(manifest_member)
        if manifest_stream is None:
            raise BatchError("result archive manifest is unreadable")
        manifest = {}
        manifest_bytes = manifest_stream.read(MAX_MANIFEST_BYTES + 1)
        if len(manifest_bytes) > MAX_MANIFEST_BYTES:
            raise BatchError("result archive manifest exceeds size limit")
        for line in manifest_bytes.decode().splitlines():
            digest, separator, name = line.partition("  ")
            if (not separator or not SHA256.fullmatch(digest) or name in manifest
                    or name == ".runpod-batch/files.sha256"):
                raise BatchError("result file manifest is invalid")
            manifest[name] = digest
        actual = set(by_name) - {".runpod-batch/files.sha256"}
        if set(manifest) != actual:
            raise BatchError("result file manifest coverage mismatch")
        scientific = actual - metadata_names
        for root_name in outputs:
            root_path = PurePosixPath(root_name)
            if not any(PurePosixPath(name) == root_path
                       or root_path in PurePosixPath(name).parents for name in scientific):
                raise BatchError(f"declared output was not produced: {root_name}")
        verified = []
        for name in sorted(actual):
            stream = archive.extractfile(by_name[name])
            if stream is None:
                raise BatchError("result member is unreadable")
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1 << 20), b""):
                digest.update(block)
            if digest.hexdigest() != manifest[name]:
                raise BatchError("result member hash mismatch")
            verified.append({"path": name, "sha256": digest.hexdigest(),
                             "bytes": by_name[name].size})

        destinations = {}
        for name in sorted(by_name):
            if name.startswith(".runpod-batch/"):
                target = metadata_dir / PurePosixPath(name).name
                root = metadata_dir.resolve()
            else:
                target = repo / name
                root = repo.resolve()
            resolved = target.resolve(strict=False)
            if root not in (resolved, *resolved.parents):
                raise BatchError("result target escapes its destination through a symlink")
            if os.path.lexists(target):
                raise FileExistsError(f"refusing to overwrite result target: {target}")
            destinations[name] = target

        metadata_dir.mkdir(parents=True)
        for name in sorted(by_name):
            member = by_name[name]
            stream = archive.extractfile(member)
            assert stream is not None
            target = destinations[name]
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
                temporary_name = temporary.name
                for block in iter(lambda: stream.read(1 << 20), b""):
                    temporary.write(block)
            try:
                os.chmod(temporary_name, (member.mode & 0o700) or 0o600)
                os.link(temporary_name, target)
            finally:
                os.unlink(temporary_name)
    return verified


def cleanup_exact(client, pod_id: str, sleep=time.sleep) -> dict:
    try:
        client.delete(pod_id)
    except ProviderError as error:
        if error.status != 404:
            raise
    for _ in range(6):
        try:
            visible = client.get_v2(pod_id)
            if pod_identifier(visible) != pod_id:
                raise BatchError("exact cleanup GET returned a different pod ID")
        except ProviderError as error:
            if error.status == 404:
                return {"id": pod_id, "delete_requested": True,
                        "absence_verified": True}
            if error.status not in (429, 500, 502, 503, 504):
                raise
        sleep(5)
    raise BatchError("exact pod remains visible after delete")


def execute(args, *, client=None, transport=None, repo=REPO,
            token_factory=lambda: secrets.token_urlsafe(48),
            nonce_factory=lambda: secrets.token_hex(6), sleep=time.sleep) -> int:
    command = " ".join(args.command).strip()
    if not command:
        raise BatchError("a command is required after --")
    if args.cpu:
        raise BatchError("HTTP batch currently requires one GPU pod")
    outputs = validate_outputs(args.out)
    source = source_identity(Path(repo), args.source_commit, args.source_ref,
                             public_check=not args.dry_run)
    nonce = "000000000000" if args.dry_run else nonce_factory()
    name = unique_name(args.name, nonce)
    token = "dry-run-token-with-256-bits-redacted-000000000000" if args.dry_run else token_factory()
    ownership_id = hashlib.sha256(token.encode()).hexdigest()
    body = build_body(args, name, token, source, command, outputs)
    plan = {
        "schema": SCHEMA, "provider_actions": False, "source": source,
        "command": command, "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
        "outputs": outputs, "request": request_summary(body),
        "transport": {"kind": "runpod-https-proxy", "port": HTTP_PORT,
                      "chunk_bytes": CHUNK_BYTES, "authentication": "ephemeral bearer"},
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    if args.max_hours * 3600 < args.wait + args.timeout + 180:
        raise BatchError("--max-hours must cover startup wait + command timeout + 180 seconds")
    receipt_path = args.receipt.resolve()
    archive_path = (args.archive or receipt_path.with_suffix(".result.tar.gz")).resolve()
    metadata_dir = receipt_path.with_suffix(".remote")
    if receipt_path.exists() or archive_path.exists() or metadata_dir.exists():
        raise FileExistsError("receipt, result archive, or remote metadata already exists")
    client = client or RunpodClient()
    transport = transport or HttpTransport()
    receipt = {**plan, "provider_actions": True, "started_at": utc_now(),
               "pod": None, "remote_status": None, "result": None,
               "cleanup": None, "error": None}
    pod_id = None
    pending: BaseException | None = None
    returncode = 125
    try:
        if client.named(name):
            raise BatchError("fresh randomized pod name already exists")
        try:
            created = client.create(body)
            candidate_id = pod_identifier(created)
            if created.get("name") != name:
                raise BatchError("create response name mismatch")
            pod_id = candidate_id
        except BaseException as error:
            recovered = reconcile_ambiguous(
                client, name, ownership_id, args.reconcile_seconds, sleep=sleep)
            if recovered is not None:
                pod_id = pod_identifier(recovered)
                receipt["pod"] = {"id": pod_id, "name": name,
                                  "creation_response_ambiguous": True}
            raise BatchError("pod creation response was refused or ambiguous; no retry") from error

        summary = wait_provider(client, pod_id, name, args, sleep=sleep)
        receipt["pod"] = {**summary, "creation_response_ambiguous": False}
        expected = {
            "job_id": name, "commit": source["commit"], "tree": source["tree"],
            "archive_sha256": source["archive_sha256"],
            "command_sha256": plan["command_sha256"], "pod_id": pod_id,
            "gpu_id": summary["gpu"]["id"],
            "gpu_count": summary["gpu"]["count"],
            "max_result_bytes": args.max_result_mib << 20,
        }
        deadline = time.monotonic() + args.timeout + args.wait
        status = transport.wait_status(
            proxy_base(pod_id), token, expected, deadline, sleep=sleep,
            provider_monitor=lambda: monitor_provider(client, pod_id, name, args))
        receipt["remote_status"] = status
        transport.download(proxy_base(pod_id), token, status, archive_path)
        verified = extract_verified(
            archive_path, outputs, Path(repo), metadata_dir, args.max_result_mib << 20)
        receipt["result"] = {
            "archive": str(archive_path), "archive_sha256": sha256_file(archive_path),
            "archive_bytes": archive_path.stat().st_size,
            "metadata": str(metadata_dir), "files": verified,
        }
        returncode = status["returncode"]
    except BaseException as error:
        pending = error
        receipt["error"] = {"type": type(error).__name__,
                            "detail": safe_error(error, (token,))}
    finally:
        if pod_id is not None:
            try:
                receipt["cleanup"] = cleanup_exact(client, pod_id, sleep=sleep)
            except BaseException as error:
                receipt["cleanup"] = {"id": pod_id, "delete_requested": False,
                                      "absence_verified": False,
                                      "error_type": type(error).__name__,
                                      "error": safe_error(error, (token,))}
                if pending is None:
                    pending = error
        receipt["finished_at"] = utc_now()
        serialized = json.dumps(receipt, sort_keys=True, allow_nan=False)
        if token in serialized:
            raise AssertionError("transport bearer reached receipt")
        write_once(receipt_path, receipt)
    if pending is not None:
        if isinstance(pending, (KeyboardInterrupt, SystemExit)):
            raise pending
        raise BatchError(safe_error(pending, (token,))) from pending
    return returncode


def parse(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    command = []
    if "--" in argv:
        cut = argv.index("--")
        argv, command = argv[:cut], argv[cut + 1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="pod-name prefix; a random suffix is always added")
    runpod_pod.add_pod_options(parser)
    parser.add_argument("--source-ref", required=True,
                        help="public exact branch ref, e.g. refs/heads/feature")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--out", action="append", default=[], metavar="PATH")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--timeout", type=int, default=5400,
                        help="scientific command timeout in seconds")
    parser.add_argument("--max-result-mib", type=int, default=4096)
    parser.add_argument("--max-price", type=float, required=True,
                        help="refuse an allocated pod above this USD/hour")
    parser.add_argument("--reconcile-seconds", type=int, default=60,
                        help="read-only name reconciliation after ambiguous POST")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate locally and print a redacted plan; no network/provider calls")
    args = parser.parse_args(argv)
    args.command = command
    if args.max_price <= 0 or args.timeout < 1 or args.max_result_mib < 1:
        parser.error("price, timeout, and result limit must be positive")
    if args.reconcile_seconds < 0:
        parser.error("--reconcile-seconds must be nonnegative")
    return args


def main(argv=None) -> int:
    try:
        return execute(parse(argv))
    except KeyboardInterrupt:
        print("runpod_http_batch: interrupted after exact-ID cleanup attempt", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"runpod_http_batch: {safe_error(error)}", file=sys.stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
