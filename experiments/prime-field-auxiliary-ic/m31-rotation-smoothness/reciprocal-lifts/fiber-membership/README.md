# Direct reciprocal coverage queries on an archived M31 fiber

For a known coordinate n with 0 < n ≤ N, form the product over primes q ≤ b
of the largest power of q at most N. Then n is b-smooth exactly when it
divides that product. Membership.lean proves this for arbitrary N and b by
prime-power divisibility. For N = 2^31−2 the products occupy 687 bits (bound
89) and 1,350 bits (211). Each query constructs the product and tests all
necessary rotations, stopping when it finds a smooth representative.
The character and distinct-key checks enforce the same eligibility conditions
as the global pair census. The two normalized scales cover each level up to
rotation, as in the torsion audit.

The output contains the archived sibling pairs covered at each of the five
levels. It omits global orbit counts and phase statistics, which require other
work. All paths matched the five-level coverage recorded in bound-211/coverage.json
at both bounds. The index path rebuilds the native public census and imports
the emitted pair keys into Python, following the previous coverage script.
The direct paths compute trial-division or divisibility membership on demand.

On one shared Apple M4 Pro, six fresh-process blocks covered all six arm
orders. The CLI reads the same prefetched public manifest each time, charges
predicate or index construction, and returns the same coverage JSON. At bound
211 the median within-block wall ratio was 9.53 for index/direct-divisibility.
The median times were 527.3 ms and 55.3 ms. At bound 89 they were 98.3 ms
and 54.2 ms, with a paired ratio of 1.85. Python process startup dominates
the direct paths; the direct trial/divisibility CLI ratios were 1.10 and
0.97 at 89 and 211.

A separate in-process experiment exercised the entire coverage function on an
already parsed manifest, charging all arithmetic setup on every call. In
12 blocks of 16 calls per arm and bound, median paired trial/divisibility CPU
ratios were 1.85 at 89 and 2.12 at 211. The direct bound-211 call used a median
0.747 ms of CPU. Both panels include result validation as specified by their
drivers. These comparisons measure independent coverage queries. Reusing an
already constructed global index has a different cost model.

Build pairs89 and pairs211 following ../bound-211/README.md, then run:

```sh
python3 query.py /path/to/public.json 211
python3 compare.py /path/to/build-directory
python3 time_predicate.py
```

Replay Membership.lean from the Lean 4.34.1 mathlib environment.
