"""Replay every native S3 root and fixed-seed product-image hit."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pair_preparer',HERE/'prepare_sage.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_fe(value):
    parts=json.loads(value)
    assert len(parts)==3 and all(0<=part<1<<64 for part in parts)
    return parts[0] | parts[1]<<64 | parts[2]<<128


def decoder(values):
    pivots={}
    for i,value in enumerate(values):
        mask=1<<i
        while value:
            k=value.bit_length()-1
            if k not in pivots:
                pivots[k]=(value,mask);break
            p,m=pivots[k];value^=p;mask^=m
        else:raise AssertionError('dependent basis')
    def decode(value):
        mask=0
        while value:
            k=value.bit_length()-1
            if k not in pivots:return -1
            p,m=pivots[k];value^=p;mask^=m
        return mask
    return decode


def s3(a,b,t):return (a+b+t)**2 + a*b*t + (a*b*t)**2


def main():
    assert len(sys.argv)==2 and sys.argv[1] in ('n41','n131')
    label=sys.argv[1]
    cfg=json.loads((HERE/f'terminal_audit_protocol_{label}.json').read_text())
    assert cfg['status']==f'FROZEN_BEFORE_IMPLICIT_TERMINAL_AUDIT_{label.upper()}'
    assert cfg['script_sha256']==sha(__file__)
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    prep=json.loads((HERE/'terminal_prepare_result.json').read_text())
    n=41 if label=='n41' else 131
    case=next(item for item in prep['cases'] if item['field_degree']==n)
    f=base.field(n);decode=f.from_integer
    raw=(HERE/f'terminal_{label}.txt').read_text().splitlines()
    header=raw[0].split()
    assert header[:3]==['TERMINAL',str(n),str(case['right_product_dimension'])]
    C,H,t=map(lambda x:decode(int(x)),header[3:6])
    count=int(header[6]);d=case['right_product_dimension']
    assert count==case['left_outputs']
    basis=[int(x) for x in raw[1:1+d]]
    left=[tuple(map(int,row.split())) for row in raw[1+d:]]
    assert len(left)==count
    product_code=decoder(basis)
    lines=(HERE/f'terminal_{label}.stdout').read_text().splitlines()
    roots=[line.split() for line in lines if line.startswith('ROOT ')]
    hits=[line.split() for line in lines if line.startswith('HIT ')]
    finals=[line.split() for line in lines if line.startswith('RESULT ')]
    assert len(finals)==1 and finals[0][1:5]==['COMPLETE',str(n),str(d),str(count)]
    expected=set()
    for index,(cint,leftcode) in enumerate(left):
        c=decode(cint)
        A=1+(c*t)**2;B=c*t;D=(c+t)**2
        candidates=base.roots(B,A,D,n)
        for right in candidates:
            if right==0:continue
            assert s3(c,right,t)==0
            dint=base.encode(right)
            p=(C*right**2+H)/right
            code=product_code(base.encode(p))
            expected.add((index,leftcode,cint,dint,code))
    found=set()
    for row in roots:
        assert len(row)==6
        index,leftcode=map(int,row[1:3])
        c,d=map(parse_fe,row[3:5]);code=int(row[5])
        found.add((index,leftcode,c,d,code))
    assert len(found)==len(roots) and found==expected
    expected_hits={(leftcode,code,c,d) for _,leftcode,c,d,code in expected if code>=0}
    found_hits=set()
    for row in hits:
        assert len(row)==6
        leftcode,rightcode=map(int,row[1:3])
        c,d,p=map(parse_fe,row[3:6])
        assert p==base.encode((C*decode(d)**2+H)/decode(d))
        found_hits.add((leftcode,rightcode,c,d))
    assert found_hits==expected_hits
    assert (case['known_left_code'],case['known_right_code'],
            *case['known_output_pairs'][0]) in found_hits
    assert int(finals[0][7])==len(roots) and int(finals[0][8])==len(hits)
    receipt=json.loads((HERE/f'terminal_{label}.receipt.json').read_text())
    assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
    assert receipt['stdout_sha256']==sha(HERE/f'terminal_{label}.stdout')
    assert receipt['stderr_sha256']==sha(HERE/f'terminal_{label}.stderr')
    result={'status':f'PASS_IMPLICIT_TERMINAL_AUDIT_{label.upper()}',
            'candidate_id':None,'field_degree':n,'left_outputs':count,
            'right_roots_replayed':len(roots),'membership_hits':len(hits),
            'known_witness':[case['known_left_code'],case['known_right_code'],
                             *case['known_output_pairs'][0]],
            'native_query_ns':int(finals[0][9]),
            'protocol_sha256':sha(HERE/f'terminal_audit_protocol_{label}.json'),
            'stdout_sha256':sha(HERE/f'terminal_{label}.stdout'),
            'script_sha256':sha(__file__)}
    (HERE/f'terminal_audit_result_{label}.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
