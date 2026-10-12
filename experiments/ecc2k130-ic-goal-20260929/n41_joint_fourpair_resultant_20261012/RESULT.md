# Exact two-block public-target filter on 33 N41 source families

For a fixed four-pair source tuple, the two degree-eight four-atom block polynomials give an exact finite-root public-target test. The checked N41 panel contains one eight-column public-point witness and 32 deterministic same-seed, distinct-column source controls. The test accepted the witness and rejected all 32 controls. An independent Sage group-law replay checked all 8,448 signed leaf assignments and agreed on every family. Among three exact implementations, direct testing of the two root sets took a median **8.34 ms per family**, versus **58.24 ms** for a factored nested resultant and **232.27 ms** for a direct Sylvester resultant. The paired median factored-resultant/root-check ratio was **6.60** in this exploratory CPU run.

## Exact condition and source law

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t^3+1)`, using `y²+xy=x³+1`. The source points are diagonal `D=P+Frob(P)`, with four signed two-atom slots rotated by `(0,7,14,21)` as frozen in the [N41 diagonal fixture](../n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json). Each source mask pair `(a,b)` supplies seed `s=a+b` and product `p=ab`; both are raised to `2^rotation`. The universal [266-term four-atom resultant](../n131_w15_rotated_fouratom_inverse_20261010/resultant.json) specializes to block polynomials `H_L(z)` and `H_R(v)` of degree eight. Their roots represent reciprocal x coordinates of the two four-atom partial sums on the finite nonexceptional chart.

For the fixed reciprocal public raw-target coordinate `t`, the upper Semaev equation is

`U(z,v,t) = (1+(zv)²)t² + zvt + (z+v)²`.

The nested resultant `Res_z(H_L(z), Res_v(H_R(v), U(z,v,t)))` vanishes exactly when a root pair `(z,v)` satisfies `U=0`, provided both block polynomials split into their audited field roots and have nonzero leading coefficients. The root-check implementation evaluates this equivalent finite-root condition directly. Every panel block had degree eight and split completely. The positive control was independently replayed from the eight signed diagonal points through both intermediate sums to the raw point and its cofactor-four public point. Full group replay of every family confirms the result on this panel; the algebraic filter itself concerns the reciprocal x coordinate, so signed point replay remains the final witness check.

The [panel](panel.json) fixes the positive tuple and eight alternative mask pairs in each of four slots. Every alternative shares the replaced slot's seed and preserves eight distinct folded columns. The [first protocol](protocol.json), [direct protocol](direct_protocol.json), and [root-check protocol](rootcheck_protocol.json) hash their own source and frozen inputs before the corresponding run. These are stage experiments with `candidate_id: null`.

## Results and accounting

All three variants used one worker, the checked repository Sage launcher, a 180 s cap, and monitored 4 GiB process-tree RSS. The [runtime receipt](sage_runtime_info.json) was saved before measured work. Internal family times below exclude launcher/import, fixture loading, and setup; parent wall and sampled RSS include them. The host lacks an isolation receipt, so CPU ratios are exploratory.

| Variant | Correct target decisions | Median internal family time | Parent wall | Sampled peak RSS | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Factored nested resultant | 33/33 | 58.24 ms | 12.93 s | 263,208,960 B | `EXIT_0` |
| Direct Sylvester nested resultant | 33/33 | 232.27 ms | 14.27 s | 255,868,928 B | `EXIT_0` |
| Two-block root check | 33/33 | 8.34 ms | 8.71 s | 251,822,080 B | `EXIT_0` |
| Independent group-law replay | 33/33, 8,448 signed assignments | stage audit | 7.26 s | 260,161,536 B | `EXIT_0` |

The root-check median components were 1.51 ms block construction, 6.25 ms root extraction, and 0.105 ms public-target evaluation. The direct resultant's median inner elimination alone took 226.23 ms. The positive family had two matching signed assignments in the group audit; the 32 controls had zero. Per-family rows and exact run statuses are in [root-check result](rootcheck_result.json), [factored result](result.json), [direct result](direct_result.json), [group audit](audit.json), and their respective `*_run_status.json` receipts.

An initial launch failed before the Sage workload because macOS rejected `RLIMIT_AS` in `preexec_fn`; [that infrastructure receipt](launch1_status.json) is retained. A subsequent sandboxed monitor lost process-list permission after launching Sage; its child completed and the correctness output is preserved as [unmonitored evidence](unmonitored_status.json). The measured run above is a separate repetition with working process-tree monitoring.

## Formalization and next search gate

[JointNorm.lean](JointNorm.lean) proves the finite-product zero criterion for two root lists under the two explicit integral-domain properties `1≠0` and `ab=0 ↔ a=0 ∨ b=0`. The checked [Lean output](lean_check.log) reports only `propext` and `Quot.sound` for both declarations. The pinned toolchain is Lean 4.34.1 with bundled Std. The readable proof is induction on the left and right root lists: a product vanishes exactly when one factor vanishes; applying this twice gives a satisfying root pair. The [proof map](PROOF_MAP.md) states the remaining formal bridge to polynomial resultants and the concrete curve.

This filter operates after all four source mask pairs and their products have been selected. N131 W18 has 34,482,792,912 admissible signed pair states per rotation; the four-slot Cartesian ceiling is `1,413,870,834,644,128,097,435,064,973,990,872,350,785,536` tuples before distinct-column and target constraints. The N41 per-family timing cannot be transferred to N131 field arithmetic as a measured cost. The next experiment is an indexed two-slot extension that tests whether the public-target condition can reject entire remaining product fibers before four-tuples are formed. Freeze the positive N41 witness and same-seed controls, measure indexed probes and complete witness preservation under 180 s/4 GiB, then transfer only a successful pruning rule to the frozen N131 public Q.
