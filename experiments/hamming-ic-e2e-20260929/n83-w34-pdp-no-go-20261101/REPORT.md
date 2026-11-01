---
title: "N83 W3+4,000-W4 five-summand PDP: pre-data no-go gate"
date: 2026-11-01
---

# N83 W3+4,000-W4 five-summand PDP: pre-data no-go gate

## Result

No bounded-memory experiment was admitted. This is a **derived and independently machine-checked pre-data result** for two precise algorithm families on curve `EC1N83Ckb1h2bcb59d56ad6`: (1) an exact Wagner-style quotient separator and (2) a target-independent exact pair-certificate table joined with tested concrete triples. It is **not** a proof that every structured, non-generic algebraic PDP is impossible.

The exact frozen base has `B=423,964` nonidentity projected points, `K=2,554` signed-Frobenius columns, subgroup order

```text
r = 2,417,851,639,230,796,216,685,689,
```

and `C(B+4,5)/r = 47.211114588...` five-point multisets per subgroup element on average. That average is a geometry diagnostic, not an algorithm.

The native verifier proves `r` prime with a recursive, complete-factorization Pocklington certificate. Therefore an exact quotient homomorphism on the working subgroup has kernel of order `1` or `r`: it is injective and provides no compression, or it is trivial and provides no filtering. Wagner's subgroup-chain separator does not exist here. The sign/Frobenius orbit is an automorphism fold, not such a quotient; the pair bound below grants its full ceiling of 166 concrete sums per stored certificate.

Under the frozen, deliberately generous envelope—2 GiB, 300 seconds, a bare 16 bytes per pair-orbit certificate, and an **assumed** one billion concrete triple tests per second—the pair-certificate family can resident-store at most 134,217,728 orbit entries representing at most 22,280,142,848 concrete pair sums. For a uniform target, `C` represented concrete pairs and `Q` tested concrete triples expose at most `C Q` target values, so

```text
Pr[success] <= C Q / r
            <= 6,684,042,854,400,000,000,000 / r
            < 0.002765.
```

This is 180.87 times below the frozen 50% admission threshold. Even granting all `C(B+1,2)=89,872,948,630` base-point pairs, the same triple-test cap gives success at most 0.011151, 44.84 times below admission. Reaching the 50% union-bound gate needs at least 54,260,236,474,378 concrete triple tests with the memory-limited certificate, or 13,451,498,343,428 tests with every pair. The bound is necessary, not sufficient: collisions and uneven sums can only lower coverage.

![Gate flow](gate_flow.pdf)

Editable/vector copies: [gate_flow.dot](gate_flow.dot), [gate_flow.svg](gate_flow.svg).

![Resource gap](resource_gap.pdf)

Editable/vector copies: [resource_gap.dot](resource_gap.dot), [resource_gap.svg](resource_gap.svg).

## Why the planted control was not run

The verifier includes the required positive-control sanity calculation. Select one pair certificate and one triple that the algorithm is scheduled to test, define the target as their five-point sum, and exact group replay will pass with one comparison. For a uniform target, that same comparison covers at most the 166 elements of one signed-Frobenius pair orbit, so its ordinary success probability is at most `166/r`.

Thus a planted-only run would validate arithmetic, certificate decoding, and witness replay while being non-discriminating about the failed ordinary-population gate. Freezing an `experiment.protocol/v1`, running that planted row, and stopping before ordinary queries would create the appearance of an experiment without an admissible research question. Instead, `gate_spec.json` freezes the pre-data rejection and `gate_output.json` records the native proof. There are no run IDs, witness rows, timeouts, or `experiment.export/v1` because no experiment began.

## Candidate assessment

- **Quotient/subgroup separator — rejected by a mathematical obstruction.** The subgroup order `r` is prime, so every homomorphism from the working subgroup has trivial or full kernel. This rejects Wagner's exact subgroup-chain mechanism, but not a non-homomorphic algebraic identity with a proved exact lifting rule.
- **Explicit pair certificate plus triple join — rejected under the frozen envelope.** The exact uniform-target bound is `C Q/r`, even after granting 166 concrete pairs per entry and an optimistic one billion triple tests per second.
- **Schroeppel–Shamir/dissection — not a rescue at this boundary.** These methods trade memory for repeated enumeration or guessed intermediate values. They do not supply a hidden additive label or a proper quotient here; the exact pair/triple exposure bound remains.
- **Existing S3 SAT chain — previously failed; not rerun.** The pinned-factor positive gate timed out under its frozen bound. Supplying all intermediate x-values made only a diagnostic pass.
- **Existing fixed offsets — previously rejected; not rerun.** The exact screen needs at least 899 complete four-sum offsets for the optimistic 50% gate and nearly `4.862e11` preceding states.
- **New non-generic algebraic index — open implementation gap.** No explicit low-degree/factored index with a pre-data state and operation bound was found. Absence of such a construction is not a nonexistence proof.

## Literature and prior evidence

- **Verified primary source:** David Wagner, “A Generalized Birthday Problem,” CRYPTO 2002, author-hosted full paper, <https://people.eecs.berkeley.edu/~daw/papers/genbday.html>. The paper's “Operations other than xor” section requires an efficiently computable quotient homomorphism and an appropriate normal-subgroup chain for the group-general k-tree. Its lower-bound section also separates generic-group k-sum from representation-specific algorithms. This directly motivates the prime-order quotient gate; the generic asymptotic result is not used as a fixed-base impossibility certificate.
- **Verified primary source:** Itai Dinur, Orr Dunkelman, Nathan Keller, and Adi Shamir, “Efficient Dissection of Composite Problems, with Applications to Cryptanalysis, Knapsacks, and Combinatorial Search Problems,” CRYPTO 2012, DOI [10.1007/978-3-642-32009-5_42](https://doi.org/10.1007/978-3-642-32009-5_42). The paper obtains time-memory tradeoffs by guessing/intersecting intermediate states and, for knapsack, by using known additive labels. It changes storage, not the number of exact target values exposed by a bounded pair/triple join here.
- **Verified primary source:** Isaac Goldstein, Moshe Lewenstein, and Ely Porat, “Improved Space-Time Tradeoffs for kSUM,” ESA 2018, arXiv [1807.03718](https://arxiv.org/abs/1807.03718). Its reductions use almost-linear hashes on integer sums. No such exact compressed additive hash exists on this prime subgroup without an efficiently computable discrete-log label.
- **Metadata and repository implementation checked; primary PDF inaccessible from this environment:** Igor Semaev, “Summation polynomials and the discrete logarithm problem on elliptic curves,” IACR ePrint [2004/031](https://eprint.iacr.org/2004/031). The existing checked S3 implementation and its frozen N83 failure were inspected. The inaccessible PDF is an evidence gap, not a novelty claim.
- **Measured/replayed repository evidence:** [N83_NEXT_CALCULUS.md](../N83_NEXT_CALCULUS.md), [N83_W34_SAT_GATE.md](../N83_W34_SAT_GATE.md), [N83_FULL_W4.md](../N83_FULL_W4.md), and the exact [geometry](../runs/n83_next_geometry_v1/geometry.json) and [representatives](../runs/n83_next_geometry_v1/representatives.json). Their hashes are frozen in `inputs.sha256`.

The downloaded literature copies were read for design but are not committed; the URLs and DOI identify the sources. No novelty claim is made for the union bound, Pocklington certificate, or subgroup argument.

## Revisit conditions

Reopen the experimental path only when at least one of these checkable conditions is met:

1. **A low-degree non-generic algebraic index:** provide explicit equations or a factored circuit for the exact 2,554-column prefix base, including exceptional group-law branches, with a proved count of represented pair/triple combinations and a native preflight below 2 GiB and `3e11` counted candidate tests. It must not be the already-negative SAT chain or fixed-offset scan.
2. **An exact batch certificate beyond explicit pairs:** prove that one resident state represents enough independently usable pair/triple combinations to invalidate the verifier's `C Q/r` accounting, give its decoding cost, and replay every decoded five-point witness. Merely hashing many sums into one bucket does not qualify.
3. **A changed resource envelope:** for the explicit pair/triple family, raise the counted-test cap above 54,260,236,474,378 with the present 2 GiB certificate, or materialize every pair and raise it above 13,451,498,343,428. These are only necessary 50% gates; a new protocol must still freeze ordinary public queries and controls before data.
4. **A genuinely new separator:** exhibit an efficiently computable exact additive map used by the algorithm and prove its fiber sizes on the working subgroup. Because the subgroup order is prime, it cannot be an ordinary proper quotient; any representation-specific escape needs its own theorem and implementation.

If a condition is met, the next step is a new write-once `experiment.protocol/v1`: A/A build/replay control, planted five-point control through the exact ordinary code path, frozen uniform public queries as the negative/null population, counted certificate/test metrics, 2 GiB/300-second (or explicitly amended) limits, and independent replay of every witness. Positive control runs first; ordinary rows run only after it passes.

## Reproduce the gate

From the repository root:

```sh
bash experiments/hamming-ic-e2e-20260929/n83-w34-pdp-no-go-20261101/verify.sh
```

The verifier uses native C++17 exact integers, checks the frozen input hashes, recursively verifies the subgroup primality certificate, recomputes all combinatorial/resource quantities, and byte-compares its result with `gate_output.json`.
