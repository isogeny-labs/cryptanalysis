# CT152 — Full independent original q223 cubic-source point census

16 November 2026 UTC. **[pcc:unverified]**; developer-local exhaustively executed and hosted source-only replay pending. This removes the **reported point-count assumption for the original source model** in CT150/CT151, conditional only on matching the deterministic original Rust source selection; not a complete DLP or a signed independent scientific PCC.

## Actual q223 source recovered

The original Rust `CheckedInstance::construct()` calls `Inst::search(223,1,200000)`. We separately translated the original field, RNG, Hasse interval candidate search, elliptic group arithmetic and Frobenius into standalone Python (no Rust producer imports) and obtained its first qualifying candidate at **trial 91**, matching the original published instance roster.

Define `K=F_223[z]/(z^3-3)`, where `z^223 = 183z`. The original source equation is

```
E/K:  y^2 = x^3 + a2*x^2 + a4*x + a6
a2 = 127 + 56*z + 199*z^2
a4 = 152 + 35*z + 36*z^2
a6 = 212 + 109*z + 150*z^2
G  = (162+197*z+140*z^2, 45+11*z+207*z^2)
ell = 2773073
```

Standalone Python checks that the field modulus is irreducible, the enumerated generator belongs to the equation and `[ell]G=O` with prime `ell`; it separately checks the unique group-order multiple in the Hasse interval. Four controlled mutations (ell, a6, generator, trial number) are rejected by checks that do not use Python `assert`.

## Distinct independent exhaustive counting engine

A separate C++17 program (no Rust/Python imports and no elliptic scalar multiplication) represents `K` as three coefficients and implements multiplication by a generic five-coefficient convolution reduced modulo `z^3-3`. It independently squares **every** field element to populate the image of the squaring map, then evaluates the cubic RHS on **every** field x-coordinate, partitioning the RHS into 0, nonzero squares, and nonsquares.

| Exact integer invariant | Original-source count |
| --- | ---: |
| Field size / x values enumerated | 11,089,567 |
| Distinct square residues including zero | 5,544,784 |
| RHS zero | 3 |
| RHS nonzero square | 5,546,144 |
| RHS nonsquare | 5,543,420 |
| Points including infinity | **11,092,292** |
| Prime-order subgroup / full order | 2,773,073 / 4×2,773,073 |

All three RHS bins add to 11,089,567. The full count follows exactly as `1 + 3 + 2*5,546,144 = 11,092,292`.

Developer-local source replay:

```bash
D=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 "$D/ct152_reconstruct_original.py" --self-test-negative > /tmp/ct152-a.json
python3 -O "$D/ct152_reconstruct_original.py" --self-test-negative > /tmp/ct152-b.json
cmp /tmp/ct152-a.json /tmp/ct152-b.json
g++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct152_exhaustive_pointcount.cpp" -o /tmp/ct152-census
/usr/bin/time -f 'wall=%e maxrss=%MKiB' /tmp/ct152-census > /tmp/ct152-c1.json
/tmp/ct152-census > /tmp/ct152-c2.json
cmp /tmp/ct152-c1.json /tmp/ct152-c2.json
/tmp/ct152-census --mutated-a6 > /tmp/ct152-cmut.json
```

Developer-local first two normal source-reconstruction JSON outputs matched exactly (SHA256 `e6b94709d099fd87ec0c8f95065c1a8c3ef50b8301e997403f963ab453860d51`). The two exhaustive C++ integer output records matched byte-for-byte (SHA256 `d242aa7e1fa01463ba2dfee1a957c6c3762fa3baaa969fb91990e63a49ea144a`), 1.44/1.38 seconds elapsed, peak 12,416 KiB RSS on the local runner. These are uncalibrated developer process observations, *not* an ECDLP speedup, cold complete solver timing, hardware-isolated benchmark or PCC verified execution.

A separate C++ negative control changes only the constant coefficient `a6[0]` from 212 to 213. It still enumerates the entire field but produces **11,087,660** points, not the canonical 11,092,292, and passes only because the exact difference is detected. No curve-family extrapolation is made.

**Prospective-status disclosure:** first exploratory reconstruction/enumeration occurred before the CT152 protocol was committed. The [protocol](CT152_SOURCE_POINTCOUNT_PROTOCOL.md) preceded this final source/CI/report publication and governs the controlled follow-up and rejection controls; do not backdate the exploratory data as preregistered.

## Mathematical result and remaining assumptions

For the original *explicit* source, independent full-point enumeration establishes `N=#E(K)=11,092,292`; hence its cubic Frobenius trace is `T=223^3+1-N=-2724`. CT151's exact polynomial identity now applies without relying on a *producer-reported original-source group order*:

```
P_t(X)=X²-tX+223,  Q(X)=X⁶+2724X³+223³
Res(P_t,Q)=223³ (t³-669t+2724)² != 0
for each Hasse-eligible integer -29<=t<=29.
```

Thus, subject to the deterministic binding of this explicit `E/K` to the actual original run, **every F223-defined elliptic-to-Weil-restriction homomorphism into Res(K/F223)(E) vanishes** by Frobenius compatibility and torsion-freeness of Hom. That is a source-specific mathematical obstruction, not an impossibility theorem for unrelated prime-field covers.

**Not covered:** The fixed-nu12 **different** q223 source with reported N=11,086,844 has not been exhaustively counted here. Nor do the point count or CT151 certificate establish that the actual root destination Jacobian is F223-isogenous to this Weil restriction. The full cover/degree-eight quotient and Jacobian homomorphism/field-descent source proof, independent original/reuse 695/701 parity, native `C169,C13a,C13b,D` pricing (the CT141 `admitted-native-price` job was skipped), and full matched *cold single-target* rho/BSGS/IC with setup, transfer, LA, verification, RSS and uncertainty remain open. PCC standing is `[pcc:unverified]`.

This point census uses only bounded developer-local CPU (no paid instance) and an additive source-only CI workflow. No original frozen fixture, PCC ledger, root branch or merge gate changed.

### References checked

- [Root crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), original source constructor `cryptanalysis:experiments/chained-transfer-public-target/native/original/ghs.rs` and `common.rs`, [CT151 Frobenius report](CT151_FROBENIUS_HOM_REPORT.md), [CT149 integer report](CT149_Q223_INJECTIVITY_REPORT.md), [CT150 source scope](CT150_CUBIC_SOURCE_SCOPE_REPORT.md), [native pricing PR #1562](https://github.com/isogeny-labs/cryptanalysis/pull/1562). Shared research-KB MCP and Conductor were not available; no novelty or absence claim. **[pcc:unverified]**.
