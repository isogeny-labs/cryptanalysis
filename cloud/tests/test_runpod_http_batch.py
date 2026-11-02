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
LEGACY_BODY_ENV_KEYS = {
    "POD_BOOT_B64", "POD_MAX_SECONDS", "RUNPOD_BATCH_BOOTSTRAP_B64",
    "RUNPOD_BATCH_CHUNK_BYTES", "RUNPOD_BATCH_COMMAND_B64",
    "RUNPOD_BATCH_COMMAND_SHA256", "RUNPOD_BATCH_JOB_ID",
    "RUNPOD_BATCH_MAX_RESULT_BYTES", "RUNPOD_BATCH_OUTPUTS_B64",
    "RUNPOD_BATCH_OWNERSHIP_ID", "RUNPOD_BATCH_PORT",
    "RUNPOD_BATCH_SOURCE_ARCHIVE_SHA256", "RUNPOD_BATCH_SOURCE_COMMIT",
    "RUNPOD_BATCH_SOURCE_REF", "RUNPOD_BATCH_SOURCE_TREE",
    "RUNPOD_BATCH_SOURCE_URL", "RUNPOD_BATCH_TIMEOUT_SECONDS", "RUNPOD_BATCH_TOKEN",
}
LEGACY_GPU_SUMMARY_KEYS = {
    "name", "cloudType", "computeType", "imageName", "containerDiskInGb", "ports",
    "gpuTypeIds", "gpuCount", "minVCPUPerGPU", "minRAMPerGPU", "environment_keys",
    "startup_sha256", "secrets_redacted",
}


def args_for(root: Path, returncode=0):
    del returncode
    return SimpleNamespace(
        name="misagi-http-test", cpu=0, gpu=["NVIDIA GeForce RTX 5090"],
        cpu_flavor=[], cpu_memory=0,
        gpu_count=1, min_vcpu=8, min_ram=24, cloud="SECURE", image=None,
        disk=80, max_hours=2.0, wait=10, timeout=30, max_result_mib=8,
        max_price=1.50, reconcile_seconds=0, dry_run=False,
        catalog_wait_seconds=0, catalog_poll_seconds=30,
        record_reconciliation_binding=False,
        minimal_bootstrap=False,
        source_commit=COMMIT, source_ref="refs/heads/test-http-batch",
        out=["results/a.json"], receipt=root / "receipt.json",
        archive=root / "result.tar.gz", command=["echo fixture > results/a.json"],
    )


def cpu_args_for(root: Path):
    args = args_for(root)
    args.cpu = 32
    args.gpu = []
    args.cpu_flavor = ["cpu3c"]
    args.cpu_memory = 64
    args.max_price = 1.00
    return args


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


def catalog_row(availability="LOW"):
    return {
        "id": "NVIDIA GeForce RTX 5090", "availability": availability,
        "secure": True, "community": True,
        "maxCount": {"secure": 8, "community": 8},
        "price": {"secure": 1.19, "community": 0.69},
    }


class FakeClient:
    def __init__(self, create_error=None, reconcile=False, wrong_name=False,
                 compute_type="GPU", image="runpod/base:1.0.2-ubuntu2404",
                 catalog_rows=None):
        self.create_error = create_error
        self.reconcile = reconcile
        self.create_calls = 0
        self.named_calls = 0
        self.deleted = []
        self.name = None
        self.wrong_name = wrong_name
        self.compute_type = compute_type
        self.image = image
        self.catalog_rows = catalog_rows or [[catalog_row()]]
        self.catalog_calls = 0

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
        if self.compute_type == "CPU":
            return {
                "id": pod_id, "name": self.name, "status": "RUNNING",
                "cpu": {"id": "cpu3c", "vcpuCount": 32, "memory": 64},
                "gpu": None, "cost": 0.96, "cloud": "SECURE",
                "image": "runpod/base:1.0.2-ubuntu2404", "cudaVersion": None,
                "ports": ["8888/http"], "dataCenterId": "EU-RO-1",
                "createdAt": "synthetic", "startedAt": "synthetic",
            }
        return {
            "id": pod_id, "name": self.name, "status": "RUNNING",
            "gpu": {"id": "NVIDIA GeForce RTX 5090", "count": 1,
                    "vcpuCount": 16, "memory": 62},
            "cost": 1.19, "cloud": "SECURE", "image": self.image,
            "cudaVersion": "13.2", "ports": ["8888/http"], "dataCenterId": "EU-RO-1",
            "createdAt": "synthetic", "startedAt": "synthetic",
        }

    def delete(self, pod_id):
        self.deleted.append(pod_id)

    def list_pods(self):
        return []

    def gpu_catalog(self, cloud, count):
        self.assert_catalog_request = (cloud, count)
        index = min(self.catalog_calls, len(self.catalog_rows) - 1)
        self.catalog_calls += 1
        return self.catalog_rows[index]


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
        if expected["compute_type"] == "CPU":
            status["hardware"]["gpus"] = []
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
        self.assertNotIn("cpuFlavorIds", summary)
        self.assertEqual(set(body["env"]), LEGACY_BODY_ENV_KEYS)
        self.assertEqual(set(batch.request_summary(body)), LEGACY_GPU_SUMMARY_KEYS)
        self.assertEqual(body["dockerEntrypoint"], ["bash", "-c"])
        self.assertEqual(
            hashlib.sha256(body["dockerStartCmd"][0].encode()).hexdigest(),
            "15d32b2c8eb6e004b3b4fbb60c6be0bbd88486561dc373cca7140b3e8286ec9b",
        )
        self.assertEqual(
            hashlib.sha256(base64.b64decode(body["env"]["POD_BOOT_B64"])).hexdigest(),
            "2074fb363f6972943a7d6ac004f510449bb2e57f0362ae0e28dc4a9d3fa7b297",
        )
        bootstrap = base64.b64decode(body["env"]["RUNPOD_BATCH_BOOTSTRAP_B64"]).decode()
        self.assertIn('cd "$JOB_WORKDIR"', bootstrap)
        self.assertNotIn("cd /root/cryptanalysis", bootstrap)

    def test_minimal_bootstrap_has_no_generic_environment_install(self):
        with tempfile.TemporaryDirectory() as directory:
            args = args_for(Path(directory))
            args.minimal_bootstrap = True
            body = batch.build_body(
                args, "misagi-http-test-0123456789ab", TOKEN,
                source_identity(), "echo fixture > results/a.json", ["results/a.json"],
            )
        bootstrap = base64.b64decode(
            body["env"]["RUNPOD_BATCH_BOOTSTRAP_B64"], validate=True,
        ).decode()
        self.assertEqual(bootstrap, batch.MINIMAL_BOOTSTRAP)
        self.assertIn('cd "$JOB_WORKDIR"', bootstrap)
        for forbidden in ("pod_env", "rustup", "pip install", "nvrtc", "apt-get"):
            self.assertNotIn(forbidden, bootstrap.lower())
        self.assertEqual(
            batch.request_summary(body)["bootstrap_sha256"],
            hashlib.sha256(bootstrap.encode()).hexdigest(),
        )
        self.assertEqual(
            batch.request_summary(body)["remote_boot_sha256"],
            hashlib.sha256(base64.b64decode(
                body["env"]["POD_BOOT_B64"], validate=True,
            )).hexdigest(),
        )
        self.assertEqual(
            batch.request_summary(body)["entrypoint"],
            ["/usr/bin/bash", "--noprofile", "--norc", "-c"],
        )
        self.assertEqual(body["env"]["BASH_ENV"], "/dev/null")
        self.assertEqual(body["env"]["PYTHONPATH"], "")
        self.assertEqual(
            body["env"]["PATH"],
            "/usr/bin:/bin",
        )
        self.assertEqual(
            body["dockerEntrypoint"],
            ["/usr/bin/bash", "--noprofile", "--norc", "-c"],
        )
        remote_boot = base64.b64decode(body["env"]["POD_BOOT_B64"], validate=True).decode()
        self.assertEqual(remote_boot, batch.MINIMAL_REMOTE_BOOT)
        self.assertIn("export PATH=/usr/bin:/bin", remote_boot)
        self.assertIn("/usr/bin/git", remote_boot)
        self.assertNotIn("apt-get", remote_boot)
        self.assertNotIn("pod_env", remote_boot)
        stage0 = body["dockerStartCmd"][0]
        self.assertEqual(stage0, batch.MINIMAL_STAGE0)
        self.assertIn("/usr/bin/base64 --decode", stage0)
        self.assertIn("/usr/bin/setsid /usr/bin/bash --noprofile --norc", stage0)
        self.assertIn("exec /usr/bin/sleep infinity", stage0)
        self.assertNotIn("SHIP_PREFETCH", stage0)
        self.assertNotIn("/start.sh", stage0)
        self.assertEqual(
            batch.request_summary(body)["startup_sha256"],
            hashlib.sha256(stage0.encode()).hexdigest(),
        )

    def test_server_treats_absent_closure_key_as_legacy_false(self):
        with tempfile.TemporaryDirectory() as directory:
            args = args_for(Path(directory))
            body = batch.build_body(
                args, "misagi-http-test-0123456789ab", TOKEN,
                source_identity(), "echo fixture > results/a.json", ["results/a.json"],
            )
        self.assertNotIn("RUNPOD_BATCH_ENVIRONMENT_CLOSED", body["env"])
        git_results = [
            __import__("subprocess").CompletedProcess([], 0, stdout=COMMIT + "\n"),
            __import__("subprocess").CompletedProcess([], 0, stdout=TREE + "\n"),
        ]
        with mock.patch.dict(os.environ, body["env"], clear=True), \
                mock.patch.object(server.subprocess, "run", side_effect=git_results) as run:
            config = server.read_config(Path("/synthetic/repo"))
        self.assertFalse(config["environment_closed"])
        self.assertEqual(run.call_args_list[0].args[0], ["git", "rev-parse", "HEAD"])
        self.assertNotIn("env", run.call_args_list[0].kwargs)

        args.minimal_bootstrap = True
        closed_body = batch.build_body(
            args, "misagi-http-test-0123456789ab", TOKEN,
            source_identity(), "echo fixture > results/a.json", ["results/a.json"],
        )
        git_results = [
            __import__("subprocess").CompletedProcess([], 0, stdout=COMMIT + "\n"),
            __import__("subprocess").CompletedProcess([], 0, stdout=TREE + "\n"),
        ]
        with mock.patch.dict(os.environ, closed_body["env"], clear=True), \
                mock.patch.object(server.subprocess, "run", side_effect=git_results) as run:
            config = server.read_config(Path("/synthetic/repo"))
        self.assertTrue(config["environment_closed"])
        self.assertEqual(
            run.call_args_list[0].args[0], ["/usr/bin/git", "rev-parse", "HEAD"],
        )
        self.assertEqual(run.call_args_list[0].kwargs["env"], server.GIT_ENV)

    def test_cpu_body_binds_one_exact_flavor_and_no_ssh(self):
        with tempfile.TemporaryDirectory() as directory:
            args = cpu_args_for(Path(directory))
            body = batch.build_body(
                args, "misagi-http-test-0123456789ab", TOKEN,
                source_identity(), "echo fixture > results/a.json", ["results/a.json"])
        self.assertEqual(body["computeType"], "CPU")
        self.assertEqual(body["cpuFlavorIds"], ["cpu3c"])
        self.assertEqual(body["cpuFlavorPriority"], "custom")
        self.assertEqual(body["vcpuCount"], 32)
        self.assertEqual(body["ports"], ["8888/http"])
        self.assertNotIn("gpuTypeIds", body)
        summary = batch.request_summary(body)
        self.assertEqual(summary["cpuFlavorIds"], ["cpu3c"])
        self.assertEqual(summary["vcpuCount"], 32)

    def test_cpu_cli_parses_exact_memory_guard(self):
        args = batch.parse([
            "cpu-http", "--cpu", "32", "--cpu-flavor", "cpu3c",
            "--cpu-memory", "64", "--source-ref", "refs/heads/test-http-batch",
            "--source-commit", COMMIT, "--receipt", "receipt.json",
            "--out", "results", "--max-price", "1.00", "--", "true",
        ])
        self.assertEqual(args.cpu, 32)
        self.assertEqual(args.cpu_flavor, ["cpu3c"])
        self.assertEqual(args.cpu_memory, 64)
        self.assertEqual(args.command, ["true"])

    def test_cpu_request_rejects_ambiguous_or_unbound_placement(self):
        with tempfile.TemporaryDirectory() as directory:
            base = cpu_args_for(Path(directory))
            bad = [
                {"cpu_flavor": ["cpu3c", "cpu5c"]},
                {"cpu_memory": 0},
                {"cpu": 12},
                {"cloud": "COMMUNITY"},
                {"gpu": ["NVIDIA GeForce RTX 5090"]},
            ]
            for changes in bad:
                args = SimpleNamespace(**vars(base))
                for key, value in changes.items():
                    setattr(args, key, value)
                with self.subTest(changes=changes), self.assertRaises(batch.BatchError):
                    batch.validate_compute_request(args)

    def test_cpu_provider_guard_is_exact_and_rejects_gpu_or_ssh(self):
        with tempfile.TemporaryDirectory() as directory:
            args = cpu_args_for(Path(directory))
            client = FakeClient(compute_type="CPU")
            client.name = "misagi-http-test-0123456789ab"
            good = client.get_v2(POD)
            summary = batch.guard_provider(good, POD, client.name, args)
            self.assertEqual(summary["cpu"]["id"], "cpu3c")
            mutations = [
                ("flavor", lambda pod: pod["cpu"].update(id="cpu5c")),
                ("vcpu", lambda pod: pod["cpu"].update(vcpuCount=16)),
                ("vcpu-bool", lambda pod: pod["cpu"].update(vcpuCount=True)),
                ("memory", lambda pod: pod["cpu"].update(memory=63)),
                ("memory-gib-reinterpretation",
                 lambda pod: pod["cpu"].update(memory=64 << 30)),
                ("memory-float", lambda pod: pod["cpu"].update(memory=64.0)),
                ("gpu", lambda pod: pod.update(gpu={"id": "unexpected"})),
                ("cuda", lambda pod: pod.update(cudaVersion="13.2")),
                ("ssh", lambda pod: pod["ports"].append("22/tcp")),
                ("cost", lambda pod: pod.update(cost=1.01)),
            ]
            for label, mutate in mutations:
                pod = json.loads(json.dumps(good))
                mutate(pod)
                with self.subTest(label=label), self.assertRaises(batch.BatchError):
                    batch.guard_provider(pod, POD, client.name, args)

    def test_cpu_dry_run_has_exact_guard_and_no_provider_action(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = cpu_args_for(root)
            args.dry_run = True
            output = io.StringIO()
            with (mock.patch.object(batch, "source_identity", return_value=source_identity()),
                  mock.patch("sys.stdout", new=output)):
                rc = batch.execute(args, repo=root)
        self.assertEqual(rc, 0)
        plan = json.loads(output.getvalue())
        self.assertFalse(plan["provider_actions"])
        self.assertEqual(plan["request"]["computeType"], "CPU")
        self.assertEqual(plan["request"]["cpuFlavorIds"], ["cpu3c"])
        self.assertEqual(plan["cpu_guard"], {
            "flavor": "cpu3c", "provider_memory_value": 64,
            "no_gpu": True, "vcpu_count": 32,
        })

    def test_proxy_url_and_source_ref_validation(self):
        self.assertEqual(batch.proxy_base(POD), f"https://{POD}-8888.proxy.runpod.net")
        for value in ("../bad", "refs/tags/v1", "refs/heads/../bad", "refs/heads/a.lock"):
            with self.assertRaises(batch.BatchError):
                batch.validate_source_ref(value)

    def test_malformed_status_list_is_rejected_cleanly(self):
        with self.assertRaises(batch.BatchError):
            batch.validate_status([], {})

    def test_remote_boot_is_shell_syntax(self):
        for script in (batch.REMOTE_BOOT, batch.MINIMAL_REMOTE_BOOT, batch.MINIMAL_STAGE0):
            result = __import__("subprocess").run(
                ["bash", "-n"], input=script, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_digest_qualified_image_must_echo_exactly_and_mismatch_is_cleaned(self):
        digest_image = (
            "runpod/base:1.0.2-ubuntu2404@sha256:"
            "e93bf61149910d35407fc865078ceb9b2887e986befd2b7c0eee322abe47ac59"
        )
        with tempfile.TemporaryDirectory() as directory:
            args = args_for(Path(directory))
            args.image = digest_image
            exact = FakeClient(image=digest_image)
            exact.name = "misagi-http-test-0123456789ab"
            summary = batch.guard_provider(exact.get_v2(POD), POD, exact.name, args)
            self.assertEqual(summary["image"], digest_image)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            args.image = digest_image
            normalized = FakeClient(image="runpod/base:1.0.2-ubuntu2404")
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                with self.assertRaises(batch.BatchError):
                    batch.execute(
                        args, client=normalized, transport=FakeTransport(result_archive()),
                        repo=root, token_factory=lambda: TOKEN,
                        nonce_factory=lambda: "0123456789ab", sleep=lambda _seconds: None,
                    )
            self.assertEqual(normalized.deleted, [POD])

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

    def test_cpu_success_fetches_and_receipt_binds_exact_provider_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = cpu_args_for(root)
            client = FakeClient(compute_type="CPU")
            transport = FakeTransport(result_archive())
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                rc = batch.execute(
                    args, client=client, transport=transport, repo=root,
                    token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                    sleep=lambda _seconds: None)
            self.assertEqual(rc, 0)
            self.assertEqual(client.deleted, [POD])
            receipt = json.loads(args.receipt.read_text())
            self.assertEqual(receipt["cpu_guard"], {
                "flavor": "cpu3c", "provider_memory_value": 64,
                "no_gpu": True, "vcpu_count": 32,
            })
            self.assertEqual(receipt["pod"]["cpu"], {
                "id": "cpu3c", "memory": 64, "vcpuCount": 32,
            })
            self.assertIsNone(receipt["pod"]["gpu"])
            self.assertEqual(receipt["remote_status"]["hardware"]["gpus"], [])

    def test_cpu_remote_status_rejects_reported_gpu(self):
        data = result_archive()
        status = terminal_status(data)
        expected = {
            "job_id": status["job_id"], "commit": COMMIT, "tree": TREE,
            "archive_sha256": SOURCE_ARCHIVE,
            "command_sha256": status["command_sha256"], "pod_id": POD,
            "compute_type": "CPU", "gpu_count": 0,
            "max_result_bytes": 8 << 20,
        }
        with self.assertRaises(batch.BatchError):
            batch.validate_status(status, expected)

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

    def test_create_refusal_retains_redacted_provider_cause_and_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            args.record_reconciliation_binding = True
            client = FakeClient(batch.ProviderError(
                f"capacity refused {TOKEN}", 500))
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                with self.assertRaises(batch.BatchError):
                    batch.execute(
                        args, client=client, transport=FakeTransport(result_archive()), repo=root,
                        token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                        sleep=lambda _seconds: None)
            receipt = json.loads(args.receipt.read_text())
            self.assertEqual(client.create_calls, 1)
            self.assertEqual(client.deleted, [])
            self.assertEqual(receipt["error"]["cause"]["type"], "ProviderError")
            self.assertEqual(receipt["error"]["cause"]["provider_status"], 500)
            self.assertIn("<redacted>", receipt["error"]["cause"]["detail"])
            self.assertNotIn(TOKEN, args.receipt.read_text())
            self.assertEqual(
                receipt["reconciliation"]["ownership_id"],
                hashlib.sha256(TOKEN.encode()).hexdigest())
            self.assertTrue(receipt["reconciliation"]["attempted"])
            self.assertEqual(receipt["reconciliation"]["last_match_count"], 0)

    def test_catalog_gate_waits_for_capacity_before_the_only_create(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            args.catalog_wait_seconds = 30
            args.catalog_poll_seconds = 30
            client = FakeClient(catalog_rows=[
                [catalog_row("NONE")], [catalog_row("LOW")],
            ])
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                rc = batch.execute(
                    args, client=client, transport=FakeTransport(result_archive()), repo=root,
                    token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                    sleep=lambda _seconds: None)
            receipt = json.loads(args.receipt.read_text())
            self.assertEqual(rc, 0)
            self.assertEqual(client.catalog_calls, 2)
            self.assertEqual(client.create_calls, 1)
            self.assertEqual(receipt["capacity_gate"]["first"]["availability"], "NONE")
            self.assertEqual(receipt["capacity_gate"]["last"]["availability"], "LOW")
            self.assertTrue(receipt["capacity_gate"]["passed"])
            self.assertTrue(receipt["capacity_gate"]["create_attempted"])

    def test_catalog_timeout_does_not_spend_create_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = args_for(root)
            args.catalog_wait_seconds = 30
            args.catalog_poll_seconds = 30
            client = FakeClient(catalog_rows=[[catalog_row("NONE")]])
            with mock.patch.object(batch, "source_identity", return_value=source_identity()):
                with self.assertRaises(batch.BatchError):
                    batch.execute(
                        args, client=client, transport=FakeTransport(result_archive()), repo=root,
                        token_factory=lambda: TOKEN, nonce_factory=lambda: "0123456789ab",
                        sleep=lambda _seconds: None)
            receipt = json.loads(args.receipt.read_text())
            self.assertEqual(client.catalog_calls, 2)
            self.assertEqual(client.create_calls, 0)
            self.assertFalse(receipt["capacity_gate"]["passed"])
            self.assertFalse(receipt["capacity_gate"]["create_attempted"])
            self.assertIn("sole create attempt was not spent", receipt["error"]["detail"])

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
            "SAFE": "dropped", "BASH_ENV": "/tmp/hook", "ENV": "/tmp/hook",
            "PYTHONPATH": "/tmp/injected", "PYTHONHOME": "/tmp/python",
            "PYTHONSTARTUP": "/tmp/startup", "LD_PRELOAD": "/tmp/injected.so",
            "RUNPOD_POD_ID": "pod-1", "HTTPS_PROXY": "http://proxy.invalid",
            "LD_LIBRARY_PATH": "/usr/local/nvidia/lib64",
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            clean = server.scrubbed_environment(environment_closed=True)
        self.assertEqual(clean, {
            **server.SCIENTIFIC_FIXED_ENV,
            "RUNPOD_POD_ID": "pod-1", "HTTPS_PROXY": "http://proxy.invalid",
            "LD_LIBRARY_PATH": "/usr/local/nvidia/lib64",
        })
        for forbidden in (
            "SAFE", "BASH_ENV", "ENV", "PYTHONPATH", "PYTHONHOME",
            "PYTHONSTARTUP", "LD_PRELOAD", "RUNPOD_API_KEY", "RUNPOD_BATCH_TOKEN",
        ):
            self.assertNotIn(forbidden, clean)

        # Legacy batch jobs preserve the exact old environment behavior.
        with mock.patch.dict(os.environ, environment, clear=True):
            compatible = server.scrubbed_environment(environment_closed=False)
        self.assertEqual(compatible.get("SAFE"), "dropped")
        self.assertEqual(compatible.get("RUNPOD_POD_ID"), "pod-1")
        for hook in server.STARTUP_HOOK_ENV_NAMES:
            if hook in environment:
                self.assertEqual(compatible.get(hook), environment[hook])
        for forbidden in server.SECRET_ENV_NAMES:
            self.assertNotIn(forbidden, compatible)

    def test_server_runtime_commands_preserve_legacy_and_close_v11(self):
        completed = __import__("subprocess").CompletedProcess([], 0, stdout="")
        for closed in (False, True):
            with self.subTest(closed=closed), mock.patch.object(
                server.subprocess, "run", side_effect=[completed, completed],
            ) as run:
                server.hardware(closed)
            smi, shell = run.call_args_list
            self.assertEqual(
                smi.args[0][0], "/usr/bin/nvidia-smi" if closed else "nvidia-smi",
            )
            self.assertEqual(
                shell.args[0][:4],
                (["/usr/bin/bash", "--noprofile", "--norc", "-c"]
                 if closed else ["bash", "-lc", "command -v nvcc >/dev/null && nvcc --version || true"][:4]),
            )
            if closed:
                self.assertEqual(smi.kwargs["env"], server.SCIENTIFIC_FIXED_ENV)
                self.assertEqual(shell.kwargs["env"], server.SCIENTIFIC_FIXED_ENV)
            else:
                self.assertNotIn("env", smi.kwargs)
                self.assertNotIn("env", shell.kwargs)

        class State:
            def update(self, **_values):
                pass

        config = {
            "bootstrap": "true", "command": "true", "timeout": 30,
            "job_id": "job-1", "outputs": ["results"], "commit": COMMIT,
            "tree": TREE, "source_archive_sha256": SOURCE_ARCHIVE,
            "command_sha256": "d" * 64, "max_result_bytes": 1 << 20,
            "chunk_bytes": 1 << 20,
        }
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for closed in (False, True):
                current = {**config, "environment_closed": closed}
                child = mock.Mock()
                child.wait.return_value = 0
                with self.subTest(closed=closed), \
                        mock.patch.object(server, "scrubbed_environment", return_value={}), \
                        mock.patch.object(server.subprocess, "Popen", return_value=child) as popen, \
                        mock.patch.object(server, "build_result_archive", return_value={}), \
                        mock.patch.object(server, "chunk_manifest", return_value=[]):
                    server.run_job(
                        repo, repo / "job", repo / "result.tar.gz", current, State(), {},
                    )
                argv = popen.call_args.args[0]
                environment = popen.call_args.kwargs["env"]
                self.assertEqual(argv[0], "/usr/bin/bash" if closed else "bash")
                if closed:
                    self.assertIn("/usr/bin/timeout", environment["JOB_CMD"])
                    self.assertIn("/usr/bin/bash --noprofile --norc", environment["JOB_CMD"])
                    self.assertEqual(environment["JOB_ENVIRONMENT_CLOSED"], "1")
                else:
                    self.assertTrue(environment["JOB_CMD"].startswith("timeout "))
                    self.assertIn(" bash -c ", environment["JOB_CMD"])
                    self.assertNotIn("JOB_ENVIRONMENT_CLOSED", environment)


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
