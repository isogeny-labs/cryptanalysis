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
from setup_fresh_common import MODES, FIXTURES, ACTUAL, STRATEGIES
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
controllers = ['freeze_setup_inputs.py','setup_fresh_common.py','run_setup_fresh.py','analyze_setup_fresh.py','replay_setup_fresh_answers.py','replay_setup_fresh_states.py','setup_checks.py','counterfactual_checks.py','FRESH_SETUP_PROTOCOL.md','setup-raw-reference-plan.json','seal_setup_provenance.py','record_setup_metrics.py','setup-frozen-inputs.json','prepare_setup_identity.py','check_setup_packet.py','bind_setup_record.py','check_setup_progress_export.py','attach_setup_record_raw.py','check_setup_identities.py']
for name in controllers:
    relative = str((P/name).relative_to(ROOT))
    assert (P/name).read_bytes() == subprocess.check_output(['git', 'show', revision+':'+relative], cwd=ROOT), 'Publish controllers before generation'
started_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
receipt = json.loads((P/'setup-build-001/receipt.json').read_text())
assert receipt['status'] == 'prepared' and receipt['source_sha256'] == hashes
pin = json.loads((P/'setup-input.json').read_text())
assert pin['binary_sha256'] == receipt['binary_sha256']
assert pin['receipt_sha256'] == digest_bytes((P/'setup-build-001/receipt.json').read_bytes())
replay = json.loads((P/'independent-setup-preparation.json').read_text())
assert replay['status']=='pass' and replay['checks']==2560 and replay['answer_checks']==20
arm = json.loads((P/'setup-identity-arm/receipt.json').read_text())
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
        strategy=STRATEGIES[mode]
        candidate = copy.deepcopy(original)
        candidate['point_decomposition']['params'].update(vector_prepare=strategy)
        if strategy in [3,5]:candidate['point_decomposition']['params']['suppress_indexed_counter']=0
        else:candidate['point_decomposition']['params'].pop('suppress_indexed_counter',None)
        impl=candidate['implementation']
        impl.update(sources_sha256=hashes,probe_mode=ACTUAL[mode],
                    pair_input_policy='original-staged-point-buffers-original-order-and-chunks' if strategy==5 else 'immutable-factor-base-indices-original-order-and-chunks',
                    indexed_counter_policy='present-original-fixed-array-constructor',
                    setup_buffer_policy={3:'original-indexed-empty',5:'original-staged',6:'observed-empty',7:'observed-reserved',8:'observed-gathered'}[strategy])
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
write(P/'setup-fresh-identities.json', identities)
write(P/'setup-fresh-generation.json', dict(status='generated_before_timing', started_utc=started_utc,
      published_generator_revision=revision,
      identity_probe_sha256_before_and_after=binary_hash,
      identity_build_receipt_sha256=digest_bytes((P/'setup-identity-arm/receipt.json').read_bytes()),
      native_preparation_binding_sha256=digest_bytes((P/'setup-input.json').read_bytes()),
      identities_sha256=digest_bytes((P/'setup-fresh-identities.json').read_bytes()),
      controllers_sha256={name: digest_bytes((P/name).read_bytes()) for name in controllers},
      argv=['python3', str(Path(__file__).relative_to(ROOT)), str(a.probe)],
      new_candidates=25, reused_candidates=15, one_target_workloads=200, fixtures=[768,807],
      scope='Contemporaneous identity generation receipt; ARM probe is not the native timing binary.'))
print(json.dumps(dict(curves=5, new_candidates=25, reused_candidates=15, one_target_workloads=200)))
