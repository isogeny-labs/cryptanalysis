"""Freeze the W10 four-pair SAT circuit and replay the archived public witness."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

import circuit_orbit as circuit

HERE=Path(__file__).resolve().parent
ROOT=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
sys.path.insert(0,str(ROOT/'output_first_fifth_20261019'))
from output_first_math import FixedSeed

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def complete_assignment(machine,initial):
    definitions={int(out):('and',int(a),int(b)) for (a,b),out in machine.and_cache.items()}
    for line in machine.xors:
        literals=[int(x) for x in line.split()[1:-1]]
        definitions[abs(literals[0])]=('xor',literals)
    values=[None]*machine.next_var
    for wire,bit in initial.items():values[wire]=int(bit)
    for wire in range(1,machine.next_var):
        if values[wire] is not None:continue
        d=definitions.get(wire)
        if d is None:raise RuntimeError(f'unassigned primary wire {wire}')
        if d[0]=='and':
            def value(x):return 1 if x==-1 else 0 if x==0 else values[x]
            values[wire]=value(d[1])&value(d[2])
        else:
            literals=d[1];bit=int(literals[0]>0)
            for literal in literals[1:]:bit^=values[abs(literal)]^int(literal<0)
            values[wire]=bit
    return values

def check_assignment(machine,values):
    for row in machine.clauses:
        literals=[int(x) for x in row.split()[:-1]]
        assert any(values[abs(wire)]==int(wire>0) for wire in literals),row
    for row in machine.xors:
        literals=[int(x) for x in row.split()[1:-1]]
        assert sum(values[abs(wire)]^int(wire<0) for wire in literals)&1,row
    return {'clauses':len(machine.clauses),'xor_rows':len(machine.xors)}

def main():
    cfg=json.loads((HERE/'orbit_build_protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_N41_W10_ORBIT_CIRCUIT_BUILD'
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    audit=json.loads(Path(cfg['sources']['w10_audit']['path']).read_text())
    assert audit['status']=='PASS_INDEPENDENT_N41_W10_FOURPAIR_PUBLIC_RELATION'
    assert audit['orientation']==cfg['orientation']==29
    fixed=FixedSeed(41,[0,3],56,11)
    target=tuple(audit['oriented_target_point'])
    base_target=tuple(audit['raw_target_point'])
    target_reciprocals=[fixed.f.frob(fixed.f.inverse(base_target[0]),k) for k in range(41)]
    assert target_reciprocals[29]==fixed.f.inverse(target[0])
    begin=time.monotonic()
    machine,wires,counts=circuit.build(target_reciprocals,cfg['sources']['w10_input']['path'])
    built=time.monotonic()
    initial={}
    def bind(bits,value):
        for j,wire in enumerate(bits):
            assert wire not in initial
            initial[wire]=(value>>j)&1
    pairs=[]
    for i,row in enumerate(audit['rows']):
        code=row['source_code'];a=fixed.source_a(code)
        assert a==row['source_masks'][0] and fixed.source_valid(a)
        product=fixed.source_product(code)
        bind(wires['mask'][i],code)
        bind(wires['source_inverse'][i],fixed.f.inverse(product))
        point=tuple(row['pair_point']);pairs.append(point)
        unrotated=fixed.e.frob(point,(41-row['rotation'])%41)
        bind(wires['out'][i],fixed.f.inverse(unrotated[0]))
    mids=[fixed.e.add(pairs[0],pairs[1]),fixed.e.add(pairs[2],pairs[3])]
    assert all(p is not None and p[0] for p in mids)
    for bits,point in zip(wires['middle'],mids):bind(bits,fixed.f.inverse(point[0]))
    bind(wires['selector'],29)
    assert fixed.e.add(*mids)==target
    values=complete_assignment(machine,initial)
    checked=check_assignment(machine,values)
    machine.write(HERE/'orbit41.xcnf')
    out={'status':'PASS_W10_FOURPAIR_FULL_ASSIGNMENT','candidate_id':None,
         'curve_id':cfg['curve_id'],'orientation':29,'source_codes':[r['source_code'] for r in audit['rows']],
         'target_reciprocal':target_reciprocals[29],
         'target_reciprocals_sha256':hashlib.sha256(json.dumps(target_reciprocals).encode()).hexdigest(),
         'counts':counts,'assignment_check':checked,
         'build_seconds':built-begin,'control_seconds':time.monotonic()-built,
         'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'formula_sha256':sha(HERE/'orbit41.xcnf'),
         'protocol_sha256':sha(HERE/'orbit_build_protocol.json'),
         'script_sha256':sha(__file__)}
    (HERE/'orbit_build_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
