# Full-length N131 union query with larger XOR matrices

The larger-matrix configuration kept **nine to ten Gaussian matrices**
admitted during a full-length, one-worker query on the exact official
ECC2K-130 public point. Its [frozen result](query_result.json) is
`BOUNDED_UNKNOWN` at the **615.074-second parent cap**, with no terminal SAT
line and **2,365,456,384 bytes** sampled combined peak RSS. The solver log,
binary and formula hashes, flags, target, and runtime are retained with the
[protocol](query_protocol.json). No relation row was inserted from this run.

| Full-length arm | Matrix policy | Parent wall | Sampled peak combined RSS | Status |
| --- | --- | ---: | ---: | --- |
| Default | CryptoMiniSat defaults | 615.048 s | 647,806,976 B | `BOUNDED_UNKNOWN` |
| Larger matrices | 16,000 rows, 20,000 columns, up to 10 matrices | 615.074 s | 2,365,456,384 B | `BOUNDED_UNKNOWN` |

Both arms used the same official-point XCNF, one worker, a 4-GiB sampled
RSS cap, and the same parent limit. The larger-matrix arm admitted the
matrices throughout its run; the default arm admitted five small matrices
initially and reported zero in later rebuilds. This establishes the
effect of the matrix-limit flags and their memory cost. Neither arm
produced a verified model within its cap. The host carried other solver
workloads, so these wall observations are bounded statuses rather than an
isolated solver-speed or IC/rho comparison.

The accompanying 135-second pair retained the same statuses. The matrix
policy has now passed its admission check and its 4-GiB resource gate, but
not the ordinary-relation gate. The next algorithmic screen should change
the decomposition search structure or add a sound pruning invariant, with
a complete planted assignment and an ordinary public-target falsifier
before more full-length solver tuning. Run `python3 verify.py` here for
the read-only custody check.
