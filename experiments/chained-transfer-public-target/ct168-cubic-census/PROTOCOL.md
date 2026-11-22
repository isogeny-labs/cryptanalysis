# CT168 — prospective complete cubic census and scalar-blind descent boundary

Date: 2026-11-16. Scientific standing [pcc:unverified].

## Target and source boundary

Independently enumerate all `223^3=11,089,567` cubic-field x values of the actual CT167 curves, `E:y^2=x^3+9` and `E_d:y^2=x^3+9(2+z)` with `z^3=-3`. Source: cryptanalysis [CT167 report](../ct167-sextic-control/CT167_REPORT.md), Python model (../ct167-sextic-control/ct167_sextic_control.py), root crypto #3877 / queue #3904. CT167's target trace 3439 was formerly conditional on a single point-order filter; seek a full, independent count. This is not the fixed-nu12 family.

## Preregistered methods and acceptance

1. Use a self-contained C++17 cubic ring implementation with direct closed formulas, a bitset of all squares from every y, and complete x enumeration. Independent reference repeats with generic polynomial convolution/reduction, retaining counts for `y^2=x^3+9`, `y^2=x^3+18+9z`, and a deliberately mutated `+z^2` negative control. Count the unique point at infinity, zero RHS once and nonzero-square RHS twice. Require 11,089,567 evaluations per curve.
2. Compare the two JSON records using a separate strict integer-only Python auditor. Reconstruct Frobenius power traces for both curves via `S_0=2,S_1=T,S_r=T*S_(r-1)-q*S_(r-2)`. Determine the least `r>=1` where source and target traces agree; explicitly test 1 through 6. Check prime-field order 219, order-73 point divisibility at `K`, `K^2`, and a negative perturbed curve.
3. A nonzero homomorphism between elliptic curves over a field is an isogeny. Over finite fields, elliptic curves are isogenous over `K^r` only if their traces over `K^r` agree (Tate). Combine necessary trace inequality for 1..5 with CT167's explicit `u^6=d` isomorphism at 6. This excludes **algebraic** scalar-blind elliptic-to-elliptic maps defined over smaller field extensions, not arbitrary finite-group encodings.
4. Publish the complete enumerator source, independent cross-check, frozen counts, trace audit, negative results, exact commands, and an evidence report; use only free local CPU and ordinary source CI, not budget-gated EKS/GPU. Existing native norm-point reuse and actual complete-cold comparison are not repeated.

## Known competing work and coordination

Read crypto AGENTS.md and session log, cryptanalysis AGENTS.md / session log, root #3877, queue #3904, and merged CT167 #1683. Prior art: Sage elliptic finite-field twists and point counts; standard Weil restriction / Tate isogeny criterion. Shared research-KB MCP absent in this runtime; no novelty claim. The crypto-autoresearcher vault remains locked and is not read. CT167 script currently passes secret `k` into each cold subprocess and uses a target-arm `[k]T==V` assertion **inside** its timed region; this makes those timings unsuitable as clean public-input solver benchmarks. Treat its negative ratio as exploratory only; independently separate the oracle from any future timed arm.

No claimed complete ECDLP gain. Full native cold `C169,C13a,C13b,D` pricing remains owner-admission/budget gated. Preserve PCC, frozen histories and repository merge gates.
