import importlib.util
import sys
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "complexity_gate.py"
SPEC = importlib.util.spec_from_file_location("complexity_gate", MODULE)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["complexity_gate"] = gate
SPEC.loader.exec_module(gate)


class ComplexityGateTests(unittest.TestCase):
    def test_prime_fields_have_no_cubic_descent(self):
        for row in gate.build_bundle()["curves"].values():
            lattice = row["subfield_lattice_certificate"]
            self.assertFalse(lattice["proper_same_characteristic_subfield_exists"])
            self.assertFalse(lattice["cubic_descent_possible_for_prime_p"])

    def test_same_field_quartic_loses_to_rho(self):
        for row in gate.build_bundle()["curves"].values():
            costs = row["same_field_costs"]
            self.assertGreater(
                costs["plane_quartic_index_calculus_soft_exponent_in_p"],
                costs["elliptic_pollard_rho_exponent_in_p"],
            )
            self.assertFalse(row["complexity_changing_gate"]["same_field_cover_or_isogeny_passes"])


if __name__ == "__main__":
    unittest.main()
