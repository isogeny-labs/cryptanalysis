"""Monitor a frozen one-worker NTL source-norm query."""
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(label):
    cfg_path = HERE / ('protocol_' + label + '.json')
    cfg = json.loads(cfg_path.read_text())
    files = {
        'native_norm.cpp': HERE / 'native_norm.cpp',
        'native_norm': HERE / 'native_norm',
        'run.py': HERE / 'run.py',
        'field.hpp': ROOT / 'n131_w20_paired_raw_quotient_20261016/field.hpp',
        'support_w20.tsv': ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv',
        'coefficients.tsv': HERE / 'coefficients.tsv',
        'sage_runtime_info.json': HERE / 'sage_runtime_info.json',
        'GF2EX.h': Path('/opt/homebrew/opt/ntl/include/NTL/GF2EX.h'),
        'GF2E.h': Path('/opt/homebrew/opt/ntl/include/NTL/GF2E.h'),
        'libntl.dylib': Path('/opt/homebrew/opt/ntl/lib/libntl.dylib'),
        'libgmp.dylib': Path('/opt/homebrew/opt/gmp/lib/libgmp.dylib'),
    }
    assert cfg['source_sha256'] == {name: sha(path) for name, path in files.items()}
    assert cfg['worker_count'] == 1 and cfg['candidate_id'] is None
    command = [str(HERE / 'native_norm'),
               str(ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv'),
               str(HERE / 'coefficients.tsv'), str(cfg['selected_count'])]
    assert cfg['command'] == command
    out_path = HERE / ('stdout_' + label + '.txt')
    err_path = HERE / ('stderr_' + label + '.txt')
    started = time.monotonic_ns()
    peak = 0
    stopped = None
    degraded = False
    consecutive_misses = 0
    with out_path.open('x') as out, err_path.open('x') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        proc = psutil.Process(child.pid)
        parent = psutil.Process()
        while child.poll() is None:
            try:
                peak = max(peak, proc.memory_info().rss + parent.memory_info().rss)
                consecutive_misses = 0
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if child.poll() is None:
                    consecutive_misses += 1
                    if consecutive_misses >= 2:
                        degraded = True
            if peak > cfg['rss_cap_bytes']:
                stopped = 'RSS_CAP'
            elif time.monotonic_ns() - started > cfg['wall_cap_seconds'] * 10**9:
                stopped = 'WALL_CAP'
            if stopped:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(0.05)
        child.wait()
    ended = time.monotonic_ns()
    lines = out_path.read_text(errors='replace').splitlines()
    source = [line for line in lines if line.startswith('SOURCE ')]
    rows = [line for line in lines if line.startswith('ROW ')]
    done = [line for line in lines if line.startswith('DONE ')]
    if stopped:
        status = 'BOUNDED_UNKNOWN'
    elif child.returncode == 0 and not err_path.read_bytes() and len(source)==1 and len(rows)==2 and len(done)==1:
        status = 'COMPLETE_NATIVE_NTL_GLOBAL_NORM'
    else:
        status = 'PRODUCER_FAILURE'
    receipt = {
        'status': status, 'candidate_id': None, 'exit_code': child.returncode,
        'stop_reason': stopped, 'monitor_degraded': degraded,
        'sampled_peak_combined_rss_bytes': peak, 'wall_ns': ended-started,
        'source_line': source, 'row_lines': rows, 'done_line': done,
        'protocol_sha256': sha(cfg_path), 'stdout_sha256': sha(out_path),
        'stderr_sha256': sha(err_path),
    }
    (HERE / ('receipt_' + label + '.json')).write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return 0 if status == 'COMPLETE_NATIVE_NTL_GLOBAL_NORM' else 1


if __name__ == '__main__':
    assert len(sys.argv) == 2
    sys.exit(main(sys.argv[1]))
