"""Exact quadratic recurrence for affine norms in the block invariant."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
mode = sys.argv[1]
assert mode in ("n41", "n131")
protocol_path = HERE / f"{mode}_protocol.json"
protocol = json.loads(protocol_path.read_text())
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
result_path = HERE / f"{mode}_result.json"
assert not result_path.exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("wall cap")))
signal.alarm(protocol["wall_cap_seconds"])
started = time.monotonic()

n = 41 if mode == "n41" else 131
S = PolynomialRing(GF(2), "u")
u = S.gen()
modulus = u**41 + u**3 + 1 if n == 41 else u**131 + u**13 + u**2 + u + 1
F = GF(2**n, name="u", modulus=modulus)
Q = PolynomialRing(F, "q")
q = Q.gen()


def dec(word):
    return F(S([(int(word) >> i) & 1 for i in range(n)]))


source = json.loads(Path(protocol["coefficients"]).read_text())
if mode == "n41":
    seed = dec(56 << 1)
    free_bits = [0, 1, 2, 3, 4, 6, 7, 8]
    rotation = 12
    targets = [("n41_public_relation_residual",
                [(e[0], e[1], c) for e, c in source["eliminant_terms"]])]
    known_codes = (228, 60)
else:
    seed = dec(source["seed_mask"] << 1)
    free_bits = [bit for bit in range(33) if bit != source["seed_mask"].bit_length()-1]
    rotation = 18
    targets = [(row["name"], row["terms"]) for row in source["rows"]]
    known_codes = (3, 16722)
basis = []
for bit in free_bits:
    a = dec(1 << (bit+1))
    basis.append(a*a + seed*a)
right_basis = [b**(1 << rotation) for b in basis]


def source_product(code, rot=0):
    value = sum((basis[i] for i in range(len(basis)) if (code >> i) & 1), F.zero())
    return value**(1 << rot)


def lin_eval(coeffs, value):
    return sum((c*value**(1 << i) for i, c in enumerate(coeffs)), F.zero())


def step(A, L, direction):
    # Y=L(p), delta=L(direction), Z=Y²+delta Y.
    # F(Y)=U(Z)+Y V(Z); Norm(F)=U²+delta U V+Z V².
    delta = lin_eval(L, direction)
    assert delta
    a0, a1, a2, a3, a4 = A
    U = [a0, a2+delta*a3+delta**2*a4, a4]
    V = [a1+delta*a2+delta**2*a3+delta**3*a4, a3]
    out = [Q.zero() for _ in range(5)]
    for i in range(3):
        out[2*i] += U[i]**2
        for j in range(2):
            out[i+j] += delta*U[i]*V[j]
    for j in range(2):
        out[2*j+1] += V[j]**2
    newL = [F.zero() for _ in range(len(L)+1)]
    for i, c in enumerate(L):
        newL[i] += delta*c
        newL[i+1] += c*c
    return out, newL


def specialize(A, value):
    return sum((a*value**i for i, a in enumerate(A)), Q.zero())


def explicit_block(A0, base_code, width, indices):
    answer = Q.one()
    for selector in range(1 << width):
        code = base_code
        for j in range(width):
            if (selector >> j) & 1:
                code ^= 1 << indices[j]
        answer *= specialize(A0, source_product(code))
    return answer


def right_gcd_degree(poly):
    remainder = q % poly
    linear = [F.one()]
    for b in right_basis:
        delta = lin_eval(linear, b)
        remainder = (remainder**2 + delta*remainder) % poly
        nxt = [F.zero() for _ in range(len(linear)+1)]
        for i, c in enumerate(linear):
            nxt[i] += delta*c
            nxt[i+1] += c*c
        linear = nxt
    return int(poly.gcd(remainder).degree())


rows = []
status = f"PASS_{mode.upper()}_DIRECT_COMPRESSED_RECURRENCE"
error = None
indices = protocol["variable_code_bit_indices"]
try:
    for name, terms in targets:
        A0 = [Q.zero() for _ in range(5)]
        for i, j, c in terms:
            A0[i] += dec(c)*q**j
        assert A0[4]
        A = A0[:]
        L = [F.one()]
        for width, index in enumerate(indices, 1):
            build_start = time.monotonic()
            A, L = step(A, L, basis[index])
            build_seconds = time.monotonic()-build_start
            if width not in protocol["tested_widths"]:
                continue
            for prefix in protocol["sampled_prefixes_by_width"][str(width)]:
                base_code = prefix << width
                compact = specialize(A, lin_eval(L, source_product(base_code)))
                explicit = explicit_block(A0, base_code, width, indices)
                assert compact == explicit
                assert compact.degree() == 4*(1 << width)
                gcd_start = time.monotonic()
                degree = right_gcd_degree(compact)
                gcd_seconds = time.monotonic()-gcd_start
                if name != "frozen_public_raw_point" and prefix == known_codes[0] >> width:
                    assert compact(source_product(known_codes[1], rotation)) == 0
                    assert degree >= 1
                row = {"target": name, "width": width, "prefix": prefix,
                       "block_codes": 1 << width, "q_degree": int(compact.degree()),
                       "compact_monomials": sum(len(a.dict()) for a in A),
                       "step_build_seconds": build_seconds, "gcd_seconds": gcd_seconds,
                       "gcd_degree": degree, "explicit_product_equal": True}
                rows.append(row)
                (HERE/f"{mode}_progress.jsonl").open("a").write(json.dumps(row, sort_keys=True)+"\n")
                print(json.dumps({"target": name, "width": width, "prefix": prefix,
                                  "gcd_degree": degree, "elapsed_seconds": time.monotonic()-started}), flush=True)
except TimeoutError as exc:
    status = "BOUNDED_UNKNOWN_WALL_CAP"
    error = str(exc)
finally:
    signal.alarm(0)
    result = {"status": status, "error": error, "candidate_id": None,
              "curve_id": protocol["curve_id"], "rows": rows,
              "total_wall_seconds": time.monotonic()-started,
              "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest()}
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"status": status, "rows": len(rows),
                      "total_wall_seconds": result["total_wall_seconds"]}), flush=True)
