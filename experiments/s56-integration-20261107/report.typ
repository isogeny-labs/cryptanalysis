#set page(paper: "a4", margin: 18mm)
#set text(size: 10pt)
= S56 parameter integration

icv1-fp56-tm132906245-e876a6ea

#image("integration.svg", width: 100%)

== Native inputs
p = 71776123356250111; a = p - 3; b = 11246936090499842.
Prime subgroup order = 71776123489156357; cofactor = 1.
Generator = (3, 8355444684664812).

EC1P56Cfph89d1f28a8527

UID suffix: 89d1f28a8527f4709853f99bf350944571bc333dfb4a726fc254f9034079b5d9.

== Integration and checks
The native constructor and catalog alias s56 share the exact parameters in both repositories. The source curve catalog and crypto mirror retain the same EC1 record. The companion ecbench-curve.json supplies the exact prime_explicit workload, rather than a searched size analogue.

Four native tests cover primality and the Hasse order witness, the twist factorization, the Frobenius discriminant, and the four distinct rational 3-isogeny kernels. These are producer assertions pending independent PCC standing, not a signed mathematical verdict.

== Corrected structural statements
The twist is 27 times 2658374934197921, a 52-bit prime. The Frobenius order has conductor 3. Four rational cyclic 3-isogeny kernels give the surface criterion at depth one; conductor 3 alone does not imply the floor. Endomorphism certification fields remain null pending admission.

== Scope and pending inputs
The reported SHA-1 counter 1841 lacks seed bytes and the encoding/derivation transcript. Full Lean formalization and signed mathematical admission remain open. No timed IC comparison or speedup row is added. The existing icx run command selects bounded analogues; the explicit ecbench fixture is the exact-curve entry point.

== Source pointers
The accompanying README.md contains the reproduction commands and full scope table. Primary sources: cryptanalysis experiments/ic-candidate-catalog/{curves.schema.json,VOLCANO_NAMING.md,validate_semantics.py}; crypto docs/curves/{ICV1.md,ic/README.md}; crypto-autoresearcher docs/lab-contract.md. KB tools and ecdb credentials were unavailable.
