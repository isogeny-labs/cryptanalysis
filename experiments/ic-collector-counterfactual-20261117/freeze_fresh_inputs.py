#!/usr/bin/env python3
"""Generate identities only after native admission and prospective ARM pinning."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time
from fresh_common import MODES, FIXTURES, ACTUAL
from source_manifest import hashes as source_hashes

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
p = argparse.ArgumentParser()
p.add_argument('probe', type=Path)
a = p.parse_args()
digest_bytes = lambda b: hashlib.sha256(b).hexdigest()
def digest(v):
    return digest_bytes(json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
def write(path, value):
    if path.exists():
        assert json.loads(path.read_text()) == value, 'Immutable identity differs: '+str(path)
    else:
        path.write_text(json.dumps(value, indent=2)+'\n')

hashes = source_hashes()
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
controllers = ['freeze_fresh_inputs.py', 'fresh_common.py', 'run_fresh.py', 'analyze_fresh.py',
               'replay_fresh_answers.py', 'replay_fresh_states.py', 'counterfactual_checks.py',
               'record_fresh_metrics.py', 'FRESH_PROTOCOL.md', 'raw-reference-plan.json']
for name in controllers:
    relative = str((P/name).relative_to(ROOT))
    assert (P/name).read_bytes() == subprocess.check_output(['git', 'show', revision+':'+relative], cwd=ROOT), 'Publish controllers before generation'
started_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
receipt = json.loads((P/'build-001/receipt.json').read_text())
assert receipt['status'] == 'prepared' and receipt['source_sha256'] == hashes
pin = json.loads((P/'optimized-input.json').read_text())
assert pin['binary_sha256'] == receipt['binary_sha256']
assert pin['receipt_sha256'] == digest_bytes((P/'build-001/receipt.json').read_bytes())
diagnostic = json.loads((P/'analysis-n24.json').read_text())
assert diagnostic['status'] == 'pass' and diagnostic['independent_answer_checks'] == 4
assert (P/'FRESH_PROTOCOL.md').is_file() and (P/'raw-reference-plan.json').is_file()
replay = json.loads((P/'independent-states-preparation.json').read_text())
assert replay['status'] == 'pass' and replay['checks'] == 2560 and replay['answer_checks'] == 20
arm = json.loads((P/'identity-arm/receipt.json').read_text())
assert arm['status'] == 'built_before_generation' and arm['source_sha256'] == hashes
binary_hash = digest_bytes(a.probe.read_bytes())
assert binary_hash == arm['binary_sha256']
# Require the contemporaneous receipt, not a retrospective hash assertion.
assert arm['purpose'] and arm['argv']
identities = {}
for index, record in enumerate(json.loads((P/'instances.json').read_text())):
    n = record['field']['degree']
    cid = record['curve_id']
    curve = dict(record['curve'], curve_id=cid)
    archive = json.loads((P/f'archive-n{n}.json').read_text())
    doc = json.loads(gzip.decompress((ROOT/'experiments/fb-archive'/archive['path']).read_bytes()))
    assert doc['field'] == record['field'] and doc['curve'] == curve
    fb = doc['factor_base']
    prior = json.loads((ROOT/'experiments/ic-static-witness-map-20261117/fresh-identities.json').read_text())[str(index)]
    case = dict(workloads={}, archive=archive)
    for mode in MODES[:3]:
        old_id = prior[mode]
        old = json.loads((ROOT/'experiments/ic-bench/candidates'/f'{old_id}.json').read_text())
        assert old['field'] == record['field'] and old['curve'] == curve and old['factor_base'] == fb
        case[mode] = old_id
    indexed_id = case[MODES[2]]
    original = json.loads((ROOT/'experiments/ic-bench/candidates'/f'{indexed_id}.json').read_text())
    for mode in MODES[3:]:
        cell = mode.rsplit('-', 1)[1]
        candidate = copy.deepcopy(original)
        candidate['point_decomposition']['params'].update(vector_prepare=5 if cell.startswith('s') else 3,
                                                          suppress_indexed_counter=int(cell.endswith('a')))
        impl = candidate['implementation']
        impl.update(sources_sha256=hashes, probe_mode=ACTUAL[mode],
                    pair_input_policy='original-staged-point-buffers-original-order-and-chunks' if cell.startswith('s') else 'immutable-factor-base-indices-original-order-and-chunks',
                    indexed_counter_policy='absent-with-accumulation-retained' if cell.endswith('a') else 'present-original-fixed-array-constructor')
        candidate_id = indexed_id.rsplit('h', 1)[0]+'h'+digest(candidate)[:12]
        write(ROOT/'experiments/ic-bench/candidates'/f'{candidate_id}.json', candidate)
        case[mode] = candidate_id
    for fixture in FIXTURES:
        assert digest_bytes(a.probe.read_bytes()) == binary_hash
        native = json.loads(subprocess.check_output([str(a.probe.resolve()), str(P/'instances.json'), str(index), 'workload', str(fixture)], text=True))
        assert native['curve_id'] == cid
        workload = dict(schema='ic-bench-workload/1', curve_id=cid,
                        subgroup_order=record['curve']['subgroup_order'], target_count=1,
                        cache_state='cold', fixture=fixture, prng='StdRng rand pinned in suite/Cargo.lock',
                        target_law='public fixed seed law in ic_affine_pipeline_probe.rs; scalar uniform on [1,r-1]',
                        targets=[[native['planted'], *native['target']]], walk_seed=native['target_seed'],
                        rho_reference='separate fresh plain and negation processes on this exact point and walk seed')
        wid = digest(workload)[:12]
        write(ROOT/'experiments/ic-bench/workloads'/f'{wid}.json', workload)
        case['workloads'][str(fixture)] = wid
    identities[str(index)] = case
assert digest_bytes(a.probe.read_bytes()) == binary_hash
write(P/'fresh-identities.json', identities)
write(P/'fresh-generation.json', dict(status='generated_before_timing', started_utc=started_utc,
      published_generator_revision=revision,
      identity_probe_sha256_before_and_after=binary_hash,
      identity_build_receipt_sha256=digest_bytes((P/'identity-arm/receipt.json').read_bytes()),
      native_preparation_binding_sha256=digest_bytes((P/'optimized-input.json').read_bytes()),
      identities_sha256=digest_bytes((P/'fresh-identities.json').read_bytes()),
      controllers_sha256={name: digest_bytes((P/name).read_bytes()) for name in controllers},
      argv=['python3', str(Path(__file__).relative_to(ROOT)), str(a.probe)],
      new_candidates=20, reused_candidates=15, one_target_workloads=210, fixtures=[726,767],
      scope='Contemporaneous identity generation receipt; ARM probe is not the native timing binary.'))
print(json.dumps(dict(curves=5, new_candidates=20, reused_candidates=15, one_target_workloads=210)))
