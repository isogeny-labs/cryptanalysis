# Predicting one M31 lift label from another under affine coordinate changes

Fix p = 2147483647 and f(X) = X³ + 2X + 14. Sample x uniformly from the whole base field. For any fixed a ≠ 0 and b with (a,b) ≠ (1,0), a Boolean function of the single label “f(x) is a square” predicts whether f(ax+b) is a square with accuracy below 50.00432%. The rule may be chosen separately for each affine transformation. This population differs from the restricted smooth-coordinate graph.

## Derivation

The archived root-exclusion certificate proves that f has no field root. Hence its cubic is irreducible, as is the monic normalization of f(aX+b). If the normalizations agreed, comparing quadratic coefficients would give b=0, and comparing linear and constant coefficients would give a²=a³=1, hence a=1. For every nonidentity map the two irreducible cubics are distinct and coprime. Over this finite field both are separable, so their product is a separable sextic.

In odd characteristic the smooth projective model of y²=f(x)f(ax+b) thus has genus two. The degree-two map to the projective line branches simply at the six finite roots. In the infinity chart v=y/x³ the equation at infinity is v²=a³. Write χ for the quadratic character and S for the sum of χ(f(x))χ(f(ax+b)) over x. The point count is p+1+S+χ(a³). Hasse–Weil gives (S+χ(a³))² ≤ 16p. [Poonen, Lectures on rational points on curves](https://math.mit.edu/~poonen/papers/curves.pdf)

Any Boolean rule is constant, copy, or complement. Copy and complement give signed agreement ±S. The constants give ±21645 because ax+b permutes the field and the target elliptic curve has 2147505293 points. Dividing the corresponding count of correct predictions by p gives the bound above. Because the two marginals coincide, the same identities also give at least 536813749 points in every one of the four source/destination cells. A zero-error rule given just the source label must abstain for both labels. Uniform negation of either nonzero character (a quadratic twist) merely exchanges Boolean labels. A rule that also sees x, or a nonuniform query distribution, has more information than this result covers.

## Exact translation check

For a=1 and b=1, the four counts in translation.csv give S=51595 and optimal accuracy 50.00120129%. The census includes x=p−1 followed by zero. translation.cpp uses repeated field squaring; verify_translation.cpp independently tabulates squares using one representative for each ±y pair. Compile each with a C++17 compiler and run without arguments. The second route uses a 256 MiB bit table. Compare each stdout byte-for-byte with translation.csv.

## Formal scope and replay

AffinePair.lean proves the degree and separability statement, the count on the two sets of fibers, and the numerical Boolean-rule bound under the genus-two Hasse–Weil inequality and the stated marginal balance. The geometric genus formula and Hasse–Weil theorem are external mathematical inputs. The complete translation table is a native enumeration.

From the project's mathlib environment set SRC to the absolute path to experiments/prime-field-auxiliary-ic, then use:

```sh
build=$(mktemp -d)
lake env lean --root="$SRC" -o "$build/M31FixtureObstruction.olean" "$SRC/M31FixtureObstruction.lean"
lake env sh -c 'export LEAN_PATH="$1:$LEAN_PATH"; lean "$2"' sh "$build" "$SRC/m31-affine-label-bound/AffinePair.lean"
```

## Can more consecutive lift bits predict the next one?

For each coordinate in the full field, retain the preceding k lift bits in increasing coordinate order, including windows crossing zero. The best possible Boolean predictor for this information chooses the more frequent successor of each history. This is an exact population ceiling even if the rule is fitted on every field element.

| History length | Maximum correct out of 2147483647 | Accuracy |
|---:|---:|---:|
| 0 | 1073752646 | 50.000504% |
| 1 | 1073767621 | 50.001201% |
| 2 | 1073767621 | 50.001201% |
| 8 | 1074029859 | 50.013413% |
| 12 | 1074925959 | 50.055141% |

For k=2 each of the four strict majorities predicts the most recent bit. With k=12 every one of the 4096 histories has both successor labels at least 260209 times each. Consequently, even a predictor permitted to abstain cannot certify any history without errors. Shorter histories merge cells and also have both successors. The census uses consecutive coordinates and uniform weighting across the field. Other strides, nonuniform queries, or extra features define different populations.

Run both compiled executables with `history12` and compare their output to history12.csv. The squaring implementation walks forward and appends the saved prefix at the end. The square-membership implementation walks backward, preloading the opposite end of the cyclic window. Run `python3 history.py` for all suffix lengths, cyclic marginal consistency, and comparison with translation.csv. Replay History.lean with `lake env lean /absolute/path/to/History.lean`. It reads the checked-in CSV, checks every cell index and count floor, and proves the 12-label optimal score is both an upper bound and attainable. The binding to actual curve labels is established by the two native enumerations.

## Adaptive choice of translated labels

Let a probe at offset t return the quadratic character of f(x+t), where f(X)=X³+2X+14 and x ranges over the whole M31 field. For **any eleven distinct offsets**, every one of the 2048 sign patterns occurs at least **330268** times.

To see this, fix the offsets and a desired sign at each. Multiply each probe value by its desired sign to obtain gᵢ(x). Since f has no root, the product of the eleven factors 1+gᵢ(x) is 2048 on matches and zero elsewhere. Expand the product and sum over x. The empty subset contributes p. For a nonempty subset of j offsets the character argument is a product of j distinct monic irreducible cubics. The quadratic coefficient 3t distinguishes the translates, so the product has 3j distinct geometric roots. Weil's character sum estimate bounds the absolute contribution by (3j−1)√p. The choice of desired signs only changes the overall sign. [Weil's estimate, Theorem 3.7](https://people.cs.uchicago.edu/~laci/papers/span1.pdf)

Using √p < 46341, the total error is at most 46341 × (3 × 11 × 1024 − 2047) = 1471095045. Subtracting this from p, dividing by 2048, and rounding up gives the stated floor. AffinePair.lean checks pairwise coprimality and the counting argument from the individual character sum bounds. Weil's estimate is an external input.

At a leaf of a deterministic adaptive rule, the observed signs fix its sequence of chosen offsets. After at most ten distinct probes, append any unseen offset with either sign. Pad to eleven distinct offsets if necessary. Each completion occurs on at least 330268 coordinates that follow the same path. Thus no such leaf can certify the new sign from the probe answers alone. This conclusion concerns exact decisions over the whole field. A smoothness-conditioned population or a rule that observes x itself requires a separate argument.

## Ten preceding bits on the smooth-coordinate population

Restrict x to the existing bound-47 census: some binary rotation of its positive representative is 47-smooth, and both x and x²+1 are quadratic nonsquares. Only x is subject to this restriction. Read the ten lift bits at x−10 through x−1 in field order and predict the bit at x. Each eligible coordinate has weight one.

Across all 1852867 coordinates, 925398 lift. Every one of the 1024 histories has both possible successors, with at least 778 coordinates per history/successor pair. The maximum score over all deterministic ten-bit Boolean rules is 943323 (50.911533%). Always predicting the more common successor gives 927469 (50.055886%). In the full field the corresponding ten-bit optimum was 50.026682%. The conditioned optimum uses the majority of each cell in the complete population. It measures the information available from this fixed probe set; it charges neither acquiring the probe bits nor looking up the answer.

Compile smooth_history.cpp with clang++ -O3 -std=c++17 and run the executable to reproduce smooth_history.csv. Rebuild with -DCHECK_JACOBI to replace repeated squaring with quadratic reciprocity. Both builds use the same population traversal and produce byte-identical tables; their total and lift marginal also match the existing smoothness census. History.lean checks the table layout, cell floor, marginals and optimal score.

### Local timing of the complete bound-47 history census

The batch build collects 32 eligible coordinates at a time. It lays out all eleven cubic values for each coordinate contiguously and passes the 352 values through thirty rounds of the existing M31 product kernel. The final batch contains three coordinates. Eligibility, population generation, history indexing and CSV output are shared with the scalar control.

From this directory, build the two executables with:

```sh
clang++ -O3 -std=c++17 smooth_history.cpp -o scalar
clang -O3 -c ../m31-native-product/product.c -o product.o
clang++ -O3 -std=c++17 -DBATCH_HISTORY smooth_history.cpp product.o -o batch
```

The table reports elapsed time and child user plus system CPU time in seconds on one Apple M4 Pro, Apple clang 21.0.0. Each row starts a fresh process and captures the complete CSV through a pipe. Wall timing includes comparing the bytes against smooth_history.csv; compilation is outside the panel. Runs took place consecutively in the listed order.

| Run | Build | Wall (s) | CPU (s) |
|---:|---|---:|---:|
| 1 | scalar | 1.287000 | 1.147059 |
| 2 | batch | 0.470934 | 0.371684 |
| 3 | batch | 0.373722 | 0.371325 |
| 4 | scalar | 1.178437 | 1.163805 |
| 5 | scalar | 1.168872 | 1.160698 |
| 6 | batch | 0.373038 | 0.370603 |
| 7 | batch | 0.376336 | 0.373462 |
| 8 | scalar | 1.150439 | 1.146111 |

The ratio of median times is 3.13 on wall time and 3.11 on CPU time. All eight outputs matched the saved table byte for byte. A batch build with M31_PORTABLE on product.c and a separate CHECK_JACOBI scalar build also reproduced it. History.lean proves the coordinatewise batch exponent by induction; ../m31-rotation-smoothness/SquareTest.lean identifies its thirtieth iterate with the field square test. Timings cover this complete public-coordinate census on this host.

### Batching orbit eligibility

The timings immediately above used the batch build at dd6b3aec8. The current batch build also groups the eligibility tests for the 31 coordinates in each orbit, using one zero padding lane. Starting at the square of the orbit representative, two binary rotations give the next squared coordinate. History.lean proves the recurrence for every orbit position. Rotate.lean proves the M31 word rotation formula.

The local comparison used the same M4 Pro, compiler and flags. Each wall interval runs from process launch through collecting stdout; CPU is child user plus system time. In the eligibility panel, replacing the history append with an increment of counts[0] retains the generation, traversal, eligibility test and output. Both builds counted 1852867. Median elapsed time fell from 190.2 ms to 71.7 ms over six runs per build. This is a separately compiled workload, so the difference is not an additive phase timing.

In the complete comparison (six runs per build), the medians were 374.3 ms and 178.1 ms. A separate four-build comparison tested which change accounted for the improvement. The direct variant advances x through the orbit and computes (x²+1) modulo p independently for each batch lane. The candidate uses the two rotations. Every complete run reproduced smooth_history.csv byte for byte.

| Four-build comparison | Median wall (ms) | Median CPU (ms) |
|---|---:|---:|
| Scalar for eligibility and history | 1153.4 | 1143.4 |
| Batched history only at dd6b3aec8 | 372.4 | 370.0 |
| Batched history and eligibility, direct squares | 176.4 | 174.1 |
| Batched history and eligibility, rotated squares | 174.1 | 172.2 |

Batching eligibility accounts for most of the additional gain. The four observations per arm give limited precision for comparing the two square-generation methods. The ratio of scalar to candidate median wall times is 6.63 on the entire public-coordinate census. Raw observations in execution order are in orbit_panel.csv.

### Does the smooth census pay for itself on the archived single-target fixture?

The archived field31_s5_base0 public.json lists 32 structured roots. The preparation code in snapshot/algebraic/optimized/benchmark.py checks a curve lift for each and retains 17 points. Checking all 31 rotations of every root gives exactly one smooth-orbit match at bound 47, x = 3; it also passes the auxiliary eligibility test and lifts. This covers 1/32 raw coordinates and 1/17 accepted coordinates. The census CSV stores counts by history, so even this one coordinate has no individually addressable entry there.

SetupCoverage.lean checks the smoothness test on both lists. Each rotated positive representative is below 2³¹, so every prime exponent is at most 30. Divisibility by (47!)³⁰ is consequently equivalent to having no prime factor above 47. A separate replay using trial division by each prime through 47 gave the same match. The stored Lean lists were compared in order against the archived public.json and same_base.txt.

Consider an intentionally favorable counterfactual: remove both basis construction and all reported native setup, at zero replacement cost, while retaining all other costs. For cold total T and those two charges S, the speedup ceiling is T/(T−S). The archived v2_batch_seed{0,1,2}.audited.json records give:

| Seed | Cold total (s) | Combined setup (ms) | Ceiling |
|---:|---:|---:|---:|
| 0 | 9.685108 | 2.397886 | 1.000248× |
| 1 | 5.167236 | 2.203726 | 1.000427× |
| 2 | 11.667566 | 2.390376 | 1.000205× |

The strict common upper bound 1.000427× is proved using the cold totals rounded down and setup rounded up to integer microseconds. This is a derived ceiling on those three recorded runs of one known fixture. It uses no cross-host timing ratios. Census acceleration alone has no demonstrated benefit for the measured single-target loop. The modern Rust crate also builds its factor base by lifting individual roots; the census artifact has no crate consumer at commit 08ed2eb14.

### What changed in the archived loop timings?

Run `python3 archived_loops.py` to compare the nine archived IC runs and the three rho records on field31_s5_base0. The replay reads the committed Git objects, compares every ordered relation record and uses exact rational arithmetic for the timing decomposition. The v1 and v2 unbatched variants have equal processed-query counts, ordered accepted rows and final ranks within each seed. Their loop speed ratios were 1.632, 1.795 and 2.349. The archive does not log every unsuccessful query.

Batching changes the stream: for each seed the ordered accepted rows differ from the unbatched v2 run. Dividing loop time by processed queries gives an average inclusive of loop overhead. A final partially consumed batch adds 47, 58 and 62 generated targets respectively; its cost stays charged.

| Seed | Unbatched v2 ns/query | Batched v2 ns/query | Unit-cost ratio | Processed-count ratio | Loop-time ratio |
|---:|---:|---:|---:|---:|---:|
| 0 | 397.44 | 278.29 | 1.428 | 1.043 | 1.489 |
| 1 | 370.95 | 267.36 | 1.387 | 3.113 | 4.319 |
| 2 | 360.29 | 256.34 | 1.406 | 0.920 | 1.293 |

Each loop-time ratio is the product of the two preceding ratios before rounding. The 4.319 figure includes an unusually short batch run in processed queries. The timing records alone do not identify an instruction-level cause for the unit-cost difference.

Keeping the observed batched query counts and allocating the entire corresponding rho cold time to those queries gives ceilings of 0.203948, 1.133058 and 0.402634 ns per processed query. SetupCoverage.lean proves the common necessary bound of less than 1.134 ns using the recorded counts and rho allowances rounded up to integer nanoseconds. These budgets measure aggregate wall time per processed query and allow concurrent arithmetic. All three seeds refer to one known public target.

### Did the loops stop earlier because they needed fewer accepted relations?

The signed-graph replay in archived_graphs.py computes the rank after every saved row. A row constrains its two vertex values up to a sign. Traversing a connected component leaves one free value if all signs agree around its cycles, and forces zero otherwise because the group order is odd. This also covers self-loops and isolated columns. All six v2 traces gain one rank per row until the final row, which contributes the first dependency. Deleting each row in turn recovers the exact support of that dependency; all six supports agree with the nonzero entries of the archived certificate weights. The earlier check_relation_ranks.py uses prefix minors and null vectors to check the rank certificates with Lean.

| Seed | Accepted rows, chain / batch | Dependency support, chain / batch | Chain / batch accepted-row ratio | Chain / batch queries per accepted row |
|---:|---:|---:|---:|---:|
| 0 | 13 / 15 | 4 / 8 | 0.867 | 1.203 |
| 1 | 15 / 14 | 6 / 7 | 1.071 | 2.905 |
| 2 | 12 / 9 | 3 / 5 | 1.333 | 0.690 |

The last two columns multiply to the processed-query ratio. On seed 1 the graph reached dependence just one accepted row sooner. Most of the 3.113-fold change in processed queries came from the difference between 4.005 million and 1.379 million queries per accepted row. On seed 2 the batched graph needed three fewer rows, yet processing took more queries overall. These are ratios of complete stopped runs; without per-rejection logs or fresh independent targets they do not establish a change in the probability of accepting an individual query. Replay with `python3 archived_graphs.py`.

### Can a walk return to an eligible point within four steps?

The archived native_v2.cpp uses 32 public step points per seed, shared by the 64 batched walks. For the 578-point eligible set A, a displacement d permits two eligible endpoints exactly when d is a difference of two elements of A. The number of eligible starting points that return is the multiplicity of d in the ordered difference histogram. Negation preserves A, so the existing batched point-addition code computes that histogram by summation.

Run `python3 archived_lags.py` to reconstruct the three step tables from the archived C++ RNG initialization, enumerate all ordered choices through lag four, and compare their displacements with all 578² ordered differences. Repeated step choices are included. The experiment counts possible paths independently of whether the archived run selected them.

For all three seeds, every displacement at lags 1, 2 and 3 has zero overlap. Thus any four consecutive positions of one walk contain at most one eligible point. At lag four the enumeration gives:

| Seed | Ordered step choices | Choices permitting return | Sum of eligible starting-point counts over choices |
|---:|---:|---:|---:|
| 0 | 1048576 | 24 | 144 |
| 1 | 1048576 | 0 | 0 |
| 2 | 1048576 | 12 | 72 |

Seed 1 thus has the same exclusion across five consecutive positions of each lane. This structural difference from independent queries is small on the scale of the archived run. Under independent uniform queries, the probability of *any* pair of hits separated by one to four same-lane steps, in the fixed first 19300166 processed queries, is at most 4 × 19300166 × (578/2147505293)² < 0.0000056. This union bound does not condition on the archived stopping event. It measures how rarely the independent reference violates this particular constraint. Longer lags and pairs from different lanes are outside the enumeration.

LagOverlap.lean checks the group-theoretic difference criterion, the at-most-one-hit implication for a separated window, and the rational inequality. The Python/C++ replay supplies the finite histogram and the seed-specific displacement counts.
