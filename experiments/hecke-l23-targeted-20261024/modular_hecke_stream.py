"""Bounded-memory finite-field Hecke functions from a streaming q-series basis."""
from sage.all import GF, matrix, vector

def build_mod(l,p,source):
    F=GF(p)
    maxpole=max(2*(l+1)*l+12,l*(2*l+3))
    prec=l*(maxpole+16)+40
    X,Y=source.E0.modular_parametrization().power_series(prec=prec)
    prec_out=(prec-2*(l+1)-6)//l-2
    max_a=maxpole//2+1
    def coeff(s):return {int(e):F(c) for e,c in zip(s.exponents(),s.coefficients())}
    # Full precision is needed only for the l+1 source powers entering T_l.
    full=[X.parent()(1)]
    for _ in range(1,l+2):full.append(full[-1]*X)
    # A later multiplication by X can lower the exponent by at most two.
    # Keep exactly the look-ahead precision needed by the largest basis power.
    cutoff=prec_out+2*max_a+3
    xshort=X.add_bigoh(cutoff);yshort=Y.add_bigoh(cutoff)
    mono={};power=X.parent()(1)
    for a in range(max_a+1):
        if a:power=(power*xshort).add_bigoh(prec_out+3+2*(max_a-a))
        mono[(a,0)]=coeff(power.add_bigoh(prec_out))
        mono[(a,1)]=coeff((power*yshort).add_bigoh(prec_out))
    funcs={};checks={}
    def identify(target,m,tag):
        basis=source.basis_L(m)
        end=min(prec_out,m+11)
        assert end>m and all(ab in mono for ab in basis)
        exponents=list(range(-m,end))
        M=matrix(F,[[mono[ab].get(e,0) for ab in basis] for e in exponents],sparse=False)
        v=vector(F,[target.get(e,0) for e in exponents])
        sol=M.solve_right(v)
        assert M*sol==v
        checks[tag]={'pole_bound':m,'checked_through_exponent':end-1,
                     'basis_size':len(basis),'equation_count':len(exponents)}
        return {basis[i]:sol[i] for i in range(len(basis)) if sol[i]}
    for k in range(1,l+2):
        tag=f'x{k}'
        funcs[(l,'x',k)]=identify(source.hecke_series(coeff(full[k]),l,prec_out),2*k*l,tag)
    for k in range(l+1):
        tag=f'xy{k}'
        funcs[(l,'xy',k)]=identify(source.hecke_series(coeff(full[k]*Y),l,prec_out),l*(2*k+3),tag)
    return funcs,{'p':p,'degree':l,'q_precision':prec,
                  'coefficient_precision':prec_out,'max_pole':maxpole,
                  'short_series_cutoff':cutoff,'function_checks':checks}
