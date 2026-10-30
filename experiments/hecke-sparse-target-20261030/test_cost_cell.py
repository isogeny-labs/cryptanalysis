"""Correctness controls for the pending cost workload; no benchmark is run."""
import unittest
from unittest.mock import patch
from modular import Curve
from cost_cell import TunedBSGS,cuda_devices


class CostCellTests(unittest.TestCase):
    def test_tuned_table_small_cap_keeps_complete_search(self):
        curve=Curve(367);point=(5,5)
        for cap in (1,2,3,5):
            solver=TunedBSGS(curve,point,5,1,cap=cap)
            self.assertLessEqual(solver.m,cap)
            for k in range(5):self.assertEqual(solver.log(curve.mul(k,point)),k)

    def test_missing_gpu_fails_closed(self):
        with patch('cost_cell.subprocess.run',side_effect=FileNotFoundError('absent')):
            with self.assertRaisesRegex(RuntimeError,'No accessible CUDA'):
                cuda_devices()


if __name__=='__main__':unittest.main()
