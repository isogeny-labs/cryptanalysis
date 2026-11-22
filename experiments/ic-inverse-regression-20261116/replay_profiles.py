#!/usr/bin/env python3
"""Existing independent Python arithmetic for all profiled answers and states."""
import hashlib, json, sys, time
from pathlib import Path
P = Path(__file__).resolve().parent; ROOT = P.parents[1]
sys.path.insert(0, str(ROOT / 'experiments/fb-archive'))
from purepy import PyField
from external import _smul
start = time.monotonic(); cpu = time.process_time(); D = P / 'profile-001'
inst = json.loads((P / 'instances.json').read_text())[4]
field = inst['field']; curve = inst['curve']
integer = lambda x: int(x, 0) if isinstance(x, str) and x.startswith('0x') else int(x)
K = PyField(field['degree'], sum(1 << e for e in field['modulus_exponents']))
a = integer(curve['coefficients'][1]); G = tuple(map(integer, curve['generator'])); r = integer(curve['subgroup_order'])
answers = []
for row in json.loads((D / 'results.json').read_text()):
    raw = row['result']; result = raw['solver'] if row['method'].startswith('rho-') else raw['report']['Ok']
    assert raw['curve_id'] == inst['curve_id'] and _smul(K, a, G, result['recovered']) == tuple(raw['target'])
    answers.append({'method': row['method'], 'scalar': result['recovered'], 'target': raw['target']})
states = 0; frames = None
for tag in ['anchor', 'current']:
    raw = json.loads((D / (tag + '-walk.json')).read_text())
    if frames is not None: assert frames == raw['frames']
    frames = raw['frames']
    assert _smul(K, a, G, raw['planted']) == tuple(raw['target'])
    for f in frames:
        expected = _smul(K, a, G, (f['a'] + f['b'] * raw['planted']) % r)
        assert expected == (None if f['infinity'] else (f['x'], f['y']))
        states += 1
assert len(answers) == 8 and states == 1024
out = {'status': 'pass', 'answers': answers, 'answer_checks': len(answers), 'state_checks': states,
       'elapsed_s': time.monotonic() - start, 'cpu_s': time.process_time() - cpu,
       'standing': 'unsigned producer invocation of existing independent Python arithmetic',
       'source_sha256': {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in ['experiments/fb-archive/purepy.py', 'experiments/fb-archive/external.py']}}
(P / 'independent-replay-profile001.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'answers'}))
