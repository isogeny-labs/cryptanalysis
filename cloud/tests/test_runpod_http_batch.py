"""Offline controls for the no-SSH Runpod HTTP batch transport."""
import hashlib
import io
import json
import base64
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tarfile
import tempfile
import threading
import unittest
from unittest import mock
import urllib.error
import urllib.request


CLOUD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CLOUD))
import runpod_http_batch as batch  # noqa: E402
import runpod_http_batch_server as server  # noqa: E402


TOKEN = "synthetic-http-bearer-with-at-least-256-random-looking-bits"
COMMIT = "a" * 40
TREE = "b" * 40
SOURCE_ARCHIVE = "c" * 64
POD = "podtest123"


def args_for(root: Path, returncode=0):
    del returncode
    return SimpleNamespace(
        name="misagi-http-test", cpu=0, gpu=["NVIDIA GeForce RTX 5090"],
        gpu_count=1, min_vcpu=8, min_ram=24, cloud="SECURE", image=None,
        disk=80, max_hours=2.0, wait=10, timeout=30, max_result_mib=8,
        max_price=1.50, reconcile_seconds=0, dry_run=False,
        source_commit=COMMIT, source_ref="refs/heads/test-http-batch",
        out=["results/a.json"], receipt=root / "receipt.json",
        archive=root / "result.tar.gz", command=["echo fixture > results/a.json"],
    )


def source_identity():
    return {
        "origin": batch.PUBLIC_ORIGIN, "ref": "refs/heads/test-http-batch",
        "commit": COMMIT, "tree": TREE, "archive_sha256": SOURCE_ARCHIVE,
        "public_ref_checked": True, "public_checked_at": "synthetic",
    }


def result_archive(output=b'{"ok":true}\n') -> bytes:
    files = {
        "results/a.json": output,
        ".runpod-batch/log.txt": b"synthetic log\n",
        ".runpod-batch/job-status.json": b'{"returncode":0}\n',
        ".runpod-batch/source.json": b'{"source":"synthetic"}\n',
    }
    manifest = b"".join(
        hashlib.sha256(data).hexdigest().encode() + b"  " + name.encode() + b"\n"
        for name, data in files.items())
    files[".runpod-batch/files.sha256"] = manifest
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def terminal_status(data: bytes, returncode=0):
    digest = hashlib.sha256(data).hexdigest()
    return {
        "schema": batch.STATUS_SCHEMA, "job_id": "misagi-http-test-0123456789ab",
        "source_commit": COMMIT, "source_tree": TREE,
        "source_archive_sha256": SOURCE_ARCHIVE,
        "command_sha256": hashlib.sha256(b"echo fixture > results/a.json").hexdigest(),
        "hardware": {"pod_id": POD, "gpus": [{"name": "NVIDIA GeForce RTX 5090"}]},
        "done": True, "archive_ready": True, "returncode": returncode,
        "archive": {"sha256": digest, "bytes": len(data), "files": 5},
        "chunks": [{"index": 0, "path": "/v1/result/000000", "offset": 0,
                    "bytes": len(data), "sha256": digest}],
    }


class FakeClient:
    def __init__(self, create_error=None, reconcile=False, wrong_name=False):
        self.create_error = create_error
        self.reconcile = reconcile
        self.create_calls = 0
        self.named_calls = 0
        self.deleted = []
        self.name = None
        self.wrong_name = wrong_name

    def named(self, name):
        self.named_calls += 1
        if self.reconcile and self.named_calls > 1:
            return [{"id": POD, "name": name, "env": {
                "RUNPOD_BATCH_OWNERSHIP_ID": hashlib.sha256(TOKEN.encode()).hexdigest()}}]
        return []

    def create(self, body):
        self.create_calls += 1
        self.name = body["name"]
        if self.create_error:
            raise self.create_error
        return {"id": POD, "name": "wrong-name" if self.wrong_name else self.name}

    def get_v2(self, pod_id):
        if pod_id in self.deleted:
            raise batch.ProviderError("gone", 404)
        return {
            "id": pod_id, "name": self.name, "status": "RUNNING",
            "gpu": {"id": "NVIDIA GeForce RTX 5090", "count": 1,
                    "vcpuCount": 16, "memory": 62},
            "cost": 1.19, "cloud": "SECURE", "image": "runpod/base:1.0.2-ubuntu2404",
            "cudaVersion": "13.2", "ports": ["8888/http"], "dataCenterId": "EU-RO-1",
            "createdAt": "synthetic", "startedAt": "synthetic",
        }

    def delete(self, pod_id):
        self.deleted.append(pod_id)

    def list_pods(self):
        return []


class FakeTransport:
    def __init__(self, data, returncode=0, fail_download=False):
        self.data = data
        self.returncode = returncode
        self.fail_download = fail_download
        self.seen_token = None

    def wait_status(self, base, token, expected, deadline, sleep=None,
                    provider_monitor=None):
        del base, deadline, sleep
        if provider_monitor is not None:
            provider_monitor()
        self.seen_token = token
        status = terminal_status(self.data, self.returncode)
        status["job_id"] = expected["job_id"]
        status["command_sha256"] = expected["command_sha256"]
        return batch.validate_status(status, expected)

    def download(self, base, token, status, destination):
        del base, status
        self.seen_token = token
        if self.fail_download:
            raise RuntimeError("synthetic download failure " + token)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.data)


class RunpodHttpBatchTest(unittest.TestCase):
    def test_body_has_http_only_and_no_cloud_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            args = args_for(Path(directory))
            body = batch.build_body(
                args, "misagi-http-test-0123456789ab", TOKEN,
                source_identity(), "echo fixture > results/a.json", ["results/a.json"])
        self.assertEqual(body["ports"], ["8888/http"])
        self.assertNotIn("PUBLIC_KEY", body["env"])
        self.assertNotIn("allowedCudaVersions", body)
        self.assertFalse(any(key.startswith(("AWS_", "ARTIFACTS_AWS_")) for key in body["env"]))
        summary = json.dumps(batch.request_summary(body))
        self.assertNotIn(TOKEN, summary)
        self.assertNotIn("RUNPOD_SSH", summary)
        bootstrap = base64.b64decode(body["env"]["RUNPOD_BATCH_BOOTSTRAP_B64"]).decode()
        self.assertIn('cd "$JOB_WORKDIR"', bootstrap)
        self.assertNotIn("cd /root/cryptanalysis", bootstrap)

    def test_proxy_url_and_source_ref_validation(self):
        self.assertEqual(batch.proxy_base(POD), f"https://{POD}-8888.proxy.runpod.net")
        for value in ("../bad", "refs/tags/v1", "refs/heads/../bad", "refs/heads/a.lock"):
            with self.assertRaises(batch.BatchError):
                batch.validate_source_ref(value)

    def test_malformed_status_list_is_rejected_cleanly(self):
        with self.assertRaises(batch.BatchError):
            batch.validate_status([], {})

    def test_remote_boot_is_shell_syntax(self):
        result = __import__("subprocess").run(
            ["bash", "-n"], input=batch.REMOTE_BOOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_success_fetches_verifies_extracts_and_deletes_exact_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            client = FakeClient()
            transport = FakeTransport(result_archive())
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                rc = batch.execute(
                    args, client=client, transport=transport, repo=root,
                    token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                    sleep=lambda _seconds: None)
            self.assertEqual(rc, 0)
            self.assertEqual(client.deleted, [POD])
            self.assertEqual((root / "results/a.json").read_text(), '{"ok":true}\n')
            receipt = json.loads(args.receipt.read_text())
            self.assertTrue(receipt["cleanup"]["absence_verified"])
            self.assertEqual(receipt["pod"]["cudaVersion"], "13.2")
            self.assertNotIn(TOKEN, args.receipt.read_text())

    def test_command_failure_is_reported_after_results_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            client = FakeClient()
            transport = FakeTransport(result_archive(b"failed output\n"), returncode=7)
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                rc = batch.execute(
                    args, client=client, transport=transport, repo=root,
                    token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                    sleep=lambda _seconds: None)
            self.assertEqual(rc, 7)
            self.assertEqual(client.deleted, [POD])
            self.assertEqual(json.loads(args.receipt.read_text())["remote_status"]["returncode"], 7)

    def test_fetch_failure_still_deletes_and_redacts_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            client = FakeClient()
            transport = FakeTransport(result_archive(), fail_download=True)
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                with self.assertRaises(batch.BatchError):
                    batch.execute(
                        args, client=client, transport=transport, repo=root,
                        token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                        sleep=lambda _seconds: None)
            self.assertEqual(client.deleted, [POD])
            receipt = args.receipt.read_text()
            self.assertNotIn(TOKEN, receipt)
            self.assertIn("<redacted>", receipt)

    def test_ambiguous_create_is_not_retried_and_reconciled_id_is_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            client = FakeClient(batch.ProviderError("ambiguous"), reconcile=True)
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                with self.assertRaises(batch.BatchError):
                    batch.execute(
                        args, client=client, transport=FakeTransport(result_archive()), repo=root,
                        token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                        sleep=lambda _seconds: None)
            self.assertEqual(client.create_calls, 1)
            self.assertEqual(client.deleted, [POD])

    def test_wrong_name_create_response_never_deletes_unowned_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            client = FakeClient(wrong_name=True)
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                with self.assertRaises(batch.BatchError):
                    batch.execute(
                        args, client=client, transport=FakeTransport(result_archive()), repo=root,
                        token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                        sleep=lambda _seconds: None)
            self.assertEqual(client.deleted, [])

    def test_missing_declared_output_fails_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            args.out.append("results/missing.json")
            client = FakeClient()
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                with self.assertRaises(batch.BatchError):
                    batch.execute(
                        args, client=client, transport=FakeTransport(result_archive()), repo=root,
                        token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                        sleep=lambda _seconds: None)
            self.assertEqual(client.deleted, [POD])

    def test_existing_result_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "results").mkdir()
            target = root / "results/a.json"
            target.write_text("incumbent\n")
            args = args_for(root)
            client = FakeClient()
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                with self.assertRaises(batch.BatchError):
                    batch.execute(
                        args, client=client, transport=FakeTransport(result_archive()), repo=root,
                        token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                        sleep=lambda _seconds: None)
            self.assertEqual(target.read_text(), "incumbent\n")
            self.assertEqual(client.deleted, [POD])

    def test_archive_traversal_and_undeclared_outputs_are_rejected(self):
        for name in ("../escape", "other/not-declared", "results//a.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive_path = root / "bad.tar.gz"
                with tarfile.open(archive_path, "w:gz") as archive:
                    data = b"bad"
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
                with self.assertRaises(batch.BatchError):
                    batch.extract_verified(
                        archive_path, ["results"], root / "repo", root / "meta", 1 << 20)

    def test_scientific_environment_scrubs_provider_transport_and_aws_keys(self):
        environment = {
            "RUNPOD_API_KEY": "provider", "RUNPOD_BATCH_TOKEN": TOKEN,
            "AWS_SECRET_ACCESS_KEY": "aws", "ARTIFACTS_AWS_ACCESS_KEY_ID": "id",
            "SAFE": "kept",
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            clean = server.scrubbed_environment()
        self.assertEqual(clean, {"SAFE": "kept"})


class HttpAdapterTest(unittest.TestCase):
    def test_get_only_authentication_and_hash_bound_chunk(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = root / "result.tar.gz"
            result.write_bytes(b"chunk-data")
            initial = {
                "schema": server.STATUS_SCHEMA, "archive_ready": True, "done": True,
                "chunks": server.chunk_manifest(result, 1 << 20),
            }
            state = server.State(root / "state.json", initial)
            httpd = server.ThreadingHTTPServer(
                ("127.0.0.1", 0), server.handler_class(state, result, TOKEN))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_port}"
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            try:
                with self.assertRaises(urllib.error.HTTPError) as missing:
                    opener.open(base + "/v1/status", timeout=2)
                self.assertEqual(missing.exception.code, 401)
                request = urllib.request.Request(
                    base + "/v1/status", headers={"Authorization": "Bearer " + TOKEN})
                with opener.open(request, timeout=2) as response:
                    self.assertTrue(json.load(response)["archive_ready"])
                request = urllib.request.Request(
                    base + "/v1/result/000000", headers={"Authorization": "Bearer " + TOKEN})
                with opener.open(request, timeout=2) as response:
                    data = response.read()
                    self.assertEqual(data, b"chunk-data")
                    self.assertEqual(response.headers["X-Content-SHA256"], hashlib.sha256(data).hexdigest())
                request = urllib.request.Request(
                    base + "/v1/arbitrary", data=b"x", method="POST",
                    headers={"Authorization": "Bearer " + TOKEN})
                with self.assertRaises(urllib.error.HTTPError) as method:
                    opener.open(request, timeout=2)
                self.assertEqual(method.exception.code, 405)
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
