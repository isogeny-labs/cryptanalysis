"""Compare normalized and denominator-carrying gates on 5,200 N41 inputs."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
OLD=ROOT/'n41_n131_linearized_quadratic_algebra_20261014'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start=time.monotonic()
    protocol=json.loads((D/'n41_protocol.json').read_text())
    assert protocol['producer_sha256']==sha(Path(__file__))
    assert all(sha(Path(path))==digest for path,digest in protocol['sources'].items())
    spec=importlib.util.spec_from_file_location('old_n41_gate',OLD/'n41_gate.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    geometry=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009'/'geometry.json').read_text())
    panel=json.loads((ROOT/'n41_w8_two_code_affine_span_20261013'/'target_result_v2.json').read_text())
    reference=json.loads((OLD/'result.json').read_text())
    audit=json.loads((OLD/'audit_result.json').read_text())
    assert reference['status']=='COMPLETE_N41_QUADRATIC_ALGEBRA_GATE'
    assert audit['status'].startswith('PASS')
    left,right=geometry['blocks'][:2]
    left_rows=old.pair_outputs(left)
    basis=old.independent(right['product_basis'])
    alpha=old.constants(basis)
    H=old.sq(right['s']);C=1^H
    assert len(left_rows)==80 and len(alpha)==7 and len(panel['panels'])==65
    decisions=0;hits=0;exceptions=0;batch_products=0
    for panel_index,panel_row in enumerate(panel['panels']):
        t=panel_row['residual_reciprocal']
        rows=[];factors=[]
        for c,_ in left_rows:
            B=old.mul(c,t);A=1^old.sq(B);E=old.sq(c)^old.sq(t)
            special=not A or not E
            rows.append((A,B,E,special))
            if not special:factors.extend((A,E))
        pre=[1]
        for value in factors:pre.append(old.mul(pre[-1],value))
        inverses=[0]*len(factors)
        if factors:
            inv_all=old.inv(pre[-1])
            for i in range(len(factors)-1,-1,-1):
                inverses[i]=old.mul(inv_all,pre[i])
                inv_all=old.mul(inv_all,factors[i])
            assert inv_all==1
        batch_products+=len(factors)
        offset=0;local_hits=0
        for row_index,(A,B,E,special) in enumerate(rows):
            if special:
                exceptions+=1
                gate=any(old.mul(A,old.sq(b))^old.mul(B,b)^E==0
                         for b,_ in old.pair_outputs(right))
            else:
                invA,invE=inverses[offset:offset+2];offset+=2
                assert old.mul(A,invA)==old.mul(E,invE)==1
                bovera=old.mul(B,invA);eovera=old.mul(E,invA)
                u=C^old.mul(H,old.mul(A,invE))
                v=old.mul(H,old.mul(B,invE))
                for a in alpha:
                    u2=old.sq(u);v2=old.sq(v)
                    u,v=(old.mul(bovera,u2)^old.mul(a,u),
                         old.mul(eovera,u2)^v2^old.mul(a,v))
                gate=(not v) if not u else not (
                    old.mul(A,old.sq(v))^old.mul(B,old.mul(u,v))^
                    old.mul(E,old.sq(u)))
                baseline,_,_=old.span_gate(A,B,E,C,H,alpha)
                assert gate==baseline,(panel_index,row_index)
            local_hits+=gate;decisions+=1
        assert offset==len(factors)
        assert local_hits==reference['rows'][panel_index]['gate_left_roots']
        hits+=local_hits
    assert decisions==5200 and hits==reference['gate_left_roots']==1
    assert exceptions==reference['exceptional_quadratics']==0
    report={'status':'N41_NORMALIZED_RECURRENCE_CONTROL_PASS',
            'protocol_sha256':sha(D/'n41_protocol.json'),
            'decisions_checked':decisions,'gate_hits':hits,
            'exceptional_quadratics':exceptions,
            'batch_denominators_inverted':batch_products,
            'wall_s':time.monotonic()-start,
            'peak_self_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (D/'n41_result.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True))


if __name__=='__main__':main()
