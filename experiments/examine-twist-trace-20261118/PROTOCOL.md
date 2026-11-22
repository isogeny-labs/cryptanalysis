# Protocol — exact twist / Frobenius-trace ECDLP transfer (2026-11-18)

**Status:** retrospective selected toy fixture, [pcc:unverified]. This audit was not preregistered before selecting the example, so no prevalence, improvement, or cryptographic-scale claims are permitted.

## Falsifiable transfer

Hypothesis to test: although E(Fp) has prime order and the quadratic twist Eᵈ(Fp) has smooth order, the extension isomorphism followed by Frobenius trace might map source ECDLP into the smooth group **while preserving the log**. Falsify immediately if trace kills source points; separately check the bare extension isomorphism and original log recovery, and count every additional cost.

Fixed field p=1009, E:y²=x³+2x+25, nonsquare d=11, Eᵈ:y²=x³+242x+987, K=Fp[s]/(s²−11). Generator: first enumerated nonidentity E(Fp) point; claimed G=(0,5) is checked. Map φ:(x,y)↦(11x,11s y), inverse φ⁻¹:(X,Y)↦(X/11,Y/(11s)); trace T=1+π. Expected #E(Fp)=991, #Eᵈ(Fp)=1029, #Eᵈ(K)=1,019,739, each to be checked by point census, Frobenius characteristic polynomial and full-order group witnesses, not used as unverified assumptions.

Compute φ(P), φ⁻¹φ(P) and Tφ(P) for every source P; require 991 distinct images and intersection with Eᵈ(Fp)={O}. Verify 1024 deterministic random subgroup homomorphism pairs. Verify H=(3,76) has order 1029, φ(G) has order 991, H+φ(G) has order 1,019,739 and that T(H)=2H, giving T's kernel/image. Exhaust all 1029 rational-twist inverse checks using [515]T and demonstrate absence of a **global** inverse.

Fix seed 20261118; sample 64 distinct logs including 0,1,990. Perform identical affine BSGS on both source and lifted image, with same baby/giant loop and original-curve check. Count group calls, underlying Fp modular multiplications/additions/inversions separately; report φ / φ⁻¹ costs (2 multiplications per point), trace, inverse and overhead separately. Common target creation excluded; no wall-time or GPU throughput claim. The matched reference is direct BSGS; rho sqrt(pi·r/2) is an **unmeasured heuristic** only.

## Acceptance and local sabotage controls

1. Reject transformation if any point falls off-curve, group order is inconsistent, kernel/image incorrect, map inverse fails, or any mapped k fails original verification.
2. Reject a *useful smooth descent* if the smooth projection cannot recover k.
3. Reject an all-cost speedup unless end-to-end cost is strictly lower on matched problems and cold setup is counted; none is claimed for this negative fixture.
4. Rerun `replay.py`; compare exact summary counters and full-output SHA-256, then reject three mutated results (wrong twist order, modified per-sample primitive cost, changed log). These are producer-local controls; only a separately signed PCC verdict gives independent standing.
5. Stop proposing twist as novel: programme's [IC mega-pass](https://github.com/isogeny-labs/crypto/blob/main/research/ic_mega_pass_20261031/brief/BRIEF.md) closed this Frobenius mechanism. Next discriminating target is a non-homomorphic cover/Jacobian correspondence outside the homomorphic conservation closure.

Run from repository root:

```sh
python3 experiments/examine-twist-trace-20261118/replay.py --out /tmp/twist-results.json
python3 experiments/examine-twist-trace-20261118/replay.py --verify-json /tmp/twist-results.json
python3 experiments/examine-twist-trace-20261118/verify_summary.py
```

The Conductor `conductor_check_conflicts`/`coord_start_work` and research-KB APIs were unavailable in this runtime; GitHub conflict search was completed, and scope is restricted to this new experiment directory.
