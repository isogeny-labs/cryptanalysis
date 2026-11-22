"""N41 test: resultant with a sparse linearized span polynomial in q."""
import hashlib
import json
import resource
import struct
import sys
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TENSOR = ROOT / "n41_target_chart_symbolic_tensor_20261014/coefficients.bin"
CODES = ROOT / "n41_triproduct_tensor_20261014/codes.txt"
SOURCE = ROOT / "n41_native_rootproduct_span_20261014/input.txt"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    return {"runner": HERE / "unit_check.py", "tensor": TENSOR,
            "codes": CODES, "source": SOURCE,
            "runtime": HERE / "sage_runtime_info.json"}


def read_case():
    codes = CODES.read_text().splitlines()
    assert codes[0] == "N41CODES1 40"
    pvals = list(map(int, codes[1].split()))
    qvals = list(map(int, codes[2].split()))
    lines = SOURCE.read_text().splitlines()
    assert lines[0] == "N41ROOTP1 1554 8 40 2"
    basis = list(map(int, lines[1].split()))
    targets = list(map(int, lines[3].split()))
    allowed = set()
    for line in lines[5:]:
        items = list(map(int, line.split()))
        if len(items) == 10:
            allowed.add((items[0], items[1]))
    assert len(allowed) == 1554
    return pvals, qvals, basis, targets, allowed


def field():
    R = PolynomialRing(GF(2), "t")
    t = R.gen()
    return GF(2**41, "t", modulus=t**41+t**3+1)


def main(mode):
    assert mode in ("smoke", "full")
    protocol = json.loads((HERE / "unit_protocol.json").read_text())
    assert protocol["source_sha256"] == {key: sha(path) for key, path in inputs().items()}
    assert protocol["mode"] == mode
    begin = time.monotonic()
    F = field()
    conv = F.from_integer
    pvals, qvals, basis_raw, targets, allowed = read_case()
    p_index = protocol["first_code_index"]
    q_indices = [j for j in range(40) if (p_index, j) in allowed]
    assert p_index == 24 and 0 < len(q_indices) <= 40 and 37 in q_indices
    p = conv(pvals[p_index])
    target = conv(targets[0])
    Rq = PolynomialRing(F, "q")
    q = Rq.gen()
    Rr = PolynomialRing(Rq, "r")
    r = Rr.gen()
    data = struct.unpack("<" + "Q"*(17*17*25*33), TENSOR.read_bytes())
    pp = [F.one()]
    for _ in range(16): pp.append(pp[-1]*p)
    powers_t = [F.one()]
    for _ in range(32): powers_t.append(powers_t[-1]*target)
    coefficients = [[F.zero() for _ in range(17)] for _ in range(25)]
    for i in range(17):
        for j in range(17):
            for k in range(25):
                offset = ((i*17+j)*25+k)*33
                v = F.zero()
                for a in range(33):
                    c = data[offset+a]
                    if c: v += conv(c)*powers_t[a]
                if v: coefficients[k][j] += v*pp[i]
    H = Rr([Rq(row) for row in coefficients])
    assert H.degree() == 24
    # The independent N41 span source has eight given generators, one
    # dependent. Greedily recover its seven-vector GF(2) basis.
    selected = []
    pivots = {}
    for value in basis_raw:
        x = value
        while x:
            bit = x.bit_length()-1
            if bit not in pivots:
                pivots[bit] = x
                selected.append(conv(value))
                break
            x ^= pivots[bit]
    assert len(selected) == 7
    rank = protocol["span_rank"]
    L = r
    span = [F.zero()]
    for v in selected[:rank]:
        alpha = L(Rq(v))
        assert alpha != 0
        L = L*L + alpha*L
        span += [x+v for x in span]
    assert L.degree() == 2**rank and L.leading_coefficient() == 1
    G = Rq.one()
    for j in q_indices: G *= q + conv(qvals[j])
    assert G.degree() == len(q_indices)
    leading = H.leading_coefficient()
    common = leading.gcd(G)
    zeros = [j for j in q_indices if leading(conv(qvals[j])) == 0]
    result = {"status": "PASS_N41_QUOTIENT_UNIT_CHECK",
              "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
              "candidate_id": None, "first_code_index": p_index,
              "allowed_second_codes": len(q_indices),
              "H_degree_r": int(H.degree()),
              "leading_degree_q": int(leading.degree()),
              "gcd_degree_q": int(common.degree()),
              "nonunit_second_codes": zeros,
              "setup_seconds_exploratory": time.monotonic()-begin,
              "peak_self_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "protocol_sha256": sha(HERE/"unit_protocol.json")}
    with (HERE/"unit_result.json").open("x") as out:
        json.dump(result,out,indent=2,sort_keys=True)
        out.write("\n")
    print(result["status"],result["gcd_degree_q"],zeros)
    return
    setup_done = time.monotonic()
    # This computes the norm over every root of the linearized polynomial
    # without enumerating its roots in the symbolic query.
    resultant_start = time.monotonic()
    resultant = H.resultant(L)
    resultant_done = time.monotonic()
    symbolic = Rq(resultant) % G
    reduction_done = time.monotonic()
    explicit = Rq.one()
    for v in span: explicit = (explicit * Rq(H(Rq(v)))) % G
    explicit_done = time.monotonic()
    assert symbolic == explicit
    zeros = [j for j in q_indices if symbolic(conv(qvals[j])) == 0]
    if rank == 7: assert zeros == [37]
    output = {
        "status": "PASS_IMPLICIT_SPAN_NORM_" + mode.upper(),
        "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "first_code_index": p_index, "span_rank": rank,
        "span_size": len(span), "allowed_second_codes": len(q_indices),
        "H_degree_r": int(H.degree()), "H_degree_q": max(int(c.degree()) for c in H.list()),
        "resultant_degree_q": int(Rq(resultant).degree()),
        "zero_second_codes": zeros,
        "symbolic_modulus_residue_sha256": hashlib.sha256(
            repr([int(x.to_integer()) for x in symbolic.list()]).encode()).hexdigest(),
        "setup_seconds_exploratory": setup_done-begin,
        "resultant_seconds_exploratory": resultant_done-resultant_start,
        "reduction_seconds_exploratory": reduction_done-resultant_done,
        "explicit_span_seconds_exploratory": explicit_done-reduction_done,
        "peak_self_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256": sha(HERE/(mode+"_protocol.json"))}
    with (HERE/(mode+"_result.json")).open("x") as out:
        json.dump(output, out, indent=2, sort_keys=True)
        out.write("\n")
    print(output["status"], rank, output["resultant_seconds_exploratory"], zeros)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    main(sys.argv[1])
