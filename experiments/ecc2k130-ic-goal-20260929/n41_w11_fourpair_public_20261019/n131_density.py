"""Frozen-seed source eligibility diagnostic for the N131 four-pair route."""
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/output_first_fifth_20261019/output_first_math.py')
sys.path.insert(0, str(SOURCE.parent))
from output_first_math import FixedSeed

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

protocol = json.loads((HERE / 'n131_density_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_N131_DENSITY'
assert sha(SOURCE) == protocol['source_sha256']
assert sha(__file__) == protocol['script_sha256']
assert protocol['sample_size_per_width'] == 8192

results = []
for width in (33, 34):
    fixed = FixedSeed(131, [0, 1, 2, 13], 898618, width)
    rng = random.Random(protocol['random_seeds'][str(width)])
    domain = (1 << (width - 1)) - 1
    codes = rng.sample(range(1, domain + 1), protocol['sample_size_per_width'])
    counts = {'source_trace_zero': 0, 'both_inverse_traces_zero': 0, 'valid': 0}
    began = time.monotonic()
    for code in codes:
        a = fixed.source_a(code)
        if fixed.f.trace(a) != 0:
            continue
        counts['source_trace_zero'] += 1
        if fixed.f.trace(fixed.f.inverse(a)) == 0 and fixed.f.trace(fixed.f.inverse(a ^ fixed.seed)) == 0:
            counts['both_inverse_traces_zero'] += 1
            if fixed.source_valid(a):
                counts['valid'] += 1
    n = len(codes)
    phat = counts['valid'] / n
    z = 1.96
    denom = 1 + z*z/n
    center = (phat + z*z/(2*n))/denom
    half = z*math.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/denom
    row = {'width': width, 'sample_size': n, 'code_domain': domain, 'counts': counts,
           'valid_fraction': phat, 'wilson_95': [center-half, center+half],
           'estimated_eligible_codes': phat*domain,
           'estimated_signed_pair_states': 4*phat*domain,
           'sample_wall_seconds': time.monotonic()-began}
    results.append(row)
    print(json.dumps(row, sort_keys=True), flush=True)

out = {'status': 'COMPLETE_N131_DENSITY_DIAGNOSTIC', 'candidate_id': None,
       'curve_id': 'EC1N131Ckb1heb5f1998f20b', 'rows': results,
       'protocol_sha256': sha(HERE/'n131_density_protocol.json'),
       'script_sha256': sha(__file__), 'source_sha256': sha(SOURCE)}
(HERE/'n131_density_result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
