# Target-conditioned trace parity in five-pair point decomposition

The four balanced reciprocal S3 links imply one exact parity equation between the five pair outputs and the public target. On the frozen N131 W29 circuit, adding that one native XOR row lowered propagation from about 59 million to about 45 million at 100,001 conflicts. A second encoding placed the same condition directly on the source-product tensor wires; it reproduced the output-row solver search on N131 and used a much wider XOR row. The compact output row was then run on the N131 public point for 595.09 target-dependent seconds and recorded `BOUNDED_UNKNOWN` at the cap.

The implementation adds a derived target-conditioned XOR constraint to the SAT-based binary point-decomposition approach studied in [A SAT-Based Approach for Index Calculus on Binary Elliptic Curves](https://pmc.ncbi.nlm.nih.gov/articles/PMC7334981/). The experiment establishes the stated algebraic identity and measured solver-stage effect for its frozen circuits; originality of the specific trace preprocessor remains a literature question.

## Identity and encoding

For the characteristic-two reciprocal S3 link used by the circuit,

`(abz)^2 + abz + (a+b)^2 + z^2 = 0`,

absolute trace cancels the two `abz` terms and gives `Tr(z) = Tr(a)+Tr(b)`. The five pair outputs are Frobenius-rotated before the four balanced links, and absolute trace is Frobenius-invariant. The links therefore imply

`Tr(z0)+Tr(z1)+Tr(z2)+Tr(z3)+Tr(z4) = Tr(target)`.

The public target fixes the right-hand bit before search. In the N41 power basis, trace selects one bit from each output, so the row has five inputs. In the N131 power basis it selects two bits per output, giving ten inputs. These rows are logical consequences of the existing circuit; the experiment measures the effect of exposing the consequence to native XOR propagation.

There is also a source-only encoding. For a fixed-seed pair, put `s=h²+h`, `H=h²`, `C=1+H=(1+h)²`, `p=a(a+s)`, and `q=p⁻¹`. The reciprocal output satisfies `Cz²+pz+H=0`. If the source pair is admissible, `u=CHq²` has trace zero. With the odd-degree half-trace `t=HT(u)`, one root is `z=(p/C)t`; the other is `z+p/C`. Writing `b=a/(1+h)` gives `p/C=b²+hb` and hence `Tr(p/C)=Tr((1+h)b)=Tr(a)=0`. Both roots therefore have the same trace. Since half-trace and squaring are GF(2)-linear, expanding `p` in source-mask bits and `q` in inverse-witness bits gives

`Tr(z) = XOR_{i,j} κ[i,j] (mask[i] AND q[j])`,

where `κ[i,j]=Tr((PB[i]/C) HT(CH e[j]²))`. The exact source gates already contain every required `mask[i] AND q[j]` wire. This gives a target-conditioned parity row directly on source witnesses without introducing new AND gates. Its coefficient weight per pair is 166 on N41 W9 and 1,866 on N131 W29; the five-pair rows have 830 and 9,330 inputs respectively.

The field calculation above assumes nonzero `p`, odd extension degree, the fixed seed and half-trace construction, and source admissibility. It is an exact relation for those inputs; it is not an independent filter on already valid decompositions. The useful question is how much earlier the solver can propagate the target bit.

## Frozen checks and measurements

All circuit comparisons use the same public point, source base, five rotations, and balanced S3 links within each field. N41 has degree 41, W9 with eight free source bits and 71 admissible canonical pair edges. N131 has degree 131, W29 with 28 free source bits. The checked Sage launcher supplied the field arithmetic runtime recorded in `sage_runtime_info.json`. The constructed model check verifies every CNF clause and native XOR row. These are ordinary-host solver diagnostics, with one CryptoMiniSat worker, a 4 GiB combined RSS cap, and alternating baseline/modified order. Wall times reflect noisy shared-host load; conflict counts, decisions, and propagations are the useful fixed-work diagnostics.

| Circuit | Exact field polynomial | Curve ID | Fixed source seed mask | Frobenius rotations | Public raw-point input |
| --- | --- | --- | ---: | --- | --- |
| N41 W9 | `u^41+u^3+1` | `EC1N41Ckb1h7d5e80d3c4d0` | 56 | 0, 6, 12, 18, 24 | `(2105655159232, 891719206310)` after the recorded orientation |
| N131 W29 | `u^131+u^13+u^2+u+1` | `EC1N131Ckb1heb5f1998f20b` | 898618 | 0, 18, 36, 54, 72 | `(877610862732227974378969808549299291499, 2063336771837286479337213121437715536874)` |

N41's 71 count is of canonical admissible pair edges, not the `fb<B>` size of a complete IC candidate. The W29 full factor-base count, orbit-folded columns, final relation matrix, and target descent are outside this circuit-stage record; `candidate_id` stays null in the N131 query row. The N131 public workload ID is `cc09e7eb202a`.

| Field and gate | Inputs in added XOR row | Formula delta | Frozen control | Fixed-conflict result |
| --- | ---: | --- | --- | --- |
| N41 W9 table-source output trace | 5 | +1 variable, clause, XOR row | constructed five-pair model passes | 20,000 conflicts: baseline 7.309M, trace 7.383M propagations |
| N41 W9 exact-source source trace | 830 | +1 variable, clause, XOR row; 0 ANDs | constructed five-pair model passes | 20,000 conflicts: baseline 7.627M, source 7.742M propagations |
| N131 W29 exact-source output trace | 10 | +1 variable, clause, XOR row | constructed five-pair model passes | 100,001 conflicts: baseline ~59M, trace ~45M propagations |
| N131 W29 exact-source source trace | 9,330 | +1 variable, clause, XOR row; 0 ANDs | constructed five-pair model passes | 100,001 conflicts: same 413,447 decisions and ~45M propagations as output trace |

All fixed-conflict runs ended `INDETERMINATE` at their declared cap. The N131 solver-reported per-thread times were 7.32/8.14 seconds for baseline and 4.77/4.41 seconds for output trace in the alternating four-run sequence; the source-trace times were 4.66/4.58 seconds in a separate alternating sequence. These are stage diagnostics.

The full N131 public-point query used one solver worker and the same 4 GiB combined RSS cap. Its measured 595.088 seconds comprised 0.018 seconds target conversion, 8.868 seconds formula construction, 0.272 seconds serialization, 585.918 seconds solver search, and 0.012 seconds terminal parsing. The monitor stopped the process at the declared target-dependent limit; the solver had emitted no SAT or UNSAT status, and its last flushed progress line showed about 499,000 conflicts. Peak sampled combined RSS was 164,954,112 bytes. The recorded status is `BOUNDED_UNKNOWN` with `stop_reason: TARGET_DEPENDENT_TIMEOUT`. The earlier baseline query on the same public point also recorded `BOUNDED_UNKNOWN` at its 595-second monitor stop; these two censored rows do not establish a relation-yield or end-to-end speed comparison.

The independent Sage census checked sign-invariant output trace on all 71 N41 eligible edges and checked the target parity of the constructed N41 and N131 decompositions. The source-tensor coefficient script then checked all 71 N41 edges, all five constructed N131 pairs, and 122 eligible members of a seeded 512-code N131 sample. N41 had 36 trace-zero and 35 trace-one canonical edges; a degree-at-most-two Boolean polynomial in the eight source-mask bits was inconsistent on that set. The coefficient vectors and exact source hashes are in `source_trace_coeff_result.json`. A separate checked-Sage group replay of the N131 constructed control found one signed five-pair sum matching the raw target with ten distinct folded columns; its receipt is `n131_trace_model_control_result.json`.

## Proof map

`TraceParity.lean` and `SourceTrace.lean` build with pinned Lean 4.34.1. `#print axioms` reports no axioms for the `TraceParity` declarations and only standard Lean foundations (`propext`, `Classical.choice`, `Quot.sound`) for the generic ring declarations:

| Mathematical step | Lean declaration | Status and hypotheses |
| --- | --- | --- |
| Trace of a characteristic-two reciprocal S3 link | `TraceParity.s3_trace` | checked, additive square-invariant trace into an exponent-two group and the exact S3 equation |
| One link determines its output trace | `TraceParity.link_output` | checked, exponent-two additive group |
| Four links imply five-pair target parity | `TraceParity.five_pair_trace` | checked, four stated link equations |
| Two roots differing by a trace-zero element have equal trace | `TraceParity.paired_root_trace` | checked, additive trace with explicit root-difference and zero-trace hypotheses |
| Fixed-seed source product factors through `1+h` | `SourceTrace.fixed_seed_product` | checked over a commutative ring |
| Quotient `p/C` equals `b²+hb` | `SourceTrace.fixed_seed_quotient` | checked with explicit inverse equation `(1+h)*dInv=1` |
| Quotient trace equals source trace | `SourceTrace.fixed_seed_quotient_trace` | checked with additive square-invariant trace and the same inverse equation |

The half-trace root formula and bit-tensor coefficient expansion are written above and independently evaluated by checked Sage; their bridge to the exact GF(2^n) model is still open in Lean. In particular, `paired_root_trace` requires the quadratic root-difference hypothesis, and `fixed_seed_quotient_trace` requires the explicit inverse equation. Formal completion requires a binary-field model with the N41/N131 polynomial moduli and the odd-degree half-trace identity. No `sorry`, custom axiom, or native-evaluation certificate appears in the checked declarations. `lean4checker --fresh` was unavailable on this host.

## Next discriminator

The next solver experiment should derive more than one independent target-conditioned constraint from a joint partial-sum elimination, because absolute trace supplies only one bit per target and the one-row N131 query remained capped. Its first gate should count independent constraints and verify that they reject source-witness families before the four full S3 links are assembled. A favorable gate then needs a fresh ordinary-relation query, useful rank, final linear algebra, one unseen target descent, and a matched same-point rho interval before an IC speedup can be selected.
