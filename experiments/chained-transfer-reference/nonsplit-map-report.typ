#set page(paper:"a4",margin:17mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Operational non-split Richelot transfer over F17
2026-11-11 · Chained ECDLP Transfers · fixed full prime-order19 source

*Unsigned/unverified standing.* The actual determinant11 correspondence and
dual operate on every285 rational class. This is same-field arithmetic,
without a DLP solver or demonstrated computational advantage. PCC383894 and
bd303e bind development/full replay. [pcc:unverified]

#image("nonsplit-map.svg",width:100%)

== Actual correspondence and balanced descent
The fixed quadratic factors are a Frobenius-stable unordered triple over
F17³. Source support has degree≤2 and splits over F17². Their compositum
F17⁶ suffices: retain each target fiber as a quadratic Mumford pair, without
choosing target roots or an F17¹² splitting. Raw target ordinate w=3Y fixes
the monic normalization and dual scaling. [pcc:unverified]

For source finite degree m and infinity count n, include the full balanced
sum Σψ(P)+(2n+m−2)ψ(∞+). Individual fiber classes may retain extension
coefficients; completed outputs must descend to F17 and pass the separate
prime-field validator. Degree drops, multiplicity and infinity contributions
are explicit. [pcc:unverified]

All285 source and target classes pass both dual norms[2]; paired additivity
and285 distinct images pass. The isogeny has geometric degree4 while its
rational kernel has1 element, consistent with odd class-group order285.
All19 elliptic scalar relations survive; reversed-chain/source norm gives[4],
recovered by5 modulo19. These recover points, not unknown DLP scalars.
[pcc:unverified]

The earlier complete PGL2 audit distinguishes source/target curves overF17;
the second nondegenerate kernel gives a reflection-equivalent target. No
unpolarized-Jacobian nonisomorphism is inferred. Retain both equivalence and
degenerate cases rather than counting more destinations. [pcc:unverified]

#pagebreak()
= Independent arithmetic, algebra and remaining limits

Crypto's pre-existing flat degree6 Fpk/Rabin engine independently replays
128 tower-field products, inverses and Frobenius powers. It imports none of
the new field/map code. The explicit bridge is gamma=T+s,
s=(gamma³+11gamma+2)/(3gamma²+5), with flat modulus
gamma⁶+12gamma⁴+4gamma³+14gamma²+10gamma+14.
PCC167595 binds the TSV and passing receipt. The engine is unchanged;
only a unit test and fixture were added. [pcc:unverified]

That validates bounded extension arithmetic, not independently the entire
Jacobian map. Both balanced engines use Cantor; harnesses and receipts are
producer-authored, unsigned evidence. No signed scientific verdict is claimed.
[pcc:unverified]

Four generic core Lean lemmas pass a7-declaration gate, crypto PCCf7eb4f.
The fundamental identity for arbitrary quadratics is
ΣGi(x)[G'jGk−GjG'k](z)=−δ(x−z)².
The other certificates establish the cleared target-curve equation under
the correspondence, balanced infinity coefficient and inverse5 recovery
under19-torsion. Actual finite fields, projective/Picard extension and global
dual construction remain written inputs from the primary sources.
[pcc:unverified]

== Reproduction and retained attempts
Consumer check.sh passes exact source guards, formatting/strict Clippy,
native25/reference43 tests and1 pre-existing ignored benchmark. Receipt
nonsplit-map-pinned-01.txt is retained. Root command: cargo test --release
--bin icprog chained_nonsplit_compositum_witnesses -- --nocapture.
The minimal sparse-checkout script automatically includes the committed TSV.
The first map run passed with an import warning, subsequently cleaned;
the first new Lean module needed explicit variable-scalar rewrites. Failed
proof/format attempts and passing receipts remain separate. [pcc:unverified]

Full account: NONSPLIT_MAP.md; source src/nonsplit_map.rs. Primary references:
Kunzweiler,DCC92(2024),§§3.1–3.2,Propositions7–8;
Galbraith corrected ch.8§8.3/ch.10§10.4.2. Upstream source receipt binds bytes.

== Next bounded task
CT15 predeclares shift2 of the existing E109/F101 source after this pipeline
validation. The shifted cover family is prior art, and the unshifted6-cycle
negative remains retained. No shifted map is yet accepted. Larger fields,
catalog/production integration and independent signed validation remain open.
[pcc:unverified]

No benchmark, cost ratio, solver comparison or paid job ran. S3/live-budget,
KB/vault and crypto frozen-ledger/archive blockers remain. No prime-field
attack or cross-prime descent is established. Canonical graphs remain current:
no signed scientific or measured performance edge has been promoted.
