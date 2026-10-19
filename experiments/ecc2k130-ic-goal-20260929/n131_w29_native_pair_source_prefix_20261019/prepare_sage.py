"""Freeze source bases for a native N41 and W29 prefix census."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'n41_n131_implicit_pair_output_20261019'
spec=importlib.util.spec_from_file_location('implicit_terminal_prepare',PRIOR/'prepare_terminal_sage.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def one(n,seed,positions,rotation,limit,fixture):
    f,s,w_basis,p_basis,C,H=prior.source_data(n,seed,positions,rotation)
    assert len(w_basis)==len(p_basis)==len(positions)
    path=HERE/f'source_n{n}.txt'
    with path.open('x') as out:
        out.write(f'SOURCE {n} {len(positions)} {prior.base.encode(s)} '
                  f'{prior.base.encode(C)} {prior.base.encode(H)} {limit} {fixture}\n')
        for w,p in zip(w_basis,p_basis):
            out.write(f'{prior.base.encode(w)} {prior.base.encode(p)}\n')
    return {'field_degree':n,'seed_mask':seed,'free_positions':positions,
            'rotation':rotation,'code_limit':limit,'fixture_code':fixture,
            'source_field':prior.base.encode(s),'quadratic_c':prior.base.encode(C),
            'quadratic_h':prior.base.encode(H),'path':str(path),'sha256':sha(path)}


def main():
    cfg=json.loads((HERE/'prepare_protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_NATIVE_PAIR_SOURCE_PREPARATION'
    assert sha(__file__)==cfg['script_sha256']
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    cases=[one(41,56,[0,1,2,3,4,6,7,8,9,10],12,1<<10,253),
           one(131,898618,[i for i in range(29) if i!=(898618).bit_length()-1],
               54,1<<20,22)]
    result={'status':'PASS_NATIVE_PAIR_SOURCE_PREPARATION','candidate_id':None,
            'cases':cases,'protocol_sha256':sha(HERE/'prepare_protocol.json'),
            'script_sha256':sha(__file__)}
    (HERE/'prepare_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
