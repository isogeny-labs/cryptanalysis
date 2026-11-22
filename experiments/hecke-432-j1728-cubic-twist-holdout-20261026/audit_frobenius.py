"""Independent character-sum and mod-3 Frobenius audit."""
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent


def prime(n):
    return n>=2 and all(n%d for d in range(2,int(n**0.5)+1))


def trace_by_character_sum(p):
    total=0
    for x in range(p):
        f=(x*x*x+x)%p
        if not f:continue
        symbol=pow(f,(p-1)//2,p)
        assert symbol in (1,p-1)
        total+=1 if symbol==1 else -1
    return -total


def main():
    protocol_path=HERE/'obstruction_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    census_path=HERE/'path_census.json'
    census=json.loads(census_path.read_text())
    assert census['protocol_sha256']==sha256(protocol_path.read_bytes()).hexdigest()
    assert census['source_code_sha256']==sha256((HERE/'path_census_sage.py').read_bytes()).hexdigest()
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    checks=[]
    for row in census['rows']:
        p=row['prime']
        assert prime(p)
        trace=trace_by_character_sum(p)
        roots=[z for z in range(3) if (z*z+p)%3==0]
        assert trace==row['trace']==0
        assert [p%3,0,1]==row['characteristic_polynomial_mod_3']
        if p%24==7:
            assert not roots and row['rational_3_paths']==row['rational_27_paths']==0
        else:
            assert p%24==23 and roots==[1,2]
            assert row['rational_3_paths']==row['rational_27_paths']==2
        checks.append({'prime':p,'trace':trace,'frobenius_eigenvalues_mod_3':roots})
    assert len(checks)==61
    out={'status':'PASS_INDEPENDENT_J1728_FROBENIUS_TRACE_AUDIT',
         'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'path_census_sha256':sha256(census_path.read_bytes()).hexdigest(),
         'p7_irreducible_cases':58,'p23_split_controls':3,
         'checks':checks}
    (HERE/'frobenius_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'p7_irreducible_cases':58,'p23_split_controls':3}))


if __name__=='__main__':main()
