# J2 independent claim-fidelity review

Task: `TASK-20261028-a07ed4`; owned joint: `J2` only.  
Archival task: `TASK-20261028-871ca0`; Conductor: `T-765`.  
Supplied immutable producer: `ffeacb44b6a151aebc84619f30a70591eb44e0f6`.  
Supplied prospective-plan commit: `dcebcd1842d112ebc3d985f02245cf0a8b7a8391`.  
Worktree: `/var/tmp/cryptanalysis-known-label-review-20261028`.  
Method: independent, source-level, adversarial fidelity review; no native Lean execution.

**Verdict: `holds` for J2's scoped source-to-claim fidelity.** The four proof-map statements match the declared source. The source proposes polynomial equalities over arbitrary commutative rings, with no cancellation, inversion, distinctness, finite-field, graph, elliptic-curve, or probabilistic assumptions. Both the original note and new proof map explicitly leave the surrounding model bridges outside these statements. I found no mismatching type or unproved bridge presented as an established Lean result in the permitted sources.

This verdict does **not** certify elaboration, kernel acceptance, transitive axioms, gate implementation, native CI, or the complete surrounding mathematical argument. No checked elaborated type or universal checked proof is assumed. Native validity remains **not verified by this reviewer**. J1 owns independent universal algebraic derivation; J3 owns the admission implementation. The review-plan prior was visible as authorized: this is an independent fidelity review, not J1's blind expression-only rederivation.

## Integrity and read boundary

I read the complete fidelity handoff, review plan, and input manifest, then only these four producer files. Each SHA-256 matches `inputs.json` exactly:

| Permitted source | Observed SHA-256 |
| --- | --- |
| `docs/known-label-next-leads-20261028/Algebra.lean` | `d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d` |
| `docs/known-label-next-leads-20261028/README.md` | `7f99c207eb07dbdd8fe58f294ed3b6728941c6b297b36e636269353c0da52d7b` |
| `docs/known-label-next-leads-20261028/CHECKS.json` | `7f36cbd7f2167f0eaef1ca93083c64bdd09628c16b2e627a6b803f8bdceb85e6` |
| `tools/lean/README.md` | `5b62ba399a527fd8e7ffbf842a8c499d05955072ca6e78f35b7404fbfa0ca635` |

`CHECKS.json:19` and `tools/lean/README.md:38-39` also agree on the algebra-source digest. The attestation records hashes of all seven inputs, including administrative files for which no expected digest was supplied. I did not inspect Git history or independently establish the supplied commits, push state, or ancestry. This finding binds the visible bytes to the supplied manifest.

No blind brief, sibling report, producer test source, linked document, other repository file, memory file, network source, or Git history was read. Test outcomes visible in the allowed `CHECKS.json` were not independently verified or rerun. No Lean/Mathlib build, experiment, cloud call, source edit, PR mutation, or subagent delegation occurred. Only the two assigned output files were created. Procedure deviations: none. One output-assembly command failed because `python` was unavailable; it made no writes and was retried with `/usr/bin/python3`.

## Source statements, quantifiers, and proof map

`Algebra.lean:8` declares `variable {K : Type*} [CommRing K]`. At source level each theorem is intended to generalize over the universe of `K`, an arbitrary type `K` with a `CommRing` instance, and all explicit `a b c : K`. `K` and its instance are implicit parameters; the three elements are universally quantified explicit parameters. This describes the source binders, not an observed elaborator printout.

| Declaration in `KnownLabelLeads` | Source lines | Proposition, with whitespace normalized | New proof map |
| --- | --- | --- | --- |
| `triangle_identity` | 10-11 | `2*a = (a+b) - (b+c) + (c+a)` | `tools/lean/README.md:47`; matches |
| `signed_second_moment` | 13-14 | `(a+b-c)^2 - (a^2+b^2-c^2) = 2*(a-c)*(b-c)` | line 48; matches |
| `signed_third_moment` | 16-18 | `-(a+b-c)^3 + 3*(a+b-c)*(a^2+b^2-c^2) - 2*(a^3+b^3-c^3) = 6*c*(a-c)*(b-c)` | line 49; matches |
| `positive_pair_product` | 20-21 | `2*a*b = (a+b-c)^2 - (a^2+b^2-c^2) + 2*c*(a+b-c)` | line 50; matches |

All signs and coefficients match, including `-2` on the cubic moment and `6*c` on its right-hand side. Each proof body is `by ring`. The four `#print axioms` commands at lines 23-26 request output; they are not evidence that output was produced. `import Mathlib` identifies a dependency, not a build receipt.

There is no `Field K`, `IsDomain K`, `Nontrivial K`, `CharZero K`, fixed characteristic, finiteness, distinctness, or nonzero premise. Numerals such as `2,3,6` denote ring elements; powers have natural exponents. There are no rational coefficients, reciprocals, division operations, or cancellation conclusions. `CommRing` permits positive characteristic, zero divisors, and the zero ring. No premise excludes those cases. In the zero ring the identities have trivial interpretations and provide no reconstruction information.

The triangle proposition uses ring multiplication `2*a`. An elliptic-curve point type with only an additive group structure cannot be substituted for `K` under these hypotheses. A point-group conclusion requires an additive-group identity or scalar-to-group map argument. None of the remaining statements defines a signature or asserts its injectivity.

## Connection to the written moment formulas

Set `s_m=i^m+j^m-k^m`. Substitution `a=i,b=j,c=k` yields the denominator-free relations

- `s_1^2-s_2 = 2*(i-k)*(j-k)`;
- `-s_1^3+3*s_1*s_2-2*s_3 = 6*k*(i-k)*(j-k)`;
- `2*i*j = s_1^2-s_2+2*k*s_1`.

With `D=(i-k)*(j-k)`, the reconstruction displayed in the original `README.md:91-93` additionally needs invertibility of `2` and `6D`. Deducing `i*j=D+k*s_1` requires cancelling `2`; deducing `i+j=s_1+k` uses the definition of `s_1`. None of these reconstruction conclusions is itself a theorem in the source.

The following hand-worked examples check missing premises. They are neither executed tests nor a replacement for J1's algebraic derivation.

| Setting | Obstruction | Invalid extension |
| --- | --- | --- |
| `F_2` | `2*0=2*1=0`, although `0!=1` | Cancelling `2` in characteristic 2. |
| `F_3`, `a=0,b=2,c=1` | Inputs are distinct and `D=2!=0`; nevertheless `6D=0`. Here `s_1=1,s_2=0,s_3=1`, and the third-moment numerator is `0`. | Dividing the third identity by `6D` to recover `c=1`; it only supplies `0=0` here. |
| `Z/35Z`, `a=5,b=7,c=0` | Inputs are distinct and `2,3,6` are units, but nonzero differences have product `D=5*7=0`. | Replacing the field/domain assumption with characteristic greater than 3 and distinctness. |
| `F_5`, `a=c=1,b=2` | `D=0` | Omitting the index-distinctness premise. |
| `Z`, `a=2,b=3,c=1` | `D=2` and `6D=12` are nonzero nonunits. | Treating every nonzero ring element as invertible. |

These examples do not refute any source proposition. They refute stronger conclusions with omitted premises. The original application explicitly specifies a prime scalar field of order `r>3` (`README.md:11-12,77`) and distinct indices (line 88). Those premises avoid these particular obstructions once formalized. The coordinate characteristic `p` is separate from the scalar characteristic `r`.

## Missing graph and elliptic-group bridges

The graph claims at `README.md:17-34` and implementation steps at lines 52-60 require the following obligations, all absent from the four Lean types:

1. **Curve and subgroup objects.** Define the nonsingular short Weierstrass curve over `F_p`, its group law, identity, and prime-order subgroup `G=<P>` of order `r>3`. Prove `Q` and all selected, oriented `R_i` belong to `G`. Coordinate-domain membership alone establishes neither subgroup membership nor a label.
2. **Scalar action and label map.** Define the `F_r` action and additive map `L:F_r^2 -> G`, `L(a,b)=[a]P+[b]Q`; prove compatibility with reduction modulo `r`, addition, subtraction, and scalar multiplication. A label is a representation; `L` has a kernel and is not an injective encoding of points. No uniqueness of point representations follows from the source.
3. **Edge semantics.** Certify `R_i+R_j=L(a_e,b_e)` for every edge, using the exact orientations. Connect dictionary collisions, repeated edges, and any admitted self-loop convention to these equations. The Lean module has no graph or edge type.
4. **Triangle recovery.** Derive `2 • R_1=T_12-T_23+T_31` in the additive group. Prove `2` is invertible in `F_r`, form the two coefficient quotients, and use `L` compatibility and injectivity of doubling on the odd-order subgroup to show that their label maps to `R_1`.
5. **Connected components.** Prove that an odd cycle supplies an initial label by alternating edge equations, and that path/tree propagation supplies correct labels throughout a connected component. Prove the parity/rank statement for bipartite components and sufficiency of one known anchor. These are graph and linear-algebra results, not ring-normalization conclusions.
6. **Consistency and representation ambiguity.** Distinguish coefficient equations from equality of represented points. A connected non-bipartite graph gives a unique coefficient solution only when the coefficient equations are consistent. Independently valid point edges can have coefficient discrepancies in `ker L`; the note acknowledges these at lines 32-34. Prove every detected discrepancy maps to the identity and specify handling rather than assuming all coefficient cycles are consistent.
7. **DLP extraction.** From `L(a,b)=O`, `b!=0`, `Q=[x]P`, and the exact order of `P`, obtain `a+bx=0` in `F_r`, then `x=-a/b`. A zero or `b=0` discrepancy does not supply this extraction. Verify `[x]P=Q` and connect that verification to early-success handling.
8. **Implementation refinement.** Prove that enumeration, target storage, propagation, and returned labels implement the defined objects and conditions. Recorded abstract-group test successes do not prove actual curve-arithmetic correctness or exhaustive graph behavior. I did not read or run the implementation/tests.

The phrase that a component determines labels therefore needs the note's verified-edge and discrepancy context. It cannot be strengthened to uniqueness of coefficient representations of group points. The new proof map makes no such strengthened claim.

## Missing signature-injectivity bridges

The reconstruction and signature claims at `README.md:88-108` require these additional steps:

1. Define the scalar field `F_r`, with prime `r>3`, and the embedding of `I={0,...,B-1}` where `B<=r`. Prove this embedding preserves index distinctness; distinct integers can otherwise coincide modulo the field characteristic.
2. Define events as a negative index `k` and an **unordered** positive pair `{i,j}`, with all indices distinct. Ordered positive pairs cannot be distinguished by symmetric moments; exchanging `i,j` must represent the same event.
3. Prove `i-k` and `j-k` are nonzero and their product `D` is nonzero in the field. Prove `2,6` are nonzero units, and justify each division in lines 91-93 from the source equalities.
4. Prove equal moment triples imply equal `D`, equal `k`, and equal positive-pair sum and product. Prove that the roots of `X^2-(s_1+k)X+(D+k*s_1)` determine the unordered positive pair under the distinctness convention. Root uniqueness uses field/domain reasoning absent from the module.
5. Prove a decoder handles roots/discriminant and index bounds and checks the actual point relation. Injection on valid inputs does not establish that every supplied moment triple has a valid preimage.
6. Define `v=(1,s_1,s_2,s_3)` and prove distinct valid events give distinct vectors. Since the first coordinate is `1!=0`, proportional vectors must have proportionality constant `1`; then prove any pair of distinct event vectors has rank two. No vector, rank, or injectivity statement appears in the source.
7. Connect the scalar polynomial evaluation to the actual constructed point `F(i)` using the group action and `L`. To claim a base of distinct affine abscissae, prove that exclusion of `O` and of pairs `F(i)=±F(j)` gives distinct usable abscissae on the specified curve.

The original note explicitly leaves finite-field signature injectivity unformalized (`README.md:150-153`). The new proof map supplies no theorem that discharges these steps.

## Missing probability and cost bridges

This section inventories obligations; it is not a machine-checked validation of the written probability argument.

1. **Sample space.** Define four independent uniform label pairs `(a_j,b_j)` in `F_r^2`, with the curve, `P,Q`, field, and index set fixed before sampling. Prove their points `T_j` are independent uniform subgroup elements using the scalar map and order of `P`.
2. **Event semantics.** Prove `F(i)+F(j)-F(k)` is the seed-point combination with coefficient vector `(1,s_1,s_2,s_3)`. For the corresponding summed labels `A_v,B_v`, identify the group relation with `A_v+xB_v=0`, where `Q=[x]P`. Define useful as additionally `B_v!=0` and connect it to discrete-log extraction.
3. **One-event probability.** Prove `(A_v,B_v)` is uniform on `F_r^2` using the nonzero coefficient vector. Count exactly `r-1` pairs satisfying the relation and `B_v!=0`, yielding `q=(r-1)/r^2`. Alternatively establish the stated conditional uniformity and its positive-probability conditioning event.
4. **Pairwise independence.** Use signature injectivity and first coordinate `1` to establish rank two for rows `v,w`. Prove the resulting maps on the independent `a` and `b` seed vectors are surjective with uniform pushforward. This yields four uniform summed labels and independence of the two useful-event indicators. Mutual independence of the whole event family is not established or needed for the stated second moment.
5. **Event count.** Prove `M=3*binomial(B,3)` for this precise event convention, handling `B<3` separately. Avoid counting positive-pair order twice or including all-plus events. The note explicitly restricts the family at lines 119-122.
6. **Second moment.** For useful-event count `X`, prove `E[X]=Mq` and `E[X^2]=Mq+M(M-1)q^2`, then justify the nonnegative-variable second-moment bound `Pr(X>0)>=Mq/(1+(M-1)q)`, including the zero-event case. None of these random variables, expectations, or inequalities is in the module.
7. **Bad-vertex subtraction.** Prove uniform evaluation at each index and the rank-two evaluation property at distinct indices. Bound identity vertices by `B/r` and plus/minus collisions by `2*binomial(B,2)/r`, totaling `B^2/r`. Connect those group events to geometric degeneracy and subtract by a union bound. Pairwise independence of useful events must not silently be reused after conditioning on absence of bad vertices.
8. **Asymptotics.** Specify primes tending to infinity and `B~r^(1/3)`, prove `Mq -> 1/2` and `B^2/r -> 0`, and deduce the written `1/3-o(1)` statement. Truncate negative finite lower bounds at zero. A distributional bound is not a measured event rate.
9. **Graph-hit probability.** Separately, `K/r` at lines 62-63 requires a fixed set of `K` distinct subgroup targets and a uniform query over the subgroup. Uniform targets do not imply uniform edges because one target can carry multiple edges. The extra random-edge model and `K=Theta(B^2)` must remain hypotheses or be established before deriving a connectivity/query claim.
10. **Complete cost.** Account for enumeration, subgroup filtering, dictionary construction, failed queries, memory, curve arithmetic, scalar replay, early success, and solver work under the stated matched protocol before any performance conclusion. Neither the identities nor a probability bound proves efficient solving or an improved complete attack cost. The note labels its graph scale heuristic and scopes the generator count (`README.md:64-68,83-86,126-140`).

## Decision table

| Claim | J2 finding |
| --- | --- |
| Four arbitrary-commutative-ring polynomial equalities are proposed | Supported by exact source and matching proof-map statements. |
| Original producer had already checked Lean proofs | Not claimed: source lines 3-5, original README lines 150-153, and CHECKS lines 26-29 explicitly say unbuilt/unverified. |
| Exact-source native admission has succeeded | Not established here. Manifest records pending CI; no terminal native output was read. |
| The identities prove graph recovery | Explicitly excluded; group/action, invertibility, graph, and implementation bridges remain absent. |
| The identities prove finite-field signature injectivity | Explicitly excluded in the original note; event quotient, field, and root arguments remain absent. |
| The identities prove probability or performance results | Explicitly excluded; distributional and complete-cost arguments remain outside the module. |
| Gate implementation matches its README | Outside J2; requires J3 and coordinator native evidence. |

The narrow source-level fidelity claim holds. Native CI, proof acceptance, J1's algebraic derivation, and J3's admission review remain separate evidence requirements. Even a successful native build would not fill the graph, signature, probability, implementation, or performance bridges inventoried here.
