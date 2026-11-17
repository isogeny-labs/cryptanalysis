#!/usr/bin/env python3
"""Prospective fixed-development four-cell instruction diagnostic."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import tarfile
import time
from counterfactual_checks import CELLS, check, equal

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
D = P/'profile-n24-001'
D.mkdir(exist_ok=False)
p = argparse.ArgumentParser()
p.add_argument('--binary', type=Path, required=True)
a = p.parse_args()
START = time.monotonic()
commands, rows = [], []
summary = dict(status='started', qualification=None, purpose='Same-binary synthetic-unit instruction diagnostic; no native-clock conclusion')
sha = lambda b: hashlib.sha256(b).hexdigest()

def limits():
    resource.setrlimit(resource.RLIMIT_AS, (32*1024**3, 32*1024**3))

def run(argv, cap, label):
    remaining = 210-(time.monotonic()-START)
    if remaining <= 0:
        raise TimeoutError('N24 diagnostic controller cap')
    proc = subprocess.Popen(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, preexec_fn=limits)
    try:
        out, err = proc.communicate(timeout=min(cap, remaining))
        code = proc.returncode
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        code = 124
    (D/(label+'.stdout')).write_text(out)
    (D/(label+'.stderr')).write_text(err)
    commands.append(dict(argv=argv, exit_code=code, label=label))
    (D/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
    assert code == 0, label+' exit'+str(code)
    return out

try:
    pin = json.loads((P/'profile-result-input.json').read_text())
    assert sha((Path('/jobs')/pin['job']/'job.json').read_bytes()) == pin['metadata_sha256']
    with tarfile.open(Path('/jobs')/pin['job']/'shards/0/out.tar.gz', 'r:gz') as tar:
        b = tar.extractfile('experiments/ic-inverse-regression-20261116/profile-001/host.json').read()
    assert sha(b) == pin['host_sha256']
    tools = json.loads(b)['tool_sha256']
    for name in ['valgrind', 'callgrind_annotate', 'objdump']:
        assert sha(Path(shutil.which(name)).read_bytes()) == tools[name]
    receipt = json.loads((P/'build-001/receipt.json').read_text())
    binary = a.binary.resolve()
    assert receipt['status'] == 'correctness_prepared' and sha(binary.read_bytes()) == receipt['binary_sha256']
    allowed = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {allowed[0]})
    metadata = json.loads((Path('/jobs')/os.environ['JOB_ID']/'job.json').read_text())
    (D/'environment.json').write_text(json.dumps(dict(allowed_cpus=allowed, selected_cpu=allowed[0], tool_sha256=tools, job_id=os.environ['JOB_ID'], source_commit=metadata['git']['commit'], binary_sha256=receipt['binary_sha256'], controller_sha256=sha(Path(__file__).read_bytes()), checks_sha256=sha((P/'counterfactual_checks.py').read_bytes()), instruction_only=True), indent=2)+'\n')
    inst = json.loads((P/'instances.json').read_text())[3]
    units = {k: 1.0 for k in ['ns_per_add', 'ns_per_double', 'ns_per_lookup', 'ns_per_row_op']}
    units.update({k: None for k in ['ns_per_sqrt', 'ns_per_as_solve', 'ns_per_s4_pair', 'ns_per_word_xor', 'ns_per_legendre', 'ns_per_inversion', 'ns_per_frobenius', 'ns_per_canon']})
    units['pinned_units'] = []
    cal = D/'synthetic-units.json'
    cal.write_text(json.dumps(dict(curve_id=inst['curve_id'], calibration=units), indent=2)+'\n')
    first = None
    for cell in CELLS:
        label = cell+'-inverse'
        capture = D/(label+'.callgrind')
        argv = ['valgrind', '--tool=callgrind', '--dump-instr=yes', '--collect-jumps=yes', '--callgrind-out-file='+str(capture), '--log-file='+str(D/(label+'.valgrind.log')), str(binary), str(P/'instances.json'), '3', 'mitm-counterfactual-'+cell, '0', str(cal)]
        raw = check(json.loads(run(argv, 120, label)), cell)
        assert raw['curve_id'] == inst['curve_id'] and raw['calibration'] == units
        if first is None:
            first = raw
        else:
            equal(first, raw)
        rows.append(dict(tag=cell, result=raw, binary_sha256=receipt['binary_sha256'], capture_sha256=sha(capture.read_bytes()), synthetic_units=True))
        (D/'results.json').write_text(json.dumps(rows, indent=2)+'\n')
        for inclusive in ['no', 'yes']:
            run(['callgrind_annotate', '--auto=no', '--threshold=100', '--inclusive='+inclusive, str(capture)], 20, label+'-inclusive-'+inclusive)
    run(['objdump', '-d', '-C', '--no-show-raw-insn', str(binary)], 20, 'shared-disassembly')
    summary.update(status='completed_unqualified', captures=4, one_binary=True)
except Exception as exc:
    summary.update(status='failed_or_capped', error=repr(exc))
finally:
    (D/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary), flush=True)
if summary['status'] != 'completed_unqualified':
    raise SystemExit(1)
