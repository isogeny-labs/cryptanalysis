import importlib.util
from fractions import Fraction
import hashlib
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
ANALYZER_PATH = (
    REPO
    / "experiments"
    / "performance-saturation-20261101"
    / "go"
    / "analyze_remote_peer_key_ab.py"
)
SPEC = importlib.util.spec_from_file_location("go_peer_key_ab_analyzer", ANALYZER_PATH)
assert SPEC is not None and SPEC.loader is not None
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


def row(case: str, replicate: int, arm: str, *, allocation_ratio: int = 5) -> dict:
    baseline = arm == ANALYZER.BASELINE_ARM
    metrics = {
        "B/op": 100 if baseline else allocation_ratio,
        "allocs/op": 100 if baseline else allocation_ratio,
        "ns/op": 105 if baseline else 100,
        "cpu-ns/op": 105 if baseline else 100,
    }
    return {
        "warmup": False,
        "case": case,
        "replicate": replicate,
        "arm": arm,
        "parsed": {"fingerprints": {"answer": case}, "metrics": metrics},
    }


class IsolationPrimitiveTests(unittest.TestCase):
    def test_numeric_psi_gate_is_exact(self) -> None:
        snapshot = {
            "psi_cpu": (
                "some avg10=10.00 avg60=20.00 avg300=30.00 total=1\n"
                "full avg10=0.00 avg60=9.00 avg300=9.00 total=0"
            ),
            "psi_memory": (
                "some avg10=0.00 avg60=1.00 avg300=1.00 total=0\n"
                "full avg10=0.00 avg60=1.00 avg300=1.00 total=0"
            ),
        }
        self.assertTrue(ANALYZER.pressure_snapshot_passes(snapshot))
        snapshot["psi_cpu"] = snapshot["psi_cpu"].replace("10.00", "10.01", 1)
        self.assertFalse(ANALYZER.pressure_snapshot_passes(snapshot))

    def test_cgroup_deltas_require_identical_non_decreasing_inventory(self) -> None:
        self.assertEqual(
            ANALYZER.counter_deltas("low 2\nhigh 3", "low 2\nhigh 3"),
            {"high": 0, "low": 0},
        )
        with self.assertRaisesRegex(ValueError, "inventory"):
            ANALYZER.counter_deltas("low 2", "low 2\nhigh 0")
        with self.assertRaisesRegex(ValueError, "decreased"):
            ANALYZER.counter_deltas("low 2", "low 1")

    def test_transport_verifier_binds_command_source_and_one_cpu_pod(self) -> None:
        token = "V8_CANONICAL_SHA256_FROM_FREEZE"
        digest = "a" * 64
        command_template = f"runner --protocol-sha256 {token}"
        command = command_template.replace(token, digest)
        startup = "b" * 64
        environment_keys = ["ONE", "TWO"]
        protocol = {
            "freeze": {"protocol_sha256": digest},
            "extensions": {
                "remote_execution": {
                    "protocol_hash_token": token,
                    "command_template": command_template,
                    "output": "go-peer-key-ab-v8-run",
                    "transport": {
                        "authentication": "ephemeral bearer",
                        "chunk_bytes": 4194304,
                        "kind": "runpod-https-proxy",
                        "port": 8888,
                    },
                    "source": {
                        "origin": "https://github.com/isogeny-labs/cryptanalysis.git",
                        "ref": "refs/heads/codex/go-peer-key-ab-v8-20261101",
                        "commit": "c" * 40,
                        "tree": "d" * 40,
                    },
                    "container_disk_gb": 60,
                    "request_environment_keys": environment_keys,
                    "image": "runpod/base:1.0.2-ubuntu2404",
                    "pod_name_prefix": "go-peer-key-ab-v8-",
                    "max_price_usd_per_hour": 1.0,
                }
            },
        }
        command_sha = hashlib.sha256(command.encode()).hexdigest()
        receipt = {
            "command": command,
            "command_sha256": command_sha,
            "outputs": ["go-peer-key-ab-v8-run"],
            "provider_actions": True,
            "transport": protocol["extensions"]["remote_execution"]["transport"],
            "source": {
                **protocol["extensions"]["remote_execution"]["source"],
                "public_ref_checked": True,
                "archive_sha256": "e" * 64,
            },
            "request": {
                "cloudType": "SECURE",
                "computeType": "CPU",
                "containerDiskInGb": 60,
                "cpuFlavorIds": ["cpu3c"],
                "cpuFlavorPriority": "custom",
                "environment_keys": environment_keys,
                "gpuCount": None,
                "gpuTypeIds": None,
                "imageName": "runpod/base:1.0.2-ubuntu2404",
                "minRAMPerGPU": None,
                "minVCPUPerGPU": None,
                "ports": ["8888/http"],
                "secrets_redacted": True,
                "startup_sha256": startup,
                "vcpuCount": 32,
                "name": "go-peer-key-ab-v8-1234",
            },
            "pod": {
                "name": "go-peer-key-ab-v8-1234",
                "cloud": "SECURE",
                "cpu": {"id": "cpu3c", "memory": 64, "vcpuCount": 32},
                "image": "runpod/base:1.0.2-ubuntu2404",
                "gpu": None,
                "cudaVersion": None,
                "creation_response_ambiguous": False,
                "cost": 0.96,
                "id": "pod-id",
            },
            "remote_status": {
                "command_sha256": command_sha,
                "source_archive_sha256": "e" * 64,
                "source_commit": "c" * 40,
                "source_tree": "d" * 40,
                "job_id": "go-peer-key-ab-v8-1234",
                "hardware": {"pod_id": "pod-id", "gpus": []},
            },
        }
        result = ANALYZER.verify_transport(receipt, protocol)
        self.assertEqual(result["source_commit"], "c" * 40)
        changed = {**receipt, "source": {**receipt["source"], "tree": "f" * 40}}
        with self.assertRaisesRegex(ValueError, "source identity"):
            ANALYZER.verify_transport(changed, protocol)


class FormalDecisionTests(unittest.TestCase):
    def test_terminal_vocabulary_and_precedence(self) -> None:
        decide = ANALYZER.choose_verdict
        common = dict(complete=True, correctness=True)
        self.assertEqual(
            decide(**common, allocation=True, timing_numeric=True, timing_isolation=True),
            "supported_within_scope",
        )
        self.assertEqual(
            decide(**common, allocation=True, timing_numeric=False, timing_isolation=True),
            "allocation_only",
        )
        self.assertEqual(
            decide(**common, allocation=False, timing_numeric=True, timing_isolation=True),
            "timing_only",
        )
        self.assertEqual(
            decide(**common, allocation=False, timing_numeric=False, timing_isolation=True),
            "unsupported",
        )
        self.assertEqual(
            decide(**common, allocation=False, timing_numeric=True, timing_isolation=False),
            "invalid_measurement",
        )
        self.assertEqual(
            decide(
                complete=True,
                correctness=False,
                allocation=True,
                timing_numeric=True,
                timing_isolation=True,
            ),
            "wrong_answer",
        )
        self.assertEqual(
            decide(
                complete=False,
                correctness=False,
                allocation=False,
                timing_numeric=False,
                timing_isolation=False,
            ),
            "inconclusive",
        )

    def test_all_six_cases_use_exact_thresholds_and_distribution(self) -> None:
        cases = [f"case-{index}" for index in range(6)]
        rows = [
            row(case, replicate, arm)
            for case in cases
            for replicate in range(1, 21)
            for arm in (ANALYZER.BASELINE_ARM, ANALYZER.CANDIDATE_ARM)
        ]
        results, allocation, timing, pairs = ANALYZER.compute_case_results(rows, cases)
        self.assertTrue(allocation)
        self.assertTrue(timing)
        self.assertEqual(pairs, 120)
        self.assertEqual(len(results), 6)
        metric = results[0]["metrics"]["ns/op"]
        self.assertEqual(metric["paired_median"]["numerator"], "21")
        self.assertEqual(metric["paired_median"]["denominator"], "20")
        self.assertEqual(metric["simultaneous_lower_bound"]["numerator"], "21")
        self.assertEqual(metric["lower_quantile"], "1/480")
        self.assertEqual(ANALYZER.LOWER_QUANTILE, Fraction(1, 480))

    def test_allocation_requires_both_metrics_in_every_case(self) -> None:
        cases = ["case"]
        rows = [
            row("case", replicate, arm, allocation_ratio=6)
            for replicate in range(1, 21)
            for arm in (ANALYZER.BASELINE_ARM, ANALYZER.CANDIDATE_ARM)
        ]
        _, allocation, timing, pairs = ANALYZER.compute_case_results(rows, cases)
        self.assertFalse(allocation)
        self.assertTrue(timing)
        self.assertEqual(pairs, 20)

    def test_exact_276_row_mismatch_flow_is_wrong_answer_after_nonzero_exit(self) -> None:
        cases = [f"case-{index}" for index in range(6)]
        rows = [
            row(case, replicate, arm)
            for case in cases
            for replicate in range(1, 21)
            for arm in (ANALYZER.BASELINE_ARM, ANALYZER.CANDIDATE_ARM)
        ]
        for case in cases:
            for replicate in range(1, 4):
                for arm in (ANALYZER.BASELINE_ARM, ANALYZER.CANDIDATE_ARM):
                    warmup = row(case, replicate, arm)
                    warmup["warmup"] = True
                    rows.append(warmup)
        self.assertEqual(len(rows), 276)
        rows[0]["parsed"]["fingerprints"] = {"answer": "different"}
        matches, mismatches = ANALYZER.correctness_inventory(rows, cases)
        self.assertEqual((matches, mismatches), (119, 1))
        self.assertTrue(ANALYZER.transport_is_complete(1, mismatches))
        self.assertEqual(
            ANALYZER.choose_verdict(
                complete=True,
                correctness=False,
                allocation=False,
                timing_numeric=False,
                timing_isolation=True,
            ),
            "wrong_answer",
        )


if __name__ == "__main__":
    unittest.main()
