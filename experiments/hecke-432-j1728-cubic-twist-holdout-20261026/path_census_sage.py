"""Check Frobenius traces and rational 3/27 paths at frozen primes."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE=Path(__file__).resolve().parent


def load(path):
    spec=importlib.util.spec_from_file_location('frozen_paths',path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    protocol_path=HERE/'obstruction_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_FROBENIUS_PATH_CENSUS'
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    sieve=json.loads(Path(protocol['inputs']['sieve_result']['path']).read_text())
    primes=[c['prime'] for c in sieve['cells']]
    assert len(primes)==58 and all(p%24==7 for p in primes)
    controls=[1319,1367,1439]
    paths=load(protocol['inputs']['path_enumerator']['path']).paths
    rows=[]
    for p in primes+controls:
        curve=EllipticCurve(GF(p),[0,0,0,1,0])
        trace=p+1-int(curve.cardinality())
        one=list(paths(curve,3,1))
        three=list(paths(curve,3,3))
        row={'prime':p,'congruence_mod_24':p%24,'trace':trace,
             'characteristic_polynomial_mod_3':[p%3,(-trace)%3,1],
             'rational_3_paths':len(one),'rational_27_paths':len(three)}
        rows.append(row)
        print(json.dumps(row,sort_keys=True),flush=True)
    assert all(r['trace']==0 and r['rational_3_paths']==0 and r['rational_27_paths']==0 for r in rows[:58])
    out={'status':'PASS_P7MOD24_J1728_3_PATH_OBSTRUCTION_CENSUS',
         'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
         'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'rows':rows,'zero_path_primes':58}
    (HERE/'path_census.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'zero_path_primes':58,'controls':rows[-3:]},sort_keys=True))


if __name__=='__main__':main()
