"""Alternating same-input, one-worker comparison of exact N41 indexes."""
import hashlib
import json
import os
import psutil
import signal
import subprocess
import time
from pathlib import Path

D = Path(__file__).resolve().parent
P = json.loads((D / 'protocol.json').read_text())
OLD = D.parent / 'n41_partial_sum_compressibility_20261017' / 'sorted_join'
NEW = D / 'sign_join'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(NEW) == json.loads((D / 'run_result.json').read_text())['binary_sha256']
assert sha(Path(P['input_path'])) == P['input_sha256']
assert sha(OLD) == json.loads((D.parent / 'n41_partial_sum_compressibility_20261017' / 'run_result.json').read_text())['binary_sha256']
rows = []
parent = psutil.Process(os.getpid())
for n, variant in enumerate(('sorted', 'sign', 'sign', 'sorted')):
    binary = OLD if variant == 'sorted' else NEW
    outpath = D / f'bench_{n}_{variant}.stdout'
    errpath = D / f'bench_{n}_{variant}.stderr'
    start = time.monotonic()
    stop = None
    peak = 0
    degraded = False
    with outpath.open('x') as out, errpath.open('x') as err:
        child = subprocess.Popen([str(binary), P['input_path']], stdout=out, stderr=err, start_new_session=True)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if child.poll() is None:
                    degraded = True
            if peak > P['rss_cap_bytes']:
                stop = 'RSS_CAP'
            elif time.monotonic() - start > P['wall_cap_s']:
                stop = 'PARENT_WALL_CAP'
            if stop:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(.02)
        child.wait()
    lines = outpath.read_text().splitlines()
    hit = [x for x in lines if x.startswith('HIT ')]
    assert stop is None and child.returncode == 0 and len(hit) == 1, (variant, stop, child.returncode, lines)
    ids = [int(x) for x in hit[0].split()[1:7]]
    assert ids == [12, 122, 116, 47, 128, 34], ids
    rows.append({'order': n, 'variant': variant, 'wall_s': time.monotonic() - start,
                 'sampled_peak_combined_rss_bytes': peak, 'monitor_degraded': degraded,
                 'binary_sha256': sha(binary), 'stdout_sha256': sha(outpath),
                 'stderr_sha256': sha(errpath), 'hit_line': hit[0],
                 'exit_code': child.returncode})
    print(json.dumps(rows[-1], sort_keys=True), flush=True)
result = {'schema': 1, 'protocol_sha256': sha(D / 'protocol.json'),
          'bench_source_sha256': sha(__file__),
          'input_sha256': P['input_sha256'], 'rows': rows,
          'independent_replay_sha256': sha(D / 'audit_result.json')}
(D / 'bench_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
