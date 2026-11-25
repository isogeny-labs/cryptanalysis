# CT167 — explicit CM-compatible sextic-twist transfer, complete toy ECDLP negative
2026-11-16. **[pcc:unverified]**. This is an ordinary prime-field *toy positive control* and a negative cost lead; it is not an attack on P-192/P-224, does not invalidate CT166, and does not demonstrate an advantage. The finite model is a different isogeny class than fixed-nu12.

## Decision and why this is different from CT166
CT166 (merged cryptanalysis #1676) conditionally excludes a nonzero *geometric* algebraic Hom from every F223 elliptic curve to the actual fixed-nu12 CM class (radicand −9,234,523). The explicit **different** source/target family below has CM field Q(sqrt(−3)), is geometrically compatible, yet its Weil restriction is simple over F223. This shows why base-field simplicity and geometric Hom obstructions must be kept separate, without revisiting the eliminated fixed-nu12 family.

Choose k=F223, K=k[z]/(z^3+3), d=2+z, L=K[u]/(u^6−d), and
- source E/k: y²=x³+9, with #E(k)=219=3·73 and public G=(132,63) of order 73;
- target E_d/K: y²=x³+9d;
- scalar-blind map φ:E(L)→E_d(L), (x,y)↦(u²x,u³y), φ(O)=O.

Algebraically φ is an isomorphism over L: (u³y)²=(u²x)³+9u⁶. Thus φ([n]P)=[n]φ(P), and the **exact same public target logarithm** is retained on the order-73 subgroup. No private scalar enters the map.

The polynomial z³+3 is irreducible over k because −3 is not a cube in F223; d^((223³−1)/6)=40∈F223 has multiplicative order six, so u⁶−d is irreducible over K (Kummer criterion, because K contains μ6). L is therefore degree 18 over F223, with explicit small fixed-degree arithmetic.

## Geometric compatibility versus descent
Counting E_b(k) for all nonzero b in the j=0 family yields precisely six traces ±5, ±23, ±28. Their cubic base-change traces are ±3220. The ordinary CM field is Q(sqrt(−3)). Multiplication of an appropriate cubic Frobenius eigenvalue by the six units of Q(√−3) gives the six possible geometric sextic-twist traces over K:
**±3220, ±3439, ±6659**.

For the explicit d=2+z, the committed bounded K-point order filter isolates T=3439 from that **a-priori six-element candidate set** (one finite K-point, not a full point census). Conditional on the standard j=0 twist-spectrum theorem and the K model binding, #E_d(K)=223³+1−3439=11,086,129; 73 does not divide this order. The full field extension L is required for the displayed u-scaled isomorphism. It is **not** proved that no other computational encoding exists over a smaller extension; in fact 73 divides #E_d(K²).

The Weil restriction A=Res_(K/k)(E_d) has Frobenius characteristic polynomial F(X)=X⁶−3439X³+223³. Its reduction mod 2 is X⁶+X³+1 = Φ9(X), irreducible over F2 because 2 has multiplicative order 6 mod 9. Therefore F is irreducible over Q and A is k-simple. Yet E and E_d become isomorphic over L, so the geometric Hom is nonzero. There is **no k-defined elliptic-to-A homomorphism**, but a finite-extension geometric isomorphism exists. This is the promised boundary control for CT161/CT166; it offers no short solving method.

## Actual public-target experiment (producer-only, negative)
The implementation in this directory has independent field-tower arithmetic, prime-73 BSGS in both groups, a deterministic public generator/target panel, complete verification of [recovered]G=Q on the source and [recovered]φ(G)=φ(Q) in the target. The source secret is used by the harness **only to generate Q and validate test controls**; BSGS receives only G and Q. Target preparation includes the degree-18 tower, map, twist-point checks and source verification. No cached target table is supplied.

Locally before repository publication, a functionally equivalent 258-line Python producer prototype passed three public-target pair solves and six directed false-equation/false-scalar controls. A balanced 16-fresh-process exploratory run (four distinct public Q, source/twist each repeated twice) produced:
- eight source BSGS processes: **10,834.892 ms** total host-spawn wall;
- eight transferred BSGS processes: **11,907.683 ms** total host-spawn wall;
- aggregate transferred/source host-spawn wall **1.0990×** (transferred is slower);
- the within-process stage is much slower under degree-18 arithmetic, but the whole-process wall is dominated by ~1.2–1.6 s startup and unisolated host scheduling. Source A/A drift is large (up to 22.5% for a pair), so **the cold-process difference is not statistically qualified**.

These values come from an explicitly **earlier local prototype**, not a hosted execution of the final committed script. The prototype source sha256 is 5bb2a2302ed44f7f6b6495705a2f864b102adaf2f154eb26eab2a3c5e12baec6, paired JSON sha256 a64113cae2d544474ed2fefb6df21ba3642fa240a23c1f87958de950ef9425b9, self-test JSON sha256 39f08a3e93be3fb9b15c49e0646f9afc1328fba6835568a35ae9dbf901aa02fa. They are non-isolated producer evidence; final committed code requires its **own** exact-head replay before any numerical result can be attributed to that version.

Commands from repository root:
\`\`\`sh
D=experiments/chained-transfer-public-target/ct167-sextic-control
python3 -B "$D/ct167_sextic_control.py" --self-test
python3 -B "$D/ct167_sextic_control.py" --paired > /tmp/ct167-paired.json
python3 -O -B "$D/ct167_sextic_control.py" --self-test
\`\`\`
For an actual independently validated measurement, require pinned binary/host, release-grade native Fp/Fp18 implementation, A/A and CPU isolation, same-source full rho/BSGS/IC, setup and peak RSS, all verified Q, cold confidence interval, and signed PCC. None exists for CT167.

## Norm-point reuse and owner-priority reconciliation
Producer-native evidence **already reports** full 695-record parity in cryptanalysis \`experiments/chained-transfer-public-target/reports/norm-point-reuse-result-01/REPORT.md\` and \`evidence/fixed-chain-norm-point-native-01/outcome.json\`: all 695 ordered records, only 48 preregistered counter replacements, all 14 phases expected exits, four whole-record omission failures. Earlier summaries saying no producer full parity are stale. **Independent signed replay/custody remains missing**, as do owner-admitted C169/C13a/C13b/D same-host prices and complete prime-field cold rho/BSGS/IC comparison. The root queue #3904 at 2026-11-16 20:10 UTC reports budget STOP (daily $216.868>$200; monthly $2,094.914>live $1,300), unknown capacity and original-store 403 failures. This work did not launch EKS/Spot/GPU compute or bypass approval.

## Implications, dead ends and next action
This positive example **does not rescue fixed-nu12** and is slower even against a basic source BSGS in an exploratory comparison. Do not spend on extending this toy twist to a full attack. The next decisive task remains the independent whole-corpus raw 695/701 replay and owner-admitted native primitive pricing, with matched cold total ECDLP costs. Any genuinely different carrier must preserve the chosen prime-order source subgroup under a scalar-blind computable map, avoid unnecessary high-degree field arithmetic, and beat the best verified cold solver including all phases.

**Proof map:** elementary field/twist identities: checked by bounded producer arithmetic; six-spectrum theorem and simple-Weil deduction: written mathematics, not Lean-kernel compiled; complete scalar recovery: producer-only toy control; complete prime-field advantage: OPEN; PCC: **unverified**.

Sources checked: crypto #3877 and #3904, #4215, #4178; cryptanalysis #1523, #1589, #1676, CT160/161/164/166 reports, original full-695 producer outcome; earlier sextic and CM work in crypto and crypto-autoresearcher. Shared KB/Conductor and repository vault were not accessible through this execution, so this report makes no novelty/absence claim.
