# CT21 seven-chain checkpoint

The canonical written proof is [SEVEN_CHAIN.md](SEVEN_CHAIN.md), byte-identical
to crypto:SEVEN_CHAIN_PROOF.md with SHA256
be2b66c9f5327a07d7b6c0b3960b5f16a9d1d1a08389a6dd5130254f1e4168ec.
It is frozen under consumer PCCd0441a and root PCCeb3240. All scientific
standing is unsigned. [pcc:unverified]

## Actual maps and evidence

Over F101, the accepted T0 sextic is [31,75,74,54,71,55,1]; the new T1
sextic is [95,26,19,27,94,91,1]. Psi has degree49 and both polarized
dual norms[7]. The full geometric kernel inclusion, regular quotient,
global descent sign witness and elliptic embedding/trace/j argument are
written in the proof. This reaches an unpolarized F101 Jacobian that is
not isomorphic to T0. No algebraic-closure distinction or solver gain is
claimed. [pcc:unverified]

| Stage | Immutable evidence | Record, unsigned |
|---|---|---|
| Actual49-point Phi kernel,2401 additions,Frobenius5/6 | evidence/seven-torsion-kernel-01.txt;source01 | b9242a |
|64 lifts,16-class Phi2 action,256 additions,Frobenius | evidence/seven-two-action-02.txt;source02 |2f72c8 |
| Actual R1,both complete12317-class domains | evidence/seven-richelot-full-03.txt;torsion/richelot source03 |c2a691 |
| All16 geometric composite-kernel cases,12 elliptic intersections | evidence/seven-chain-geometric-05.txt;source05 |c1b585 |
| All109 source scalars,naive comparison,reverse28/inverse74/direct4 | evidence/seven-chain-source-06.txt;source05 |afd0a9 |
| Both complete Psi domains and correct exact equations | evidence/seven-chain-full-08.txt;identity-source-10.txt |2b4435 |
| Complete guard25native/65reference unit+two integrations | evidence/seven-chain-complete-11.txt;source10 |2dc32d |
| Third integration:all120 geometric branch automorphisms per target | evidence/seven-chain-automorphisms-integration-12.txt;tests/richelot_automorphisms.rs |c2a806 |
| Written global proof | SEVEN_CHAIN.md |d0441a |

The full graph tests evaluate every class once per immutable map. Exact
canonical class keys then reuse those actual outputs for both norms and
12317 deterministic paired-addition cases in each direction. This retains
all cases and includes both complete rational domains; it is not all12317²
addition pairs. No production evaluator uses a corpus or a scalar label.
The direct halving evaluator and quarter-coordinate evaluator agree on all109
original source points. Quarter inverses are82/85 on109/113; source inverse28
is74. [pcc:unverified]

Strict all-target Clippy13 passes including the third integration. Source
guards and formatting pass in the complete guard. Consumer scoped benchrec
checks16 records successfully. The local ledger has a valid append-only
chain/prefix relative to frozen2450815e2; that is distinct from the failed
current-main prefix requirement below. No full root-library rerun was made.
[pcc:unverified]

## Corrections and preserved failures

Unsigned9b9e0a mistyped the first two nonconstant T0 coefficients in its
claim prose. Correcting record2b4435 explicitly supersedes that source-equation
assertion: actual T0 is [31,75,74,54,71,55,1]. Every evaluator used the
unchanged actual constructor. Fresh receipt10 prints and asserts the correct
source/target equations and repeats the109-source check. The wrong claim,
its ledger row and every receipt remain unchanged. [pcc:unverified]

Native chain04 failed compilation on an uninferred array length;05 corrects
only the annotation. Clippy07 failed RNG literal grouping;09 preserves the
same seed value and passes. The root automorphism adapter initially supplied
an array to the existing polynomial API's Vec argument; that compile failure
and corrected result are preserved upstream. The new Lean module initially
needed an explicit scalar-zero rewrite; both failed and passing logs remain.
No validator, kernel check, axiom policy, arithmetic engine or acceptance
corpus was weakened. [pcc:unverified]

## CI and immutable ledger obstruction

Parent PR1484 freezes2450815e2. Focused43085588914 succeeds with25native/
57reference unit+two integrations and one old ignored benchmark. Required
store/gate/records and all CodeQL completed. Separate cppcheck/clang-tidy
jobs contain real findings in unchanged C files; full logs are archived as
standard xz with raw/archive digests in evidence/seven-phi-ci-observation-01.json.
They are not described as DNS failures or clean-code passes. [pcc:unverified]

Main advanced to fb3f88a03 through1485/1486, adding five checkpoint-bypass
ledger rows. Main61/frozenPhi60 share only56 rows. Prefix verification fails
and PR1484 is dirty; both histories remain intact. PCC9c0b68 and
evidence/seven-consumer-ledger-fork-01.json retain the comparison. Canonical
problem: crypto:problems/chained-transfer-admission-and-ledger-sync.md.
No rebase, force, lineage choice, rechain, claim deletion or protection bypass.
New research can be checkpointed and reviewed while merge remains blocked.
[pcc:unverified]

The focused workflow retains manual/main events and increases timeout25→45
minutes for the added complete corpora and cold builds. It does not add an
expensive PR event, ignore a new test or reduce correctness scope. Final-head
focused replay must contain25native/65reference unit+three integrations and
the one previously ignored benchmark. Do not infer that CI ran from a local
pass or a predecessor's success. [pcc:unverified]

## Reproduce and continue

Use Rust1.99.1 and run check.sh. Upstream75a737b8 native/seven/separate102/
five-input source manifests remain unchanged; old field, elliptic, Cantor
and gluing engines are reused. The root automorphism example and consumer
third integration are byte-identical. Lean4.35.0 checks ten new conditional
helpers across ChainTransport/RichelotDescent, with90 written source lemmas
total. Actual geometry and Torelli remain explicit written dependencies.
Sources and hashes are in the proof and immutable snapshots. [pcc:unverified]

Next CT22 develops direct base-field formulas for both elliptic quotient
norms of a balanced class, including repeated support, zero support and
infinities. Compare against both existing norms on all12317 classes of C0
and C1, then integrate only after source/whole-map controls. This is proposed
arithmetic engineering, not an admitted performance result. S3/livebudget
still block benchmarks, solvers and paid allocation. Root ledger/archive,
KB/ecdb and vault-locked atlas8edec422a remain separate open requirements.
[pcc:unverified]
