#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= The first Jacobian seven-transfer using F101 arithmetic
2026-11-12 · fixed T0→T1 forward evaluator · scientific standing unsigned

The existing forward Psi now has a constructor and evaluator that use
F101 arithmetic throughout. Native prototype15/PCC72e1d8 matches every
12,317 concrete output of the old transfer,with bijection,all fixed-partner
sums,negations,identity and wrong-model controls. Selected alpha numerator,
denominator,kernel and curve coefficients match the old maps exactly.
This is an evaluator of the existing degree49 Jacobian map. [pcc:unverified]

#image("psi.svg",width:100%)

== Exact stages and their acceptance
The source and destination are the actual nonsplit sextics
T0=[31,75,74,54,71,55,1] and T1=[95,26,19,27,94,91,1]. Both rational
Jacobian groups have order12,317=109·113. The constructor takes accepted
fixed covers and the selected elliptic kernel cubics[72,100,35,1] and
[59,46,8,1]. It reuses existing Kohel and prime-field engines;parameter
discovery remains inherited input provenance. [pcc:unverified]

#table(columns:2,stroke:0.4pt,
 [Stage],[Existing-engine evidence],
 [Both T0 norms H0],[Every12,317 old output/group/exception controls;585f35/2fcf0b],
 [Quarter and alpha],[Public inverse4 scalars82/85;coefficient-identical selected degree7 maps],
 [T1 pullbacks K1],[All109/113 inputs,old RiPi,norm4/off-diagonal0;5143f5],
 [Balanced assembly],[Original reduction arithmetic body byte-exact after extraction],
)

All four T0/T1 pullbacks additionally pass49,300 ordered elliptic-group
additions. Actual infinity multiplicities are[1,2] for T0 and[2,1] for T1.
The two T1 covers each have116 finite-valued witnesses and two rational
pole witnesses;all four geometric pole branches are retained. Separate
flat-field replays5ab2bd/5eb5b1/850e92 validate the exact equations,
degrees,complete source domains,infinities and poles. [pcc:unverified]

#pagebreak()
= Why the replacement computes the same transfer

The accepted global factorization is4Psi=K1 alpha H0. Each H0 component
is the pushforward of its exact degree4 cover;each K1 component is the
corresponding T1 pullback. On the actual elliptic rational groups,
4·82=1 modulo109 and4·85=1 modulo113. Moving these public quarter
scalars before alpha therefore gives Psi on J(T0)(F101),since4 is
invertible on the order12,317 destination group. This uses no discrete-log
labels and does not propose a global inverse morphism of[4]. The old
adjoint norm7 preserves the original109/113 DLP components and recovery.
Upstream PRIME_FIELD_PSI_PROOF.md/78176c records the complete argument.
[pcc:unverified]

The curve maps are identified globally using exact polynomial equations,
degree4 and a proved difference-degree bound16. More than16 distinct
agreement points force equality. Old quotient/Picard/polarization/norm
facts and expected-value provenance remain explicit dependencies. A
negative ordinate passes the curve equation but fails the witnesses;
equation fitting alone would not identify the map. [pcc:unverified]

== Pullback jets and exact infinity bookkeeping
For finite P=(X,Y),form U=N-XQ²,V=YQ³/M moduloU. In the finite support
algebra,F M²=Y²Q⁶. Supplied units Yi,Qi give the explicit inverse
M inverse=F M Yi² Qi⁶,even if the quotient has nilpotents. Two bound
QuarticFibre lemmas d4010b/4286c9 prove the actual cleared factorization
and inverse,local kernel/axiom gate3413a4:2theorems,zero trusted native.
That proof-stage census136written helpers/25modules remains partial formalization.
[pcc:unverified]

Since divQ=f\*(O)-2(infinity++infinity-),a generic degree4 fibre has
balanced plus count-1. At P=+q,a degree dropk gives plus=k-1;at P=-q
it gives plus=-1. The Y sign is essential. The implemented rational
elliptic groups have odd order;geometric nonzero2-torsion needs another
chart and is outside this implemented domain. QUARTIC_PULLBACK_PROOF.md/
4934b4 supplies the divisor derivation and original-engine custody.
[pcc:unverified]

== Actual production integration and complete acceptance
The actual SevenChain.forward now selects the prime-field entry. Its exact
old body remains forward_reference;the new complete comparison calls that
explicit reference. Original dual,naive,source,geometric and chained
controls remain. Complete changed check.sh04 exits0:25native/90reference
unit+five integrations,one pre-existing ignored benchmark,all source guards,
fmt and strictClippy. PCC76871d pins the whole131756-byte raw log as
standardXZ14932bytes,raw/archive hashes/exact roundtrip and all eight
unchanged post-run source02 hashes. [pcc:unverified]

The workspace restart interrupted03 before reference completion. Its full
available partial48451bytes,metadata and sourcehash receipt remain frozen
underf87a99;04 retries the identical source and complete check. No partial
run is counted as passed. The new ready child targets immediate1505 at6cf;
its own exact-headCI is separate. Parent1505 focused43165729371 succeeds
25native/85reference+five,fullfd53e1;parent1501 remains fixed5ceb/green.
[pcc:unverified]

Written PRIME_FIELD_PSI.md,QUARTIC_PULLBACKS.md and T0_SECOND_QUARTIC.md
copy upstream78176c/4934b4/a38aa4. Independent curve certificates and the
faithful finite-algebra lemmas remain explicit dependencies;actual geometric
formalization is partial. Existing reducer/old-chain bodies have exact
extraction custody. The isolated upstream adjoint/T2/chain-compression
results are outside this consumer checkpoint. [pcc:unverified]

Matched cold construction,transfer,solve,recovery and verification costs
await S3/profile/livebudget admission. No timing gain is claimed. KB/ecdb
unavailable;autoresearcher atlas vault locked. Frozen ledger forks and
parent1484 C/conflict findings persist;integrate bottom-up after actual
gates,retarget/rerun after parents land. [pcc:unverified]
