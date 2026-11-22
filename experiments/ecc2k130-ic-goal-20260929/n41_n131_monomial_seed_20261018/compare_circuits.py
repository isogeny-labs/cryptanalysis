"""Paired exact-five circuit counts on frozen public targets and seed variants."""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

protocol = json.loads((HERE / 'circuit_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_COUNTS'
for label, source in protocol['sources'].items():
    assert sha(source['path']) == source['sha256'], label
rows = []
for field, path, public_x, seeds in (
    ('N41', ROOT / 'n41_w9_lazy_source_20261017/circuit.py',
     protocol['n41_public_raw_x'], (56, 36)),
    ('N131', ROOT / 'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py',
     protocol['n131_public_raw_x'], (898618, 524800))):
    design = module(path, 'paired_' + field)
    target = design.F.inverse(public_x)
    assert target == protocol['expected_target_reciprocal'][field]
    original_bits = list(design.BITS)
    for mask in seeds:
        assert [i for i in range(design.WIDTH) if i != mask.bit_length() - 1] == original_bits
        design.SEED_MASK = mask
        design.SEED = mask << 1
        design.H = design.F.square(design.previous.halftrace(design.SEED) if field == 'N131'
                                   else design.halftrace(design.SEED))
        design.C = 1 ^ design.H
        design.PB = [design.F.square(value) ^ design.F.mul(design.SEED, value)
                     for value in design.BASE]
        start = time.monotonic()
        circuit, _, counts = design.build(target) if field == 'N131' else design.build(target, 'exact5')
        row = {'field': field, 'seed_mask': mask, 'H': design.H, 'C': design.C,
               'target_reciprocal': target, 'build_wall_seconds': time.monotonic()-start,
               **counts}
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
        del circuit
(HERE / 'circuit_counts.json').write_text(json.dumps({
    'status':'COMPLETE_PAIRED_CIRCUIT_COUNTS','candidate_id':None,
    'protocol_sha256':sha(HERE / 'circuit_protocol.json'),
    'script_sha256':sha(Path(__file__)), 'rows':rows}, indent=2, sort_keys=True)+'\n')
