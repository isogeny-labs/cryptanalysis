# T-1791 independent source-fidelity review

Reviewer: `source_fidelity`. Plan: `p997-fiber-20261107-v1`, committed at `639fb3de7ae6558a8beed6c119a820edefc266b1`. Reviewed source: `927d1eada55ff51e87b89930cad48672147e0929`. Review date: 2026-11-07. No repository files were changed. The blind input and sibling reviewer reports were not read. This is a source-fidelity and finite-record replay review; the coordinator owns the fresh Lean machine gate.

## Results

All 17 seal entries match, and all 18 files in the p997 directory, including its seal, match the reviewed Git base. The archived audit passed in an isolated scratch copy and reproduced `audit.json` byte for byte. A separate integer-mod-997 reconstruction re-enumerated the cyclic chains across all 997 j-values and all ten special-twist models, recovered exactly 62 generic source classes and 1,800 paired chains, and checked 2,306 archived edge occurrences against degree-2/3 division-polynomial roots, nonbacktracking, explicit Vélu coefficients, dual roots, and j-invariants. No special twist contributed a chain pair. Direct point enumeration gave 1,008 points on each B and E, a 336-point rational dual-isogeny image with exactly three B preimages per reachable E point, and the archived 72-image histogram `{12:6,24:60,48:6}`. These checks passed.

The five Lean declarations faithfully express conditional arithmetic at the stated scope. They do not define a modular curve, morphism, reduction, chain census, or finite source-to-B assignment. The full-image interval 79–217 and complement 791–929 are supported conditionally on the prior normalized degree-24 modular-map/reduction identity and cusp-image theorem. The archived p997 audit itself does not prove those bridges. The producer explicitly marks this limitation in RESULT.md:76–81.

## Source-to-claim map

All unqualified local paths below are relative to the reviewed repository.

| Claim | Load-bearing source and check | Verdict |
| --- | --- | --- |
| p997 artifact custody | `SEAL.sha256`:1–17; fresh `seal-check.stdout`; `base-input-comparison.json` | holds: 17/17 seal checks and 18/18 base-file equality |
| 62 generic classes, 1,800 paired chains | `census.json` full rows; `census_sage.py`:23–34,45–79; imported `hecke-432-stable-kernel-chains-20261025/enumerate_chains_sage.py`:15–34; fresh `finite-source-recheck.json` | holds at finite-chain implementation scope; 2,306 raw edges checked, source j and traces checked, every represented path set reproduced, all j values reconstructed |
| Hecke trace −838; total 1,836 | `census.json` metadata; `census_sage.py`:72–79; p937 `screen_result.json`:4–9 and `screen_next_prime_sage.py`:21–33 | inconclusive as a fresh Hecke computation: recorded twice by code using Sage CuspForms, but no fresh modular-symbols/Hecke trace run was performed here; arithmetic 997+1−(−838)=1836 holds |
| 36 rational cusps | `audit.py`:56–61 and p937 screen code:15–17; exact denominator/unit formula freshly replayed | holds as formula evaluation; geometric interpretation uses the established cusp criterion |
| 72 recorded E outputs, histogram 12×6 / 24×60 / 48×6 | complete `image.json` rows; `audit.py`:66–90,113–115; own counter over all rows | holds as an archived-record fact; 1,800 row keys align with the census |
| Three rational B preimages per recorded E output | `image.json` candidate sets; `audit.py`:73–86; independent enumeration of every B point in `finite_source_recheck.py` | holds; saved sets equal the full inverse-image sets, not merely three matching examples |
| Recorded E output is the quarter-shift projection of that source | `evaluate_sage.py`:31–110; j3/j9 selection at70–73, Frobenius checks84–95; imported kernel and coordinate helpers; exact intermediate-map hash | source implementation is present and coherent, but fresh full quarter-shift/Sage reevaluation was not done; inconclusive for independent numerical reexecution of this bridge |
| A 12-source E fiber forces a partial positive B fiber | `Prime997FiberSaturation.lean`:18–21 | holds as arithmetic implication from a+b+c=12; concrete application requires an actual map whose three B-fiber counts sum to the projected count |
| A 72-source E fiber saturates three capped lifts | Lean:10–14 | holds conditionally on each cap24 and sum72; no actual 72-source E fiber occurs in this archive |
| A 48-source E fiber needs two positive capped lifts | Lean:23–27 | holds conditionally on each cap24 and sum48 |
| Histogram lower-bound arithmetic78 | Lean:29–30; audit:92 | holds as arithmetic; the lemma is a closed numeral equality and proves no cardinality theorem |
| Noncuspidal B interval78–216 | RESULT:56–62; audit:92–93; all preimage cosets disjoint over distinct E points | holds conditionally on the degree24 source-fiber cap and concrete map decomposition |
| Full B interval79–217 | RESULT:14–21,63–64; audit:100–102 | holds conditionally on the preceding bridge and all rational cusps mapping to B identity; audit only checks absence of E identity from noncuspidal rows and adds1 |
| Complement791–929 | Lean:32–35; audit:121–122; enumerated B order1008 | holds conditionally on full-image bounds; `complement_bounds` assumes those bounds |
| No exact B image count is forced by archived projection alone | RESULT:20–21,92–95; `compatible-lift-assignments.json` | holds; two explicit assignments obey the same cosets, projected counts and cap24 while using78 versus216 noncuspidal B points |
| Protocol was frozen before both producers ran | protocol:2–3 and Git history below | inconclusive as authenticated timing; declaration is present, but protocol and outputs entered Git together |

## Geometric and implementation bridges

1. **Chain-to-X0 point interpretation.** The finite-chain recheck validates the archived chains and exhaustive all-j arithmetic. Identifying these pairs with distinct noncuspidal X0(432)(F997) points uses the standard moduli interpretation and the generic quadratic-twist quotient. All contributing classes are generic; the extra-automorphism special classes contribute zero. The independent archived Hecke equality corroborates the expected cardinality but was not freshly recomputed here.
2. **Coordinates and intermediate invariants.** The evaluator uses `hecke-27-coordinate-bridge-20261025/coordinate_map.json`, `kernel-transport` chain reconstruction, and sealed `intermediate_j.json`. Its local source explicitly filters by both j3 and j9 and demands one point per shift. The saved rows retain counts, E outputs and B candidates, but not Pplus/Pminus, pushed polynomials, or intermediate j-values. The Python audit trusts the saved filter counts rather than recalculating these constructions.
3. **Normalized modular-map identity and degree.** The p997 prose appeals to a known degree24 normalized map. The earlier `hecke-432-map-identity-20261025/RESULT.md` supplies a written Sturm/differential argument, links modular degree24 to the LMFDB record, and explicitly leaves Lean modular-curve/Sturm formalization open. This earlier result was read for provenance, not independently replayed in this review. The p997 audit hardcodes24 at lines92–93 and does not verify degree or good reduction.
4. **Cusp identity.** The earlier map-identity report invokes a cusp-field/torsion control and Manin–Drinfeld for normalized cusp images. The p997 audit computes how many cusps are rational, but never evaluates their B images. Its `+1` at102 relies on that prior theorem. Absence of E identity among the saved noncuspidal E outputs is freshly checked.
5. **Source-dependent choice of B lift.** Every row retains the full three-point candidate coset. No source-dependent B-point selector is present. This is precisely the remaining exact-image calculation named by the producer; neither the arithmetic lemmas nor histogram replaces it.

## Attacks and nearby false or widened claims

The archived audit is a consistency audit, and the following widened readings fail with explicit scratch controls in `boundary-controls.json`:

- It is false that an audit pass validates every source isogeny edge. Changing `census.rows[0].two_paths[0][0].kernel_x` from605 to606 gives degree-two division-polynomial residual722, yet the archived audit exits0. The original root605 passes the separate finite-source recheck.
- It is false that an audit pass checks source j metadata. Changing `image.rows[0].source_j` from17 to0 still exits0 because source matching uses `(source_ainvs,pair)` at audit:46–52. The unmodified j metadata passed the independent recheck.
- It is false that an audit pass independently recomputes each source's projection. Swapping the complete E/coset values between source rows0 and1 keeps every check and histogram passing. The archive has no independent per-row quarter-shift reconstruction in audit.py.
- It is false that the projected histogram alone selects the concrete B image. `compatible-lift-assignments.json` gives explicit per-coset allocations at both endpoints78 and216. Both respect all observed source totals and the cap24. These are combinatorial compatibility witnesses, not claims to construct modular maps realizing either endpoint.
- The probe has status `COMPLETE_F997_E_PROJECTION` but only5 rows. The evaluator uses this same status under `--limit` (lines125–139); the full audit's row-key and cardinality checks reject substituting it for the full image. Status text alone is insufficient evidence of completion.

These controls identify limits of the audit and prevent wider claims. They do not refute the original unmodified census or the stated conditional bounds.

## Protocol and dependency provenance

`screen_result.json` first entered Git in `7deed84b3f596868999a120285bd5c5957b4016a`, authored/committed 2026-10-25T16:37:18−07:00 =23:37:18Z. The protocol records freeze23:38:31Z. The p997 protocol, census, image and seal entered Git together in `c52366084d022bb755c83533c12a1ef5a14c00a8`, authored/committed16:43:47−07:00 =23:43:47Z. Thus selection of997 is prior-committed, while separate pre-execution publication of the p997 protocol is not established by Git history. The fixed rule and first selected candidate agree; this is an exhaustive census, not a timing comparison.

The local seal binds all p997 payloads and the Lean dependency declaration, but excludes external `screen_result.json`, coordinate_map.json and imported Python helpers. `protocol.json` pins only intermediate_j by hash. Extraction from reviewed Git base now binds the missing external bytes for this replay, but does not retroactively establish their pre-execution pins. Original Sage scripts also contain fixed macOS runtime/cache paths. No new Sage launch or cloud work occurred.

The Lean toolchain is v4.35.0-rc4 and declared mathlib revision021c46bdd042f67b538b9f9871d556a93713a9a9. The archived command uses absolute macOS paths and the retained axiom log lists only propext/Classical.choice/Quot.sound. These checked hashes preserve the archived evidence; its text does not authenticate execution. Fresh declaration compilation and transitive axiom audit are coordinator-owned in the current review.

## Replay records and unresolved obligations

`audit-replay-receipt.json` records exact command, scratch working directory, exit0, pre/post input hashes, exclusive resource lock, one CPU, CPU30s/address-space512MiB/wall60s limits. Elapsed audit time was approximately0.054s; this is a replay receipt, not a performance result. The scratch audit output was byte-identical to the sealed audit.json. `finite_source_recheck.py` and `finite-source-recheck.json` retain the additional finite reconstruction. Source/reviewer output was never written into the reviewed repository.

Unresolved obligations are: fresh full Sage source-to-quarter-shift projection reevaluation; fresh independent Hecke trace; faithful formal objects for modular map/reduction/census and their required bridges; fresh review of prior Sturm/degree/cusp proofs if the review intends to certify those dependencies; source-dependent B lift extraction for an exact image; authenticated pre-execution protocol timing if that historical process claim is to be promoted. The coordinator's fresh Lean gate remains separate from this report.

Complete actual source access is listed in `sources-read.json`, distinguishing full semantic reads, byte/hash-only reads, and grep-only snippets. No sibling-report access occurred. Blind algebra rederivation was neither attempted nor claimed by this reviewer.
