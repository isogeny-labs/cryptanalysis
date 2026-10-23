"""Search for another conductor-6 class containing the x=16 regular point."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve_from_j, GF, prime_range

HERE = Path(__file__).resolve().parent


def squarefree(n):
    n = abs(n)
    d = 2
    while d * d <= n:
        if n % (d * d) == 0:
            return False
        while n % d == 0:
            n //= d
        d += 1
    return True


def fundamental(d):
    return (d < 0 and
            ((d % 4 == 1 and squarefree(d)) or
             (d % 4 == 0 and (d // 4) % 4 in (2, 3) and squarefree(d // 4))))


def main():
    raw = (HERE / "general_search_protocol.json").read_bytes()
    protocol = json.loads(raw)
    assert protocol["status"] == "FROZEN_BEFORE_SEARCH"
    assert protocol["prime_interval"] == [2000, 100000]
    checked = 0
    candidates = []
    hit = None
    for p0 in prime_range(2000, 100001):
        p = int(p0)
        if p in protocol["exclude_primes"]:
            continue
        checked += 1
        model = EllipticCurve_from_j(GF(p)(-121))
        t = int(model.trace_of_frobenius())
        delta = t*t - 4*p
        if delta % 36:
            continue
        dk = delta // 36
        if not fundamental(dk):
            continue
        c = int(model.endomorphism_order().conductor())
        row = {"p": p, "trace": t, "DK": dk, "frobenius_conductor": 6,
               "endomorphism_conductor": c}
        candidates.append(row)
        if c == 6:
            hit = row
            break
    result = {"status": "ELIGIBLE_CLASS_FOUND" if hit else "BOUNDED_SEARCH_EXHAUSTED",
              "protocol_sha256": hashlib.sha256(raw).hexdigest(),
              "primes_checked": checked, "candidate_rows": candidates, "hit": hit}
    (HERE / "general_search_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "candidate_rows"}, sort_keys=True))


if __name__ == "__main__":
    main()
