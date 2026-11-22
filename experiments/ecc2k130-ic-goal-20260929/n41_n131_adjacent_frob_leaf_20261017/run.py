#!/usr/bin/env python3
"""Frozen one-worker N41 adjacent-Frobenius public-point join."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_linked_frobenius_pair_20261012'
BASE = ROOT / 'n41_w7_entropy_cubic_20261011/w8'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write('\n')


def paths():
    return {'runner': Path(__file__), 'prepare_receipt': HERE / 'prepare_result.json',
            'native_source': HERE / 'adjacent_join.cpp',
            'native_binary': HERE / 'adjacent_join',
            'input': HERE / 'adjacent_input.tsv',
            'included_group_source': ROOT / 'n41_w8_ninepair_join_control_20261012/join9.cpp',
            'prior_linked_audit': PRIOR / 'audit_result.json',
            'geometry': BASE / 'geometry.json', 'fixture': BASE / 'fixture.json',
            'sage_runtime': HERE / 'sage_runtime_info.json'}


def freeze():
    prep = json.loads((HERE / 'prepare_result.json').read_text())
    assert prep['status'] == 'FROZEN_ADJACENT_SOURCE_DERIVATION'
    assert sha(HERE / 'adjacent_join.cpp') == prep['output_sha256']['adjacent_join.cpp']
    assert sha(HERE / 'adjacent_input.tsv') == prep['output_sha256']['adjacent_input.tsv']
    prior = json.loads((PRIOR / 'audit_result.json').read_text())
    assert prior['status'] == 'PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION'
    save('protocol.json', {'status': 'FROZEN_N41_ADJACENT_PUBLIC_JOIN',
         'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
         'target_law': 'four raw preimages of one frozen public subgroup point',
         'public_point': [920359962848, 755404565011],
         'source_pair_slots': 10, 'independent_edges': 9,
         'linked_rotation_gap': 1, 'distinct_folded_columns_required': 18,
         'left_keep': 5000000, 'right_probe_cap': 5000000,
         'worker_count': 1, 'wall_cap_seconds': 180,
         'rss_cap_bytes': 4*1024**3,
         'source_sha256': {name: sha(path) for name, path in paths().items()}})


def run():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_N41_ADJACENT_PUBLIC_JOIN'
    assert protocol['source_sha256'] == {name: sha(path) for name, path in paths().items()}
    start = time.monotonic_ns()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    parent = psutil.Process()
    peak, stop = 0, None
    with (HERE / 'stdout.log').open('x') as out, (HERE / 'stderr.log').open('x') as err:
        child = subprocess.Popen([str(HERE / 'adjacent_join'), str(HERE / 'adjacent_input.tsv')],
                                 stdout=out, stderr=err)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                rss = parent.memory_info().rss + process.memory_info().rss
            except psutil.NoSuchProcess:
                rss = parent.memory_info().rss
            peak = max(peak, rss)
            if rss > protocol['rss_cap_bytes']:
                stop = 'RSS_CAP'
            elif time.monotonic_ns()-start >= protocol['wall_cap_seconds']*10**9:
                stop = 'TOTAL_WALL_CAP'
            if stop:
                child.kill()
                break
            time.sleep(0.05)
        code = child.wait()
    end = time.monotonic_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    stdout = (HERE / 'stdout.log').read_text()
    stderr = (HERE / 'stderr.log').read_text()
    hit = next((line for line in stdout.splitlines() if line.startswith('HIT ')), None)
    exhausted = next((line for line in stdout.splitlines() if line.startswith('EXHAUSTED ')), None)
    status = ('BOUNDED_UNKNOWN' if stop else
              'HIT_PENDING_INDEPENDENT_REPLAY' if hit and code == 0 else
              'EXHAUSTED' if exhausted and code == 0 else 'ERROR')
    save('receipt.json', {'status': status, 'candidate_id': None,
         'worker_count': 1, 'stop_reason': stop, 'exit_code': code,
         'runner_wall_ns': end-start,
         'peak_combined_rss_bytes_sampled': peak,
         'child_user_seconds': after.ru_utime-before.ru_utime,
         'child_system_seconds': after.ru_stime-before.ru_stime,
         'hit_line': hit, 'exhausted_line': exhausted,
         'stdout_sha256': sha(HERE / 'stdout.log'),
         'stderr_sha256': sha(HERE / 'stderr.log'),
         'protocol_sha256': sha(HERE / 'protocol.json')})
    print(status, (end-start)/1e9, peak)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
