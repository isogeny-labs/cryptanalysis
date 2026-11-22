"""Run the frozen public-point circuit with exact batched residuals."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ROOT = PARENT.parent
OLD = ROOT/'n131_w18_two_terminal_bilinear_20261015'
sys.path.insert(0,str(PARENT))
sys.path.insert(0,str(OLD))
import batch  # noqa: E402
import terminal as prior  # noqa: E402


def configure():
    prior.HERE = HERE
    prior.SOLVER_CAP = 590
    prior.SOLVER_FLAGS = ['--threads=1','--maxtime=590','--zero-exit-status',
                          '--verb=1','--printsol=1']
    def exact_residuals(raw_target, joint_states):
        rows, _ = batch.residuals(raw_target,joint_states,prior.independent)
        return rows
    prior.residuals = exact_residuals
    return prior


if __name__=='__main__':
    configure().query()
