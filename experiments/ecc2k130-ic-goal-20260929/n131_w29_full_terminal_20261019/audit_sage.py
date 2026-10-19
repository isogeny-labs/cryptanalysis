"""Independent Sage replay of the complete-stream prefix and reported roots."""
import collections
import hashlib
import importlib.util
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'n41_n131_implicit_pair_output_20261019'
spec=importlib.util.spec_from_file_location('pair_preparer',PRIOR/'prepare_terminal_sage.py')
prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()

def unpack(data):
    return int.from_bytes(data[:8],'little')+(int.from_bytes(data[8:16],'little')<<64)+(data[16]<<128)

def bracket_fields(line):
    return [sum(int(limb)<<(64*i) for i,limb in enumerate(json.loads(s)))
            for s in re.findall(r'\[[^]]+\]',line)]

def raw_halftrace(x):
    out=x
    for _ in range(65):
        x=x**4;out+=x
    return out

def main():
    cfg=json.loads((HERE/'audit.protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_FULL_TERMINAL_AUDIT'
    assert sha(__file__)==cfg['script_sha256']
    for record in cfg['inputs'].values():assert sha(record['path'])==record['sha256']
    f=prep.base.field(131);F=f.from_integer
    fixture=json.loads((ROOT/'n41_n131_fivepair_w9_w29_20261017'/'n131_control_3p2.json').read_text())
    coefficients=json.loads((ROOT/'n131_w33_freecode_resultant_20261018'/'coefficients.json').read_text())
    public=next(row for row in coefficients['rows'] if row['name']=='frozen_public_raw_point')
    assert F(public['point'][0])*F(public['reciprocal'])==1
    assert public['reciprocal']==770794657550069419943936485965613853151
    assert fixture['middle_reciprocals'][2]==1240393003299480760304964344285952783315
    positions=[i for i in range(29) if i!=(898618).bit_length()-1]
    _,s,src,left_basis,Cl,Hl=prep.source_data(131,898618,positions,54)
    _,_,_,right_basis,Cr,Hr=prep.source_data(131,898618,positions,72)
    old=(PRIOR/'terminal_n131.txt').read_text().splitlines()
    prior_entries=[tuple(map(int,line.split())) for line in old[29:]]
    assert len(prior_entries)==2128
    with (HERE/'all.bin').open('rb') as inp:raw=inp.read(2128*17)
    actual=[unpack(raw[i:i+17]) for i in range(0,len(raw),17)]
    assert collections.Counter(actual)==collections.Counter(c for c,_ in prior_entries)
    lookup=dict(prior_entries)
    for cint in actual:
        code=lookup[cint]
        w=prep.source_code(src,code,f.zero())
        assert prep.valid(w,s)
        product=prep.source_code(left_basis,code,f.zero())
        c=F(cint)
        assert Cl*c*c+product*c+Hl==0
    images=[raw_halftrace(F(1<<i)**2) for i in range(131)]
    for tnum in (1240393003299480760304964344285952783315,
                 770794657550069419943936485965613853151):
        t=F(tnum)
        for cint in actual[:128]:
            c=F(cint);z=c+1/c+t+1/t
            assert (1+(c*t)**2)*(c+t)**2/(c*t)**2==z**2
            h=raw_halftrace(z**2)
            bits=prep.base.encode(z)
            table=sum((images[i] for i in range(131) if bits>>i&1),f.zero())
            assert table==h and h*h+h==z*z
    result={'status':'PASS_FULL_TERMINAL_SAGE_AUDIT','candidate_id':None,
            'prefix_outputs_replayed':len(actual),
            'linear_map_controls':256,'queries':{}}
    for label in ('baseline','linear','public_linear','public_baseline'):
        receipt=json.loads((HERE/f'{label}.receipt.json').read_text())
        assert receipt['status']=='COMPLETE'
        lines=(HERE/f'{label}.stdout').read_text().splitlines()
        final=[line.split() for line in lines if line.startswith('QUERY ')]
        assert len(final)==1 and final[0][1]=='COMPLETE' and int(final[0][2])==134219672
        target=F(json.loads((HERE/f'{label}.protocol.json').read_text())['target_reciprocal'])
        samples=[line for line in lines if line.startswith('SAMPLE ')]
        hits=[line for line in lines if line.startswith('HIT ')]
        assert len(samples)==2 and int(final[0][6])==len(hits)
        for line in samples:
            cnum,dnum=bracket_fields(line)
            c,d=F(cnum),F(dnum)
            assert prep.s3(c,d,target)==0
            assert int(line.rsplit(' ',1)[1])==-1
        checked=[]
        for line in hits:
            head=line.split(' [',1)[0].split()
            assert len(head)==4
            index,lc,rc=map(int,head[1:])
            cnum,dnum=bracket_fields(line)
            c,d=F(cnum),F(dnum)
            assert prep.s3(c,d,target)==0
            assert lc==lookup.get(cnum,lc)
            wl=prep.source_code(src,lc,f.zero())
            wr=prep.source_code(src,rc,f.zero())
            assert prep.valid(wl,s) and prep.valid(wr,s)
            pl=prep.source_code(left_basis,lc,f.zero())
            pr=prep.source_code(right_basis,rc,f.zero())
            assert Cl*c*c+pl*c+Hl==0
            assert Cr*d*d+pr*d+Hr==0
            checked.append({'index':index,'left_code':lc,'right_code':rc,
                            'left_reciprocal':cnum,'right_reciprocal':dnum})
        result['queries'][label]={'root_count':int(final[0][5]),
                                   'valid_source_hits':checked,
                                   'sample_roots_replayed':len(samples)}
    assert result['queries']['baseline']['valid_source_hits']==result['queries']['linear']['valid_source_hits']
    assert result['queries']['public_baseline']['valid_source_hits']==result['queries']['public_linear']['valid_source_hits']
    assert any(x['left_code']==22 and x['right_code']==29 for x in result['queries']['linear']['valid_source_hits'])
    result['protocol_sha256']=sha(HERE/'audit.protocol.json')
    result['script_sha256']=sha(__file__)
    (HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
