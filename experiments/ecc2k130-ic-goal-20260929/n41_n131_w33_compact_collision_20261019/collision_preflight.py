"""Exact affine collision-space audit for the canonical N131 W33 source."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_n131_fivepair_w9_w29_20261017'))
import circuit_n131_3p2 as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'collision_protocol.json').read_text())
assert protocol['script_sha256'] == sha(__file__)
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (HERE / 'collision_result.json').exists()
assert protocol['width'] == 33 and protocol['seed'] == design.SEED
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('collision preflight wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
F, N = design.F, design.N
bits = [i for i in range(protocol['width']) if i != design.SEED_MASK.bit_length()-1]
base = [1 << (i+1) for i in bits]
assert len(base) == 32 and all(F.frob(value,131)==value for value in base)


def echelon(columns):
    basis = {}
    kernel = []
    for index, column in enumerate(columns):
        value = column
        code = 1 << index
        while value:
            pivot = value.bit_length()-1
            if pivot not in basis:
                basis[pivot] = (value,code)
                break
            current,label = basis[pivot]
            value ^= current
            code ^= label
        else:
            kernel.append(code)
    return basis,kernel


def solve(basis,value):
    code = 0
    while value:
        pivot = value.bit_length()-1
        if pivot not in basis:
            return None
        current,label = basis[pivot]
        value ^= current
        code ^= label
    return code


def evaluate(code,columns):
    value = 0
    for i,column in enumerate(columns):
        if code >> i & 1:
            value ^= column
    return value


rows=[]
for k in range(N):
    rotated = [F.frob(value,k) for value in base]
    rotated_seed = F.frob(protocol['seed'],k)
    columns = rotated+base
    basis,kernel = echelon(columns)
    assert len(basis)+len(kernel)==64
    for e in (0,1):
        for f in (0,1):
            offset = (rotated_seed if e else 0) ^ (protocol['seed'] if f else 0)
            solution = solve(basis,offset)
            assert solution is None or evaluate(solution,columns)==offset
            assert all(evaluate(word,columns)==0 for word in kernel)
            rows.append({'frobenius_power':k,'source_endpoint_e':e,'other_endpoint_f':f,
                         'rank':len(basis),'kernel_dimension':len(kernel),
                         'feasible':solution is not None,
                         'solution_code':solution,
                         'kernel_codes':kernel if solution is not None else [],
                         'collision_pair_count_before_source_filter':
                             (1<<len(kernel)) if solution is not None else 0})
signal.alarm(0)
histogram={}
for row in rows:
    key=str(row['rank'])
    histogram[key]=histogram.get(key,0)+1
nontrivial=[row for row in rows if row['feasible'] and row['frobenius_power']!=0]
result={'status':'EXACT_N131_W33_AFFINE_COLLISION_SPACES',
        'candidate_id':None,'curve_id':protocol['curve_id'],
        'width':protocol['width'],'source_code_bits':len(base),
        'seed':protocol['seed'],'source_basis':base,
        'case_count':len(rows),'feasible_case_count':sum(row['feasible'] for row in rows),
        'nonzero_distance_feasible_count':len(nontrivial),
        'nonzero_distance_pair_occurrence_count':
            sum(row['collision_pair_count_before_source_filter'] for row in nontrivial),
        'rank_histogram':histogram,'cases':rows,
        'wall_seconds':time.monotonic()-started,
        'self_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'collision_protocol.json')}
(HERE/'collision_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in
                  ('status','case_count','feasible_case_count',
                   'nonzero_distance_feasible_count',
                   'nonzero_distance_pair_occurrence_count','rank_histogram',
                   'wall_seconds')},sort_keys=True))
