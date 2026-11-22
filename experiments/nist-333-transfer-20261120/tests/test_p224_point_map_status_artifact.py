import json
import unittest
from pathlib import Path


ARTIFACT = Path(__file__).parents[1] / "artifacts" / "p224_point_map_status.json"


class P224PointMapStatusArtifactTests(unittest.TestCase):
    def test_exact_sign_collision_and_kernel_controls(self):
        result = json.loads(ARTIFACT.read_text())
        point_map = result["implemented_map"]
        self.assertTrue(point_map["exact_sign_pair_collision"])
        self.assertEqual(point_map["base_image_sha256"], point_map["negative_image_sha256"])
        checks = result["kernel_fiber_checks"]
        self.assertTrue(checks["three_generators_exactly_collapsed"])
        self.assertTrue(checks["transverse_nonkernel_three_torsion_distinguished"])


if __name__ == "__main__":
    unittest.main()
