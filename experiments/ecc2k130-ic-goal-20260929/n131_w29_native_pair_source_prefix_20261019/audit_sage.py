"""Independent source-prefix and pair-output replay against Sage tables."""
import hashlib
import json
import sys
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'n41_n131_implicit_pair_output_20261019'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_fe(value):
    parts=json.loads(value)
    assert len(parts)==3 and all(0<=part<1<<64 for part in parts)
    return parts[0] | parts[1]<<64 | parts[2]<<128


def field(n):
    ring=PolynomialRing(GF(2),'z');z=ring.gen()
    modulus=z**41+z**3+1 if n==41 else z**131+z**13+z**2+z+1
    return GF(2**n,name='z',modulus=modulus)


def main():
    assert len(sys.argv)==2 and sys.argv[1] in ('n41','n131')
    label=sys.argv[1];n=41 if label=='n41' else 131
    cfg=json.loads((HERE/f'audit_protocol_{label}.json').read_text())
    assert cfg['status']==f'FROZEN_BEFORE_NATIVE_PAIR_SOURCE_AUDIT_{label.upper()}'
    assert cfg['script_sha256']==sha(__file__)
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    prepared=json.loads((HERE/'prepare_result.json').read_text())
    case=next(item for item in prepared['cases'] if item['field_degree']==n)
    f=field(n)
    text=(HERE/f'{label}.stdout').read_text().splitlines()
    trace=[line.split() for line in text if line.startswith('TRACE ')]
    prefix=[line.split() for line in text if line.startswith('PREFIX ')]
    fixtures=[line.split() for line in text if line.startswith('FIXTURE ')]
    final=[line.split() for line in text if line.startswith('RESULT ')]
    assert len(trace)==len(fixtures)==len(final)==1
    assert final[0][1:5]==['COMPLETE',str(n),str(len(case['free_positions'])),
                            str(case['code_limit'])]
    valid,outputs,failed,batches=map(int,final[0][5:9])
    assert outputs==2*valid and failed==0
    assert batches==2*((case['code_limit']+4095)//4096)
    mask=parse_fe(trace[0][1])
    for i in range(n):
        assert f.from_integer(1<<i).trace()==((mask>>i)&1)
    if n==41:
        assert valid==281 and outputs==562
    expected=[]
    raw=(PRIOR/f'terminal_{label}.txt').read_text().splitlines()
    d=int(raw[0].split()[2])
    for line in raw[1+d:]:
        c,code=map(int,line.split());expected.append((c,code))
    assert len(expected)==(562 if n==41 else 2128)
    found=[]
    for row in prefix:
        assert len(row)==4
        code=int(row[1]);c0,c1=map(parse_fe,row[2:])
        found.extend([(c0,code),(c1,code)])
    assert len(found)==len(expected) and sorted(found)==sorted(expected)
    fixture_code=int(fixtures[0][1])
    fixture_outputs=list(map(parse_fe,fixtures[0][2:]))
    assert fixture_code==case['fixture_code']
    assert sorted(fixture_outputs)==sorted(c for c,code in expected
                                            if code==fixture_code)
    receipt=json.loads((HERE/f'{label}.receipt.json').read_text())
    assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
    assert receipt['stdout_sha256']==sha(HERE/f'{label}.stdout')
    assert receipt['stderr_sha256']==sha(HERE/f'{label}.stderr')
    result={'status':f'PASS_NATIVE_PAIR_SOURCE_AUDIT_{label.upper()}',
            'candidate_id':None,'field_degree':n,'source_codes_visited':case['code_limit'],
            'valid_codes_reported':valid,'outputs_reported':outputs,
            'sage_reference_codes':len(expected)//2,'sage_outputs_replayed':len(found),
            'native_source_ns':int(final[0][9]),
            'native_peak_rss_bytes':int(final[0][10]),
            'protocol_sha256':sha(HERE/f'audit_protocol_{label}.json'),
            'stdout_sha256':sha(HERE/f'{label}.stdout'),
            'script_sha256':sha(__file__)}
    (HERE/f'audit_result_{label}.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
