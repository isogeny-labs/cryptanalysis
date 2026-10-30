"""Run the frozen class walk after the two-sheet gate passes."""
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
gate = json.loads((HERE/'fiber_gate.json').read_text())
assert gate['status'] == 'PASS_UNIFORM_TWO_SHEET_GATE'
assert (gate['dk'], gate['f'], gate['p'], gate['u']) == (-2631, 6, 23743, 16)
command = ['/Volumes/SSD990/cryptanalysis/sage', '-python', str(HERE/'tools'/'exp11_class_walk.py')]
env = os.environ.copy()
env.update(PFS_WALK_DK='-2631', PFS_WALK_F='6', PFS_WALK_L='2,3', PFS_WALK_PMIN='23743')
start = time.monotonic()
try:
    result = subprocess.run(command, cwd=HERE, env=env, capture_output=True, text=True, timeout=600)
    stdout, stderr = result.stdout, result.stderr
    exit_code, timed_out = result.returncode, False
except subprocess.TimeoutExpired as exc:
    stdout = (exc.stdout or b'').decode(errors='replace')
    stderr = (exc.stderr or b'').decode(errors='replace')
    exit_code, timed_out = None, True
(HERE/'producer.stdout').write_text(stdout)
(HERE/'producer.stderr').write_text(stderr)
receipt = {'command': command, 'environment': {k: env[k] for k in
           ('PFS_WALK_DK','PFS_WALK_F','PFS_WALK_L','PFS_WALK_PMIN')},
           'cap_seconds': 600, 'exit_code': exit_code, 'timeout': timed_out,
           'wall_seconds': time.monotonic()-start,
           'output': 'data/exp11_class_walk_D2631_f6.json'}
(HERE/'producer_launch.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
