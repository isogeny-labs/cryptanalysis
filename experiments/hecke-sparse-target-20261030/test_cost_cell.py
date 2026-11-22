"""Correctness controls for the pending cost workload; no benchmark is run."""
import unittest
from contextlib import ExitStack,redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import cost_cell
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

    def invoke(self,workload):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        output=Path(temporary.name)/'receipt.json'
        with ExitStack() as stack:
            stack.enter_context(patch.object(sys,'argv',['cost_cell.py','--arm','generic','--out',str(output)]))
            stack.enter_context(patch('cost_cell.subprocess.run'))
            stack.enter_context(patch('cost_cell.cuda_devices',return_value=['unit-test device, not a benchmark host']))
            stack.enter_context(patch('cost_cell.run_cell',side_effect=workload))
            stack.enter_context(patch('cost_cell.signal.signal'))
            alarm=stack.enter_context(patch('cost_cell.signal.alarm'))
            stack.enter_context(redirect_stdout(io.StringIO()))
            with self.assertRaises(SystemExit) as exited:cost_cell.main()
        return exited.exception.code,json.loads(output.read_text()),alarm

    def test_timeout_retains_completed_and_interrupted_phase_evidence(self):
        def timeout(arm,progress=None):
            if progress is not None:
                progress.update(benchmark_executed=True,
                    phases={'completed':{'wall_seconds':0.25}},
                    interrupted_phase={'name':'pending','complete':False})
            raise TimeoutError('unit-test injected timeout')
        code,result,alarm=self.invoke(timeout)
        self.assertEqual(code,124)
        self.assertEqual(result['status'],'cost_cell_timeout')
        self.assertTrue(result['benchmark_executed'])
        self.assertEqual(result['phases']['completed']['wall_seconds'],0.25)
        self.assertFalse(result['interrupted_phase']['complete'])
        self.assertIsNone(result['qualified_speedup'])
        self.assertEqual(alarm.call_args.args,(0,))

    def test_arithmetic_failure_is_retained_without_an_execution_claim(self):
        def fail(arm,progress=None):raise AssertionError('unit-test arithmetic failure before work')
        code,result,alarm=self.invoke(fail)
        self.assertEqual(code,1)
        self.assertEqual(result['error_type'],'AssertionError')
        self.assertFalse(result['benchmark_executed'])
        self.assertEqual(result['phases'],{})
        self.assertEqual(alarm.call_args.args,(0,))

    def test_interrupt_retains_receipt_and_cancels_alarm(self):
        def fail(arm,progress=None):raise KeyboardInterrupt()
        code,result,alarm=self.invoke(fail)
        self.assertEqual(code,130)
        self.assertEqual(result['status'],'cost_cell_interrupted')
        self.assertEqual(alarm.call_args.args,(0,))

    def test_success_also_cancels_alarm(self):
        def done(arm,progress=None):return {'status':'unit-test success fixture'}
        code,result,alarm=self.invoke(done)
        self.assertEqual(code,0)
        self.assertEqual(result['status'],'unit-test success fixture')
        self.assertEqual(alarm.call_args.args,(0,))

    def test_interrupted_phase_is_separate_from_completed_costs(self):
        curve=Curve(367);progress={'phases':{}}
        def fail():raise ArithmeticError('injected failure within a phase')
        with self.assertRaises(ArithmeticError):
            cost_cell.record_phase(progress,'unit-phase',fail,curve)
        self.assertEqual(progress['phases'],{})
        self.assertEqual(progress['interrupted_phase']['name'],'unit-phase')
        self.assertFalse(progress['interrupted_phase']['complete'])
        self.assertGreaterEqual(progress['interrupted_phase']['wall_seconds_until_interruption'],0)

    def test_existing_receipt_prevents_any_new_workload(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'receipt.json';original=b'previous receipt\n'
            output.write_bytes(original)
            with patch.object(sys,'argv',['cost_cell.py','--arm','generic','--out',str(output)]), \
                 patch('cost_cell.subprocess.run'), \
                 patch('cost_cell.cuda_devices') as devices, \
                 patch('cost_cell.run_cell') as workload:
                with self.assertRaises(FileExistsError):cost_cell.main()
            devices.assert_not_called();workload.assert_not_called()
            self.assertEqual(output.read_bytes(),original)


if __name__=='__main__':unittest.main()
