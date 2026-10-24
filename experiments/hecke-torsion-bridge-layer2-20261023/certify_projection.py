"""Certify full rank of the 166-row projection onto brand-new columns."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent
FIRST_VALIDATOR=HERE.parent/'hecke-torsion-bridge-20261023'/'validate.py'
sparse_rank=runpy.run_path(str(FIRST_VALIDATOR))['sparse_rank']

def sha(path):return sha256(path.read_bytes()).hexdigest()

def main():
    data=json.loads((HERE/'result.json').read_text())
    rows=data['accepted_rows'];new=set(data['new_from_prior_indices'])
    assert len(rows)==166 and len(new)==412
    occurrences=Counter(int(j) for row in rows for j,v in row['coefficients'].items()
                        if int(j) in new and v)
    private_rows=sum(any(occurrences[int(j)]==1 for j,v in row['coefficients'].items()
                         if int(j) in new and v) for row in rows)
    basis={};pivots=[];q=101
    for rec in rows:
        v={int(j):int(x)%q for j,x in rec['coefficients'].items() if int(j) in new and x%q}
        while v:
            pivot=min(v)
            if pivot not in basis:
                inv=pow(v[pivot],-1,q)
                basis[pivot]={j:x*inv%q for j,x in v.items() if x}
                pivots.append(pivot)
                break
            factor=v[pivot]
            for j,x in basis[pivot].items():
                value=(v.get(j,0)-factor*x)%q
                if value:v[j]=value
                else:v.pop(j,None)
        else:
            raise AssertionError('dependent new-column projection')
    assert len(pivots)==166 and len(set(pivots))==166
    selected=[{str(j):v for j,v in row['coefficients'].items() if int(j) in set(pivots)}
              for row in rows]
    assert sparse_rank(selected)==166
    out={'status':'SECOND_LAYER_NEW_PROJECTION_FULL_ROW_RANK_CERTIFIED',
         'result_sha256':sha(HERE/'result.json'),'script_sha256':sha(HERE/'certify_projection.py'),
         'first_validator_sha256':sha(FIRST_VALIDATOR),
         'modulus_for_pivot_selection':q,'pivot_column_indices':pivots,
         'exact_selected_minor_rank':166,'new_column_count':412,
         'rows_with_private_new_column':private_rows,
         'new_column_occurrence_histogram':{str(k):v for k,v in sorted(Counter(occurrences.values()).items())},
         'candidate_id':None,'timing_claim':None}
    (HERE/'projection_certificate.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'pivots':len(pivots),
                      'private_rows':private_rows},sort_keys=True))

if __name__=='__main__':main()
