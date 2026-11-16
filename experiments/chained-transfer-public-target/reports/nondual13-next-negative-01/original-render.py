"""Render the Rust-projected native fields; no research arithmetic in Python."""
from pathlib import Path
import json,subprocess,shutil,textwrap,typst
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/nondual13-next-negative-01';p.mkdir(exist_ok=True)
shutil.copyfile('/workspace/scratch/ct77-next-native-audit-01/report-data.json',p/'data.json');d=json.loads((p/'data.json').read_text())
def label(name,ident):return json.dumps(name+' / K\n'+'\n'.join(textwrap.wrap(ident,37)))
(p/'flow.dot').write_text('''digraph actual {graph[rankdir=TB,bgcolor="white",ranksep=.35,nodesep=.3];node[shape=box,style=rounded,fontname="DejaVu Sans",fontsize=9];edge[fontname="DejaVu Sans",fontsize=9];
E2[label='''+label('E2',d['E2_id'])+'''];E3[label='''+label('E3',d['E3_id'])+'''];{rank=same;E2;E3;}E2->E3[label="actual gamma3 / delta3: each degree13\\nboth signed[13] identities",dir=both,color="#287b80"];
G2[label="same G2 / original fixed route\\nHLP(2,1): D12 nonsquare\\nsupplied-source identification unsupported",color="#a14b35"];
G3[label="transported G3 / new fixed route\\nHLP(0,0): D24 nonsquare\\nsupplied-source identification unsupported",color="#a14b35"];
{rank=same;G2;G3;}E2->G2[style=dotted,label="retained intermediate negative"];E3->G3[style=dotted,label="mask fixed BEFORE model builder"];G2->G3[style=dashed,label="same kernel transported\\nno Jacobian map constructed",color="#a14b35"];}''');subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
table='\n'.join('['+str(row['case'])+'], ['+str(row['D'][0])+'], ['+('absent'if row['sqrt_D_in_K']is None else'present')+'], ['+('fixed match'if row['case']==d['matched_case']else'retained')+'],'for row in d['all6_model_diagnostics'])
(p/'report.typ').write_text(r'''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.45em)
#text(size:17pt,weight:"bold")[One more fixed edge, another unsupported model]
#v(3pt)
#text(fill:rgb("#a14b35"),weight:"bold")[UNSIGNED NATIVE RESULT · 6d2c97 · prospective bbfd74]

The fixed third elliptic edge exists and its middle degree169 composite is nonbacktracking. The SAME transported gluing kernel uniquely matches HLP(0,0), smooth with nonsquare D24. The required supplied-E3 Jacobian identification is unsupported. Preserve both this result and the intermediate E2,D12 failure; no retwist or alternate case is selected.

#image("flow.svg",width:100%,height:53mm,fit:"contain")

#table(columns:(1fr,1fr,1fr,1.4fr),inset:3pt,
[*HLP case*],[*D in F223*],[*sqrt(D) in K*],[*Selection status*],
'''+table+r''')

== Exact elliptic and transport evidence
The new E3 has a=(99,74,32),b=(192,90,87) over K=F223[z]/(z³−3). Both whole signed[13] identities hold. The middle169 composite has zero curve residual, nonzero derivative, coprime169/168 x degrees and exact degree12 kernel intersection. The actual old second dual gives168 and rejects101. All36/36 points,1024 additions each way,four2-torsion images and five original public targets pass; reversed sequential maps give[2197] on those targets. No whole2197 expansion is claimed.

The model phase retains entire E0/E1/E2 parity and the old nonsquare failure. All64 actual coordinate transports,three conjugate maps,Frobenius,4096 additions/original alternating-pairing rows and135 independent masks are checked. The fixed G3 mask9511681577844867105 is printed before the six-model builder. All outcomes remain in the raw data. A smooth F223 quartic with P0=(1:0:217) exists; the required supplied-source identification does not follow.

== Whole-record controls and mathematical scope
One unfiltered test passes in each phase. All FIVE elliptic and NINE model records compare exactly without masks; both actual prior-constructor record occurrences are retained and crosschecked. Removing an actual complete PUBLIC or MATCHED_MODELS record rejects101/no accepted output. Source guards and original-compiled/runtime executable equality pass after the exact clean-source checkpoint.

Both original Lean gates accept the finite223-residue nonroot theorem for12/24, zero trusted; exact local bindingee88e7 passes (unsigned). Failed default-recursion proof01 is retained; bounded02 changes no statement. Field primality, the odd-extension tower law, polarized quotient geometry and program correspondence remain separate. The cyclic169 argument reuses the written degree/pole/torsion bridges and generic norm-product theorem. HLP Proposition15 identifies over sqrt(T),D=16*T; this is not a universal Jacobian nonexistence theorem. E3's j-orbit is disjoint from E0/E1/E2, without a Jacobian distinction claim.

== Next task
Preserve whole data in new genuine18 and add strict replay/CI. Then change mechanism to the incomplete cold arithmetic census: prospectively optimize observer bookkeeping with whole-ledger parity controls. No further edge, complete second Jacobian map, calibrated advantage or novelty is claimed here.

#text(size:7.6pt)[Sources: sourcef0167e43/checkpoint43625626244/native6d2c97; NONDUAL13_NEXT_NEGATIVE_DERIVATION_01.md; all raw and actual binaries retained; whole150136/88312/326200/211464B XZ pending genuine18. Primary HLP math/9809210 Proposition15 and following remark, Sutherland2025Lectures4/5/22. All results unsigned; no timing benchmark or signed execution.]
''');typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# The additional fixed edge has another unsupported matched model

Native6d2c97: actual third lambda2 map and its dual pass the middle169 rational/nondual controls and all point/public checks; all five elliptic whole records compare exactly. The same full kernel transports through actual64/4096/135 controls to HLP(0,0), smooth with D24 nonsquare. The required supplied-E3 identification fails; the intermediate E2,D12 negative remains retained. All nine model whole records compare without masks or deduplication; both actual entire-record omission controls reject101/no output. These are unsigned local observations. [pcc:unverified]

[PDF](report.pdf) · [editable actual diagram](flow.dot) · [SVG](flow.svg) · [Rust projected data](data.json) · [written derivation](../../NONDUAL13_NEXT_NEGATIVE_DERIVATION_01.md) · [native scope](../../evidence/nondual13-next-native-01/scope.json). Whole raw/actual executables await new genuine18. No full2197 expansion, complete second Jacobian map, universal nonexistence, calibrated ECDLP advantage or novelty is established. The next mechanism is the incomplete cold arithmetic census, under a new prospective observer protocol. [pcc:unverified]

Supplemental finite residue proof68cd8c has both original434/435 gates and exact local bindingee88e7 passing, zero trusted. It proves all223 canonical Nat residues square to neither12 nor24, using kernel decision. Field primality/encoding, the tower law and geometry remain separate. Failed default-recursion01 and accepted bounded02 preserve the same statement. [pcc:unverified]
''');shutil.copyfile(__file__,p/'original-render.py');print('PDF bytes',(p/'report.pdf').stat().st_size)
