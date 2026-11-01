import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "experiments"
    / "performance-saturation-20261101"
    / "gpu"
    / "analyze_gpu_aa.py"
)
SPEC = importlib.util.spec_from_file_location("gpu_aa_analyzer", SOURCE)
assert SPEC is not None and SPEC.loader is not None
ANALYZER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ANALYZER
SPEC.loader.exec_module(ANALYZER)


EXPECTED_GPU = "NVIDIA GeForce RTX 5090"
VALID_BACKEND = f"cuda:{EXPECTED_GPU} sm_120 x170 code=sm_120"


class GpuAaAnalyzerTests(unittest.TestCase):
    def write_inventory(self, session: Path, rows: list[str]) -> None:
        metadata = session / "metadata"
        metadata.mkdir(parents=True)
        (metadata / "gpu.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    @staticmethod
    def inventory_row(gpu: str) -> str:
        return f"0, GPU-test, {gpu}, 12.0, 32607, 595.91.07, P0, 50, 575, 2407, 1750"

    def test_exact_rtx5090_inventory_and_backend_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            self.write_inventory(session, [self.inventory_row(EXPECTED_GPU)])
            ANALYZER.validate_gpu_inventory(session, EXPECTED_GPU)
        self.assertEqual(
            ANALYZER.validate_cuda_backend(VALID_BACKEND, EXPECTED_GPU),
            VALID_BACKEND,
        )

    def test_rtx4090_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            self.write_inventory(
                session, [self.inventory_row("NVIDIA GeForce RTX 4090")]
            )
            with self.assertRaisesRegex(ANALYZER.GateError, "expected exactly"):
                ANALYZER.validate_gpu_inventory(session, EXPECTED_GPU)
        with self.assertRaisesRegex(ANALYZER.GateError, "unexpected CUDA GPU"):
            ANALYZER.validate_cuda_backend(
                "cuda:NVIDIA GeForce RTX 4090 sm_89 x128 code=sm_89",
                EXPECTED_GPU,
            )

    def test_malformed_and_multiple_gpu_inventory_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            self.write_inventory(session, ["0, GPU-test, NVIDIA GeForce RTX 5090"])
            with self.assertRaisesRegex(ANALYZER.GateError, "malformed"):
                ANALYZER.validate_gpu_inventory(session, EXPECTED_GPU)
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            row = self.inventory_row(EXPECTED_GPU)
            self.write_inventory(session, [row, row.replace("GPU-test", "GPU-other")])
            with self.assertRaisesRegex(ANALYZER.GateError, "exactly one GPU row"):
                ANALYZER.validate_gpu_inventory(session, EXPECTED_GPU)
        for backend in (
            f"cuda:{EXPECTED_GPU}",
            f"cuda:{EXPECTED_GPU}, {EXPECTED_GPU} sm_120 x340 code=sm_120",
            None,
        ):
            with self.subTest(backend=backend):
                with self.assertRaisesRegex(
                    ANALYZER.GateError, "malformed|unexpected CUDA GPU"
                ):
                    ANALYZER.validate_cuda_backend(backend, EXPECTED_GPU)

    def test_answer_gate_remains_exact(self) -> None:
        workload = ANALYZER.WORKLOADS[0]
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "current"
            report = {
                **ANALYZER.expected_fields(workload),
                "echelon_mode": "cuda",
                "echelon_backend": VALID_BACKEND,
            }
            prefix.with_suffix(".json").write_text(
                json.dumps(report), encoding="utf-8"
            )
            prefix.with_suffix(".log").write_text(
                "F4_F2_ECHELON: 30225 x 842 words, 27250 pivots: "
                "upload 1.0 ms, device 2.0 ms, download 3.0 ms, "
                "1.07e10 word XORs\n",
                encoding="utf-8",
            )
            prefix.with_suffix(".smi.csv").write_text("telemetry\n", encoding="utf-8")
            prefix.with_suffix(".status").write_text("0\n", encoding="utf-8")

            observed = ANALYZER.validate_execution(prefix, workload, EXPECTED_GPU)
            self.assertEqual(observed["device_ms"], 2.0)

            report["rank"] += 1
            prefix.with_suffix(".json").write_text(
                json.dumps(report), encoding="utf-8"
            )
            with self.assertRaisesRegex(ANALYZER.GateError, "rank="):
                ANALYZER.validate_execution(prefix, workload, EXPECTED_GPU)


if __name__ == "__main__":
    unittest.main()
