"""Identify Hecke functions over the target finite field from bounded q-series."""
from sage.all import GF, QQ, matrix, vector

def build_mod(l,p,source):
    F=GF(p)
    maxpole=2*(l+1)*l+12
    prec=l*(maxpole+16)+40
    X,Y=source.E0.modular_parametrization().power_series(prec=prec)
    Lq=X.parent()
    powers=[Lq(1)]
    for _ in range(1,maxpole//2+2):powers.append(powers[-1]*X)
    def coeff(s):return {int(e):F(c) for e,c in zip(s.exponents(),s.coefficients())}
    mono={}
    for a,P in enumerate(powers):
        mono[(a,0)]=coeff(P)
        mono[(a,1)]=coeff(P*Y)
    prec_out=(prec-2*(l+1)-6)//l-2
    funcs={};ranks={}
    def identify(target,m):
        basis=source.basis_L(m)
        rows=list(range(-m,prec_out))
        assert len(rows)>len(basis)+10 and prec_out>m
        M=matrix(F,[[mono[ab].get(e,0) for ab in basis] for e in rows],sparse=False)
        v=vector(F,[target.get(e,0) for e in rows])
        sol=M.solve_right(v)
        assert M*sol==v and M.rank()==len(basis)
        return {basis[i]:sol[i] for i in range(len(basis)) if sol[i]},len(basis)
    for k in range(1,l+2):
        f,m=identify(source.hecke_series(coeff(powers[k]),l,prec_out),2*k*l)
        funcs[(l,'x',k)]=f;ranks[f'x{k}']=m
    for k in range(l+1):
        f,m=identify(source.hecke_series(coeff(powers[k]*Y),l,prec_out),l*(2*k+3))
        funcs[(l,'xy',k)]=f;ranks[f'xy{k}']=m
    return funcs,{'p':p,'degree':l,'q_precision':prec,'coefficient_precision':prec_out,
                  'max_pole':maxpole,'basis_sizes':ranks}
