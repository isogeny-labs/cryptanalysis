# Adaptive zero-test theorem and complete p=313 replay

**Theorem.** An adaptive search that learns only the Boolean result of each
proposed two-point public relation covers exactly the scalar candidates on
its all-negative query path. If every queried coefficient sum is nonzero,
`N` relation tests can hit at most `N` of the `q` uniformly possible target
scalars. The result allows each next coefficient vector and offset pair to
depend arbitrarily on all earlier zero-test answers. The checked Lean
declarations prove both the exact success-set identity and the cardinality
bound over any finite field, plus the scalar-to-public-group bridge under an
injective scalar-to-point map.

For a query `(a,b,t₁,t₂)`, the public equation is

`a(Q−t₁G)+b(Q−t₂G)=O`.

Writing `Q=wG` and `a+b≠0`, it holds precisely when
`w=(a t₁+b t₂)/(a+b)`. A failed test reports that `w` is not this one
candidate. Until a hit, every transcript is the same string of failures;
therefore all pre-hit queries are fixed by the strategy and cannot cover
more targets than the number of distinct candidates they name. The theorem
models this one-bit feedback channel. A procedure using coordinates or other
target-dependent information has a different information law and requires
separate analysis.

## Complete public-group replay

The frozen protocol uses `E/F₃₁₃: y²=x³−x−2`, `G=(2,2)` of order 331,
every target `Q=wG` for `0≤w<331`, and 16 queries at most per target. At each
miss, SHA-256 applied to the previous Boolean transcript chooses the next
coefficients and distinct offsets. The producer checks the relation with
actual finite-curve group operations, stops at the first hit, and saves every
target's status. Its 16 negative-path queries name **15 distinct candidates**;
query 4 repeats the candidate from query 1 (one-based indices). All 15
candidate targets hit, and the other 316 targets exhaust the 16-query cap.

| Exact metric | Result |
| --- | ---: |
| Target scalars enumerated | 331 |
| Queries allowed per target | 16 |
| Distinct negative-path candidates | 15 |
| Hit targets | 15 |
| Group-relation tests across the complete census | 5,188 |
| Uniform-target hit fraction | 15/331 |
| Theorem's bound | 16/331 |

The independent `audit.py` reconstructs the SHA-256 schedule from the frozen
protocol, checks every scalar equation and first-hit index, and recomputes
all counts. It passed on all 331 rows. The checked Sage launcher saved its
runtime receipt before the group-operation replay. This is a deterministic
event and operation census; it does not time a same-target rho comparison or
price a rational-lift search. The p=313 generator order used here also has
the checked Lean certificate in the parent public-first proof PR.

## Reproduce

From the repository root, run
`/Volumes/SSD990/cryptanalysis/sage --runtime-info`, then
`/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run_sage.py`,
`python3 audit.py`, and, from `formal/`, `lake build AdaptiveZeroTest`.
The actual command output, dependency manifest, protocol, raw census,
independent audit, and source files are covered by `SEAL.sha256` and checked
with `python3 verify.py`.

The next proof step is an information bound for strategies that inspect
public point encodings or use group operations to construct their next
query. The one-bit theorem gives a sharp control case for that larger model.
