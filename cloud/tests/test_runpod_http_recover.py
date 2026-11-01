"""Offline controls for recovering a detached Runpod HTTP batch."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tarfile
import tempfile
import unittest


CLOUD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CLOUD))
import runpod_http_batch as batch  # noqa: E402
import runpod_http_recover as recover  # noqa: E402


TOKEN = "synthetic-recovery-bearer-with-at-least-256-random-looking-bits"
POD = "podrecover123"
NAME = "misagi-recover-0123456789ab"
COMMIT = "a" * 40
TREE = "b" * 40
SOURCE_ARCHIVE = "c" * 64
COMMAND = "printf fixture > results/a.json"
COMMAND_SHA = hashlib.sha256(COMMAND.encode()).hexdigest()


def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def args_for(root: Path):
    return SimpleNamespace(
        pod_id=POD, pod_name=NAME,
        cpu=0, gpu=["NVIDIA GeForce RTX 5090"], cpu_flavor=[], cpu_memory=0,
        gpu_count=1, min_vcpu=16, min_ram=62, cloud="SECURE",
        image="runpod/base:1.0.2-ubuntu2404", disk=100,
        max_hours=2.0, wait=10, max_price=1.19,
        source_ref="refs/heads/recovery-test", source_commit=COMMIT,
        source_tree=TREE, source_archive_sha256=SOURCE_ARCHIVE,
        command_sha256=COMMAND_SHA, command_timeout=30, max_result_mib=8,
        out=["results/a.json"],
        receipt=root / "receipt.json", archive=root / "result.tar.gz",
        tool_commit="d" * 40, reason="workspace_transport_disconnected",
    )


def listed_pod(args):
    environment = {
        "RUNPOD_BATCH_TOKEN": TOKEN,
        "RUNPOD_BATCH_OWNERSHIP_ID": hashlib.sha256(TOKEN.encode()).hexdigest(),
        "RUNPOD_BATCH_JOB_ID": args.pod_name,
        "RUNPOD_BATCH_SOURCE_URL": batch.PUBLIC_ORIGIN,
        "RUNPOD_BATCH_SOURCE_REF": args.source_ref,
        "RUNPOD_BATCH_SOURCE_COMMIT": args.source_commit,
        "RUNPOD_BATCH_SOURCE_TREE": args.source_tree,
        "RUNPOD_BATCH_SOURCE_ARCHIVE_SHA256": args.source_archive_sha256,
        "RUNPOD_BATCH_COMMAND_B64": b64(COMMAND),
        "RUNPOD_BATCH_COMMAND_SHA256": args.command_sha256,
        "RUNPOD_BATCH_OUTPUTS_B64": b64(json.dumps(args.out, separators=(",", ":"))),
        "RUNPOD_BATCH_TIMEOUT_SECONDS": str(args.command_timeout),
        "RUNPOD_BATCH_CHUNK_BYTES": str(batch.CHUNK_BYTES),
        "RUNPOD_BATCH_MAX_RESULT_BYTES": str(args.max_result_mib << 20),
        "RUNPOD_BATCH_PORT": str(batch.HTTP_PORT),
        "POD_MAX_SECONDS": str(int(args.max_hours * 3600)),
    }
    return {"id": args.pod_id, "name": args.pod_name, "env": environment}


def provider_pod(args):
    return {
        "id": args.pod_id, "name": args.pod_name, "status": "RUNNING",
        "cloud": args.cloud, "image": args.image, "cost": 1.19,
        "ports": [f"{batch.HTTP_PORT}/http"], "cudaVersion": "13.2",
        "gpu": {"id": args.gpu[0], "count": 1, "vcpuCount": 16,
                "memory": 62},
    }


def result_archive() -> bytes:
    files = {
        "results/a.json": b'{"ok":true}\n',
        ".runpod-batch/log.txt": b"synthetic recovery log\n",
        ".runpod-batch/job-status.json": b'{"returncode":0}\n',
        ".runpod-batch/source.json": b'{"source":"synthetic"}\n',
    }
    manifest = b"".join(
        hashlib.sha256(data).hexdigest().encode() + b"  " + name.encode() + b"\n"
        for name, data in files.items())
    files[".runpod-batch/files.sha256"] = manifest
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def terminal_status(args, data: bytes):
    digest = hashlib.sha256(data).hexdigest()
    return {
        "schema": batch.STATUS_SCHEMA, "job_id": args.pod_name,
        "source_commit": args.source_commit, "source_tree": args.source_tree,
        "source_archive_sha256": args.source_archive_sha256,
        "command_sha256": args.command_sha256,
        "hardware": {"pod_id": args.pod_id,
                     "gpus": [{"name": args.gpu[0]}]},
        "done": True, "archive_ready": True, "returncode": 0,
        "archive": {"sha256": digest, "bytes": len(data), "files": 5},
        "chunks": [{"index": 0, "path": "/v1/result/000000", "offset": 0,
                    "bytes": len(data), "sha256": digest}],
    }


class FakeClient:
    def __init__(self, args):
        self.args = args
        self.deleted = []

    def list_pods(self):
        return [listed_pod(self.args)]

    def get_v2(self, pod_id):
        if pod_id in self.deleted:
            raise batch.ProviderError("gone", 404)
        return provider_pod(self.args)

    def delete(self, pod_id):
        self.deleted.append(pod_id)


class FakeTransport:
    def __init__(self, args, data, fail=None):
        self.args = args
        self.data = data
        self.status = terminal_status(args, data)
        self.fail = fail

    def wait_status(self, base, token, expected, deadline, sleep,
                    provider_monitor=None):
        del base, deadline, sleep, provider_monitor
        self.assert_token(token)
        return batch.validate_status(self.status, expected)

    def download(self, base, token, status, destination):
        del base, status
        self.assert_token(token)
        if self.fail is not None:
            raise batch.BatchError(f"{self.fail}: {token}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.data)

    @staticmethod
    def assert_token(token):
        if token != TOKEN:
            raise AssertionError("wrong synthetic bearer")


class RecoveryTests(unittest.TestCase):
    def test_environment_contract_is_exact_and_redacts_bearer(self):
        with tempfile.TemporaryDirectory() as directory:
            args = args_for(Path(directory))
            args.outputs = batch.validate_outputs(args.out)
            token, safe = recover.environment_contract(listed_pod(args), args)
            self.assertEqual(token, TOKEN)
            self.assertEqual(safe["source"]["commit"], COMMIT)
            self.assertEqual(safe["outputs"], ["results/a.json"])
            self.assertNotIn(TOKEN, json.dumps(safe, sort_keys=True))

    def test_environment_contract_rejects_changed_source(self):
        with tempfile.TemporaryDirectory() as directory:
            args = args_for(Path(directory))
            args.outputs = batch.validate_outputs(args.out)
            pod = listed_pod(args)
            pod["env"]["RUNPOD_BATCH_SOURCE_TREE"] = "e" * 40
            with self.assertRaisesRegex(batch.BatchError, "frozen recovery binding"):
                recover.environment_contract(pod, args)

    def test_recovers_verifies_extracts_receipts_and_cleans_exact_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            args = args_for(root)
            data = result_archive()
            client = FakeClient(args)
            code = recover.execute(
                args, client=client, transport=FakeTransport(args, data),
                repo=repo, sleep=lambda _: None,
                tool_binding_fn=lambda _repo, commit: {
                    "path": recover.TOOL_PATH, "commit": commit,
                    "sha256": "f" * 64})
            self.assertEqual(code, 0)
            self.assertEqual(client.deleted, [POD])
            self.assertEqual((repo / "results/a.json").read_bytes(), b'{"ok":true}\n')
            receipt = json.loads(args.receipt.read_text())
            self.assertEqual(receipt["schema"], recover.SCHEMA)
            self.assertTrue(receipt["cleanup"]["absence_verified"])
            self.assertEqual(receipt["remote_status"]["returncode"], 0)
            self.assertEqual(receipt["result"]["archive_sha256"],
                             hashlib.sha256(data).hexdigest())
            self.assertNotIn(TOKEN, args.receipt.read_text())

    def test_failure_redacts_bearer_and_still_cleans(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            args = args_for(root)
            client = FakeClient(args)
            with self.assertRaisesRegex(batch.BatchError, "download failed"):
                recover.execute(
                    args, client=client,
                    transport=FakeTransport(args, result_archive(), "download failed"),
                    repo=repo, sleep=lambda _: None,
                    tool_binding_fn=lambda _repo, commit: {
                        "path": recover.TOOL_PATH, "commit": commit,
                        "sha256": "f" * 64})
            self.assertEqual(client.deleted, [POD])
            text = args.receipt.read_text()
            self.assertNotIn(TOKEN, text)
            self.assertIn("<redacted>", text)


if __name__ == "__main__":
    unittest.main()
