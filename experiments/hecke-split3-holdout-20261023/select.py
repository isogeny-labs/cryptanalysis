"""Frozen class-group selection for a split-degree-3 Hecke holdout."""
import hashlib
import json
from math import isqrt
from pathlib import Path

from sage.all import BinaryQF, is_prime, pari

HERE = Path(__file__).resolve().parent


def squarefree(n):
    return all(n % (k * k) for k in range(2, isqrt(n) + 1))


def main():
    raw = (HERE / "search_protocol.json").read_bytes()
    protocol = json.loads(raw)
    assert protocol["status"] == "FROZEN_BEFORE_CLASS_SELECTION"
    rows, chosen = [], None
    for d in range(300, 1501):
        if d % 24 != 23 or not squarefree(d):
            continue
        h1, h3 = int(pari.qfbclassno(-d)), int(pari.qfbclassno(-9*d))
        norm2 = BinaryQF(2, 1, (1 + 9*d)//8)
        assert int(norm2.discriminant()) == -9*d
        order = int(norm2.form_class().order())
        assert 2*h3 % order == 0
        cycles = 2*h3 // order
        row = {"d": d, "h1": h1, "h3": h3, "norm2_order_f3": order,
               "predicted_signed_cycles": cycles}
        rows.append(row)
        if h3 != 2*h1 or not 6 <= cycles <= 12:
            continue
        for v in range(1, isqrt(50000 - 9*d) + 1):
            p = v*v + 9*d
            if p < 10000 or not is_prime(p) or p in (2, 3, 5, 11):
                continue
            row.update({"v": v, "p": p, "u_abs": 2*v})
            assert (2*v)**2 - 4*p == -d*6*6
            chosen = row
            break
        if chosen:
            break
    result = {"status": "FROZEN_HOLDOUT_SELECTED" if chosen else "NO_HOLDOUT_IN_BOUND",
              "protocol_sha256": hashlib.sha256(raw).hexdigest(),
              "fundamental_d_cases_checked": len(rows), "rows": rows, "chosen": chosen,
              "script_sha256": hashlib.sha256((HERE / "select.py").read_bytes()).hexdigest()}
    (HERE / "selection.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, sort_keys=True))


if __name__ == "__main__":
    main()
