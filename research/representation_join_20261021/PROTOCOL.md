# Correctness protocol, 2026-10-21

Purpose: qualify a bounded reference API against exhaustive enumeration, not
estimate performance or ordinary-query yield. No cloud/GPU campaign launched.
The deterministic test source fixes the complete fixture and target corpus.
Test outputs retain both initial fixture errors and corrected results.

Commands (from this directory):

```sh
sh check.sh
g++ -std=c++17 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer test.cpp -o /tmp/representation-join-sanitize
ASAN_OPTIONS=detect_leaks=0 /tmp/representation-join-sanitize
```

The default `Budget` is 1,000,000 pairs per join and 1,000,000 outputs.
Domain: 3<p<=101, prime p and nonsquare quadratic modulus; fixtures p=5,7,11.
Tests exit 1 on a failed assertion and 0 on complete success. No timing interval,
speed ratio, memory claim, factor-base yield estimate, or ledger promotion.
The sanitizer rerun disables leak checking only because sandbox /proc inspection
failed after the correctness assertions completed; the initial log is retained.

Reference: unfiltered Cartesian-product addition followed by the same exact
admissibility condition. Four-point witnesses have a separate exhaustive
four-index enumerator; both share arithmetic, so this is not independent
arithmetic verification. Group-law closure, commutativity, bounded associativity,
inverse, invalid-field/curve/point, duplicate and resource-cap controls apply.
Public fixture scalars construct Q outside the solving API. No production targets.

All reported counts are unit-test coverage, not experimental success rates.
Canonical performance graphics remain unchanged because no cost is measured.
