# CT38 — rational shadow versus geometric 7-kernel certification

**2026-11-12 · [pcc:unverified].** A bounded, independent negative-control audit for the fixed F101 two-factor Jacobian transfer fixture. This is classical abelian-variety theory, not a new attack or theorem.

## Precise observation and proof

Let `k=F101`, and let `f:A→B` be any isogeny of abelian surfaces over `k` whose target has `|B(k)|=N=12,317=109·113`. This includes the product of `E109:y²=x³+x+46` and `E113:y²=x³+44x+21`, as well as the fixed isogenous genus-2 Jacobian targets (assuming their verified rational order). Write `[m]` for multiplication on `B`.

Choose `K=101·N=1,244,017`, `m1=1+K=1,244,018` and `m0=1+4K=4,976,069`. Then:

1. **All rational images coincide.** Every `b∈B(k)` obeys `[N]b=0`, hence `[m1]b=[m0]b=b`. Thus `f`, `[m1]∘f` and `[m0]∘f` agree on **every rational source class**, every rational addition-table entry, and every roundtrip checked only through rational classes.
2. **Their first-order differential is identical.** `d[m]` on the tangent space is multiplication by `m mod 101`; both multipliers equal 1 modulo 101. Their composites have exactly the same differential as `f`.
3. **Their geometric 7-primary behavior differs.** `m1≡6≡−1 (mod 7)` but `m0≡0 (mod 7)`. On `B[7](kbar) ≅ (Z/7Z)^4`, the first is negation, the second is zero. The latter kills all `7⁴=2,401` geometric 7-torsion points. Both multiplications are separable since `101∤m`. Their degrees are `m^4` (dimension 2); they are not equal to the intended degree-49/2401 transfers.

Because an isogeny `f` is geometrically surjective, `[m0]∘f` has genuinely additional kernel points beyond `ker(f)`. This proves that even the entire 12,317-class rational corpus **plus tangent normalization** cannot, in isolation, certify a prescribed geometric kernel or degree. [pcc:unverified]

**Essential limitation:** The actual existing independent degree-49/2401 or degree-bounded quartic identification certificates, if rigorously established, **reject** this high-degree impostor. CT38 does not claim the native map is defective or contradict the degree-bounded CT28 cube-identity argument. Its point is to keep the independent geometric certificates as distinct requirements; full rational testing must not be promoted to proof of them.

## Executed bounded controls (local, unsigned)

Two independently written standard-library implementations, Python and Go, enumerate the exact 109 and 113 rational points, verify all their scalar orders, then check both multipliers on **all 222** elliptic rational points. Thus all `109·113=12,317` product pairs are fixed coordinatewise. The deliberate bad multiplier `102` changes **all 220 nonidentity** points. The Python oracle additionally verifies roots of the Frobenius characteristic polynomials mod 7, `(2,5)` and `(4,6)`. Python ordinary and optimized modes produce byte-identical output and `py_compile` succeeds. The `7⁴` geometric group is a theorem, not a field-extension enumeration. [pcc:unverified]

```sh
python3 -B experiments/chained-transfer-reference/ct38/ct38_rational_shadow.py > /tmp/ct38.normal
python3 -O -B experiments/chained-transfer-reference/ct38/ct38_rational_shadow.py > /tmp/ct38.optimized
diff -u /tmp/ct38.normal /tmp/ct38.optimized
python3 -m py_compile experiments/chained-transfer-reference/ct38/ct38_rational_shadow.py
go run experiments/chained-transfer-reference/ct38/ct38_shadow_independent.go
```

Local hashes: Python source SHA256 `22223a1dc8d0b64dda4017376a7d78404b3c5c45857b2bc7bad59826ff4ac927`; Python stdout `a746d12a4874ff29ae8e70df9456b2974b54eafd60d3d2e0125fb0847e06f798`; Go source `46860504da6cf7a82aa987aa0dcf97433768803d3a0263e482314b56259c3f51`; Go stdout `6f8feb001db4d461c1b995b38b4a5c9bf9f55472aa3965b6622588ce5c802359`. These are producer receipts, **not PCC signed verdicts**.

## What must be checked before certifying the real transfers

- Independently establish exact genus-2 isogeny degree, geometric 7-primary kernel and universal dual/Picard composition, including normalization.
- Keep separate complete 12,317-class Cantor replay with nonsplit, repeated, ramified, finite-pole and infinity cases; these tests remain valuable.
- Require separately admitted matched complete-cost benchmarks to compare any full DLP advantage; no speedup or EKS/cloud expenditure here.

The current whole-prime-field forward evaluator is already being integrated in `crypto#3877` and `cryptanalysis#1505`; this audit deliberately does not modify its frozen source. No merge gates bypassed. [pcc:unverified]

## Primary sources / fallback

- `crypto:research/chained_jacobian_transfers_20261110/PRIME_FIELD_CHECKPOINT.md` and `INTEGRATION_HANDOFF.md`.
- `cryptanalysis:experiments/chained-transfer-reference/ct37/CT37_FROBENIUS_ISOTYPY.md` (factor models and counts), and CT36's independently checked rational-function duals.
- J. S. Milne, *Abelian Varieties*, §§8 and 12, https://jmilne.org/math/xnotes/AVs.html (multiplication endomorphisms, isogeny degree and tangent maps).
- Root `QUARTIC_COVER_PROOF.md` (degree-bounded identification; the present impostor lies outside its hypotheses).

The shared research-KB MCP and local CLI and the encrypted autoresearcher atlas were unavailable in this runtime. GitHub source, the current AGENTS.md/session log, and Milne's classical treatment were used as fallback; no exhaustive novelty/absence statement. [pcc:unverified]
