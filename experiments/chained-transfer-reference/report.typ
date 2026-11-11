#set page(paper:"a4",margin:18mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Pinned chained-transfer and small-prime oracle
2026-11-11 · cryptanalysis · producer-run development checks

*Standing: unsigned and unverified.* The unchanged pre-existing BigUint
arithmetic checks complete finite class sets. Both implementations use Cantor;
the field-point counter shares the existing Fp2 lineage. Agreement is not
signed independent validation of every layer. No benchmark or computational
advantage is claimed. [pcc:unverified]

== Source custody and execution scope
Current crypto pin:75a737b8366ec6c78ed8672886423fcbe69853a2. Seven runtime
SHA-256 inputs include native Cargo/source files and the external unchanged
src/prime_hyperelliptic/fp2.rs. The consumer enables small-prime and refuses
source/reference drift before compiling. The reference files remain pinned
to cryptanalysis68594c8874c75a0a6c04a3874adb1374088ca4f5.

check.sh passes native formatting, strict Clippy and25 tests, then reference
formatting, strict Clippy and29 tests with1 existing benchmark ignored. Raw
receipt small-prime-pinned-01.txt; PCC-20261111-465843 remains unsigned.
Earlier18db046,b280efc,aabae197 pin metadata and every raw receipt remain
retained. No failed attempt was replaced. [pcc:unverified]

== Exact four-field comparison
#table(columns:(0.5fr,1fr,1fr,1fr),inset:5pt,
[p],[Each Jac order],[Self-inverse source/target],[Elliptic quotient orders],
[13],[180],[4 / 4],[10 / 18],
[29],[960],[4 / 16],[40 / 24],
[31],[1008],[16 / 4],[28 / 36],
[101],[9216],[4 / 16],[96 / 96],
)
On all eight complete models, BigUint independently computes the monic chart
change, paired additions, dual norms, self-inverse counts, Fp/Fp² Jacobian
orders and elliptic quotient orders. The first13/29/101 fields were fixed
before execution;31 was separately added as a nonresidue control and uses3
rather than2. [pcc:unverified]

Different rational2-torsion counts obstruct a base-field Jacobian isomorphism;
equal counts at13 do not establish one. The source prime subgroups are5,5,7,3.
The native backend validates odd primes≤4096 and caps enumeration at101.
These tiny correctness fixtures do not establish large-field performance,
cryptographic-size support or transfer between prime characteristics.
[pcc:unverified]

The earlier r17 fixture retains10,404 source additions/inverses,289 target
subgroup additions, complete Richelot-image translation checks and independent
point-count orders. Its initial target is source-isomorphic and its complete
elliptic endpoint matches a direct shortcut. [pcc:unverified]

#pagebreak()
= Retained two-hop construction and limits
#image("chain.svg",width:100%)
The predeclared successor second pairing has determinant67, base11 and
third-model coefficients[38,9,29,62,86,17,8]. All9,216 target classes have
BigUint additions/dual norms checked, independent order9,216 and self-inverse
count8. The rational composite kernel has8 elements,4 self-inverse; do not
confuse it with geometric degree16. Source P=(48,20),r3 reaches the canonical
class u(T)=T²+86T+27,v(T)=34T+7. Upstream native checks include trivial
next-kernel/previous-dual intersection and reversed-chain/source norm[8].
[pcc:unverified]

The source global successor argument derives n R f∗ = tau phi[2] for its
first elliptic projection in characteristic≠2,3,5, with
tau(X,V)=(X/100+1/125,−V/1000). The actual base translation(1/125,0) is
included. Seven cleared ring lemmas compile upstream; projective/Picard
completion is a written argument, not a full Lean construction. It is not
asserted as a collapse of the final Jacobian-valued two-hop map.
[pcc:unverified]

== Reproduction and review
Check out crypto and cryptanalysis as siblings, with the exact pinned native
and external Fp2 files, then run experiments/chained-transfer-reference/check.sh.
Cargo.lock and source manifests freeze the dependencies. The focused
push-main/manual workflow checks out that same runtime closure and runs both
suites. Actual final-head CI is tracked in GitHub separately from local
receipts. Prior focused run42986170752 succeeded on exactc6bc590; its raw
Actions log is retained without treating it as signed PCC scientific standing.
[pcc:unverified]

Crypto’s original PR3877 remains subject to its current-main ledger-prefix
fork and historical archived-receipt gates. No history or verifier was
rewritten. S3 checkpoint credentials, live IsoLab budget/capacity, KB/ecdb and
the autoresearcher vault binding remain unavailable. No performance run has
been launched. The queue is crypto issue3904; locked-atlas integration stays
in its source handoff.

Primary sources: Galbraith corrected ch.8 §8.3,ch.10 §§10.3–10.4/10.6;
Kunzweiler,DCC92(2024),DOI10.1007/s10623-024-01366-1,Propositions7–8.
The new arithmetic covers bounded fixtures; independent signed validation,
full geometric formalization and any computational advantage remain open.
