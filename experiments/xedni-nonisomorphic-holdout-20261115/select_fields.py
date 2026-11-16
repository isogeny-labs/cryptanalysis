"""Deterministically select the first eight unseen prime-order fields."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def prime(n):
    if n < 2:
        return False
    for d in range(2, int(n**0.5) + 1):
        if n % d == 0:
            return False
    return True

def curve_order(p):
    total = p + 1
    for x in range(p):
        rhs = (x*x*x - x - 2) % p
        if rhs:
            symbol = pow(rhs, (p - 1)//2, p)
            assert symbol in (1, p - 1)
            total += 1 if symbol == 1 else -1
    return total

def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    selected = []
    scanned = []
    p = 678
    while len(selected) < 8:
        p += 1
        if prime(p):
            q = curve_order(p)
            scanned.append([p, q, prime(q)])
            if prime(q):
                selected.append([p, q])
    assert selected == protocol["expected_fields"]
    print(json.dumps({"schema": "xedni-nonisomorphic-holdout-selection-v1",
                      "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
                      "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      "selected": selected, "scanned": scanned}, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
