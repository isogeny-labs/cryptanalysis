# CT165 — Abstract group obstruction to prime-field ECDLP transfers into fixed-nu12 k-rational carriers

2026-11-16 · **[pcc:unverified]** · Local finite-arithmetic audit, NOT signed independent PCC.

## Result (source-specific, stronger than an algebraic Hom obstruction)

Let `k = F_223`, `K = F_(223^3)`. CT160's actual fixed-nu12 source and target elliptic curves over K each have `#E'(K) = 11,086,844 = 4 * 2,771,711`. Let `A = Res_(K/k)(E')`, and let `B/k` be **any** abelian variety k-isogenous to A (including a genuinely constructed quotient corresponding to any CT163 Frobenius-stable kernel). Weil restriction gives `#A(k) = #E'(K)`; a k-isogeny preserves the zeta/Frobenius polynomial and hence `#B(k)=#A(k)`.

For **every** elliptic curve `E/k` and **every abstract group homomorphism** `f:E(k)->B(k)`, the image has order **at most 4**, and is 2-primary. In particular, for every odd prime `ell` dividing `#E(k)`, `f|E(k)[ell] = 0`. No injective scalar-preserving transfer on any odd-prime-order ECDLP subgroup of E(k) can land in B(k). **The statement does not assume f is algebraic**, unlike CT151/CT161.

This is an elementary finite-group no-go for these **fixed** targets, not a universal cross-characteristic, higher-genus, or computational-map impossibility theorem. [pcc:unverified]

## Exact proof

The Hasse bound implies `|#E(k)-(223+1)| <= 2 sqrt(223)`, so every possible integer `m=#E(k)` belongs to the 59 integers `195..253`, inclusive. Complete trial division certifies that 2,771,711 is prime. Since this prime is greater than 253, `gcd(m,11,086,844)` is a power of two and at most four. A homomorphism image is a quotient of E(k) and a subgroup of B(k); Lagrange's theorem makes its order divide both group orders. Thus no image can have nonzero odd-order elements.

The exhaustive **necessary-order** census, including integer values not realized as elliptic-curve orders, gives:

| gcd(m,11,086,844) | Eligible m values |
|---|---:|
| 1 | 30 |
| 2 | 14 |
| 4 | 15 |
| other | 0 |

This proves the bound uniformly over every actual E/k. For source-order `ell` odd, a scalar-preserving map on a cyclic order-`ell` subgroup is a homomorphism there, and its image must be zero. Even if its behavior elsewhere is nonlinear, the same obstruction applies to that subgroup.

## Source identity and independent checks

Four existing immutable files were read by exact Git **blob SHA** from the current PR branch: `CT160_FULL_CENSUS.json` (`9a8fb444...`), `CT160_GENERATOR_AUDIT.json` (`84086b49...`), `CT163_RESULT.json` (`1b93b009...`), and `CT164_RESULT.json` (`e9f7fafe...`). These supply the actual fixed elliptic orders and the nine prospective stable quotient kernels; they are not evidence that six mixed quotients are explicit Jacobians.

The independently written Python and JavaScript scanners recompute the Hasse interval using distinct integer-square-root methods, factor 2,771,711, bind all four original JSON inputs to their Git blob hashes, and recompute each gcd using independent algorithms. Both locally emitted **byte-identical canonical JSON**, with Python normal and `-O` agreeing. Each checked seven directed negative-control mutations (changed counts, altered prime factor, missing/rebound kernels, wrong quotient order, and boolean-as-integer). Frozen emitted local JSON SHA256: `92b863ed712c6d1cb81a9accf24463a4d8c592af2d30489bc2d6c1e093ff49eb`.

Prospective fixture binding and dual replay followed the CT165 written protocol. The earlier preliminary local gcd/factor observation **preceded** that protocol, so prospective status is not misrepresented. These were local producer-created implementations, not an independent PCC signature. Current-head hosted CI must be inspected separately. [pcc:unverified]

## Reproducible commands

From `cryptanalysis` checkout:

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 -S "$D/ct165_group_no_go.py" --fixtures "$D" --self-test
python3 -O -S "$D/ct165_group_no_go.py" --fixtures "$D" --self-test
node "$D/ct165_independent.mjs" "$D"
```

Compare exact canonical output bytes. No changes to CT160–164 original fixtures or native Rust, PCC ledger, cost measurements or owner compute.

## Implications and next discriminator

A Jacobian k-isogenous to these fixed nu12 Weil restrictions cannot be the **k-rational output group** for an odd-prime-order **prime-field** ECDLP transfer, irrespective of how an abstract group hom is implemented. This strengthens CT161's algebraic `Hom_k(E,B)=0` for the specified group-level direction. The obstruction does **not** rule out `B(k^d)`, transfer into a different Frobenius/isogeny class whose order shares the source's subgroup prime, or other computational representations. It also does not rule out a complete extension-field DLP algorithm operating on E'(K).

Prior work reviewed: CT160 original finite point count and generator audit; CT161 Weil polynomial simplicity/Hom theorem; CT163/164 kernel and 2-primary screens; the bielliptic genus-2 and P-256 explicit higher-genus covers already in crypto (avoid duplicating those maps); Hasse's standard theorem and Lagrange's subgroup theorem. Shared research-KB/Conductor unavailable in this connector environment; no novelty claim.

**Change of direction:** do not expend native pricing or smooth-genus-3 construction effort claiming the current k-rational fixed nu12 class solves E(F223) odd-primary inputs. The existing owner-admitted 695/701 original/reuse native replay and genuine C169/C13a/C13b/D costs remain valuable for **extension-field source/transfer characterization** and must be measured separately once approved. For a prime-field ECDLP advantage, first certify a target `B(k)` with matching `ell`-primary order and an explicit scalar-blind injective map; then run identical complete cold rho/BSGS/IC and transferred solves with full setup, correction, linear algebra, verification, memory and confidence intervals. Until then there is no measured prime-field end-to-end advantage. [pcc:unverified]
