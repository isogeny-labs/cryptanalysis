#set page(paper:"a4",margin:17mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Balanced genus2 arithmetic without a Weierstrass chart
2026-11-11 · Chained ECDLP Transfers · bounded development prototype

*Unsigned/unverified standing.* The monic split-sextic prototype supports
checked primes5..101. Production arithmetic and the1,940-row cover catalog
remain unchanged. No benchmark or computational advantage. [pcc:unverified]

#image("balanced.svg",width:100%)

== Primary representation and reduction
Store a degree2 effective divisor relative to K=∞++∞−:
finite(u,v) + n∞+ + (2−deg(u)−n)∞− − K,
with monic u, degree≤2, deg(v)\<deg(u), u dividing f−v², and
0≤n≤2−deg(u). Identity is(1,0,1); the infinity difference δ is(1,0,2).
The inverse sends v to−v mod u and n to2−deg(u)−n.
Galbraith corrected Definition10.4.9/Theorem10.4.19 supply uniqueness.
[pcc:unverified]

Affine Cantor composition retains the signed infinity count. Reduction uses
a cubic ℓ matching the required infinity branch, exact quotient(f−ℓ²)/u,
and the actual valuation of y−ℓ. Degree4 interpolation with leading±1 is
handled explicitly; treating both poles as order3 there would be incorrect.
All output degree/infinity bounds and divisions are checked.
[pcc:unverified]

Six core Lean lemmas audit degree/count bookkeeping, inverse counts, branch
updates and the infinity-polynomial square. They do not construct valuations
or Picard groups. The6-declaration gate passes; crypto PCC-1cadd0 remains
unsigned. [pcc:unverified]

== Independent arithmetic controls
All10,404 classes of y²=x⁶+1/F101 biject with the existing odd chart at(10,0).
Paired additions, every inverse/cancellation, δ-translation and first quotient
norm agree. All six degree/infinity patterns occur; δ has order3.
All10,404 classes of y²=(x+1)⁶+1 also match after translation, with nonzero
infinity polynomial x³+3x²+3x+1. Both engines use Cantor; this is
producer-run agreement, not signed scientific validation. [pcc:unverified]

#pagebreak()
= Full prime-order transfer and unresolved scope

The existing E109/F101 source y²=x³+x+46 pulls back through(x,y)↦(x²,y)
to C:y²=x⁶+x²+46 without rational Weierstrass points. Every source scalar
passes pullback/norm[2] and inverse55 recovery. Point recovery does not
compute the unknown DLP scalar. [pcc:unverified]

The balanced Jacobian has11,663 classes. Separate elliptic point counts
give109 and107 for the source and normalized reciprocal quotient
y²=x³+x²+96; the product agrees. All11,663 paired arbitrary-class norm
additions pass. The norm has109 images and equal fibers107. These are
rational counts, not geometric kernel degrees. [pcc:unverified]

The primary F37 example y²=x⁶+x+1 reproduces Galbraith Example10.4.18;
1,211 fixed associativity triples and malformed/foreign-model controls pass.
Exact source: src/balanced.rs. The closed-point norm helper is shared with
the earlier cubic prototype, whose tests pass again after the refactor.
[pcc:unverified]

== Receipts and reproduction
Run experiments/chained-transfer-reference/check.sh with Rust1.99.1 on PATH
and the immutable upstream75a737b8 runtime closure available. Receipt
balanced-pinned-01.txt binds source guards, formatting, strict Clippy,
native25 and reference37 passing tests, with1 pre-existing benchmark ignored.
PCC-8b7ca0 remains unsigned. First compile and Clippy failures are retained;
no prior receipt, witness or test was rewritten. [pcc:unverified]

Full written argument: BALANCED.md. Primary source: Galbraith corrected
ch.10§10.4.2, especially Definition10.4.9, Lemmas10.4.10/14,
Theorem10.4.19 and Example10.4.18; corrected ch.8§8.3 for Picard norm.
Crypto's SOURCES_20261111.md binds the primary PDF bytes and retrieval gaps.

== What remains open
This bounded prime-field prototype does not implement large-prime or
extension-field arithmetic, nonmonic/inert models, catalog replay, normalized
Montgomery/Edwards targets or production integration. It narrows the catalog
problem without closing it. [pcc:unverified]

Next: prove and construct Frobenius-stable nonrational Richelot splittings on
predeclared E19/F17, then implement the actual correspondence and descent.
No such correspondence is supplied here. The old rational-factor constructor
restriction is not a universal kernel obstruction. [pcc:unverified]

S3 admission, live IsoLab budget/capacity, KB and the encrypted atlas remain
unavailable. No solver comparison, relation collector or paid job ran.
Crypto PR3877 remains blocked by frozen-ledger/history and archived-receipt
requirements. Canonical transfer/leaderboard graphs are unchanged because no
signed finding or performance edge is promoted. Source queue: crypto3904.
