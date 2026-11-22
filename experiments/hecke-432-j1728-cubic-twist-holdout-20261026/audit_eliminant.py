"""Independent modular root audit of the characteristic-zero j1728 factor."""
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent


def at(coeffs,x,p):
    value=0
    for coeff in reversed(coeffs):value=(value*x+coeff)%p
    return value


def main():
    protocol_path=HERE/'eliminant_audit_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_MODULAR_ELIMINANT_AUDIT'
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    elimination=json.loads(Path(protocol['inputs']['elimination_result']['path']).read_text())
    sieve=json.loads(Path(protocol['inputs']['sieve_result']['path']).read_text())
    census=json.loads(Path(protocol['inputs']['path_census']['path']).read_text())
    assert elimination['status']=='EXACT_J1728_X_ELIMINANT'
    assert elimination['resultant_degree']==36
    assert len(elimination['factors'])==1 and elimination['factors'][0]['degree']==18 and elimination['factors'][0]['multiplicity']==2
    coeffs=[int(x) for x in elimination['factors'][0]['coefficients_low_to_high']]
    rows=[]
    for cell in census['rows']:
        p=cell['prime']
        roots=[x for x in range(p) if at(coeffs,x,p)==0]
        rows.append({'prime':p,'mod_24':p%24,'degree_18_root_count':len(roots),'x_roots':roots})
    assert all(r['degree_18_root_count']==0 for r in rows[:58])
    assert all(r['degree_18_root_count']==2 for r in rows[-3:])
    assert all(not c['j1728_C_points'] for c in sieve['cells'])
    out={'status':'PASS_MODULAR_J1728_ELIMINANT_ROOT_AUDIT',
         'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
         'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'p7_zero_root_primes':58,'p23_control_root_counts':[r['degree_18_root_count'] for r in rows[-3:]],
         'rows':rows}
    (HERE/'eliminant_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'p7_zero_root_primes':58,'controls':rows[-3:]},sort_keys=True))


if __name__=='__main__':main()
