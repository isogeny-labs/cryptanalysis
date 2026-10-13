# Exact 14-bit linked-subtotal signature gate on the N131 W18 source

**A 14-bit linear signature distinguishes the two Frobenius-linked subtotal outcomes for every one of the 66,382 pair-output roots in the frozen W18 source.** The source census covers all 33,191 pair codes, and the independent [table audit](table_audit_result.json) checks every code, root discriminator, mask pair, and signature difference. A constructed N131 SAT assignment then passes the complete [signature-gated circuit](sat/control_result.json): `438380` variables, `1998046` clauses, and `80810` native XOR rows. Its 42,092,793-byte XCNF was built with peak parent RSS `383352832` bytes. The [full independent curve replay](audit_protocol.json) and [all-root addition-formula replay](fast_audit_protocol.json) are separate live checks; their terminal results determine promotion to an ordinary public query.

## Exact source map and separator

The [Sage census](census_sage.py), frozen by [protocol.json](protocol.json), solves the pair-output quadratic for each canonical W18 seed-212 code. Each code has two standard reciprocal roots. For each root `a=1/x`, it evaluates the x coordinate of `P+τ^16(P)` and `P-τ^16(P)` from x alone, stores their reciprocals in the [complete compressed table](rows.tsv.gz), and checks 32 signed Sage curve-point additions during production. The job reported `33191` codes, `66382` roots, and zero collisions in the low 24 reciprocal bits after `185.2310115` seconds of exploratory wall. The compressed table SHA-256 is recorded in [census_result.json](census_result.json).

The [frozen hash search](hash_selection_protocol.json) tests seeds 1 through 1000 in order, drawing fourteen 131-bit masks with Python `random.Random(seed)`. The first separator is seed **42**. Bit `j` of its signature is the parity of the field encoding AND mask `j`. The [hash manifest](hash_manifest.json) retains every mask. All `66382` nonzero plus/minus differences have a nonzero 14-bit signature, as independently checked in [table_audit_result.json](table_audit_result.json). Using unmixed low bits would require 18 bits for this table.

## Why the gate selects the intended subtotal

For `P=(x,y)` on `y²+xy=x³+1`, set `F=x³+1`, `A₀=0`, and `B₀=1`. The recurrences

`Aⱼ₊₁=Aⱼ²+Bⱼ²F`, `Bⱼ₊₁=Bⱼ²x`

give `y^(2^j)=Aⱼ+Bⱼy` and `xBⱼ=x^(2^j)`. For `X=x^(2^16)` and `d=x+X`, the usual characteristic-two addition formula gives

`x(P+τ^16P) = d + [A₁₆²+(1+B₁₆)²F+dA₁₆]/d²`.

The x coordinate for `P-τ^16P` differs by `(X/d)²+X/d`. The frozen source avoids the exceptional denominator and zero-reciprocal cases. The existing first Semaev addition constraint supplies the two subtotal possibilities. The gate computes fourteen XORs of the first subtotal reciprocal and requires the source-selected plus signature. The checked [Lean theorem](SignatureSelect.lean) proves that a signature separating two complete roots selects the plus root; [PROOF_MAP.md](PROOF_MAP.md) records the concrete curve bridge and its formalization status.

The [gate source](gate.py) factors selector equality through a prefix trie with `115843` nodes, then adds guarded clauses for the fourteen signature bits of each of the `66382` pair roots. The [construction diagnostic](stage_result.json) records the exact formula counts and exploratory build wall. The [SAT protocol](sat/protocol.json) was frozen before its [constructed control](sat/control_result.json). The public-query wrapper in [gate_v2.py](gate_v2.py) checks the independent all-source replay status before calling the target-dependent solver.

## Measurement and next gate

| Item | Exact status or count |
| --- | ---: |
| W18 canonical source codes | `33191` |
| Pair-output roots | `66382` |
| 14-bit signature collisions | `0` |
| SAT constructed assignment | `PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS` |
| Constructed XCNF bytes | `42092793` |
| Constructed parent peak RSS | `383352832` bytes |
| All-source Sage point replay | live process, terminal status pending |
| All-root Sage addition-formula replay | live process, terminal status pending |
| Frozen public-point query | pending independent replay gate |

The constructed control and formula-size diagnostics ran on a contended host; their wall times are exploratory. After an all-root independent audit passes, the next run is one ordinary query on frozen point `[1052727368764798954359115163823647684025, 2071227447786120917960296877345506689833]`, with one worker, a 600-second total target-dependent cap, and 4-GiB combined RSS. A terminal SAT model requires independent signed group replay before it becomes a relation row. Preserve every capped or failed status with its exact phase and resource receipt.
