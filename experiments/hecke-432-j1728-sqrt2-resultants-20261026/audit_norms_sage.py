"""Independent determinant replay of every K-to-Q norm in the bridge gate."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, NumberField, PolynomialRing

HERE=Path(__file__).resolve().parent


def k_eval(v,a,K):
    value=K(0)
    for raw in reversed(v):value=value*a+K(QQ(raw))
    return value


def relative_unit_norm(v,a,K):
    c=[k_eval(k,a,K) for k in v]
    c0=c[0];c1=c[1] if len(c)>1 else K(0)
    return c0*c0-2*c1*c1


def main():
    pp=HERE/'bridge_protocol.json';protocol=json.loads(pp.read_text())
    rp=HERE/'bridge_gate.json';result=json.loads(rp.read_text())
    assert result['status']=='EXACT_FULL_REDUCTION_BRIDGE_GATE'
    assert result['protocol_sha256']==sha256(pp.read_bytes()).hexdigest()
    base=json.loads(Path(protocol['inputs']['base_certificate']['path']).read_text())
    relative=json.loads(Path(protocol['inputs']['sqrt2_certificate']['path']).read_text())
    pair_norms=json.loads(Path(protocol['inputs']['pair_norms']['path']).read_text())
    Qx=PolynomialRing(QQ,'x')
    K=NumberField(Qx([QQ(c) for c in base['field_polynomial_coefficients_low_to_high']]),'a');a=K.gen()
    elements={'source_y_denominator':k_eval(base['source_y_denominator_coefficients_low_to_high'],a,K),
              'base_unit':k_eval(base['unit'],a,K)}
    for record in relative['records']:
        elements['relative_unit_'+str(record['base_degree'])]=relative_unit_norm(record['unit'],a,K)
    for row in pair_norms['rows']:
        elements['pair_resultant_'+str(row['base_degree'])]=k_eval(row['resultant_coefficients_low_to_high'],a,K)
    records=[]
    for saved in result['norms']:
        element=elements[saved['name']]
        determinant=QQ(element.matrix().det())
        expected=QQ(int(saved['numerator']))/QQ(int(saved['denominator']))
        assert determinant==expected==QQ(element.norm())
        records.append({'name':saved['name'],'determinant_matches':True,
                        'matrix_size':int(element.matrix().nrows())})
    out={'status':'PASS_INDEPENDENT_DETERMINANT_NORM_AUDIT',
         'bridge_gate_sha256':sha256(rp.read_bytes()).hexdigest(),
         'records':records}
    (HERE/'norm_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'records':len(records)}))


if __name__=='__main__':main()
