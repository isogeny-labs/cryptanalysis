# Measured finding: the PKM prime-field tower does NOT give a sub-√p oracle (B1 dead as posed)

**Status:** result from the lab's OWN measured data, reconciling both Mythos reads. Every
number [pcc:unverified] (one engine/host per the repo's own disclaimer). Source:
`isogeny-labs/lfd-summation-systems/experiments/ic-solving-degree/rows-merged.jsonl`
(5,818 settled systems) + repo README bounds (LFD≥7 for m=3; LFD≤mk+1 all m).

## The question (reduced)
Both subagents reduced every sub-√p claim to one measurable quantity: does the
per-decomposition **solving degree (LFD = Caminata–Gorla solving degree)** stay BOUNDED as
the tower height k grows, or grow with k? Factor base = μ_{2^k} ⊂ F_p*, so N=|V|=2^k;
the balanced index-calculus point is N≈p^{1/m} ⇒ k≈(log₂p)/m, #vars ≈ mk ≈ log₂p.

## Measured growth law  LFD(m,k), prime family
| m | k range | measured LFD | slope dLFD/dk | law | verdict |
|--:|--------:|-------------:|-------------:|----|--------|
| 2 | 1..14 | 3,4,4,4,4,5,5,5,5,6,6,6,6,7 | 0.25 | ~k/4 | sublinear |
| 3 | 1..4  | 4,7,7,7 | ~0 in window (→8 at k=6) | ~const/k-quarter | BOUNDED-ish |
| 4 | 1..4  | 5,9,13,13 | 2.8 | **mk+1** | linear, saturates cap |
| 5 | 1..4  | 6,11,16,21 | 5.0 | **mk+1 (exact)** | linear, saturates cap |
| 6 | 1..4  | 7,13,19,25 | 6.0 | **mk+1 (exact)** | linear, saturates cap |
| 7 | 1..3  | 8,15,22 | 7.0 | **mk+1 (exact)** | linear, saturates cap |
| 8 | 1..3  | 9,17,25 | 8.0 | **mk+1 (exact)** | linear, saturates cap |

For m≥5 the measured LFD equals the proven upper bound mk+1 on every cell — solving degree
grows **linearly in k with slope ≈ m**, i.e. maximally.

## Contrast that nails the mechanism (binary family, same table)
| m | k range | measured LFD | verdict |
|--:|--------:|-------------:|--------|
| 3 | 2..7 | 6,7,7,7,7,7 | BOUNDED (flat 7) |
| 4 | 2..5 | 8,12,13,9 | bounded/non-monotone |
Binary stays bounded through m=4; prime does not past m=3. That is exactly the Frobenius /
Weil-descent structure extension fields have and F_p lacks — the same asymmetry the frontier
repo's exp6 measured directly (S₃(x₁,x₂,x(R))=0 has ≈p solutions over F_p, ≤16 over F_{p²}).

## Exponent implication
- LFD bounded (O(1) in k) ⇒ #monomials ≈ (mk)^{O(1)} = polylog(p) ⇒ poly(log p) oracle ⇒
  sub-√p possible. **Seen only at m=3** (and m=3 gives index-calculus exponent ≥ 1/2 — cannot
  beat rho regardless).
- LFD = mk+1 (linear) ⇒ D ≈ mk ≈ log₂p ⇒ #monomials ≈ C(2mk, mk) ≈ p² ⇒ per-decomposition
  Macaulay cost ≈ (p²)^ω ≫ p^{1/2}. **Seen at every arity m≥5 that a sub-√p exponent needs.**

**Conclusion.** The one arity whose oracle degree is bounded (m=3) is exactly the one that
cannot beat √p; the arities that could (m≥5) have solving degree pinned to the mk+1 cap. On
this measured evidence the PKM two-power-subgroup tower does **not** furnish the p-independent
/ polylog-degree decomposition oracle a sub-√p exponent requires. **Lead B1 is dead as posed.**
This is the clean, publishable negative result M2 put at 70% and M1 made the top-ranked
decider ("read the step degrees") — now settled on the lab's own data.

## What would overturn it (falsifiers kept open)
1. A different prime-field presentation (not the two-power subgroup chain) whose measured LFD
   is bounded at m≥5 — none known; the "split" / System-(4) presentations are in-repo to test.
2. The short high-m lever (k≤4) hiding a plateau: extend m=5 to k=5,6 (one `msum-growth` cell
   each) and check it leaves the mk+1 line. Prediction: it does not.
3. The rigorous exponent step: feed LFD=mk+1 into `experiments/ic-costmodel` and confirm the
   IC/rho crossover p* does not exist below cryptographic sizes. (Next experiment.)
