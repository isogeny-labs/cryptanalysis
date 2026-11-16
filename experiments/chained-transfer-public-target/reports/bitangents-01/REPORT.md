# Actual q223 bitangent coordinates and Frobenius

2026-11-13. All standing unsigned; formalization partial.

Observed nativee887a9,unsigned: the fixed q223/seed1 quartic has28 distinct certified W-coordinate bitangents over L=F223[w]/(w⁶−3). The original Rabin constructor checks irreducibility; z=w² embeds the original cubic K. All basis-product/Frobenius checks and all15 original quartic coefficients match through the original inverse Moore matrix. One unfiltered serial test passes, all2338 selected input hashes unchanged. [pcc:unverified]

Actual Frobenius cycle lengths are6,6,6,3,6,1; fixed line counts for F,F²,F³,F⁶ are1,1,4,28. Hence the minimal field containing all line coordinates has degree6. This coordinate finding agrees with the separate written geometric two-torsion argument65f7a4. It does not assume semisimple order-three Frobenius. [pcc:unverified]

The28 lines comprise12 coordinate-zero and16 generic lines. Every original binary quartic restriction equals scale times a quadratic squared, with all five coefficients checked. All gradient/line minors vanish modulo the contact quadratic in both charts; all28 fixed mutations of contact certificates fail. Sixteen contact quadratics split over L and12 remain nonsplit. Their contact points are not required to lie in L. [pcc:unverified]

Construction and exceptional scope: recover the six Ciani coefficients from original Core.rmat, transport each line by the original inverse Moore matrix and normalize in W coordinates. Generic Y=uX+vZ uses U=u²,V=v² with C(U)+L(U)V=0 and4A(U)³(c+eV+bV²)−(D(U)+E(U)V)²=0. The elimination polynomial has degree10 and6 distinct U candidates. The implementation retains the L=C=0 branch, but this actual curve exercises it zero times; no general branch-coverage claim is made. [pcc:unverified]

Readable derivation and proof map: bitangents/DERIVATION-01.md freezes all formulas, zero-coefficient families and exceptional cases. RESULTS-01.md records the actual observations and gaps. Four exact original local PCC bindings a01f8f/5288a0/6cd1a8/d79edc cover general commutative-ring denominator and constant factors, faithful resultant necessity under both original equations, and exact order6 of literal28-entry native permutation data. [pcc:unverified]

Both unchanged original producerLean4.35 and consumerLean4.34.1 gates pass4 declarations/0trusted. Ring proofs use propext,Classical.choice,Quot.sound; the closed permutation theorem uses none. No sorry, custom axiom, native_decide or fresh lean4checker result. These declarations do not prove the geometric identification of the literal permutation or define actual theta/divisor/Jacobian objects. [pcc:unverified]

The square restriction gives twice a geometric degree-two contact divisor. The standard28-odd-theta/bitangent theorem for smooth plane quartics in odd characteristic supplies completeness. The actual theta correspondence, Frobenius/torsion identification, Weil pairing, geometric torsion basis, stable isotropic kernels and a nondual codomain/map remain written or unimplemented. No kernel count or nonexistence theorem follows from this coordinate test alone. [pcc:unverified]

Independent parent checks are settled: sourceec826 passes full25fdf5 with503 guards/11 positive phase pairs/four actual admission controls. Allfive exact-source workflows succeed,c225d2; all46 native records and21 original canonical PCC digests match. Genuine f824e8/39084d publishes allten closed trees as13 large S3 objects and7 small whole Git objects, with all2334 then-current hashes preserved. New bitangent independent full/CI and its raw publication remain next. [pcc:unverified]

Next: finish this source/proof/report checkpoint and its own independent replay, then use the actual permutation in an independently checked symplectic stable-kernel calculation before constructing kernel coordinates. Current arithmetic/timings are correctness diagnostics, not an admitted benchmark. Original S3 checkpoint/live budget/capacity, complete accounting and strongest references remain required for any computational-advantage claim. [pcc:unverified]

Sources: bitangents/DERIVATION-01.md,RESULTS-01.md,lean/BitangentAlgebra.lean; original primary source catalog evidence/bitangent-plan-01; nativee887a9; exact proof bindings and retained native records. Existing reports/v2-native-02/flow.dot and the candidate-catalog curves.yaml at HEAD were checked; no new curve endpoint or isogeny edge is added. This is an auxiliary line-coordinate graph. Editable DOT/SVG/renderer/Typst and allnativeJSON are adjacent.
