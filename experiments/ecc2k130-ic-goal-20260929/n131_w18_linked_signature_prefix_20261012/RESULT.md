# Exact 14-bit linked-subtotal signature gate on the N131 W18 source

**A 14-bit linear signature distinguishes the two Frobenius-linked subtotal outcomes for every one of the 66,382 pair-output roots in the frozen W18 source.** The source census covers all 33,191 pair codes, and the independent [table audit](table_audit_result.json) checks every code, root discriminator, mask pair, and signature difference. An independent Sage audit then replayed **265,528 signed binary-curve additions** across every root with zero mismatches. A constructed N131 SAT assignment passed the complete [signature-gated circuit](sat/control_result.json): `438380` variables, `1998046` clauses, and `80810` native XOR rows. The ordinary query on the frozen N131 public point recorded `BOUNDED_UNKNOWN` at its `600.151128208`-second target-dependent cap with peak sampled combined RSS `789528576` bytes. The [terminal audit](query_audit_result.json) rebuilt its 42,093,277-byte XCNF byte for byte.

## Exact source map and separator

The [Sage census](census_sage.py), frozen by [protocol.json](protocol.json), solves the pair-output quadratic for each canonical W18 seed-212 code. Each code has two standard reciprocal roots. For each root `a=1/x`, it evaluates the x coordinate of `P+τ^16(P)` and `P-τ^16(P)` from x alone, stores their reciprocals in the [complete compressed table](rows.tsv.gz), and checks 32 signed Sage curve-point additions during production. The job reported `33191` codes, `66382` roots, and zero collisions in the low 24 reciprocal bits after `185.2310115` seconds of exploratory wall. The compressed table SHA-256 is recorded in [census_result.json](census_result.json).

The [frozen hash search](hash_selection_protocol.json) tests seeds 1 through 1000 in order, drawing fourteen 131-bit masks with Python `random.Random(seed)`. The first separator is seed **42**. Bit `j` of its signature is the parity of the field encoding AND mask `j`. The [hash manifest](hash_manifest.json) retains every mask. All `66382` nonzero plus/minus differences have a nonzero 14-bit signature, as independently checked in [table_audit_result.json](table_audit_result.json). Using unmixed low bits would require 18 bits for this table.

## Why the gate selects the intended subtotal

For `P=(x,y)` on `y²+xy=x³+1`, set `F=x³+1`, `A₀=0`, and `B₀=1`. The recurrences

`Aⱼ₊₁=Aⱼ²+Bⱼ²F`, `Bⱼ₊₁=Bⱼ²x`

give `y^(2^j)=Aⱼ+Bⱼy` and `xBⱼ=x^(2^j)`. For `X=x^(2^16)` and `d=x+X`, the usual characteristic-two addition formula gives

`x(P+τ^16P) = d + [A₁₆²+(1+B₁₆)²F+dA₁₆]/d²`.

The x coordinate for `P-τ^16P` differs by `(X/d)²+X/d`. The frozen source avoids the exceptional denominator and zero-reciprocal cases. The existing first Semaev addition constraint supplies the two subtotal possibilities. The gate computes fourteen XORs of the first subtotal reciprocal and requires the source-selected plus signature. The checked [Lean theorem](SignatureSelect.lean) proves that a signature separating two complete roots selects the plus root; [PROOF_MAP.md](PROOF_MAP.md) records the concrete curve bridge and its formalization status.

The [gate source](gate.py) factors selector equality through a prefix trie with `115843` nodes, then adds guarded clauses for the fourteen signature bits of each of the `66382` pair roots. The [construction diagnostic](stage_result.json) records the exact formula counts and exploratory build wall. The [SAT protocol](sat/protocol.json) was frozen before its [constructed control](sat/control_result.json). The [public-query wrapper](public_gate_v3.py) checked the complete [independent all-root addition audit](fast_audit_result.json), source hashes, constructed control, and archived control formula before launching the target-dependent run.

## Measurement and next gate

| Item | Exact status or count |
| --- | ---: |
| W18 canonical source codes | `33191` |
| Pair-output roots | `66382` |
| 14-bit signature collisions | `0` |
| SAT constructed assignment | `PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS` |
| Constructed XCNF bytes | `42092793` |
| Constructed parent peak RSS | `383352832` bytes |
| All-root Sage addition-formula replay | `PASS_INDEPENDENT_SAGE_ALL_W18_LINKED_ADDITION_FORMULAS`; `265528` signed additions |
| Slower Sage point-object replay | `OPERATOR_STOPPED_REDUNDANT_POINT_OBJECT_AUDIT`, exit `143`, zero progress markers; [receipt](slow_audit_stop_receipt.json) |
| Frozen public-point query | `BOUNDED_UNKNOWN` at `600.151128208` s; [receipt](sat/query_result.json) |
| Public-query terminal audit | `PASS_N131_SIGNATURE_GATE_TERMINAL_RECEIPT_AUDIT` |

The public run used point `[1052727368764798954359115163823647684025, 2071227447786120917960296877345506689833]`, workload `cc09e7eb202a`, one worker, and the frozen 4-GiB combined RSS cap. Its exclusive target-dependent phase costs were `2545919666` ns for target orbit and fibers, `108726668292` ns for formula construction, `913337167` ns for serialization, `487923676791` ns for capped solver search, and `41526292` ns for terminal parsing. The parent stopped the solver at `TOTAL_QUERY_TIMEOUT` with exit code `-9` and no terminal SAT/UNSAT line. The [public XCNF archive](query_archive_receipt.json) and [read-only verifier](verify_query_archive.py) replay the original 42,093,277 bytes from a 9,597,988-byte gzip file. The constructed control and public query ran on a contended host; their wall times are exploratory.

The gate removes the linked sign ambiguity exactly, but its table clauses expand the public formula to `438395` variables and `1998058` clauses, and this solver did not finish within the cap. The next falsifiable step is to encode the x-only Frobenius prefix directly through its recurrence, eliminating the 33,191-code guarded lookup. Measure constructed formula size, complete-assignment correctness, and preprocessing/search phase costs under the same frozen public workload before another full query. A terminal SAT model requires independent signed group replay before it becomes a relation row.
