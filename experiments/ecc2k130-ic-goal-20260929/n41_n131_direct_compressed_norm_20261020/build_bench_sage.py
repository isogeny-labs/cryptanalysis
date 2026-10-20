"""Paired direct and compressed N131 width-four norm construction."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol_path = HERE/"build_bench_protocol.json"
protocol = json.loads(protocol_path.read_text())
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
assert not (HERE/"build_bench_result.json").exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("build benchmark wall cap")))
signal.alarm(protocol["wall_cap_seconds"])
started = time.monotonic()
S = PolynomialRing(GF(2), "u")
u = S.gen()
F = GF(2**131, name="u", modulus=u**131+u**13+u**2+u+1)
R = PolynomialRing(F, names=("p", "q"))
p,q = R.gens()
Q = PolynomialRing(F, "z")
z = Q.gen()
U = PolynomialRing(F, "x")
x = U.gen()


def dec(word):
    return F(S([(int(word) >> i) & 1 for i in range(131)]))


source = json.loads(Path(protocol["coefficients"]).read_text())
seed = dec(source["seed_mask"] << 1)
bits = [bit for bit in range(33) if bit != source["seed_mask"].bit_length()-1]
basis = []
for bit in bits[:4]:
    a = dec(1 << (bit+1))
    basis.append(a*a+seed*a)


def direct(H):
    N = H
    for b in basis:
        N = N*N(p+b,q)
    return N


def compressed(terms):
    # Coefficients of the input quartic in p, represented in F[z].
    A = [Q.zero() for _ in range(5)]
    for i,j,c in terms:
        A[i] += dec(c)*z**j
    L = x
    for b in basis:
        delta = L(b)
        assert delta
        a0,a1,a2,a3,a4 = A
        U0 = [a0,a2+delta*a3+delta**2*a4,a4]
        V0 = [a1+delta*a2+delta**2*a3+delta**3*a4,a3]
        B = [Q.zero() for _ in range(5)]
        for i in range(3):
            B[2*i] += U0[i]**2
            for j in range(2):
                B[i+j] += delta*U0[i]*V0[j]
        for j in range(2):
            B[2*j+1] += V0[j]**2
        A = B
        L = L**2+delta*L
    return A,L


rows = []
for name in protocol["target_order"]:
    row = next(row for row in source["rows"] if row["name"]==name)
    terms = row["terms"]
    H = sum((dec(c)*p**i*q**j for i,j,c in terms),R.zero())
    order = protocol["method_order"][name]
    data = {}
    for method in order:
        t = time.monotonic()
        if method == "direct":
            data[method] = direct(H)
        else:
            data[method] = compressed(terms)
        data[method+"_seconds"] = time.monotonic()-t
    A,L = data["compressed"]
    Lp = sum((c*p**i for i,c in L.dict().items()),R.zero())
    reconstructed = R.zero()
    for i,coeff in enumerate(A):
        coeff_q = sum((c*q**j for j,c in coeff.dict().items()),R.zero())
        reconstructed += coeff_q*Lp**i
    assert reconstructed == data["direct"]
    result = {"target":name,"direct_build_seconds":data["direct_seconds"],
              "compressed_build_seconds":data["compressed_seconds"],
              "build_ratio":data["direct_seconds"]/data["compressed_seconds"],
              "expanded_terms":len(data["direct"].dict()),
              "compressed_terms":sum(len(a.dict()) for a in A),
              "coefficient_identity":True}
    rows.append(result)
    print(json.dumps(result),flush=True)
signal.alarm(0)
result={"status":"PASS_PAIRED_N131_DIRECT_COMPRESSED_BUILD",
        "candidate_id":None,"curve_id":protocol["curve_id"],"rows":rows,
        "total_wall_seconds":time.monotonic()-started,
        "self_maxrss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":hashlib.sha256(protocol_path.read_bytes()).hexdigest()}
(HERE/"build_bench_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
