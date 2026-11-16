# CT146 — corrected-half transport identity versus Frobenius trace

Date: 2026-11-15. Parent: cryptanalysis #1533, CT145 #1584. Root: crypto #3877. Standing: **[pcc:unverified]**.

## Mathematical result and precise limitation

CT145's counterexample remains valid: quadratic field trace Z + Frobenius(Z) may differ from [2]Z even when [2]Z descends. However CT125's **old transported target norm** is not a field trace: it is an elliptic isogeny gamma evaluated on source Q. Its proposed new value is the double of already transported, corrected point Z.

Let gamma:E(L)->E'(L) be a group homomorphism, [2]P=Q, and T be an order-two point. Setting Z=gamma(P+T) gives

    [2]Z = gamma([2]P+[2]T) = gamma(Q).

This holds even when Z is not Frobenius fixed. With composable homomorphisms gamma1 and gamma2 the same identity gives

    [2]gamma2(gamma1(P+T)) = gamma2(gamma1(Q)).

Hence the direct and retained-lift replacement agrees algebraically with its *reference elliptic norm computation*, subject to actual maps preserving the group law and the field embeddings/descent being faithful. The literal sequential route applies the one-hop identity twice. The proof covers infinity, 2-torsion and generic halves; no odd-order assumption is needed.

This **does not prove** the separate specialized Jacobian equality N(Phi(Z))=[2]Z universally. The actual source computes the same target class Phi(Z) in both implementations and retains the independent final Jacobian norm check. Under the hypotheses the reference and reused elliptic norm values coincide, so the final acceptance predicates agree, but actual full-fixture runtime parity remains untested. [pcc:unverified]

## Source binding

Inspected original Rust Git blob 8016634385d76207b23a3eb3a4dae9b0366ac68d. The original halves routine checks [2]P=Q; the constructor checks four actual rational E[2] points; correction points come from those; gamma evaluates the prepared rational maps; the old norm calls gamma on Q, and the original final check computes the actual Jacobian norm.

The source canary checks the pinned Git blob, required structural guards, preserved source norm and final actual norm, and executes CT125's original source transformer in memory. The rational-map group-homomorphism and exact base-change/descend compatibility must still be proved or independently verified on the q223 instance. Polynomial residual certificates are not by themselves a full global proof. [pcc:unverified]

## Exhaustive independent toy check

An independent integer-encoded F5[u]/(u²-2) implementation, not importing CT145 arithmetic, ran locally in normal and optimized Python, returning identical JSON:

| Test | Result |
| --- | ---: |
| E(F25) points | 36 |
| Geometric order-two points | 4 |
| Rational-over-F5 order-two points | 2 |
| Corrected (P,T) pairs | 144 |
| Single-map checks ([2],[3],[5],[7],[13]) | 720/720 |
| Composed map checks | 432/432 |
| Rational-double, nonrational trace-different combinations | 24 |
| Non-2-torsion correction / nonhomomorphic translation controls | Both rejected |

The witness Z=(4+u,3) retains [2]Z=(0,1), trace(Z)=(2,2), yet [2][5]Z=[5][2]Z. Thus trace inequality does not invalidate this homomorphism identity. Toy E(F25) has only **two** F5-rational E[2] points, unlike the four rational E[2] points of the original q223 instance. The toy scalar endomorphisms are not the actual degree-13 rational maps. [pcc:unverified]

Reproduction from the repository root:

    python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct146_transport_identity_canary.py
    python3 -O experiments/chained-transfer-public-target/norm-point-reuse-01/ct146_transport_identity_canary.py

For the source-bound check add both options: --original-rust experiments/chained-transfer-public-target/fixed-jacobian-chain-evaluator-01/src/lib.rs and --ct125-builder experiments/chained-transfer-public-target/norm-point-reuse-01/build_norm_reuse.py.

## Next acceptance gates

Complete actual original/reuse 695/701-record parity including 672 exceptional descriptors; verify original q223 isogeny homomorphism and embedding/descend; retain independently computed Jacobian norm and all negative records. Then run only owner-approved same-host ABBA C169/C13a/C13b/D, strongest cold rho/BSGS/IC comparison with setup, transport, linear algebra, verification, memory, uncertainty and signed PCC. No original-prime solver advantage is claimed here.

Sources checked: cryptanalysis #1533/#1584/#1553/#1562/#1576/#1581, crypto #3877/#4215/#4178, original Rust lib.rs and rational.rs, AGENTS.md. Existing blocker: problems/chained-transfer-public-target-destination-bridge.md. The shared research-KB was not exposed in this runtime, so no novelty or absence claim. No paid compute, protected merge or frozen fixture change. **[pcc:unverified]**
