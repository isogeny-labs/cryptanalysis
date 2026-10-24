"""Recover squarefree Hecke fibers from moments and form rational Frobenius traces."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import EllipticCurve, GF, PolynomialRing, matrix, vector, classical_modular_polynomial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H
def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return [-1,-1] if P.is_zero() else [int(P[0]),int(P[1])]

def powers(Fpoly,limit):
    """Newton sums of a monic polynomial, including p_0=degree."""
    n=Fpoly.degree();c=Fpoly.list();out=[Fpoly.base_ring()(n)]
    for m in range(1,limit+1):
        if m<=n:
            v=-sum(c[n-i]*out[m-i] for i in range(1,m))-m*c[n-m]
        else:
            v=-sum(c[n-i]*out[m-i] for i in range(1,n+1))
        out.append(v)
    return out

def main():
    path=HERE/'trace_protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_TRACE_RECONSTRUCTION'
    functions_path=ROOT/'hecke-degree-next-screen-20261024/l29_functions.json'
    factor_path=HERE/'factor_result.json'
    saved=json.loads(functions_path.read_text());factor=json.loads(factor_path.read_text())
    F=GF(20023);funcs={}
    for tag,coeff in saved['functions'].items():
        ell,part,k=tag.split(':')
        funcs[(int(ell),part,int(k))]={tuple(map(int,ab.split(','))):F(v) for ab,v in coeff.items()}
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[29])
    phi=classical_modular_polynomial(29)
    R=rd.PT;X=R.gen();output=[]
    factor_rows={tuple(r['source']):r for r in factor['rows']}
    for source in protocol['source_points']:
        record=factor_rows[tuple(source)]
        assert record['squarefree'] and record['max_factor_degree']==7
        P=rd.E([*source,1]);f=rd.neighbour_x(29,P)
        assert f.degree()==30 and f.is_squarefree()
        s=powers(f,58)
        assert all(s[k]==rd.funcs[(29,'x',k)](P[0],P[1]) for k in range(1,31))
        t=[rd.funcs[(29,'xy',k)](P[0],P[1]) for k in range(30)]
        M=matrix(F,30,30,lambda i,j:s[i+j])
        assert M.rank()==30
        coefficients=M.solve_right(vector(F,t))
        h=sum(coefficients[i]*X**i for i in range(30))
        assert (h*h+h-X**3+X**2+10*X+20)%f==0
        traces=[];total=rd.E(0)
        for fpart,mult in f.factor():
            assert mult==1
            d=int(fpart.degree())
            if d==1:
                alpha=-fpart[0]
                beta=h(alpha)
                Q=rd.E(alpha,beta)
                trace=Q
                jQ=rd.j(Q)
            else:
                K=GF(20023**d,'alpha',modulus=fpart)
                alpha=K.gen();beta=h(alpha)
                Eext=EllipticCurve(K,H.AINV)
                Q=Eext(alpha,beta)
                jQ=rd.A(alpha,beta)/(alpha-rd.x0)**11
                trace=Eext(0)
                for k in range(d):
                    trace+=Eext(alpha**(20023**k),beta**(20023**k))
                assert trace==Eext(trace[0]**20023,trace[1]**20023) if not trace.is_zero() else True
                trace=rd.E(0) if trace.is_zero() else rd.E([F(trace[0]),F(trace[1]),F(1)])
            assert phi(F(rd.j(P)),jQ)==0
            total+=trace
            traces.append({'factor_degree':d,'factor_coefficients':[int(c) for c in fpart.list()],
                           'point_x':[int(c) for c in alpha.polynomial().list()] if d>1 else [int(alpha)],
                           'trace':key(trace),'j_neighbor_rational':bool(jQ**20023==jQ)})
        assert total==rd.a_l[29]*P==rd.E(0)
        output.append({'source':source,'source_j':int(rd.j(P)),
                       'x_polynomial_coefficients':[int(c) for c in f.list()],
                       'y_polynomial_coefficients':[int(c) for c in h.list()],
                       'moment_matrix_rank':int(M.rank()),
                       'factor_traces':traces,'group_sum':key(total)})
        print(json.dumps({'source':source,'factor_degrees':[r['factor_degree'] for r in traces],
                          'group_sum':key(total)}),flush=True)
    result={'status':'L29_FROBENIUS_ORBIT_TRACES_PRODUCED','protocol_sha256':sha(path),
            'source_sha256':{'functions':sha(functions_path),'factors':sha(factor_path)},
            'sources':output,'candidate_id':None,'timing_claim':None}
    (HERE/'trace_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
