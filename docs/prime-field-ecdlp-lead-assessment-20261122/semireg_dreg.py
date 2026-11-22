import sympy as sp

# Semi-regular degree of regularity from the Fröberg/Bardet-Faugere-Salvy Hilbert series.
# For a (homogeneous) semi-regular system of equations of degrees d_i in n variables,
#   H(z) = [ prod_i (1 - z^{d_i}) ] / (1 - z)^n
# and D_reg = index of the first non-positive coefficient of the power series H(z).
# This is the degree the first fall / solving degree tracks UNDER semi-regularity;
# the whole B1 question is whether the real tower systems stay BELOW this.

z = sp.symbols('z')

def dreg_semiregular(degrees, n, maxdeg=400):
    num = sp.Integer(1)
    for d in degrees:
        num *= (1 - z**d)
    series = sp.series(num/ (1-z)**n, z, 0, maxdeg).removeO()
    poly = sp.Poly(series, z)
    # coefficients indexed by degree
    cdict = poly.as_dict()
    for k in range(0, maxdeg):
        c = cdict.get((k,), 0)
        if c <= 0:
            return k
    return None  # not reached within maxdeg (system not 0-dimensional / under-determined)

def dreg_complete_intersection(degrees):
    return sum(d-1 for d in degrees) + 1

# ---- self-check: for m == n (regular sequence / complete intersection),
#      the Hilbert-series D_reg must equal sum(d_i - 1) + 1 ----
print("SELF-CHECK (complete intersection m=n): Hilbert-series D_reg vs sum(d_i-1)+1")
ok = True
for degs in ([2,2],[2,2,2],[3,3],[2,3],[4,4,4],[2,2,2,2]):
    n = len(degs)
    hs = dreg_semiregular(degs, n)
    ci = dreg_complete_intersection(degs)
    match = (hs == ci)
    ok &= match
    print(f"  degs={degs} n={n}:  HS={hs}  CI-formula={ci}  {'OK' if match else 'MISMATCH'}")
print("  -> instrument", "VALIDATED" if ok else "FAILED", "\n")

# ---- Semaev decomposition shapes (over-determined regime index calculus lives in) ----
# Semaev S_{m+1} has total degree 2^{m-1} in each variable. Different prime-field
# formulations give different (n_vars, #eqs). We tabulate the semi-regular D_reg for
# a spread of plausible shapes so the lab can read off the baseline for ITS exact
# (n, degrees) once those are supplied. Everything here is the PREDICTION (an upper
# reference), not a measurement.
print("Semi-regular D_reg for over-determined families  (#eqs = n+k redundancy):")
print(f"{'arity m':>7} | {'d=2^(m-1)':>9} | {'n vars':>6} | {'#eqs':>4} | {'D_reg(semi-reg)':>15}")
print("  " + "-"*58)
for m in range(3,7):
    d = 2**(m-1)
    n = m                      # m summation variables
    for extra in (0,1,2):      # mild over-determination
        neq = n + extra
        degs = [d]*neq
        dr = dreg_semiregular(degs, n)
        tag = "(complete int.)" if extra==0 else ""
        print(f"{m:>7} | {d:>9} | {n:>6} | {neq:>4} | {str(dr):>15}  {tag}")
print()
print("Reading: measured solving degree AT or ABOVE these => semi-regular => PDP exponent")
print(">= 1/2 by construction (B1 dead as posed). Measured degree staying BOUNDED while t")
print("grows, and BELOW these, is the only signal that keeps a sub-sqrt(p) claim alive.")
