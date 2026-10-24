"""Exact row-combination witnesses for the third-frontier induced ranks."""
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent
PREV_VALIDATOR=HERE.parent/'hecke-torsion-bridge-layer2-20261023'/'validate.py'
sparse_rank=runpy.run_path(str(PREV_VALIDATOR))['sparse_rank']

def sha(path):return sha256(path.read_bytes()).hexdigest()
def clean(v):return {k:x for k,x in v.items() if x}

def subtract(v,b,factor):
    for k,x in b.items():
        y=v.get(k,0)-factor*x
        if y:v[k]=y
        else:v.pop(k,None)

def combine(rows,combo):
    out={}
    for i,factor in combo.items():
        for col,value in rows[i].items():
            key=int(col)
            y=out.get(key,0)+factor*value
            if y:out[key]=y
            else:out.pop(key,None)
    return out

def kernel_combinations(rows,discarded):
    wanted=set(discarded);basis={};closed=[]
    for i,row in enumerate(rows):
        v={int(j):Fraction(x) for j,x in row.items() if int(j) in wanted and x}
        coeff={i:Fraction(1)}
        while v:
            pivot=min(v)
            if pivot not in basis:
                inv=1/v[pivot]
                basis[pivot]=({j:x*inv for j,x in v.items()},
                              {j:x*inv for j,x in coeff.items()})
                break
            factor=v[pivot]
            b,bc=basis[pivot]
            subtract(v,b,factor);subtract(coeff,bc,factor)
        else:
            assert coeff
            closed.append(coeff)
    return closed,len(basis)

def encode(v):return {str(k):str(x) for k,x in sorted(v.items()) if x}

def main():
    protocol=json.loads((HERE/'certificate_protocol.json').read_text())
    data=json.loads((HERE/'result.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_CLOSED_COMBINATION_CERTIFICATES'
    assert protocol['result_sha256']==sha(HERE/'result.json')
    rows=(data['base_rows']+data['layer1_rows']+data['layer2_rows']+
          [r['coefficients'] for r in data['accepted_rows']])
    assert len(rows)==844
    output={}
    for name,baseline_count,baseline_rank in [('previous',276,266),('first',110,100),('old',70,60)]:
        discarded=data['discard_'+name+'_indices']
        retained=set(data[name+'_column_indices'])
        closed,rank_b=kernel_combinations(rows,discarded)
        nontrivial=[c for c in closed if any(i>=baseline_count for i in c)]
        assert len(closed)==844-rank_b
        assert len(nontrivial)==len(closed)-baseline_count
        assert sparse_rank(rows[:baseline_count])==baseline_rank
        selected=[];base_images=[];records=[]
        for combo in nontrivial:
            combined=combine(rows,combo)
            assert not (set(combined)&set(discarded))
            image={str(j):v for j,v in combined.items() if j in retained}
            trial=sparse_rank(rows[:baseline_count]+base_images+[image])
            novel=trial>baseline_rank+len(base_images)
            if novel:
                base_images.append(image);selected.append(len(records))
            records.append({'combination':encode(combo),'retained_image':encode({int(j):v for j,v in image.items()}),
                            'selected_as_novel':novel})
        induced=baseline_rank+len(selected)
        assert induced==data['rank_results']['101']['induced_'+name+'_rank']
        output[name]={'discarded_projection_rank':rank_b,'closed_combination_count':len(closed),
                      'nontrivial_combination_count':len(nontrivial),
                      'selected_novel_indices':selected,'induced_rank':induced,
                      'induced_increment':len(selected),'records':records}
    out={'status':'EXACT_THIRD_FRONTIER_CLOSED_COMBINATIONS_CERTIFIED',
         'result_sha256':sha(HERE/'result.json'),
         'certificate_protocol_sha256':sha(HERE/'certificate_protocol.json'),
         'script_sha256':sha(HERE/'certify_closed.py'),
         'previous_validator_sha256':sha(PREV_VALIDATOR),
         'boundaries':output,'candidate_id':None,'timing_claim':None}
    (HERE/'closed_certificates.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],
                      'increments':{k:v['induced_increment'] for k,v in output.items()},
                      'nontrivial':{k:v['nontrivial_combination_count'] for k,v in output.items()}},sort_keys=True))

if __name__=='__main__':main()
