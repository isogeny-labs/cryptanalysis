"""Independent exact-integer matrix audit for translation closure at three stages."""
from hashlib import sha256
import json
from pathlib import Path
from sage.all import ZZ, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'rank_validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_EXACT_RANK_REPLAY'
    paths={'control':HERE/'control_result.json','translation':HERE/'translation_result.json',
           'rank':ROOT/'hecke-l29-trace-orbits-20261024/all_rank_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    old=[tuple(a) for a in data['frontier']['column_representatives']]
    assert old==[tuple(a) for a in data['control']['column_representatives']]
    base=[z['coefficients'] for z in data['seed']['accepted_rows']]+data['frontier']['rows']
    sign=[z['coefficients'] for z in data['sign']['sign_rows']]
    # The anchor is the previously saved orbit representative of (1,8630).
    anchor_old=old.index((1,8630))
    def rank(rows,columns,anchor):
        entries={(i,int(j)):int(v) for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)]=1
        return matrix(ZZ,len(rows)+1,columns,entries,sparse=False)
    controls={}
    for stage,rows in [('seed_plus_degree2_3_hecke',base),
                       ('seed_plus_degree2_3_hecke_plus_inversion',base+sign)]:
        saved=data['control']['results'][stage]
        before=rank(rows,len(old),anchor_old)
        after=rank(rows+[z['coefficients'] for z in saved['selected_rows']],len(old),anchor_old)
        assert int(before.rank())==saved['baseline_rank']
        assert int(after.rank())==saved['exact_integer_rank']==len(old)
        controls[stage]={'baseline_exact_rank':int(before.rank()),
                         'shift_augmented_exact_rank':int(after.rank())}
        print(json.dumps({'stage':stage,**controls[stage]},sort_keys=True),flush=True)

    keys=[tuple(a) for a in data['translation']['column_representatives']]
    l23=[tuple(a) for a in data['l23']['all_column_representatives']]
    l29=[tuple(a) for a in data['l29']['all_column_representatives']]
    idx={a:i for i,a in enumerate(keys)}
    def remap(row,reps):return {str(idx[reps[int(j)]]):v for j,v in row.items()}
    rows=[remap(z['coefficients'],old) for z in data['seed']['accepted_rows']]
    rows += [remap(z,old) for z in data['frontier']['rows']]
    rows += [remap(z['coefficients'],old) for z in data['sign']['sign_rows']]
    rows += [remap(z['coefficients'],l23) for z in data['l23']['accepted_rows']]
    rows += [remap(z['coefficients'],l29) for z in data['l29']['accepted_rows']]
    rows += [z['coefficients'] for z in data['rank']['trace_rows']]
    anchor=idx[(1,8630)]
    before=rank(rows,len(keys),anchor)
    first=rank(rows+[data['translation']['selected_rows'][0]['coefficients']],len(keys),anchor)
    after=rank(rows+[z['coefficients'] for z in data['translation']['selected_rows']],len(keys),anchor)
    assert int(before.rank())==3958
    assert int(first.rank())==int(after.rank())==3959
    newcols=sorted(set(range(len(keys)))-{idx[a] for a in old})
    projection=int(after.matrix_from_columns(newcols).rank())
    assert projection==10 and int(after.rank())-projection==3949
    out={'status':'PASS_EXACT_TRANSLATION_RANK_REPLAY','controls':controls,
         'trace_baseline_rank':int(before.rank()),
         'first_shift_rank':int(first.rank()),'all_shifts_rank':int(after.rank()),
         'new_column_projection_rank':projection,'induced_old_rank':int(after.rank())-projection,
         'source_sha256':{k:sha(v) for k,v in paths.items()}}
    (HERE/'rank_validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'trace_baseline_rank':out['trace_baseline_rank'],
                      'first_shift_rank':out['first_shift_rank'],
                      'induced_old_rank':out['induced_old_rank']},sort_keys=True),flush=True)

if __name__=='__main__':main()
