# Rational degree-2 isogeny: ECDLP transfer audit (2026-11-18)

**Standing:** [pcc:unverified]. These are deterministic producer-local enumerations and replay assertions, not an independent signed PCC theorem, measurement, execution or speedup verdict.

## 3–6 line result

**Hypothesis:** A classical separable 2-isogeny transports an odd-prime subgroup logarithm, but cannot smooth the prime-order factor by changing coordinates alone.  
**Method:** Enumerate both F_1009 groups, evaluate maps and dual on every source point, exhaust all 491² source-subgroup pair laws, reconstruct 491 inverses, solve 64 planted DLPs with matched affine BSGS and field-operation counters.  
**Result:** Both groups have order 982=2·491; source-to-target kernel has size two and image size 491; all 64 logs recover. Transport adds 128 modular inversions and 384 modular multiplications compared with the same BSGS on the original group.  
**Verdict:** Classical subgroup transport **passes**, an inverse on the whole group **fails** (2-to-1), and cheaper solving through this transformation **fails** for the measured solver; not a new attack.  
**Next discriminating step:** Only compare an isogeny path with a specified, demonstrably cheaper destination solving algorithm, including the map, inversion or log-backtransport, verification, setup and matched rho costs.

## Explicit obligations

| Obligation | Pass/fail and precise scope |
|---|---|
| Non-singular source and target | **PASS** — b=13≠0; a²−4b=69≠0 mod 1009; targets count 982 |
| Rational source and target cardinality | **PASS (exhaustive toy enumeration)** — #E(F_1009)=#E'(F_1009)=982 |
| 2-isogeny subgroup homomorphism | **PASS (exhaustive on H)** — 491²=241,081 ordered pairs; image points on target |
| Kernel and global image | **PASS** — ker(phi)={O,(0,0)}, image size 491; exactly two rational preimages per image point |
| Source odd-prime subgroup preservation | **PASS** — H=<G>, G=(849,405), ord(G)=491, image phi(H) has order 491 and is injective |
| Map forward cost | **PASS (accounted)** — per non-kernel map: one field inverse, three multiplies, one square, three field adds/subtracts; the exact affine implementation counts these |
| Dual map / composition | **PASS** — psi(phi(P))=[2]P for all 982 source points; psi includes X/4,Y/8 scaling; two constant inverse precomputations not charged to per-query table |
| Inverse on H | **PASS** — phi|H inverse is [246]psi; recovered all 491 subgroup points; optionally measured per-sample cost included below |
| Inverse on full E(F_1009) | **FAIL (mathematical obstruction)** — degree-two kernel makes phi two-to-one; no single-valued group inverse on the full group |
| Target group smoothness improvement | **FAIL** — 982=2·491 on both curves; largest prime 491 unchanged; transport does not change prime-order DLP hardness |
| Log recovery on source | **PASS (producer-local)** — source and transformed matched BSGS both recovered 64/64 planted k, with original-curve [k]G=Q checks |
| Complete transformation cheaper | **FAIL for this measured BSGS route** — identical group operations, more field operations from mapping; no setup/solver advantage found |
| Asymptotic ECDLP breakthrough | **NOT ESTABLISHED** — standard isogeny and group operation counts; no mathematical speedup theorem or scaling data |
| Independent signed certification | **PENDING** — replay is producer-authored; no CI-main PCC signed standing, independent implementation or tamper-proof runtime attestation |

The target map is phi(x,y)=(x+11+13/x, y(13/x²−1)), with phi(O)=phi(0,0)=O.
The target is E': y²=x³−22x²+69x.
The dual is computed by applying the corresponding 2-isogeny on E' and scaling x by 4⁻¹ and y by 8⁻¹.
Because psi∘phi=[2] and 2 is invertible mod 491, the inverse on H exists even though no global inverse exists.

## Counted solver costs — 64 solved examples

All rows use the **same** 64 exponents, the same BSGS baby-step width 23 and exact source-point verification. The transformed case maps **both** G and Q per instance. No map cost is hidden in the solver. The optional point inverse is not necessary to extract k and is therefore shown separately.

| Charged primitive | Direct BSGS | phi + target BSGS | Optional [246]psi(Q') |
|---|---:|---:|---:|
| Ordinary group adds | 2,352 | 2,352 | 320 |
| Group doubles | 746 | 746 | 448 |
| Identity cases | 195 | 195 | 64 |
| Field adds/subs | 21,686 | 22,070 | 5,568 |
| Field multiplies | 8,434 | 8,818 | 3,200 |
| Field squares | 3,844 | 3,972 | 1,280 |
| Field inversions | 3,098 | 3,226 | 832 |
| Forward phi calls | 0 | 128 | 64 (internal to psi) |
| Dual psi calls | 0 | 0 | 64 |

Per DLP, phi+target BSGS costs exactly **2 additional inversions, 6 multiplies, 2 squares and 6 adds/subs**, with no reduction in group calls. The optional inverse costs a further 13 inversions, 5 ordinary additions and 7 doubles per example in this implementation. Two shared inverse constants 1/4 and 1/8 are setup work excluded from the table. The full 982-point census, formula discovery, curve coefficient construction, Python dispatch, hash-table lookup, memory, allocations and program startup are not charged; this is **not** a cold end-to-end wall-clock comparison and not a stage promotion into the IC leaderboard.

The standard Pollard-rho birthday heuristic sqrt(pi*r/2) with r=491 gives ~27.77 expected group-walk steps. Direct BSGS here charges 3,098 nontrivial group operations/64=48.406 per solved example including original log verification, plus identity cases. Comparing these numbers is **context only**, not a measured matched rho implementation. BSGS has O(sqrt(r)) group operations and O(sqrt(r)) memory; the isogeny overhead adds O(log p) field operations per input at constant degree. Nothing here changes the exponent.

## Replay, audit, and falsification

```bash
python3 experiments/examine-2isogeny-20261118/replay.py --out /tmp/2isog-RESULTS.json
python3 experiments/examine-2isogeny-20261118/replay.py --verify-json /tmp/2isog-RESULTS.json
# The committed RESULTS_SUMMARY.json records seed, all 64 k, per-row inversion costs,
# all primitive totals, and hashes of replay.py and the full local output.
```

* Fixed seed **20261118**; all 64 logs and per-example inversion counts are in `RESULTS_SUMMARY.json`. Replaying `replay.py` produces the entire unabridged JSON (64 rows, all counters and asserts) deterministically.
* Script exact SHA-256: `a3c393e966d65fbdf55edf58dd2ef03e5703da02fcce71def82386893348254a`.
* Local full output exact SHA-256: `7423fa32d660a86d49f4f86f20755e515a3133a362238934ba81a639b7208bed`.
* Deliberately changing the first row's recovered transferred log by +1 made replay comparison exit nonzero with `FAIL: JSON replay mismatch`; this is only a producer-local mutation test, not independent verification.

## Existing mechanisms and sources checked

* Classical 2-isogeny/dual baseline: Silverman, *Arithmetic of Elliptic Curves*, Chapter X §4; a worked explicit presentation is in [the paper on y²=x³−pqx](https://onlinelibrary.wiley.com/doi/10.1155/2014/825634), §2; general [Vélu formula overview / original Sage source](https://sources.debian.org/src/sagemath/8.6-6/sage/src/sage/schemes/elliptic_curves/ell_curve_isogeny.py).
* The repository already has an ell=2 Vélu constructor in [`suite/src/isogeny/velu.rs`](../../suite/src/isogeny/velu.rs), and a larger [transfer-audit incompleteness problem](../../problems/transfer-audit-completeness.md). This experiment is a toy regression, not a proposed first or newly discovered mechanism.
* Closure map scanned: [`crypto/research/ic_mega_pass_20261031/brief/BRIEF.md`](https://github.com/isogeny-labs/crypto/blob/main/research/ic_mega_pass_20261031/brief/BRIEF.md), [`report/REPORT.md`](https://github.com/isogeny-labs/crypto/blob/main/research/ic_mega_pass_20261031/report/REPORT.md), and the transfer lead atlas directory. Individual atlas YAML fetches failed as non-UTF8/encoded content; these sources were **not** treated as independently read or as negative novelty evidence.
* Cross-repository research-KB and Conductor claim-work tools were not exposed in this automation runtime; branch `research/examine-2isogeny-obligations-20261118` avoids touching pre-existing experiment lanes. PCC creation/signature and an external implementation remain open.

**Outcome classification:** known math / local **EMPIRICAL** exhaustive toy check / no cryptographic-scale conclusion. [pcc:unverified]
