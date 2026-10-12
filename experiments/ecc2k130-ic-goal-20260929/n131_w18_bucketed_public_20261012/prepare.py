"""Freeze target-ordered, source-valid two-mask bucket formulas."""
import hashlib,json,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'n131_w18_allseed_fourpair_20261012'
TRACE=HERE.parent/'n131_w18_joint_pair_filter_20261012'
sys.path.insert(0,str(BASE));sys.path.insert(0,str(TRACE))
from fourpair_v2 import build,check_assignment,field_config,support
from trace_circuit import trace_extend

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    started=time.monotonic_ns()
    p=json.loads((HERE/'protocol.json').read_text())
    sources={'prepare':HERE/'prepare.py','base_builder':BASE/'fourpair_v2.py',
             'trace_source':TRACE/'trace_circuit.py','base_formula':TRACE/'ordinary.xcnf',
             'fixture':BASE/'n41_diagonal/control_fixture.json',
             'geometry':HERE.parent/'n41_w7_entropy_cubic_20261011/w8/geometry.json'}
    assert {k:sha(v) for k,v in sources.items()}==p['source_sha256']
    fixture=json.loads(sources['fixture'].read_text())
    field,_,rotations=field_config('n41')
    circuit,wires,_=build('n41',int(fixture['target_reciprocal']))
    trace_extend(circuit,wires,field)
    assert check_assignment(circuit,wires,fixture,field,rotations)['status']=='PASS_COMPLETE_CONSTRUCTED_ASSIGNMENT'
    replay=HERE/'base_replay.xcnf';assert not replay.exists();circuit.write(replay)
    assert sha(replay)==sha(sources['base_formula'])
    base=replay.read_bytes();replay.unlink()
    header,body=base.split(b'\n',1)
    toks=header.split();assert toks[:2]==[b'p',b'cnf']
    assert int(toks[2])==14803 and int(toks[3])==38702
    maskvars=[wires['masks'][0],wires['masks'][1]]
    assert len(maskvars[0])==len(maskvars[1])==8
    columns=support('n41');eligible={}
    for a,ca in columns.items():
        for b,cb in columns.items():
            if a>=b or ca==cb:continue
            bucket=(a&63)|((b&63)<<6)
            eligible[bucket]=eligible.get(bucket,0)+1
            if (a&63)!=(b&63):
                bucket=(b&63)|((a&63)<<6)
                eligible[bucket]=eligible.get(bucket,0)+1
    public=fixture['public_target']
    target_bytes=b''.join(int(x).to_bytes(6,'little') for x in public)
    def order(bucket):
        return hashlib.sha256(b'joint-bucket-v1'+target_bytes+bucket.to_bytes(2,'little')).digest()
    ordered=sorted(eligible,key=order)
    selected=ordered[:p['bucket_attempts']]
    assert len(selected)==p['bucket_attempts']
    rows=[]
    for rank,bucket in enumerate(selected):
        first=bucket&63;second=bucket>>6
        units=[(wire if (value>>i)&1 else -wire)
               for bits,value in ((maskvars[0],first),(maskvars[1],second))
               for i,wire in enumerate(bits[:6])]
        unit_bytes=b''.join(f'{v} 0\n'.encode() for v in units)
        formula=b'p cnf '+toks[2]+b' '+str(int(toks[3])+len(units)).encode()+b'\n'+unit_bytes+body
        path=HERE/f'bucket_{rank:02}.xcnf';assert not path.exists();path.write_bytes(formula)
        rows.append({'rank':rank,'bucket':bucket,'low6_masks':[first,second],
                     'admissible_unordered_source_edges':eligible[bucket],
                     'unit_literals':units,'formula_sha256':sha(path),
                     'formula_bytes':len(formula)})
    elapsed=time.monotonic_ns()-started
    result={'status':'FROZEN_BUCKET_FORMULAS','candidate_id':None,
            'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','public_target':public,
            'raw_preimage_index':fixture['raw_preimage_index'],
            'eligible_bucket_count':len(ordered),'source_mask_count':len(columns),
            'first_two_mask_variables':maskvars,'plan':rows,
            'base_formula_sha256':sha(sources['base_formula']),
            'protocol_sha256':sha(HERE/'protocol.json'),
            'prepare_wall_ns':elapsed}
    (HERE/'bucket_plan.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],len(ordered),selected,flush=True)

if __name__=='__main__':main()
