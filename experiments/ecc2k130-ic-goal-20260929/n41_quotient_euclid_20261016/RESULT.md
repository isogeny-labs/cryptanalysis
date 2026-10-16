# A quotient Euclid gate isolates the frozen N41 witness code

**The source-labelled quotient gate retained exactly second code 37 in the
rank-seven witness chart and rejected the other 38 allowed codes.** On the
control chart and both rank-three checks it rejected all 39 allowed codes.
The [independent replay](verification.json) matches the frozen finite-code
oracle in all four cells. This supplies an exact implementation of the
nonunit-pivot splitting proposed after the implicit-norm experiment.

## Construction

The input is the frozen N41 three-product tensor over
`GF(2)[t]/(t^41+t³+1)` on curve `EC1N41Ckb1h7d5e80d3c4d0`.
For first code `p=24` and each of the two frozen residual charts, let
`H(q,r)` be the specialized tensor polynomial. It has degree 16 in `q`
and 24 in `r`. The 39 source-allowed second-code values define the
squarefree polynomial `G(q)=∏(q+q_j)`. Its quotient ring is
`R=GF(2^41)[q]/(G)`.

The leading coefficient of `H` in `r` is a unit in `R`, checked by an exact
extended-GCD inverse and multiplication replay. Normalize `H` to monic.
For the frozen binary third-product basis, form the monic linearized span
annihilator by `L_{i+1}(r)=L_i(r)^2+L_i(v_i)L_i(r)`, reducing each step
modulo `H` in `R[r]`. Run Euclid on `H` and the final remainder. A unit
pivot permits exact division. A nonunit pivot splits the active code
polynomial by its GCD with that pivot; its factor is kept as a suspect and
Euclid restarts on the complementary factor. A unit constant final GCD
rejects that active code set. The output is a source-labelled set of
possible second codes, ready for exact witness extraction.

For an allowed code `q_j`, evaluation `R → GF(2^41)` is a ring map. Thus
monic reduction and each unit-pivot Euclidean division specialize to the
corresponding field computation. The split factorization covers every
`q_j` root of the active polynomial. Any branch rejected by a unit GCD
has a Bezout certificate and cannot contain a common root of `H(q_j,r)`
and `L_V(r)`. This proves that the gate retains every genuine span root;
the positive source triple here is `(24,37,10)`. The [proof map](PROOF_MAP.md)
records the Lean scope and remaining executable-code bridge.

## Frozen run

The [protocol](protocol.json) fixes source and input hashes, one worker,
180 s wall cap and a monitored 4 GiB RSS threshold. The parent observed
4.21 MB peak RSS; the native program reported the same `ru_maxrss` value
on this macOS host. The parent wall was 7.044 s and native worker wall was
6.687 s. Times are ordinary-host component diagnostics.

| Chart | Span rank | Gate kept codes | Exact oracle codes | Reduce `L` | Euclid gate | Nonunit splits |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| Witness | 3 | `[]` | `[]` | 0.000003 s | 0.0155 s | 0 |
| Witness | 7 | `[37]` | `[37]` | 0.853 s | 1.957 s | 1 |
| Control | 3 | `[]` | `[]` | 0.000016 s | 0.403 s | 0 |
| Control | 7 | `[]` | `[]` | 2.252 s | 1.172 s | 0 |

The [native result](result.json), [parent receipt](receipt.json), and raw
logs preserve the phase timings and status. The earlier explicit 39-code
oracle took 1.121 s of native worker time for these two charts and ranks;
this quotient gate took 6.687 s, a 5.97-fold cost on these frozen inputs.
The single pair of runs is not an isolated wall benchmark. It is enough
to reject this implementation as the next speed candidate at this region
size; a larger first-code sweep would multiply its current cost.

The first bounded parent launch hit a macOS `preexec_fn` resource-limit
exception before child execution. The second parent launch used an
interpreter without `psutil` and also stopped before child execution. Both
launch failures are retained under `launch_failure_v1/` and
`launch_failure_v2/`; the completed parent used the frozen Python 3.9.10
interpreter and a 50 ms RSS poll. Its monitor cannot rule out a transient
peak between polls, so the child `ru_maxrss` is also recorded.

The run is a target-conditioned component on the archived N41 witness and
control residual charts. The next useful algorithm experiment should
reduce the degree-24 tower cost before testing a full first-code panel:
batch field inversions and sparse polynomial division against the 39
independent specializations provide the measured 1.121 s reference. A
new joint constraint must beat that source-labelled oracle on frozen
ordinary N41 inputs before promotion to the N131 W20 source-bound gate.
The proposal retains `candidate_id: null` until a complete IC pipeline
is specified.
