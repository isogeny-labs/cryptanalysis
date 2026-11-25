# Recorded results

Date: October 29, 2026. **No ECC2K-130 private scalar was recovered.**

| Experiment | Result |
| --- | --- |
| Published ECC2K-130 parameters | All field, curve, subgroup, cofactor, and encoding checks passed |
| Independent arithmetic checks | 12 scalar multiplications of the published points matched OpenSSL |
| Unit tests | 28 tests passed, including the tensor engine and coordinate encoder |
| Hashed factor bases, demo GF(2^13) | Recovered k = 1427; 51 relations; full certificate verified |
| Hashed factor bases, demo GF(2^19) | Recovered k = 114415; 158 relations; full certificate verified |
| Actual-curve small factor-base sample | Enumerated bases with 14, 10, and 17 points; no decomposition of Q over these particular bases |
| Actual target, bounded BSGS | No k in [0, 4294967296); 65,536 baby steps and 65,536 giant steps; 7.30 seconds |
| Actual target, reference rho | 99,999 walk additions; no solution; 6.09 seconds; checkpoint saved |
| Actual target, full-size hashed bases | Preflight exceeded the configured enumeration budget before starting the search |
| Recursive Cauchy/mode/Hermite engine | Exact answer 143 matched independent exhaustive sum; 101 calls, including 100 leaves and 50 mode tuples |
| Tensor-indexed factor-base demo GF(2^13) | Recovered k = 1427 with 31 verified relations; 50 tensor witness queries |
| Actual target, implicit coordinate tensor graph | Compiled 2,694,680 edges, maximum degree 1,032, and 1,195,386 circuit variables |
| Actual target, tensor engine | Default u_0=0; exact-summation fallback exceeded the configured operation budget |

The two demos use different, deliberately small curves, with subgroup orders 2003
and 130873 respectively. Their recovered scalars are not the ECC2K-130 scalar.
The solver receives only each instance's public curve, P, Q, subgroup order, and
cofactor; the demo generation scalar is not an input to relation finding.

The actual ECC2K-130 target and parameters are unmodified. The BSGS result excludes
only the specified interval. The bounded rho run provides no guarantee about the
remaining search effort or success of a future run. Timings are measurements in
this workspace, not performance claims for a tuned native implementation.

The scalar recursive contraction engine and coordinate encoder are implemented.
The recursive check uses experimental small parameters to exercise the nonleaf
code; the challenge uses the manuscript's default policy. These tests do not
validate the external theorem or demonstrate a practical subexponential attack.
The complete V-polynomial generalization is not needed for this task and is not
implemented. The older ordinary backend still requires about 2.61e19 points per
base with two challenge factor bases. Resource limits are explicit and
configurable, not mathematical impossibility claims.

The new JSON records are `recursive-tensor-check.json`, `tensor-demo13.json`, and
`challenge-tensor.json`. The challenge graph is generated from the public target
and recorded affine hash seeds, without enumerating its full factor bases or
supplying a hidden scalar. Its contraction attempt produced no challenge
relation or scalar. See [TENSOR_IMPLEMENTATION.md](TENSOR_IMPLEMENTATION.md).

Machine-readable records, full demo certificates, and the rho checkpoint are in
`results/`. Reproduce the suite in a separate directory with:

```bash
python run_experiments.py --output-dir results-reproduced
```

Using an existing output directory resumes its rho checkpoint, so cumulative
counters will increase. Individual searches and verification commands are in
[README.md](README.md).
