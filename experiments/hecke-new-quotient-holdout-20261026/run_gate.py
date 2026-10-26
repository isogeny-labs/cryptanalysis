"""Run the frozen two-sheet gate through checked Sage with a wall cap."""
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
command = ['/Volumes/SSD990/cryptanalysis/sage', '-python', str(HERE/'fiber_gate.py'),
           '--dk', '-2631', '--f', '6', '--p', '23743', '--u', '16',
           '--output', str(HERE/'fiber_gate.json')]
start = time.monotonic()
try:
    result = subprocess.run(command, cwd=HERE, capture_output=True, text=True, timeout=300)
    stdout, stderr = result.stdout, result.stderr
    exit_code, timed_out = result.returncode, False
except subprocess.TimeoutExpired as exc:
    stdout = (exc.stdout or b'').decode(errors='replace')
    stderr = (exc.stderr or b'').decode(errors='replace')
    exit_code, timed_out = None, True
(HERE/'gate.stdout').write_text(stdout)
(HERE/'gate.stderr').write_text(stderr)
receipt = {'command': command, 'cap_seconds': 300, 'exit_code': exit_code,
           'timeout': timed_out, 'wall_seconds': time.monotonic()-start}
(HERE/'gate_launch.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
