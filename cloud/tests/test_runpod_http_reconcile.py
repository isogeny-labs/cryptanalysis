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
        "request": {"name": NAME},
        "reconciliation": {"name": NAME, "ownership_id": OWNERSHIP},
        "pod": None,
        "cleanup": None,
        "error": {"type": "BatchError", "detail": "ambiguous create"},
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
        self.assertTrue(record["absence_verified_by_name_and_marker"])
        self.assertIsNone(record["matched_pod_id"])
        self.assertEqual(client.deleted, [])

    def test_one_exact_owned_pod_is_deleted_and_404_verified(self):
        pod = {
            "id": POD_ID, "name": NAME,
            "env": {"RUNPOD_BATCH_OWNERSHIP_ID": OWNERSHIP},
        }
        args, out, client = self.run_case(FakeClient([pod]))
        self.assertEqual(reconcile.execute(args, client=client, sleep=lambda _s: None), 0)
        record = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(record["matched_pod_id"], POD_ID)
        self.assertEqual(client.deleted, [POD_ID])
        self.assertEqual(record["cleanup"], {
            "id": POD_ID, "delete_requested": True, "absence_verified": True,
        })

    def test_wrong_ownership_marker_is_never_deleted(self):
        pod = {
            "id": POD_ID, "name": NAME,
            "env": {"RUNPOD_BATCH_OWNERSHIP_ID": "0" * 64},
        }
        args, out, client = self.run_case(FakeClient([pod]))
        self.assertEqual(reconcile.execute(args, client=client, sleep=lambda _s: None), 0)
        self.assertEqual(client.deleted, [])
        self.assertTrue(json.loads(out.read_text())["absence_verified_by_name_and_marker"])

    def test_multiple_owned_matches_fail_closed_without_delete(self):
        pods = [
            {"id": POD_ID + suffix, "name": NAME,
             "env": {"RUNPOD_BATCH_OWNERSHIP_ID": OWNERSHIP}}
            for suffix in ("a", "b")
        ]
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


if __name__ == "__main__":
    unittest.main()
