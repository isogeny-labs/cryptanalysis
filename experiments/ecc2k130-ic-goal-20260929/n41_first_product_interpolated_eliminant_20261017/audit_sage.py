#!/usr/bin/env sage -python
"""Independent elliptic-curve replay of interpolated-code survivors."""
import hashlib,itertools,json,time
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
GEO=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    start=time.monotonic_ns()
    protocol=json.loads((HERE/'audit_protocol.json').read_text())
    files={'audit_sage':HERE/'audit_sage.py','sweep_result':HERE/'sweep_result.json',
           'geometry':GEO,'runtime':HERE/'sage_runtime_info.json'}
    assert protocol['source_sha256']=={k:sha(p) for k,p in files.items()}
    geo=json.loads(GEO.read_text());sweep=json.loads((HERE/'sweep_result.json').read_text())
    poly=PolynomialRing(GF(2),'t');t=poly.gen()
    field=GF(2**41,name='t',modulus=t**41+t**3+1)
    def dec(v):return field(poly([(v>>i)&1 for i in range(41)]))
    curve=EllipticCurve(field,[1,0,0,0,1])
    def point(row):return curve([dec(row['raw_sum'][0]),dec(row['raw_sum'][1])])
    target=curve([dec(v) for v in geo['positive_control']['raw_target']])
    panels=[]
    for panel in sweep['panels']:
        suffix_rows=[geo['blocks'][k]['states'][sid] for k,sid in enumerate(panel['suffix_state_ids'],3)]
        suffix=sum((point(row) for row in suffix_rows),curve(0))
        residual=target-suffix
        assert residual!=curve(0) and residual[0]!=1
        assert 1/(residual[0]+1)==dec(panel['residual_chart'])
        hits=[];states_checked=0
        for candidate in panel['zero_triples']:
            buckets=[]
            for slot,mask in enumerate(candidate['masks']):
                states=[(sid,row) for sid,row in enumerate(geo['blocks'][slot]['states'])
                        if row['a']==mask]
                assert len(states)==4
                buckets.append(states)
            for group in itertools.product(*buckets):
                states_checked+=1
                free=[row for sid,row in group]
                columns=[col for row in free+suffix_rows for col in row['columns']]
                if len(set(columns))!=14:continue
                total=sum((point(row) for row in free+suffix_rows),curve(0))
                if total==target:
                    hits.append({'state_ids':[sid for sid,row in group]+panel['suffix_state_ids'],
                                 'masks':candidate['masks'],'products':candidate['products'],
                                 'distinct_columns':len(set(columns))})
        panels.append({'name':panel['name'],'survivor_code_triples':len(panel['zero_triples']),
                       'signed_state_combinations_checked':states_checked,'group_hits':hits})
    assert len(panels[0]['group_hits'])>=1 and panels[1]['group_hits']==[]
    out={'status':'PASS_INTERPOLATED_SWEEP_GROUP_AUDIT','curve_id':geo['curve_id'],
         'protocol_sha256':sha(HERE/'audit_protocol.json'),'source_sha256':protocol['source_sha256'],
         'panels':panels,'elapsed_ns':time.monotonic_ns()-start}
    with (HERE/'audit_result.json').open('x') as output:json.dump(out,output,indent=2,sort_keys=True);output.write('\n')
    print(json.dumps({'status':out['status'],'hits':len(panels[0]['group_hits']),
                      'states_checked':states_checked}))
if __name__=='__main__':main()
