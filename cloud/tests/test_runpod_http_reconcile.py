"""Offline controls for delayed ambiguous-create cleanup."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace


CLOUD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CLOUD))
import runpod_http_batch as batch  # noqa: E402
import runpod_http_reconcile as reconcile  # noqa: E402


TOKEN = "synthetic-http-bearer-with-at-least-256-random-looking-bits"
OWNERSHIP = hashlib.sha256(TOKEN.encode()).hexdigest()
NAME = "misagi-f4-geometry-v12-0123456789ab"
POD_ID = "pod_delayed_123"


def controller_receipt() -> dict:
    return {
        "schema": batch.SCHEMA,
        "provider_actions": True,
        "request": {
            "api": "runpod-rest/v2", "name": NAME, "cloud": "SECURE",
            "image": "synthetic/image:v2", "disk": 1,
            "ports": ["8888/http"], "mounts": {},
            "gpu": {
                "id": "synthetic-gpu", "count": 1,
                "minVcpuCountPerGpu": 1, "minRamPerGpu": 1,
            },
            "cpu": None, "globalNetworking": False,
            "startJupyter": False, "startSsh": False,
            "environment_keys": [
                "POD_MAX_SECONDS", "RUNPOD_BATCH_OWNERSHIP_ID",
                "RUNPOD_BATCH_TOKEN",
            ],
            "startup_sha256": "1" * 64, "entrypoint": ["bash", "-c"],
            "secrets_redacted": True,
        },
        "provider_api": batch.provider_api_binding(),
        "reconciliation": {
            "name": NAME,
            "ownership_id": OWNERSHIP,
            "attempted": True,
            "attempts": 1,
            "last_match_count": 0,
            "owned_pod_id": None,
        },
        "pod": None,
        "cleanup": None,
        "error": {"type": "BatchError", "detail": "ambiguous create"},
    }


def v2_pod(pod_id=POD_ID, ownership=OWNERSHIP):
    return {
        "id": pod_id, "name": NAME, "status": "RUNNING",
        "actions": ["stop", "terminate"], "image": "synthetic/image:v2",
        "args": "", "disk": 1, "mounts": {}, "ports": ["8888/http"],
        "env": {"RUNPOD_BATCH_OWNERSHIP_ID": ownership}, "registry": None,
        "cloud": "SECURE", "dataCenterId": "SYNTHETIC", "cudaVersion": "13.2",
        "ssh": {}, "template": None, "cost": 0.1, "locked": False,
        "runtime": None, "createdAt": "synthetic", "startedAt": "synthetic",
        "globalNetworking": {"enabled": False},
        "gpu": {"id": "synthetic-gpu", "count": 1,
                "vcpuCount": 1, "memory": 1},
    }


class FakeClient:
    def __init__(self, pods):
        self.pods = pods
        self.deleted = []

    def named(self, name):
        return [pod for pod in self.pods if pod.get("name") == name]

    def delete(self, pod_id):
        self.deleted.append(pod_id)

    def get_v2(self, pod_id):
        if pod_id in self.deleted:
            raise batch.ProviderError("gone", 404)
        return next(pod for pod in self.pods if pod.get("id") == pod_id)


class AmbiguousCreateReconciliationTests(unittest.TestCase):
    def run_case(self, client, mutate=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        source = root / "controller.json"
        value = controller_receipt()
        if mutate is not None:
            mutate(value)
        source.write_text(json.dumps(value), encoding="utf-8")
        out = root / "reconciliation.json"
        args = SimpleNamespace(controller_receipt=source, out=out)
        return args, out, client

    def test_no_exact_owned_pod_records_absence_without_delete(self):
        args, out, client = self.run_case(FakeClient([]))
        self.assertEqual(reconcile.execute(args, client=client, sleep=lambda _s: None), 0)
        record = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(
            record["schema"], "runpod.http-batch.ambiguous-create-reconciliation/v2")
        self.assertEqual(record["provider_api"]["version"], "v2")
        self.assertEqual(record["provider_http"]["inventory"], {
            "method": "GET", "path": "/v2/pods", "status": 200,
            "pagination": "complete",
        })
        self.assertTrue(record["absence_verified_by_name_and_marker"])
        self.assertIsNone(record["matched_pod_id"])
        self.assertEqual(client.deleted, [])

    def test_one_exact_owned_pod_is_deleted_and_404_verified(self):
        pod = v2_pod()
        args, out, client = self.run_case(FakeClient([pod]))
        self.assertEqual(reconcile.execute(args, client=client, sleep=lambda _s: None), 0)
        record = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(record["matched_pod_id"], POD_ID)
        self.assertEqual(client.deleted, [POD_ID])
        self.assertEqual(record["cleanup"], {
            "id": POD_ID, "delete_requested": True,
            "delete_http_status": 204, "absence_http_status": 404,
            "absence_verified": True,
        })
        self.assertEqual(record["provider_http"]["cleanup"], {
            "delete": {
                "method": "DELETE", "path": f"/v2/pods/{POD_ID}", "status": 204,
            },
            "absence": {
                "method": "GET", "path": f"/v2/pods/{POD_ID}", "status": 404,
            },
        })

    def test_wrong_ownership_marker_is_never_deleted(self):
        pod = v2_pod(ownership="0" * 64)
        args, out, client = self.run_case(FakeClient([pod]))
        self.assertEqual(reconcile.execute(args, client=client, sleep=lambda _s: None), 0)
        self.assertEqual(client.deleted, [])
        self.assertTrue(json.loads(out.read_text())["absence_verified_by_name_and_marker"])

    def test_changed_current_ownership_marker_is_never_deleted(self):
        class ChangedOwnershipClient(FakeClient):
            def get_v2(self, pod_id):
                return v2_pod(pod_id, ownership="0" * 64)

        args, out, client = self.run_case(ChangedOwnershipClient([v2_pod()]))
        with self.assertRaisesRegex(batch.BatchError, "reconciliation ownership"):
            reconcile.execute(args, client=client, sleep=lambda _s: None)
        self.assertEqual(client.deleted, [])
        record = json.loads(out.read_text())
        self.assertEqual(record["matched_pod_id"], POD_ID)
        self.assertEqual(record["provider_http"]["ownership"], {
            "method": "GET", "path": f"/v2/pods/{POD_ID}", "status": 200,
        })
        self.assertIsNotNone(record["error"])

    def test_multiple_owned_matches_fail_closed_without_delete(self):
        pods = [v2_pod(POD_ID + suffix) for suffix in ("a", "b")]
        args, out, client = self.run_case(FakeClient(pods))
        with self.assertRaises(batch.BatchError):
            reconcile.execute(args, client=client, sleep=lambda _s: None)
        self.assertEqual(client.deleted, [])
        self.assertIsNotNone(json.loads(out.read_text())["error"])

    def test_receipt_with_existing_pod_identity_is_refused(self):
        args, _out, client = self.run_case(
            FakeClient([]), lambda value: value.update(pod={"id": POD_ID}),
        )
        with self.assertRaises(batch.BatchError):
            reconcile.execute(args, client=client, sleep=lambda _s: None)
        self.assertEqual(client.deleted, [])

    def test_legacy_or_unbound_transport_receipt_is_refused(self):
        mutations = {
            "missing-v2-api": lambda value: value["request"].pop("api"),
            "legacy-request-key": lambda value: value["request"].update(
                cloudType="SECURE"),
            "wrong-openapi": lambda value: value["provider_api"].update(
                openapi_sha256="0" * 64),
        }
        for label, mutate in mutations.items():
            args, out, client = self.run_case(FakeClient([]), mutate)
            with self.subTest(label=label), self.assertRaises(batch.BatchError):
                reconcile.execute(args, client=client, sleep=lambda _s: None)
            self.assertFalse(out.exists())
            self.assertEqual(client.deleted, [])

    def test_capacity_timeout_without_create_attempt_is_refused(self):
        def mark_unspent(value):
            value["capacity_gate"] = {"create_attempted": False}
            value["reconciliation"].update({
                "attempted": False,
                "attempts": 0,
                "last_match_count": None,
            })

        args, out, client = self.run_case(FakeClient([]), mark_unspent)
        with self.assertRaises(batch.BatchError):
            reconcile.execute(args, client=client, sleep=lambda _s: None)
        self.assertFalse(out.exists())
        self.assertEqual(client.deleted, [])

    def test_failed_immediate_inventory_remains_reconcilable(self):
        def mark_inventory_failure(value):
            value["capacity_gate"] = {"create_attempted": True}
            value["reconciliation"]["last_match_count"] = None

        args, out, client = self.run_case(FakeClient([]), mark_inventory_failure)
        self.assertEqual(reconcile.execute(args, client=client, sleep=lambda _s: None), 0)
        self.assertTrue(json.loads(out.read_text())["absence_verified_by_name_and_marker"])
        self.assertEqual(client.deleted, [])

    def test_non_integer_zero_match_counts_are_refused(self):
        for malformed in (False, 0.0):
            with self.subTest(malformed=malformed):
                args, out, client = self.run_case(
                    FakeClient([]),
                    lambda value, malformed=malformed: value["reconciliation"].update(
                        last_match_count=malformed),
                )
                with self.assertRaises(batch.BatchError):
                    reconcile.execute(args, client=client, sleep=lambda _s: None)
                self.assertFalse(out.exists())
                self.assertEqual(client.deleted, [])


if __name__ == "__main__":
    unittest.main()
