# Odd-prime kernel assessment and independent Frobenius audit

For the accepted F17 and shiftedF101 examples,the actual Frobenius-module
argument excludes rational maximal-isotropic kernels at3/5;F17 also has
none at7. ShiftedF101 has four abstract candidates at7,not yet explicit
geometric kernels,codomains or maps. Fixed finite-module controls and strict
Clippy pass(PCC034bed/afecb5);standing remains unsigned. [pcc:unverified]

## Actual elliptic factors and the coprime projection argument

The completed split-quotient maps identify the odd-prime torsion modules
with E1[ell]⊕E2[ell],since their degree4 is prime toell3/5/7. Their
polarized pairing changes by a nonzero common scalar,so isotropy is
preserved. Accepted Richelot targets have the same odd-prime module
property through their degree4 isogenies. These are standard written
torsion/polarization inputs,not merely rational-group cardinality arguments.
[pcc:unverified]

The explicit elliptic counts give traces t1/t2=−1/3 atp17 and−7/−11
atp101. Frobenius characteristic factors are fi=X²−tiX+p moduloell.
The identity

    (X−t2)f1−(X−t1)f2=p(t1−t2)

makes them coprime for every fixedell3/5/7:trace difference is±4 and
p is a unit. CRT block projections are polynomials in Frobenius. Thus
every invariant plane W splits as(W∩V1)⊕(W∩V2). [pcc:unverified]

If either quadratic is irreducible,that elliptic block has no invariant
line. An invariant2-plane must then be one whole elliptic block,which is
not isotropic under its nondegenerate alternating pairing. This excludes
a stable maximal-isotropic kernel. The argument remains valid when the
other block has repeated eigenvalues;no unverified Jordan type is assumed.
[pcc:unverified]

|p|ell|Roots of first/second characteristic factor|Stable maximal-isotropic planes|
|---|---|---|---|
|17|3|none /1,2|0|
|17|5|none /1,2|0|
|17|7|none /4,6|0|
|101|3|none /none|0|
|101|5|4(repeated) /none|0|
|101|7|2,5 /4,6|4 candidates|

At101/7 each factor has two distinct eigenlines. The four mixed sums of
one line from each block are precisely the stable isotropic planes;whole
blocks remain nonisotropic. Each candidate would preserve the order109
subgroup if realized by an isogeny with7-primary kernel. This does not
construct that isogeny or establish its destination's Jacobian model,
normalization,dual,coefficient descent or cost. Those remain next.
[pcc:unverified]

The negatives concern rational maximal-isotropicell-kernels for these
exact polarized examples. They do not exclude arbitrary-degree/unpolarized
isogenies,extension-defined kernels or other covers. No universal DLP
transfer impossibility or prime-field attack follows. [pcc:unverified]

## Complete finite-module controls and formal scope

`src/odd_kernels.rs` enumerates every RREF2-plane in four dimensions over
each fixed field:130/806/2850 planes for3/5/7. Among them40/156/400 are
maximal isotropic. Every nonzero ratio of the two block pairing scales
gives the stated invariant-plane count. Basis tests verify the Frobenius
similitude multiplier p. Characteristic gcds/roots use the pre-existing
BigUint polynomial engine. [pcc:unverified]

Block companion matrices are finite linear-algebra controls. They are not
asserted to be the actual repeated-eigenvalue torsion representation.
The written coprime/irreducible argument supplies the negative independently
of that Jordan choice;the positive control has squarefree factors,where
the eigenline classification is determined. Discovery and frozen0/4
regression receipts remain separate. [pcc:unverified]

Six core Lean `OddKernelProjectors.lean` lemmas pass gate6,PCC8b67e3:
explicit Bezout identity,unit coprime certificate,projector product,
complementary idempotents and all fixed quadratic root lists. They certify
polynomial/finite data,not subspace classification,actual torsion,
polarization or geometric isogeny construction. Total68 written project
lemmas;no new axioms. [pcc:unverified]

Primary source reviewed:J.S.Milne,*Abelian Varieties*,Version2.0,
2008-03-16,https://www.jmilne.org/math/CourseNotes/AV.pdf,
SHA256f5ca4e63e5092a4b102daad1470e4cbed5fe8f82115e3a28c8881e3f67f6aaef.
I§13 Galois-invariant Weil pairings/Proposition13.2 functoriality,
I Proposition10.20 Tate characteristic polynomial,II Theorem1.1
point counts/Frobenius,and I Remark8.12 quotient isogenies. These support
the stated module inputs;no unreviewed positive explicit-map theorem is
substituted for a construction. KB/ecdb remain unavailable,no novelty claim.

## Separately authored polynomial Frobenius oracle

Closed cryptoPR3918 at3a972adb7aaaf1ee10dde605dc48f2c9822dbda5 supplied
a separately authored,std-only Rust test. The original243-line source is
preserved verbatim as evidence/external-ct16-original.rs,SHA256
284e4d72af09fa0729bfa14a7c06249ce8fe78cb6194f01cc0008bf63ab2b04a.
Compiled unchanged underRust1.99.1,it passes. A formatting-only copy in
tests/frobenius_independent.rs also passes Cargo/strict Clippy and enters
the registered consumer CI. No algorithm,fixture or lint exemption changed.
[pcc:unverified]

It imports no producer field,Richelot or Cantor code. Independent modular
polynomial quotient arithmetic checks both source cubic factorizations,
both reflected target sextic Rabin irreducibility/Frobenius orbits,and
all15 pair/matching counts at extension degrees1/2/3/6. This cross-checks
the bounded CT16 branch/Frobenius data with another implementation. It does
not independently evaluate the whole Jacobian correspondence or provide
signed scientific standing. Source custody/original/raw receipts are bound
by PCCed9aff. No closed PR reopened or frozen ledger lineage imported.
[pcc:unverified]

## Exact validation and next task

Current targeted odd-kernel discovery/regression,external unchanged oracle,
Cargo integration,formatting and strict Clippy pass. Full current native25/
reference50-unit-plus1-integration CI is pending;1 old benchmark remains
ignored. Prior sourceda66ab9d9 passes exact-head43026964101:native25/
reference49,one old benchmark ignored/guards(PCCf2de08),andPR1481 merged
ee3f177b4 at13:21:37Z. Immutable scopes remain separate. [pcc:unverified]

Receipts:odd-kernel-proposal-01,odd-kernels-01/02,
odd-kernels-clippy-01/02,external-frobenius-custody-01,
external-frobenius-01,external-frobenius-cargo-01. Run check.sh with
Rust1.99.1 and unchanged crypto75a737b8 runtime closure. Every page of
odd-kernels-report.pdf and its diagram are inspected before publication.
[pcc:unverified]

CT19 next constructs the fixed101 rational7-isogenies on both elliptic
factors,including actual kernel polynomials,cleared curve identities,full
109/113 scalar relations and point recovery. Any subsequent Jacobian
gluing/7-hop must have its own geometric kernel/codomain/dual/descent checks.
Direct original-source controls remain mandatory for a cost claim.
Additional externally supplied CRT projector constants are preserved as
unexecuted controls:17 projector scalars210/76;101 scalars9266/3052.
[pcc:unverified]

No benchmark,solver gain,paid job or cross-prime descent was demonstrated.
S3 transport/live allowance,KB/vault and crypto frozen-ledger/archive gates
remain blocked. Production/catalog/large-prime coverage remains open.
Canonical performance/transfer graphs are unchanged. [pcc:unverified]
