"""Pure-Python replay of selection, point counts, and matrix receipts."""
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))


def squarefree(n):
    n = abs(n)
    return all(n % (d * d) for d in range(2, isqrt(n) + 1))


def fundamental(d):
    return d < 0 and ((d % 4 == 1 and squarefree(d)) or
                      (d % 4 == 0 and (d // 4) % 4 in (2, 3) and squarefree(d // 4)))


def trace_abs(j, p):
    k = j * pow((1728 - j) % p, -1, p) % p
    a, b = 3 * k % p, 2 * k % p
    signed_sum = 0
    for x in range(p):
        value = (x * x * x + a * x + b) % p
        signed_sum += 0 if value == 0 else 1 if pow(value, (p - 1) // 2, p) == 1 else -1
    return abs(signed_sum)


def class_number(disc):
    count = 0
    for a in range(1, isqrt((-disc) // 3) + 2):
        for b in range(-a, a + 1):
            numerator = b * b - disc
            if numerator % (4 * a):
                continue
            c = numerator // (4 * a)
            if a > c or (b < 0 and (abs(b) == a or a == c)):
                continue
            if gcd(gcd(a, abs(b)), c) == 1:
                count += 1
    return count


def main():
    protocol, result = read("general_search_protocol.json"), read("general_search_result.json")
    assert result["protocol_sha256"] == sha("general_search_protocol.json")
    assert protocol["prime_interval"] == [2000, 100000]
    checked = 0
    candidates = []
    for p in range(2000, 2132):
        if not is_prime(p):
            continue
        checked += 1
        t = trace_abs(-121, p)
        delta = t * t - 4 * p
        if delta % 36 == 0 and fundamental(delta // 36):
            candidates.append({"p": p, "trace_abs": t, "DK": delta // 36})
    assert checked == result["primes_checked"] == 18
    assert candidates == [{"p": 2131, "trace_abs": 28, "DK": -215}]
    assert result["hit"] == {"p": 2131, "trace": -28, "DK": -215,
                              "frobenius_conductor": 6, "endomorphism_conductor": 6}
    assert 28 * 28 - 4 * 2131 == -215 * 6 * 6
    class_numbers = {str(f): class_number(-215 * f * f) for f in (1, 2, 3, 6)}
    assert class_numbers == {"1": 14, "2": 14, "3": 28, "6": 28}
    gate, audit, delta = read("fiber_gate_result.json"), read("audit.json"), read("comparison.json")
    exact = read("exact_rank.json")
    assert gate["status"] == "PASS_UNIFORM_TWO_SHEET_GATE"
    assert {f: v["class_number"] for f, v in gate["strata"].items()} == class_numbers
    assert audit["status"] == "VERIFIED_D215_F6_BRANCH_MATRIX"
    assert audit["branch"]["endomorphism_conductor"] == 6
    assert delta["status"] == "PASS_SECOND_CLASS_BRANCH_DELTA"
    assert exact["status"] == "PASS_PAIRED_EXACT_RANKS"
    assert exact["ranks"] == {"regularized": {"full_QQ": 112, "nonfloor_QQ": 108},
                              "original": {"full_QQ": 111, "nonfloor_QQ": 108}}
    assert (audit["point_count"], audit["row_count"], audit["ranks"]["2+3"]["full_QQ"]) == (168, 140, 112)
    assert delta["preserved_original_rows"] == 138 and len(delta["added_rows"]) == 2
    output = {"status": "PASS_INDEPENDENT_SECOND_CLASS_REPLAY",
              "general_search_protocol_sha256": sha("general_search_protocol.json"),
              "producer_protocol_sha256": sha("producer_protocol.json"),
              "class_numbers": class_numbers, "small_primes_recounted": checked,
              "direct_point_count_trace_abs": 28,
              "regularized_producer_sha256": sha("data/exp11_class_walk_D215_f6.json"),
              "original_producer_sha256": sha("legacy/data/exp11_class_walk_D215_f6.json"),
              "exact_rank_sha256": sha("exact_rank.json"),
              "candidate_id": None, "timing_claim": None}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
