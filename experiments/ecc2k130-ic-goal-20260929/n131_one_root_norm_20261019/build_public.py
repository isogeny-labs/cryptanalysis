"""Write the frozen N131 public-point one-root norm circuit."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

import build as experiment

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'public_build_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
control = json.loads((HERE / 'build_result.json').read_text())
assert control['status'] == 'PASS_N131_ONE_ROOT_NORM_CONSTRUCTED_CIRCUIT'
assert control['protocol_sha256'] == sha(HERE / 'protocol.json')
assert not (HERE / 'formula.xcnf').exists()
started = time.monotonic()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('public build wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
target = experiment.F.inverse(experiment.public['raw_point'][0])
assert target == protocol['public_reciprocal']
circ, wires, counts, policy = experiment.build(target)
assert counts == control['counts']
assert policy == control['policy_counts']
assert counts['clauses'] <= experiment.protocol['promotion_max_clauses']
path = HERE / 'formula.xcnf'
circ.write(path)
assert path.stat().st_size <= experiment.protocol['promotion_max_formula_bytes']
record = {
    'mask': wires['mask'],
    'out': wires['out'],
    'source_inverse': wires['source_inverse'],
    'middle': wires['middle'],
    'public_raw_point': experiment.public['raw_point'],
    'public_reciprocal': target,
    'rotations': experiment.protocol['rotations'],
}
(HERE / 'input_wires.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
signal.alarm(0)
result = {
    'status': 'PASS_N131_ONE_ROOT_NORM_PUBLIC_CIRCUIT',
    'candidate_id': None,
    'curve_id': experiment.protocol['curve_id'],
    'counts': counts,
    'policy_counts': policy,
    'public_raw_point': experiment.public['raw_point'],
    'public_reciprocal': target,
    'formula_bytes': path.stat().st_size,
    'formula_sha256': sha(path),
    'input_wires_sha256': sha(HERE / 'input_wires.json'),
    'wall_seconds': time.monotonic() - started,
    'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'public_build_protocol.json'),
}
(HERE / 'public_build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ('status', 'counts', 'formula_bytes', 'wall_seconds')}, sort_keys=True))
