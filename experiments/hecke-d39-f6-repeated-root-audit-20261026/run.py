"""Save runtime and bounded checked-Sage scan receipts."""
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
SAGE = '/Volumes/SSD990/cryptanalysis/sage'
runtime = subprocess.run([SAGE, '--runtime-info'], capture_output=True, text=True, check=True)
(HERE / 'runtime-info.json').write_text(runtime.stdout)
command = [SAGE, '-python', str(HERE / 'scan.py')]
start = time.monotonic()
try:
    result = subprocess.run(command, cwd=HERE, capture_output=True, text=True, timeout=120)
    exit_code, timed_out = result.returncode, False
    stdout, stderr = result.stdout, result.stderr
except subprocess.TimeoutExpired as exc:
    exit_code, timed_out = None, True
    stdout = (exc.stdout or b'').decode(errors='replace')
    stderr = (exc.stderr or b'').decode(errors='replace')
(HERE / 'scan.stdout').write_text(stdout)
(HERE / 'scan.stderr').write_text(stderr)
receipt = {'command': command, 'exit_code': exit_code, 'timeout': timed_out,
           'cap_seconds': 120, 'wall_seconds': time.monotonic() - start}
(HERE / 'launch.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
