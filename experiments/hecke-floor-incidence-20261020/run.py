#!/usr/bin/env python3
"""Launch the frozen D15/f6 producer through the checked Sage runtime."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

P = Path(__file__).resolve().parent
SAGE = '/Volumes/SSD990/cryptanalysis/sage'
def sha(name):
    return hashlib.sha256((P / name).read_bytes()).hexdigest()

def main():
    protocol = json.loads((P / 'protocol.json').read_text())
    gate = json.loads((P / 'launch_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_D15_F6_PRODUCER'
    assert gate['status'] == 'FROZEN_BEFORE_D15_F6_LAUNCH'
    assert gate['protocol_sha256'] == sha('protocol.json')
    assert gate['runner_sha256'] == sha('run.py')
    for name, digest in protocol['input_sha256'].items():
        assert sha(name) == digest, name
    command = [SAGE, '-python', str(P / 'tools/exp11_class_walk.py')]
    env = os.environ.copy()
    env.update(protocol['environment'])
    start = time.perf_counter_ns()
    try:
        proc = subprocess.run(command, cwd=str(P), env=env,
                              capture_output=True, text=True, timeout=protocol['timeout_seconds'])
        status = 'PROCESS_COMPLETE' if proc.returncode == 0 else 'PROCESS_FAILED'
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        status, code = 'PROCESS_TIMEOUT', None
        stdout = exc.stdout.decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        stderr = exc.stderr.decode(errors='replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
    elapsed = time.perf_counter_ns() - start
    (P / 'stdout.txt').write_text(stdout)
    (P / 'stderr.txt').write_text(stderr)
    result_name = 'data/exp11_class_walk_D15_f6.json'
    receipt = {'status': status, 'command': command, 'environment': protocol['environment'],
               'exit_code': code, 'subprocess_wall_ns': elapsed,
               'protocol_sha256': sha('protocol.json'),
               'launch_protocol_sha256': sha('launch_protocol.json'),
               'runtime_info_sha256': sha('sage_runtime.json'),
               'stdout_sha256': sha('stdout.txt'), 'stderr_sha256': sha('stderr.txt'),
               'result_sha256': sha(result_name) if (P / result_name).exists() else None}
    (P / 'launch.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': status, 'elapsed_seconds': round(elapsed / 1e9, 3),
                      'result_sha256': receipt['result_sha256']}))

if __name__ == '__main__':
    main()
