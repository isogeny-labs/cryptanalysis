"""Matched fixed-conflict source-gate topology comparison on one public point."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
VARIANTS = ('exact5', 'exact3', 'table5')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = {path.name: sha(path) for path in
           [Path(__file__), HERE / 'circuit.py', HERE / 'fixture.json',
            HERE / 'screen_result.json', HERE / 'sage_runtime_info.json', SOLVER] +
           [HERE / (variant + '.xcnf') for variant in VARIANTS]}
protocol = {'status': 'FROZEN_FIXED_CONFLICT_PROBE',
            'curve_id': json.loads((HERE / 'fixture.json').read_text())['curve_id'],
            'variants': VARIANTS, 'order': VARIANTS,
            'conflict_cap': 100000, 'time_cap_seconds_per_variant': 60,
            'worker_count': 1, 'source_sha256': sources}
with (HERE / 'probe_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
rows = []
for variant in VARIANTS:
    formula = HERE / (variant + '.xcnf')
    command = [str(SOLVER), '--threads=1', '--maxconfl=100000',
               '--maxtime=60', '--zero-exit-status', '--verb=1',
               '--printsol=1', str(formula)]
    stdout_path = HERE / (variant + '_probe.stdout')
    stderr_path = HERE / (variant + '_probe.stderr')
    start = time.monotonic_ns()
    with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
        process = subprocess.run(command, stdout=stdout, stderr=stderr,
                                 timeout=65, check=False)
    elapsed = time.monotonic_ns() - start
    output = stdout_path.read_text(errors='replace')
    statuses = [line for line in output.splitlines() if line.startswith('s ')]
    rows.append({'variant': variant, 'command': command, 'elapsed_ns': elapsed,
                 'exit_code': process.returncode, 'status_lines': statuses,
                 'last_restart': next((line for line in reversed(output.splitlines())
                                       if line.startswith('c rst ')), None),
                 'stdout_sha256': sha(stdout_path),
                 'stderr_sha256': sha(stderr_path)})
    print(json.dumps(rows[-1]), flush=True)
result = {'status': 'COMPLETE_EXPLORATORY_FIXED_CONFLICT_PROBE',
          'rows': rows, 'protocol_sha256': sha(HERE / 'probe_protocol.json')}
with (HERE / 'probe_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
