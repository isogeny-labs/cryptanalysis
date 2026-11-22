import math
from math import lgamma, log2

# C_dec(m,p): the maximum per-decomposition oracle cost (in group/field ops, as a
# count) an index-calculus PDP attack may spend and still beat a negation-rho
# baseline, under an ideal-oracle model. Derived from the M1+M2 reconciliation.
#
# Model (ideal oracle, single-target):
#   factor base |F| = p^a ;  decomposition prob pi ~ 1/m! ;
#   relation-collection attempts ~ m! * |F|  (each costs one oracle solve C_dec)
#   linear algebra ~ c * m * |F|^2            (sparse)
#   rho baseline  T_rho ~ 0.886 * p^(1/2)
# Require BOTH phases < T_rho:
#   LA:        c*m*p^(2a) < 0.886*p^0.5   -> needs 2a < 0.5  (a < 1/4)
#   relations: m!*p^a*C_dec < 0.886*p^0.5 -> C_dec < 0.886 * p^(0.5 - a) / m!
# Two factor-base policies:
#   a = 1/(m+1)  (balanced, M2)  -> total IC exponent 2/(m+1)
#   a = 1/m      (Semaev-natural, M1)
#
# We report log2 of the budget so numbers stay legible.

def log2_fact(m): return lgamma(m+1)/math.log(2)

def budget_log2(m, nbits, a):
    e = 0.5 - a
    return log2(0.886) + nbits*e - log2_fact(m)

def la_ok(m, a):
    return 2*a < 0.5  # LA phase stays below rho in exponent

policies = {"a=1/(m+1) [balanced]": lambda m: 1.0/(m+1),
            "a=1/m [Semaev]":        lambda m: 1.0/m}
ps = [64,128,192,256]
ms = [3,4,5,6,7,8]

lines=[]
def out(s): lines.append(s); print(s)

out("BUDGET TABLE  C_dec(m,p) = max per-decomposition oracle cost to beat negation-rho")
out("Entries are log2(C_dec_max)  (i.e. the oracle may cost up to 2^entry ops).")
out("A NEGATIVE entry => IC cannot beat rho at that (m,p) for ANY oracle (budget < 1 op).")
out("'LA' column: does the linear-algebra phase alone stay sub-rho? (needs a<1/4)")
out("")
for pol,af in policies.items():
    out(f"### policy {pol}")
    hdr = "  m |  a      | IC-exp |  LA-ok | " + " | ".join(f"p=2^{b:<4}" for b in ps)
    out(hdr); out("  "+"-"*(len(hdr)-2))
    for m in ms:
        a=af(m); icexp = 2*a if pol.startswith("a=1/(m+1)") else (a+ (0.5 - (0.5-a)))  # total exp
        # total IC exponent = max(a + (exponent of C_dec contribution), 2a); at the budget boundary
        # the binding exponent is simply max(2a, a+? ). We report the relation+LA balanced exponent:
        icexp = max(2*a, a)  # = 2a here; informative only
        row=f"  {m} | {a:6.4f} | {2*a:5.3f}  | {'yes' if la_ok(m,a) else 'NO ':>4}  | "
        cells=[]
        for b in ps:
            v=budget_log2(m,b,a)
            cells.append(f"{v:8.1f}")
        out(row+" | ".join(cells))
    out("")

# Reference anchors
out("Reference: known concrete oracle costs to compare against the budget --")
out("  * reported in-house F4 per decomposition ~ 5e8..5e9 ops = log2 ~ 28.9..32.2")
out("  * M2's Graeffe/iterated-norm estimate at m=3,fp32,N=2^8 ~ 1e6..1e7 = log2 ~ 20..23")
out("Read: an oracle 'passes' cell (m,p) iff its log2(cost) < the table entry.")

open("budget_table.txt","w").write("\n".join(lines)+"\n")

# also CSV
import csv
with open("budget_table.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["policy","m","a","IC_total_exp_2a","LA_ok","nbits","log2_Cdec_max"])
    for pol,af in policies.items():
        for m in ms:
            a=af(m)
            for b in ps:
                w.writerow([pol,m,f"{a:.6f}",f"{2*a:.4f}","yes" if la_ok(m,a) else "no",b,f"{budget_log2(m,b,a):.3f}"])
print("\nsaved -> budget_table.txt , budget_table.csv")
