"""Freeze and build the exact source-selector-eliminated W20 control."""
import hashlib,json,resource,time
from pathlib import Path
import selector

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'n131_w20_output_inverse_linear_20261012'
W20=HERE.parent/'n131_w20_sevenpair_gate_20261010'
old,seven=selector.old,selector.seven

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(name,value):
    with (HERE/name).open('x') as out:
        json.dump(value,out,sort_keys=True,indent=2);out.write('\n')
def inputs():
    p=selector.prior
    return [HERE/'selector.py',HERE/'experiment.py',PRIOR/'linear.py',
            PRIOR/'protocol.json',PRIOR/'basis_rank_result.json',
            W20/'sevenpair_circuit.py',W20/'support_w20.tsv',
            W20/'sage_audit_result.json',p.PRIOR/'run.py',
            p.ROOT/'n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py',
            p.ROOT.parent/'koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py',
            p.ROOT/'n41_basis_aware_quartic_20261011/sparse.py']
def freeze():
    e=selector.eliminate_basis()
    original=HERE.parent/'n131_w20_selector_elimination_20261013/basis_result.json'
    assert sha(HERE/'basis_result.json')==sha(original)
    assert json.loads((HERE/'basis_result.json').read_text())['codes_checked']==1<<19
    assert json.loads((HERE/'basis_result.json').read_text())['product_images']==e['product_images']
    assert json.loads((HERE/'basis_result.json').read_text())['code_images']==e['code_images']
    prior=json.loads((PRIOR/'protocol.json').read_text())
    write('protocol.json',{'status':'FROZEN_BEFORE_SELECTOR_ELIMINATION_CONTROL',
        'curve_id':prior['curve_id'],'candidate_id':None,
        'product_rank':19,'left_nullity':112,
        'source_codes_per_slot':132045,'pair_slots':7,
        'control_fixture_sha256':sha(W20/'sage_audit_result.json'),
        'rss_cap_bytes':4*1024**3,'wall_cap_seconds':120,
        'source_sha256':{str(x):sha(x) for x in inputs()+[original]},
        'basis_result_sha256':sha(HERE/'basis_result.json')})
    print('FROZEN_SELECTOR_ELIMINATION',flush=True)
def checked_protocol():
    data=json.loads((HERE/'protocol.json').read_text())
    assert data['source_sha256']=={str(x):sha(x) for x in inputs()+[HERE.parent/'n131_w20_selector_elimination_20261013/basis_result.json']}
    assert data['basis_result_sha256']==sha(HERE/'basis_result.json')
    return data
def control():
    protocol=checked_protocol()
    fixture=json.loads((W20/'sage_audit_result.json').read_text())
    target_a=old.standard_reciprocal(fixture['constructed_raw_target_z'])
    start=time.monotonic_ns();circuit,wires,e=selector.build(target_a)
    built=time.monotonic_ns()
    circuit.write(HERE/'control.xcnf')
    written=time.monotonic_ns()
    initial={}
    def bind(vector,value):
        initial.update({wire:(value>>bit)&1 for bit,wire in enumerate(vector)})
    seed,bits=seven.seed_and_bits();pair=old.pair
    h2=pair.gf_square(pair.gf_half_trace(seven.coordinate(seed)))
    for item in fixture['selected']:
        slot=item['slot']
        code=seven.selector_code(item['masks'][0],bits)
        a=old.standard_reciprocal(item['unrotated_pair_output_z'])
        b=old.inverse(a)
        product=pair.gf_mul(1^h2,a)^pair.gf_mul(h2,b)
        assert selector.reconstruct(product,e['code_images'],e['pivots'])==code
        bind(wires['outputs'][slot],a);bind(wires['output_inverse'][slot],b)
        for side,mask in enumerate(item['masks']):
            x=seven.coordinate(mask);inv=old.inverse(x)
            assert x and old.trace(inv)==0
            bind(wires['inverse_witnesses'][slot][side],inv)
    for vector,z in zip(wires['intermediates'],fixture['intermediate_z']):
        bind(vector,old.standard_reciprocal(z))
    rotated=[pair.gf_frobenius(old.standard_reciprocal(item['unrotated_pair_output_z']),
                               item['rotation']) for item in fixture['selected']]
    middle=[old.standard_reciprocal(z) for z in fixture['intermediate_z']]
    left=rotated[0]
    for index in range(1,7):
        right=middle[index-1] if index<6 else target_a
        total=left^rotated[index]^right
        branch=pair.gf_mul(pair.gf_mul(left,rotated[index]),right)^old.halftrace(pair.gf_square(total))
        assert branch in (0,1)
        initial[wires['branches'][index-1]]=branch
        left=right
    assignment=old.complete_assignment(circuit,initial)
    checked=old.check_assignment(circuit,assignment)
    result={'status':'PASS_SELECTOR_ELIMINATED_CONSTRUCTED_CONTROL',
        'formula_sha256':sha(HERE/'control.xcnf'),
        'formula_bytes':(HERE/'control.xcnf').stat().st_size,
        'variables':circuit.next_var-1,'and_gates':circuit.and_count,
        'clauses':len(circuit.clauses),'native_xor_rows':len(circuit.xors),
        'assignment_check':checked,'initial_variables':len(initial),
        'construction_ns':built-start,'serialization_ns':written-built,
        'peak_process_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'protocol.json')}
    write('control_result.json',result)
    print(result['status'],result['variables'],result['clauses'],result['native_xor_rows'],flush=True)
if __name__=='__main__':
    import sys
    {'freeze':freeze,'control':control}[sys.argv[1]]()
