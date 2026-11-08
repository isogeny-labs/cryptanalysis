# Base-point selection, arithmetic progressions, and what `Q = [k]P` can reveal about `k` (2026-11-08)

**Kind.** Research note with a checked Lean development and an exact toy-curve
sanity check. No new measurement of record; the one measured input is quoted
from `crypto`'s generator-effect study and cited by path.

**Question (owner, 2026-11-08).** Does the choice of base point `P` on an
elliptic curve affect the hardness of recovering `k` from `Q = [k]P`? Can
arithmetic progressions, of scalars or of points, be used to derive
information about `k` from `P` and `Q`? If not, prove it in Lean.

**Answer.**

1. **Base-point choice carries no information about `k`.** For any two base
   points `P` and `P' = [c]P` of the same prime-order subgroup, a logarithm to
   one base is a logarithm to the other after multiplying by `c` or `c⁻¹ mod n`.
   Any solver for base `P'` is a solver for base `P` at the price of one
   scalar multiplication and one modular inversion. This is an algebraic
   identity, not a heuristic, and it is proved in Lean
   (`formal/BasePointIndependence.lean`, theorems `transfer`, `transfer_back`,
   `transfer_roundtrip`). The statement is about the subgroup: it says nothing
   about choosing a *different subgroup* or a *different curve*, which do change
   hardness (cofactor attacks, anomalous curves, MOV, isogeny transfers).
2. **"Impossible" is computational, not information-theoretic.** `Q`
   determines `k` uniquely when `P` has exact order `n` (Lean theorem
   `log_unique`). So no theorem can say "`Q` contains no information about
   `k`"; it contains all of it. What can be proved is that *no base point is a
   weaker lens than any other*, which is (1).
3. **Arithmetic progressions of scalars give away exactly one logarithm.** If
   `Q_i = [k + i·d]P`, then `Q_{i+1} − Q_i = [d]P` for every `i` and
   `Q_i = Q_0 + [i]D` (Lean theorems `ap_const_diff`, `ap_log_shift`,
   `ap_diff_indep_of_start`). The differences do not depend on `k`. Solving one
   DLP for `D` reveals the step `d`; the start `k` is exactly as hidden as in a
   single instance. The progression structure is a *shift*, and shifts are free
   in any group.
4. **Where progression structure does leak, it is through something other than
   the group law.** Four cases, two of them measured in this lab:
   - **Progression factor bases collapse.** A known-log base `{[1]P, …, [B]P}`
     has a pairwise sumset of at most `2B − 1` points instead of about `B²/2`
     (Lean theorem `ap_base_sum_mem`). `crypto`'s dry run measured the yield
     ratio against an abscissa base at **0.0097 [0.0074, 0.0130]** on c1 and
     **0.0092 [0.0072, 0.0126]** on c2, against a predicted `(4B+1)/r`
     (`crypto:research/generator_effect_ic_20261019/DRYRUN.md`, "Result 2";
     `[pcc:unverified]` here, the record's own receipts are in that directory).
     The toy check below reproduces the mechanism exactly: 409 distinct sums
     for `B = 205`, the bound `2B − 1`, against 21 092 for a random base.
   - **Geometric progressions do leak: Cheon's auxiliary-input problem.** Given
     `P, [k]P, [k²]P, …, [k^d]P` with `d | n − 1`, `k` is recovered in about
     `√(n/d) + √d` group operations (Cheon, EUROCRYPT 2006; literature, not in
     the lab's knowledge base this session). The contrast with (3) is the whole
     point: an arithmetic progression of scalars is an *additive* structure
     and the group law absorbs it; a geometric progression is *multiplicative*
     in the exponent and the group law does not.
   - **Progressions in protocol nonces.** If ECDSA nonces satisfy
     `k_i = k_0 + i·d` (or any known affine relation), two signatures give the
     private key by linear algebra modulo `n`; this is the related-nonce
     attack family (Bellare, Goldwasser and Micciancio, CRYPTO 1997, for
     linear-congruential DSA nonces; Howgrave-Graham and Smart 2001 and
     Nguyen and Shparlinski 2002 for partial-bit leaks via the hidden number
     problem). The leak is in the signature equation, which is linear in the
     nonce, not in the DLP.
   - **Progressions of points with partial coordinates.** The elliptic-curve
     linear congruential generator `U_i = U_0 + [i]G` *is* an arithmetic
     progression of points; given the most significant bits of a few
     consecutive `U_i`, lattice reduction recovers the sequence (Gutierrez and
     Ibeas, Des. Codes Cryptogr. 2007; Mefenza and Vergnaud 2016). This is a
     statement about coordinate bits of consecutive points, and it recovers
     the *points*, not a discrete logarithm.
5. **Coordinates along a progression look random.** Exponential-sum bounds of
   Kohel and Shparlinski (ANTS 2000) and Lange and Shparlinski (2005) show the
   `x`-coordinates of `[k]P` for `k` in an interval or progression are
   equidistributed with square-root error terms, so statistical tests on
   `x([k+i·d]P)` cannot see `k`. The toy check agrees: 16-bin chi-square 10.7
   (progression) against 22.0 (random scalars) on 4 000 points, 15 degrees of
   freedom, and lag-1 rank correlation under 0.01 in both arms.

**What this does not say.** Nothing here concerns index-calculus cost as a
function of the *curve* or the *subgroup*, which `crypto`'s E3a study found
does move with the base's cofactor classes
(`crypto:research/generator_effect_ic_20261019/README.md`). It also does not
say that a standard's `G` is "safe": the transfer identity makes `G` and a
random generator equally hard, which is also what `crypto`'s E4 measured
(every generator arm equivalent inside [0.98, 1.02],
`crypto:research/generator_effect_ic_20261019/E0_E4.md`, "Primary";
`[pcc:unverified]` here). A backdoor would have to live in the curve, not in
the point.

## Proof map

| result | Lean declaration | hypotheses | axioms used | status |
|:--|:--|:--|:--|:--|
| transfer of a logarithm to base `[c]P` | `AddCommGroupLite.transfer` | `n • P = 0`, `c·c' ≡ 1 (mod n)` | `propext` | checked |
| transfer back (solver form) | `AddCommGroupLite.transfer_back` | none | `propext` | checked |
| the two transfers are inverse | `AddCommGroupLite.transfer_roundtrip` | as `transfer` | `propext` | checked |
| `Q` determines `k` | `AddCommGroupLite.log_unique` | `P` of exact order `n`, `k₁, k₂ < n` | `propext` | checked |
| progression has constant difference | `AddCommGroupLite.ap_const_diff` | none | `propext` | checked |
| `Q_i = Q_0 + [i]D` | `AddCommGroupLite.ap_log_shift` | none | `propext` | checked |
| differences independent of the start | `AddCommGroupLite.ap_diff_indep_of_start` | none | `propext` | checked |
| progression base sumset inside `{[2]P, …, [2B]P}` | `AddCommGroupLite.ap_base_sum_mem` | `1 ≤ i, j ≤ B` | `propext`, `Quot.sound` | checked |

Statement fidelity. The group is an abstract additive commutative group
(`AddCommGroupLite`, four axioms), which every subgroup of `E(F_q)` satisfies.
Scalars are natural numbers; "`k mod n`" is handled by `smul_mod`. The order
hypothesis is `n • P = 0` (any multiple of the order) for the transfer
theorems and exact order for uniqueness. Nothing about fields, curves or
coordinates enters, which is the content of the result: the base-point
question is settled in the group alone. The sumset theorem is stated for
scalars `1..B` with the same `P` as the base generator; the symmetric base
`{±[i]P}` of the dry run gives `4B + 1` by the same argument.

Missing bridge, stated plainly: there is no Lean statement that "no efficient
algorithm extracts `k`" (that is the ECDLP assumption, unproved for any
group), and the equidistribution results of item 5 are not formalised; they
are cited and checked numerically only.

## Check receipt

`formal/check.sh` runs the pinned toolchain (`formal/lean-toolchain`,
`leanprover/lean4:v4.34.1`, no Mathlib, no Lake dependencies) and writes
`formal/RECEIPT.txt` with `lean --version`, the file's SHA-256 and every
`#print axioms` line. The committed receipt shows the standard foundations
only (`propext`, `Quot.sound`); `sorryAx` does not appear. Run on
2026-11-08 with the Lean 4.34.1 Linux release binary unpacked into the
session scratchpad (elan is not installed in this environment).

## Toy-curve sanity check

`sanity.py` (seed 20261108; `sanity.out` is its output) uses c1 of the
generator-effect dry run: `y² = x³ − 3x + 6723661` over `F_8582641`, prime
order `r = 8580037`.

| check | result |
|:--|:--|
| `[k·c⁻¹ mod r]([c]P) = [k]P`, 200 random `(k, c)` | 200 / 200 |
| `Q_{i+1} − Q_i = [d]P`, 49 consecutive differences | all equal |
| `Q_i = Q_0 + [i]D`, 50 points | all equal |
| distinct pairwise sums, progression base `B = 205` | 409 = `2B − 1` |
| distinct pairwise sums, random base `B = 205` | 21 092 of 21 115 pairs |
| 16-bin chi-square of `x([k+i·d]P)`, 4 000 points | 10.66 (df 15) |
| 16-bin chi-square of `x([k_i]P)`, `k_i` uniform | 21.95 (df 15) |

These are exact arithmetic checks of the theorems and of the sumset
mechanism, not a statistical study; the controlled-experiment rules would
apply before any distributional claim is made.

## Out-of-the-box leads worth a measured study (none started)

- **Additive vs multiplicative exponent structure as a design axis.** Item 4
  says the group law absorbs additive exponent structure and exposes
  multiplicative structure (Cheon). A systematic look at *which* scalar
  relations an attacker can exploit (`k`, `k+d`, `k·u`, `k²`, `1/k`) maps onto
  the known results: shifts and unit multiples are free and harmless, powers
  are Cheon's, inverses are the Boneh–Boyen strong-DH family. This table does
  not exist in the lab's notes and would be a cheap, fully formalisable
  addition.
- **Progression sumsets are the *right* object for a known-log base.** The
  dry run showed the progression base loses because its sumset is small. The
  dual reading is that a small sumset is a *short* representation: Freiman's
  theorem says any base whose pairwise sumset is `O(B)` is essentially a
  generalised arithmetic progression. So "which base has the largest
  sumset for its size" (the Sidon / `B_2`-set question) is the exact
  combinatorial optimum for a known-log MITM base, and `B_2`-sets of size `B`
  in `Z/n` with sumset about `B²/2` are constructible (Bose–Chowla,
  Singer). This connects the lab's known-log factor-base line to additive
  combinatorics and has not been tried here.

## Sources checked

- **Knowledge base.** The `research-kb` MCP server was not connected in this
  session and the fallback `scripts/research-kb` requires the
  `crypto-autoresearcher` and `research-kb` sibling checkouts, which are absent
  here. No `source_id` could be recorded; the literature items above are from
  memory and are labelled as such. A follow-up session with the server should
  run `search_knowledge` on "generator choice ECDLP", "random
  self-reducibility discrete logarithm", "elliptic curve linear congruential
  generator predict", "Cheon auxiliary inputs" and "known-log factor base
  sumset", and attach the ids.
- `crypto:research/generator_effect_ic_20261019/PLAN.md` §1 (the
  `(a, b) ↦ (a·c⁻¹, b)` coupling argument, the informal version of `transfer`).
- `crypto:research/generator_effect_ic_20261019/DRYRUN.md` Result 2 (the
  progression base sumset collapse, measured).
- `crypto:research/generator_effect_ic_20261019/E0_E4.md` (E4: standard `G`
  against random generators, all arms equivalent).
- `crypto:research/generator_effect_ic_20261019/README.md` (E3a: yield follows
  the base's cofactor classes, not the generator).
