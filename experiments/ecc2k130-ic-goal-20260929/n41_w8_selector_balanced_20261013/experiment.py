"""Freeze and build the N41 W8 direct-parity unpinned public formula."""
import hashlib,json,time,resource
from pathlib import Path
import circuit
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
GEO=circuit.GEO
F=circuit.F
old=circuit.old

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
    with (HERE/name).open('x') as out:
        json.dump(value,out,sort_keys=True,indent=2);out.write('\n')
def sources():
    return [HERE/'circuit.py',HERE/'experiment.py',GEO,
        ROOT/'n131_w20_selector_elimination_v2_20261013/selector.py',
        ROOT/'n41_basis_aware_quartic_20261011/replay.py',
        ROOT/'n41_w8_fixed_sum_table_20261009/audit.json',
        ROOT/'n41_w8_fixed_sum_table_20261009/geometry.py',
        ROOT/'n131_w20_output_inverse_linear_20261012/linear.py',
        ROOT.parent/'koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py',
        ROOT.parent/'koblitz-s5-invariant-20260924/circuit_sat.py',
        ROOT/'n41_basis_aware_quartic_20261011/sparse.py']
def freeze():
    e=circuit.projector();g=e['geometry']
    wbits=[F.square(v)^v for v in g['blocks'][0]['basis']]
    support=set()
    for mask in range(256):
        w=circuit.xor(wbits[i] for i in range(8) if mask>>i&1)
        if w and circuit.trace(F.inv(w))==0:support.add(mask)
    assert support=={int(k) for k in g['mask_columns']} and len(support)==125
    for code in range(1<<7):
        product=circuit.xor(v for j,v in enumerate(e['basis']) if code>>j&1)
        assert circuit.w20.reconstruct(product,e['codes'],e['pivots'])==code
        assert circuit.w20.reconstruct(product,e['products'],e['pivots'])==product
        expect=circuit.xor(e['source_bits'][j] for j in range(7) if code>>j&1)
        assert circuit.w20.reconstruct(product,e['sources'],e['pivots'])==expect
    save('preflight.json',{'status':'PASS_N41_W8_SELECTOR_PREFLIGHT',
        'support_masks':len(support),'codes_checked':128,
        'source_product_rank':7,'pivot_coordinates':e['pivots'],
        'permitted_pair_codes':40,'slot_count':7})
    from pathlib import Path
    solver=Path('/opt/homebrew/bin/cryptominisat5')
    save('protocol.json',{'status':'FROZEN_BEFORE_N41_W8_SELECTOR_CONTROL_AND_PUBLIC',
        'curve_id':g['curve_id'],'candidate_id':None,
        'source_sha256':{str(p):sha(p) for p in sources()},
        'solver_sha256':sha(solver),'solver_path':str(solver),
        'preflight_sha256':sha(HERE/'preflight.json'),
        'public_point':g['positive_control']['subgroup_target'],
        'raw_target':g['positive_control']['raw_target'],
        'rotations':g['rotations'],'fixed_seed_sum_code':g['fixed_seed_sum_code'],
        'wall_cap_seconds':180,'rss_cap_bytes':4*1024**3,'worker_count':1,
        'solver_flags':['--threads=1','--maxtime=180','--zero-exit-status','--verb=1','--printsol=1']})
    print('FROZEN_N41_SELECTOR_PUBLIC',flush=True)
def checked():
    p=json.loads((HERE/'protocol.json').read_text())
    assert p['source_sha256']=={str(x):sha(x) for x in sources()}
    assert p['preflight_sha256']==sha(HERE/'preflight.json')
    assert p['solver_sha256']==sha(p['solver_path'])
    return p

def fixture_assignment(wires,g,target):
    positive=g['positive_control'];initial={}
    def bind(row,value):initial.update({w:(value>>i)&1 for i,w in enumerate(row)})
    e=circuit.projector();basis=g['blocks'][0]['basis']
    points=[];rotated=[]
    for i,state in enumerate(positive['states']):
        rotation=g['rotations'][i]
        c_rot=circuit.standard(state['z'])
        c=circuit.frob(c_rot,circuit.N-rotation)
        b=F.inv(c)
        bind(wires['outputs'][i],c);bind(wires['inverses'][i],b)
        code=sum(((state['a']>>bit)&1)<<j for j,bit in enumerate(e['bits']))
        assert state['a'] in g['permitted_canonical_a']
        w1=circuit.xor((F.square(basis[j])^basis[j]) for j in range(8) if state['a']>>j&1)
        w2=w1^e['seed']
        assert circuit.trace(F.inv(w1))==circuit.trace(F.inv(w2))==0
        bind(wires['endpoints'][i][0],F.inv(w1))
        bind(wires['endpoints'][i][1],F.inv(w2))
        points.append(tuple(state['raw_sum']))
        rotated.append(c_rot)
    add=lambda x,y:circuit.replay.add(F,x,y)
    middle_points=[add(points[0],points[1]),add(points[2],points[3]),
                   add(points[4],points[5])]
    middle_points.extend((add(middle_points[0],middle_points[1]),
                          add(middle_points[2],points[6])))
    assert all(point and point[0] for point in middle_points)
    assert add(middle_points[3],middle_points[4])==tuple(positive['raw_target'])
    middle=[F.inv(point[0]) for point in middle_points]
    for row,value in zip(wires['middle'],middle):bind(row,value)
    links=[(rotated[0],rotated[1],middle[0]),
           (rotated[2],rotated[3],middle[1]),
           (rotated[4],rotated[5],middle[2]),
           (middle[0],middle[1],middle[3]),
           (middle[2],rotated[6],middle[4]),
           (middle[3],middle[4],target)]
    for j,(left,right,upper) in enumerate(links):
        total=left^right^upper
        branch=F.mul(F.mul(left,right),upper)^F.halftrace(F.square(total))
        assert branch in (0,1)
        initial[wires['branches'][j]]=branch
    return initial

def control():
    p=checked();g=circuit.geometry();target=F.inv(g['positive_control']['raw_target'][0])
    start=time.monotonic_ns();c,w,e=circuit.build(target);built=time.monotonic_ns()
    c.write(HERE/'public.xcnf');written=time.monotonic_ns()
    initial=fixture_assignment(w,g,target)
    values=old.complete_assignment(c,initial)
    checked_rows=old.check_assignment(c,values)
    save('control_result.json',{'status':'PASS_N41_SELECTOR_CONSTRUCTED_ASSIGNMENT',
        'variables':c.next_var-1,'clauses':len(c.clauses),'xor_rows':len(c.xors),
        'and_gates':c.and_count,'formula_bytes':(HERE/'public.xcnf').stat().st_size,
        'formula_sha256':sha(HERE/'public.xcnf'),'assignment_check':checked_rows,
        'initial_variables':len(initial),'construction_ns':built-start,
        'serialization_ns':written-built,
        'peak_process_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'protocol.json')})
    print('PASS_N41_SELECTOR_CONSTRUCTED_ASSIGNMENT',flush=True)
if __name__=='__main__':
    import sys
    {'freeze':freeze,'control':control}[sys.argv[1]]()
