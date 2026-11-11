#set page(paper:"a4",margin:17mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Odd-prime kernels beyond the Richelot dead ends
2026-11-11 · Chained ECDLP Transfers · CT18

*Unsigned/unverified standing.* No rational maximal-isotropic3/5 kernels
for either accepted17/101 example,nor7 forF17. ShiftedF101 has four abstract
7-kernel candidates,without explicit geometric kernels,codomains or maps.
PCC034bed/afecb5 bind finite-module controls. No solver/advantage claimed.
[pcc:unverified]

#image("odd-kernels.svg",width:100%)

== Actual-module argument and finite controls
The elliptic quotient traces are−1/3 at17 and−7/−11 at101. Their
Frobenius factors fi=X²−tiX+p satisfy
(X−t2)f1−(X−t1)f2=p(t1−t2). Trace difference±4 is a unit modulo
the fixed3/5/7,so block projections are polynomials inFrobenius.
Every invariant plane splits across the two elliptic blocks.
[pcc:unverified]

If one factor is irreducible,it has no invariant line. Any invariant2-plane
is then a whole elliptic block,which is not isotropic. This argument does
not assume the other block's Jordan type,including the repeated root at
101/5. At101/7,both blocks split with distinct eigenvalues2/5 and4/6;
the four sums of one eigenline from each block are the stable isotropic
planes. These give candidates only. [pcc:unverified]

All130/806/2850 RREF2-planes and40/156/400 maximal-isotropic planes over
3/5/7 are checked,every nonzero component pairing-scale ratio. Finite
companion models are controls;the written CRT/irreducible argument supplies
the actual-module negative. Degree4 split/Richelot isogenies transport odd
torsion equivariantly and scale pairings by units. No arbitrary-degree,
unpolarized or extension-kernel impossibility follows. [pcc:unverified]

Six core Lean lemmas,PCC8b67e3,gate6,check Bezout/coprime/projector algebra
and all quadratic root lists. They do not construct torsion spaces,
invariant-plane geometry or isogenies. Total68 written project lemmas.
[pcc:unverified]

#pagebreak()
= Independent branch audit and exact validation

Closed cryptoPR3918 source3a972adb7 supplies a separately authored std-only
Rust polynomial oracle. Its original243-line source is preserved verbatim,
SHA256284e4d72af09fa0729bfa14a7c06249ce8fe78cb6194f01cc0008bf63ab2b04a.
Compiled unchanged underRust1.99.1,it passes. A formatting-only integration
copy passes Cargo/strict Clippy and enters registered consumer CI. No
algorithm,fixture or lint exemption changed. [pcc:unverified]

The oracle imports no producer field,Richelot or Cantor code. Another
modular polynomial implementation checks both source cubic factorizations,
both reflected target sextic Rabin irreducibility/Frobenius orbits,and
all15 pairs/matchings at extension degrees1/2/3/6. It independently
cross-checks CT16 branch data,not the complete Jacobian correspondence or
signed standing. PCCed9aff binds original,custody and passing receipts.
No closed PR reopened or frozen ledger imported. [pcc:unverified]

== Primary mathematical inputs
J.S.Milne,Abelian Varieties,Version2.0,2008-03-16,CourseNotes/AV.pdf:
I§13 Galois-invariant Weil pairing/Proposition13.2 functoriality,
I Proposition10.20 Tate characteristic polynomial,II Theorem1.1
point counts/Frobenius,I Remark8.12 quotient isogenies. PDF SHA256 and
review scope are in ODD_KERNELS.md/frozen proposal. No positive explicit-map
theorem is substituted for an actual construction. KB/ecdb unavailable;
no novelty claim.

Current odd-kernel discovery/regression,external original/integration,
formatting and strict Clippy pass. Full native25/reference50-unit-plus1-
integration CI pending;one old benchmark ignored. Prior da66ab9d9 exact-head
43026964101 passes native25/reference49/guards,PR1481 mergedee3f177b4.
Older receipts retain their immutable scope. [pcc:unverified]

Reproduce consumer check.sh with Rust1.99.1/crypto75a737b8 guards. Targeted
test:`fixed_odd_prime_invariant_isotropic_planes`;integration:
`cargo test --release --test frobenius_independent` with consumer manifest.
Proof:upstream OddKernelProjectors.lean. Raw receipts are named
odd-kernel-proposal-01,odd-kernels-01/02,external-frobenius-custody-01,
external-frobenius-01/Cargo/Clippy. Full report:ODD_KERNELS.md.
[pcc:unverified]

== Next construction and limits
CT19 constructs fixed101 rational7-isogenies on both elliptic factors:
actual kernel polynomials,cleared curve identity,full109/113 scalar and
point-recovery controls. Any later Jacobian gluing/hop needs separate
kernel,codomain,dual and coefficient-descent validation. Original-source
controls remain mandatory;CRT scalar projectors remain unexecuted extras.

No benchmark,solver gain,paid allocation or cross-prime descent demonstrated.
S3 transport/live allowance,KB/vault and crypto frozen-ledger/archive gates
persist. Production/catalog/large primes stay open. [pcc:unverified]
