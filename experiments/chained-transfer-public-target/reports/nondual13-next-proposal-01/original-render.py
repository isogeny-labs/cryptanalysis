"""Prospective diagram/report rendering only; no research computation."""
from pathlib import Path
import json,subprocess,shutil,textwrap,typst
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/nondual13-next-proposal-01';p.mkdir()
e2='N4-E13x13-short-2088c9e2bd44dfea66094a767e22a1f2ebffdd4e963244cb320d93408e58b4b5'
label=json.dumps('actual E2 / K\n'+'\n'.join(textwrap.wrap(e2,40))+'\nG2 fixed mask1155175778390933505\nmatched HLP(2,1): D12 nonsquare')
(p/'flow.dot').write_text('''digraph proposed {graph[rankdir=TB,bgcolor="white",ranksep=.35];node[shape=box,style=rounded,fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=9];E2[label='''+label+''']; E3[label="E3 / K: NOT CONSTRUCTED\\nno curve ID or outcome yet",style="rounded,dashed"]; G3[label="same transported G3\\nfix full mask BEFORE model builder\\nall six models retained",style="rounded,dashed"]; E2->E3[label="PROPOSED single lambda2 degree13 edge\\ncompare actual old-dual lambda4",style=dashed];E3->G3[label="PROPOSED all64 actual conjugate transports\\n4096 additions/pairings;135 masks",style=dashed];}''');subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
(p/'report.typ').write_text(r'''#set page(paper:"a4",margin:15mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(leading:.55em)
#text(size:18pt,weight:"bold")[One more fixed edge, the same gluing kernel]
#v(4pt)
#text(fill:rgb("#a57535"),weight:"bold")[PROSPECTIVE PROTOCOL · no third-edge code or E3 result]

The previous fixed second-hop model failed supplied-source acceptance: its unique HLP(2,1) match is smooth with nonsquare D12. Preserve that result. This new descriptive study takes exactly one more lambda2 elliptic edge and asks whether the same transported kernel has an admissible prime-field model.

#image("flow.svg",width:100%,height:77mm,fit:"contain")

== Elliptic gate
Reconstruct actual gamma2 through the unchanged Kohel engine and compare all coefficients. Construct gamma3 and its actual lambda4 dual. Check both signed[13] identities, whole curve/separability identities and the exact middle169 composite E1→E3. Its denominator intersection with psi13(E1)² must be the complete degree12 gamma2 denominator. Substituting the old dual must actually give168 and reject101.

== Fixed full-kernel gate
Retain complete E0/E1/E2 parity and the unsupported E2 row. Transport the SAME full kernel through gamma3 and both coefficient conjugates; check64 points,4096 additions/original alternating pairings,Frobenius and135 independent masks. Fix the new mask before reading square-D or smoothness. Retain all six cases; never retwist or reselect after seeing the outcome.

== Bounds and interpretation
Publish protocol before code and exact source checkpoint before native execution. Versioned120s builds;900s/2GiB per unfiltered native phase; whole outputs/source/actual executable custody and real rejection controls. No timing benchmark. A positive model requires a separate complete Jacobian-map protocol and direct-composite baseline. A negative or timeout remains preserved. Full2197 expansion is outside this bounded phase; sequential original public-target checks remain required.

#text(size:8pt)[Sources: NONDUAL13_NEXT_EDGE_PROTOCOL_01.md; source5ea2ab3c/native27fb3a/report14b605; original phaseA252fd8 and generic norm-product Lean theorem; Sutherland2025Lectures4/5/22, HLP math/9809210 Proposition15 and following remark. Original929inputs/prior21workflows stay immutable. No E3, Jacobian-map, novelty, signed execution or computational-advantage result is asserted. Vault/KB and benchmark-admission limitations remain separate.]
''');typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Prospective fixed third-edge preflight

[Protocol](../../NONDUAL13_NEXT_EDGE_PROTOCOL_01.md) freezes exactly one additional lambda2 edge on actual E2, its middle169 rational/nondual controls and the same full-kernel transport before model admissibility. Existing native27fb3a remains negative for the intermediate supplied-source model; no retwist or alternate case is chosen. No successor implementation or E3 result exists yet. [pcc:unverified]

[PDF](report.pdf) · [editable proposed diagram](flow.dot) · [SVG](flow.svg). The diagram marks every new edge and vertex proposed. No cost graph exists because no new data have been measured. Whole original source, native outputs, negative controls and primary references remain linked through the protocol. [pcc:unverified]
''');shutil.copyfile(__file__,p/'original-render.py');print('PDF bytes',(p/'report.pdf').stat().st_size)
