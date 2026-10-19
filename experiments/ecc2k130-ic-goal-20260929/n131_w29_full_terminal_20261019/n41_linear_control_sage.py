"""Exhaust the frozen N41 terminal outputs through both half-trace paths."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'n41_n131_implicit_pair_output_20261019'
spec=importlib.util.spec_from_file_location('pair_preparer',PRIOR/'prepare_terminal_sage.py')
prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def raw_halftrace(x):
    out=x
    for _ in range(20):x=x**4;out+=x
    return out

def main():
    cfg=json.loads((HERE/'n41_linear_control.protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_N41_LINEAR_CONTROL'
    assert cfg['script_sha256']==sha(__file__)
    for record in cfg['inputs'].values():assert sha(record['path'])==record['sha256']
    lines=(PRIOR/'terminal_n41.txt').read_text().splitlines()
    head=lines[0].split();assert head[:3]==['TERMINAL','41','10']
    f=prep.base.field(41);F=f.from_integer
    C,H,t=map(lambda x:F(int(x)),head[3:6])
    rows=[tuple(map(int,line.split())) for line in lines[11:]]
    assert len(rows)==562
    images=[raw_halftrace(F(1<<i)**2) for i in range(41)]
    roots=hits=0;found=[]
    basis=[F(int(x)) for x in lines[1:11]]
    products={prep.base.encode(prep.source_code(basis,code,f.zero())):code for code in range(1<<10)}
    for index,(cnum,leftcode) in enumerate(rows):
        c=F(cnum);A=1+(c*t)**2;B=c*t;D=(c+t)**2
        assert A!=0 and B!=0
        q=A*D/B**2;z=c+1/c+t+1/t
        assert q==z**2
        direct=raw_halftrace(q)
        bits=prep.base.encode(z)
        table=sum((images[i] for i in range(41) if bits>>i&1),f.zero())
        assert direct==table and table**2+table==q
        expected={prep.base.encode(x) for x in prep.base.roots(B,A,D,41)}
        actual={prep.base.encode(B/A*table),prep.base.encode(B/A*(table+1))}
        assert actual==expected and len(actual)==2
        roots+=2
        for dnum in actual:
            d=F(dnum);assert prep.s3(c,d,t)==0
            p=(C*d**2+H)/d
            code=products.get(prep.base.encode(p))
            if code is not None:
                hits+=1;found.append([index,leftcode,code,cnum,dnum])
    assert roots==1124 and hits==1
    assert found[0][1:3]==[253,63]
    result={'status':'PASS_N41_LINEAR_TERMINAL_CONTROL','candidate_id':None,
            'left_outputs':len(rows),'s3_roots':roots,'product_image_hits':hits,
            'hit':found[0],'protocol_sha256':sha(HERE/'n41_linear_control.protocol.json')}
    (HERE/'n41_linear_control_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
