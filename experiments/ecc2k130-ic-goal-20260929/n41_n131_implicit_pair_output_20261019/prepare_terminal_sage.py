"""Freeze target-conditioned two-pair residuals and left output domains."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location('pair_preparer', HERE / 'prepare_sage.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_data(n, seed_mask, positions, rotation):
    f = base.field(n)
    s = f.from_integer(seed_mask << 1)
    h = base.halftrace(s, n)
    assert h is not None
    H, C = h**2, 1 + h**2
    src = [f.from_integer(1 << (i + 1)) for i in positions]
    basis = [(w**2 + s*w)**(1 << rotation) for w in src]
    return f, s, src, basis, C**(1 << rotation), H**(1 << rotation)


def source_code(src,code,zero):
    return sum((src[i] for i in range(len(src)) if code >> i & 1), zero)


def valid(w,s):
    v=w+s
    return (w!=0 and v!=0 and w.trace()==0 and v.trace()==0 and
            (1/w).trace()==0 and (1/v).trace()==0)


def s3(a,b,t):
    return (a+b+t)**2 + a*b*t + (a*b*t)**2


def one_case(n,seed_mask,positions,left_rotation,right_rotation,
             left_limit,left_known,right_known,target):
    f,s,src,_,_,_=source_data(n,seed_mask,positions,left_rotation)
    _,_,_,right_basis,Cright,Hright=source_data(n,seed_mask,positions,right_rotation)
    _,_,_,left_basis,Cleft,Hleft=source_data(n,seed_mask,positions,left_rotation)
    outputs=[]
    valid_codes=0
    for code in range(left_limit):
        w=source_code(src,code,f.zero())
        if not valid(w,s):continue
        valid_codes+=1
        p=sum((left_basis[i] for i in range(len(positions)) if code>>i&1),f.zero())
        roots=base.roots(p,Cleft,Hleft,n)
        assert len(roots)==2
        for c in roots:
            assert c!=0 and Cleft*c**2+p*c+Hleft==0
            outputs.append((base.encode(c),code))
    assert any(code==left_known for _,code in outputs)
    w=source_code(src,right_known,f.zero())
    assert valid(w,s)
    pR=sum((right_basis[i] for i in range(len(positions)) if right_known>>i&1),f.zero())
    right_roots=base.roots(pR,Cright,Hright,n)
    assert len(right_roots)==2
    t=f.from_integer(target)
    witnesses=[(c,base.encode(d)) for c,code in outputs if code==left_known
               for d in right_roots if s3(f.from_integer(c),d,t)==0]
    assert witnesses
    path=HERE / f'terminal_n{n}.txt'
    with path.open('x') as out:
        out.write(f'TERMINAL {n} {len(positions)} {base.encode(Cright)} '
                  f'{base.encode(Hright)} {target} {len(outputs)}\n')
        for b in right_basis:out.write(f'{base.encode(b)}\n')
        for c,code in outputs:out.write(f'{c} {code}\n')
    return {'field_degree':n,'left_rotation':left_rotation,
            'right_rotation':right_rotation,'left_code_limit':left_limit,
            'left_valid_codes':valid_codes,'left_outputs':len(outputs),
            'right_product_dimension':len(positions),'known_left_code':left_known,
            'known_right_code':right_known,'known_output_pairs':witnesses,
            'target_reciprocal':target,'path':str(path),'sha256':sha(path)}


def main():
    cfg=json.loads((HERE/'terminal_prepare_protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_IMPLICIT_TERMINAL_PREPARATION'
    assert sha(__file__)==cfg['script_sha256']
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    fixture=json.loads((ROOT/'n41_n131_fivepair_w9_w29_20261017'/
                        'n131_control_3p2.json').read_text())
    assert fixture['pairs'][3]['masks'][0]==22
    assert fixture['pairs'][4]['masks'][0]==29
    f41=base.field(41)
    t41=base.encode(1/f41.from_integer(1434452595080))
    start=time.monotonic()
    rows=[one_case(41,56,[0,1,2,3,4,6,7,8,9,10],12,24,
                   1<<10,253,63,t41)]
    rows.append(one_case(131,898618,
        [i for i in range(29) if i != (898618).bit_length()-1],54,72,
        4096,22,29,fixture['middle_reciprocals'][2]))
    result={'status':'PASS_IMPLICIT_TERMINAL_PREPARATION','candidate_id':None,
            'cases':rows,'wall_seconds':time.monotonic()-start,
            'protocol_sha256':sha(HERE/'terminal_prepare_protocol.json'),
            'script_sha256':sha(__file__)}
    (HERE/'terminal_prepare_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
