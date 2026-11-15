# Index calculus with and without an auxiliary curve

On identical target inputs, using the same three-point relation search and
linear algebra, the two index-calculus variants performed about the same.

| Field | With auxiliary curve | Without auxiliary curve |
|---|---:|---:|
| F_(2^31-1) | 0.572 s | 0.573 s |
| F_(2^61-1) | 24.885 s | 25.471 s |

These are median times from three runs per variant, including factor-base
construction. Their observed timing ranges overlap. The differences do not
show a meaningful speed advantage from auxiliary factor-base selection.

The 61-bit field row uses the same 38-bit prime subgroup as the previous
experiment; it is not a 61-bit prime-order DLP benchmark.

## What changed between the variants

Both receive the same curve, subgroup order, P, and Q. Both use exactly
500 factor-base representatives for the first target and 989 for the second,
with both signs available. No scalar or factor-base logarithm is supplied.

With the auxiliary curve, x-values come from the auxiliary-isogeny coset.
Without it, ordinary consecutive x-values starting at 10 are lifted to the
target until the same number of representatives is obtained. The latter
constructs no auxiliary curve or isogeny. In the 61-bit field, both use the
same cofactor projection into the 38-bit subgroup.

All subsequent work is identical: signed pair-sum tables, three-point relation
search, and modular linear algebra. Both use batch inversion and the same
field arithmetic. All 12 runs were independently audited: every point
relation, elimination certificate, and recovered logarithm was verified.

## Scope of this comparison

This measures the choice of factor base in the implemented index-calculus
pipeline. The auxiliary maps are not used by its explicit pair-sum relation
solver. The low-degree polynomial-system advantage proposed in the slides
therefore is not measured by these earlier timings. The algebraic solver has
since been implemented and separately tested; see
[../algebraic/README.md](../algebraic/README.md) for its polynomial-system
benchmarks and bounded larger attempts.

## Solver-only measurements

| Field | Variant | Median | Minimum | Maximum | Factor-base setup |
|---|---|---:|---:|---:|---:|
| F_(2^31-1) | Auxiliary | 0.551689 s | 0.533415 s | 0.605072 s | 0.019897 s |
| F_(2^31-1) | Plain | 0.567618 s | 0.539617 s | 0.585530 s | 0.004895 s |
| F_(2^61-1) | Auxiliary | 24.6392 s | 24.6160 s | 25.2812 s | 0.245680 s |
| F_(2^61-1) | Plain | 25.2885 s | 22.6906 s | 26.9665 s | 0.182202 s |

Setup was measured once per variant and field. Seeds 0, 1, and 2 were used
for the three serial solver runs. Curve selection, order certification,
compilation, and independent auditing are excluded for both variants.
Memory usage is not benchmarked. These fresh measurements use a common
optimized solver, including batching and walk updates in the 31-bit case,
so they supersede the earlier one-off timings for comparison purposes.

## Exact targets

The first uses p=2147483647, y^2=x^3+2x+14, prime order n=2147505293,
P=(1,814455902), and Q=(988441464,1643383878). Both recover k=123456789.

The second uses p=2305843009213693951, y^2=x^3+3, prime subgroup order
r=157632877033, P=(78862349111012854,1899276942447683421), and
Q=(2143001111092283373,24199046229151799). Both recover
k=55300485039 modulo r. The smaller mixed-order components are common work
and excluded from this subgroup comparison.

## Reproduce

Requires Python with SymPy and a C++17 compiler supporting __uint128_t.

```sh
cd /workspace/index_calculus_demo/comparison
python prepare_comparison.py
g++ -O3 -std=c++17 -Wall -Wextra -DFIELD_BITS=31 -o ic31 compare_ic.cpp
g++ -O3 -std=c++17 -Wall -Wextra -DFIELD_BITS=61 -o ic61 compare_ic.cpp
python benchmark.py
```

Measurements were taken on an Intel Xeon Platinum 8370C at 2.80 GHz using
g++ 14.2.0 and Python 3.12.14. The benchmark runs sequentially and audits each
result. Public inputs, relation lists, cancellation certificates, and logs
are retained by variant and seed. Individual measurements are in runs.json;
aggregates are in summary.json.
