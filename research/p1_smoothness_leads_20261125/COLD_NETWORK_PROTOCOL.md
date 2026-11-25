# Frozen cold relation-rank and target-descent panel

This protocol extends the committed exact hit census to a deterministic
single-target workload. It is frozen before the rank/descent run. The
decomposition oracle is an explicit group-addition sum table, so its operation
counts are finite combinatorial diagnostics; they are not `msolve` timings or
full prime-field index-calculus costs. All local output has producer-only
standing `[pcc:unverified]`.

## Fixed workload

- Use the field, prime-order curve, five rational isogenies, coordinate bound
  `x < 20`, and unique normalized pullbacks in `NETWORK_PROTOCOL.md`.
- Set `G = E.gens()[0]`. The only target is `R = 137*G`. Construct `R` before
  precomputation, exclude scalar 137 from all known-scalar relation streams,
  and use 137 solely as the final verification value.
- The single-arm reference is the fifth isogeny in the degree-ordered list:
  the second degree-19 arm, whose 451-hit set is largest in the prior frozen
  census. The five-arm network is the other comparison. The base curve is an
  additional labeled reference.

## Charged algorithm

1. For each arm, sort its normalized factor-base points by integer `(x,y)`.
   Construct an unordered two-summand table by adding every pair with
   replacement, retaining the first pair for each sum. Charge one group
   addition per pair, including duplicates. The table is the decomposition
   oracle; report its build additions and distinct hit count.
2. Canonicalize each nonzero factor-base point with its negative by the same
   `(x,y)` order. Use one logarithm variable per sign pair, with known
   coefficient `+1` or `-1` in each relation. For each arm independently,
   scan `s=1,2,...,10192` excluding `s=137`. At each `s`, query the table
   once for `s*G`. If it hits, use only the retained pair to add the exact
   equation `s = log(P)+log(Q) mod 10193`. Stop that arm at full matrix rank
   or report it censored after the stream. Count all attempted membership
   queries, hit equations, and rank-increasing equations.
3. For a full-rank arm, solve the linear system over `GF(10193)` and check
   every recovered logarithm by scalar multiplication on `E`. Starting at
   `t=0`, query `R+t*G` until an arm hits; return
   `log(P)+log(Q)-t mod 10193` and verify its scalar multiplication equals
   the target. A censored arm cannot participate in descent.
4. For the five-arm network, complete precomputation on **all five** arms,
   then at each `t` query them in degree-list order, stopping at the first
   hit. Charge each attempted arm query. Report sums of build additions and
   precomputation queries, plus descent queries. For each single-arm
   reference, report its corresponding cold counts.

This fixed scan is not a random-trial expectation. It reports the actual
rank and same-target outcome on this fixture; it must not be used as an
asymptotic speedup claim. `[pcc:unverified]`
