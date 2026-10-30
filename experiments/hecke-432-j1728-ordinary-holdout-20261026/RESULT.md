# Ordinary `j=1728` source-coordinate screen for the level-432 inverse

The source-free screen over primes `1440 < p < 5000` found a precise two-stage split. For the 110 primes with `p ≡ 5 (mod 12)`, the rational `j=1728` C fiber was empty. For the 107 primes with `p ≡ 1 (mod 12)`, nine primes had 18 rational C points each, but the C–E resolvent had zero rational pairs at every one of them. The inverse-filter stage therefore selected no prime for a complete 16/27-path multiplicity comparison under either frozen cap.

## Method and frozen selection

The first protocol, [`sieve_protocol.json`](sieve_protocol.json), fixes ascending prime selection, `p ≡ 5 (mod 12)`, the cap 5000, the exact coordinate/resolvent/branch inputs and hashes, and the threshold of four valid triples across two C points. It was written before that screen. The second protocol, [`sieve_split_protocol.json`](sieve_split_protocol.json), records a separate exploratory follow-up for `p ≡ 1 (mod 12)`. Its residue-class choice was informed by a prior exact eliminant-root check; it was frozen before the C–E screen and is not a blinded holdout.

Both screens enumerate `C: y²+y=x³−7` and `E: y²=x³+432` over each prime field, apply the rational source-`j` map, evaluate the degree-12 C–E resolvent, and then apply the exact B-branch filter only to rational resolvent pairs. Every prime, including zero cells, remains in [`sieve_result.json`](sieve_result.json) or [`sieve_split_result.json`](sieve_split_result.json). These primes have characteristic above three; `j=1728` is ordinary when `p ≡ 1 (mod 4)`.

| Prime class | Prime cells | Rational C points with source `j=1728` | Rational C–E resolvent pairs | Selected prime |
| --- | ---: | ---: | ---: | --- |
| `p ≡ 5 (mod 12)` | 110 | 0 | 0 | none below cap |
| `p ≡ 1 (mod 12)` | 107 | 162 | 0 | none below cap |

The nine C-nonempty primes in the second class are 1753, 2917, 3037, 3229, 3433, 3541, 3877, 4093, and 4597. Each has 18 C points. The exact degree-18 source-`j=1728` x-eliminant has 18 distinct roots at eight of these primes and 17 at 2917; the C-point total remains 18 there because one x-coordinate has two C points. [`audit.py`](audit.py) independently reconstructs the C point equation, source-`j` rational function, eliminant roots, rational E points, and C–E resolvent evaluations, then compares all 217 saved cells. Its receipt is [`audit.json`](audit.json).

## Interpretation and next experiment

The first loss occurs before the level-16 factor for `p ≡ 5 (mod 12)`. In the split class, the source C fiber appears, but the rational C–E correspondence is empty under this frozen cap. This separates two arithmetic filters that had been bundled together in the earlier `p ≡ 11 (mod 12)` multiplicity tests. The finite screen does not establish a universal congruence obstruction; the next proof task is to factor the C–E resolvent after imposing source `j=1728` over the relevant CM fields and determine its Frobenius splitting condition. If a later prime passes the rational C–E gate, the complete 16/27 inverse should enumerate both quartic-twist source classes and preserve the same source `j` sequence identifiers.

This bounded finite-field diagnostic extends the [prior Frobenius obstruction](../hecke-432-j1728-cubic-twist-holdout-20261026/RESULT.md) to the ordinary residue classes as an empirical screen. The next proof obligation concerns splitting of the C–E correspondence in those classes.
