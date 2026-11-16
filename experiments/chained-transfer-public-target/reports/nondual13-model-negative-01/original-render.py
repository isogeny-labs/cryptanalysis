"""Render literal Rust diagnostics; no research calculations in Python."""
from pathlib import Path
import json,subprocess,shutil,textwrap,typst
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/nondual13-model-negative-01';p.mkdir(exist_ok=True)
shutil.copyfile('/workspace/scratch/ct77-nondual-model-obstruction-02/report-data.json',p/'data.json');d=json.loads((p/'data.json').read_text())
old=json.loads((s/'reports/nondual13-phaseA-01/data.json').read_text())
def wrapped(value):return '\n'.join(textwrap.wrap(value,37))
nodes='\n'.join(name+'[label='+json.dumps(name+' / K\n'+wrapped(old[name+'_id']))+'];'for name in ['E1','E2'])
(p/'flow.dot').write_text('''digraph actual {graph[rankdir=TB,bgcolor="white",nodesep=.18,ranksep=.35];node[shape=box,fontname="DejaVu Sans",fontsize=8,style=rounded];edge[fontname="DejaVu Sans",fontsize=8];
'''+nodes+'''
{rank=same; E1; E2;}\n{rank=same; J1; C2;}\nE1->E2[label="actual gamma2: degree13\\nall64 product2-torsion transports",color="#287b80"];
J1[label="current J1 / F223\\n'''+wrapped('Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4').replace('\n',r'\n')+'''",color="#295477"];
C2[label="matched HLP(2,1) quartic / F223\\nsmooth; rational P0=(1:0:181)\\nD=12; no sqrt(D) in K\\nno supplied-source transfer ID",color="#a14b35"];
J1->C2[label="required second Jacobian map\\nUNSUPPORTED",style=dashed,color="#a14b35"];
E1->J1[style=dotted,label="original matched HLP(1,0)"];
E2->C2[style=dotted,label="same transported kernel\\nmask fixed BEFORE model builder"];
}''');subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
table='\n'.join('['+str(row['case'])+'], ['+str(row['D'][0])+'], ['+('absent'if row['sqrt_D_in_K']is None else'present')+'], ['+('fixed match'if row['case']==d['matched_case']else'retained')+'],'for row in d['all6_model_diagnostics'])
(p/'report.typ').write_text(r'''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.45em)
#text(size:17pt,weight:"bold")[The fixed second-hop model is unsupported]
#v(3pt)
#text(fill:rgb("#a14b35"),weight:"bold")[UNSIGNED NEGATIVE RESULT · claim27fb3a · protocol23ab48]

The actual second elliptic hop exists. Its full transported gluing kernel uniquely matches HLP(2,1), whose discriminant is D=12. This is nonsquare in K=F223[z]/(z³−3). The matched prime-field quartic is smooth and has a rational point, but the supplied-source Jacobian identification is unsupported. No second Jacobian map or computational gain follows.

#image("flow.svg",width:100%,height:60mm,fit:"contain")

#table(columns:(1fr,1fr,1fr,1.4fr),inset:3pt,align:left,
[*HLP case*],[*D in F223*],[*sqrt(D) in K*],[*Selection status*],
'''+table+r''')

== What was actually checked
One unfiltered native test passes with all64 coordinate transports, three actual coefficient-conjugate maps, Frobenius, all4096 addition/pairing rows and135 independent original masks. The pairing is the original alternating2-torsion form, not a Miller implementation. Both entire old model panels agree exactly. Original Adapter/NormNew checks the full starting J1 tag. The target mask is fixed before model construction and before reading smoothness or square-D.

All six whole records compare exactly without masks. Removing the actual complete MATCHED_MODELS record rejects101/no accepted output. Source guards and actual compile/runtime executable equality pass. These are local unsigned observations; a passing census does not mean endpoint acceptance.

== Independent arithmetic and the mathematical boundary
A separate Rust loop retains all223 base-field squares and excludes12; another gives12^111=222 modulo223. A quadratic root cannot lie in a degree3 extension by the tower law. Original quotient identities have coefficients D*A_i and D²*B_i and require sqrt(D) for the specified source. HLP Proposition15 gives its polarized identification after adjoining sqrt(T), with D=16*T. This records failure of the supplied-source construction, not universal nonexistence of any F223 Jacobian for the ppav.

== Frozen failure and the next experiment
No retwist or alternate square case is selected. A later fixed elliptic edge may be studied under a new prospective protocol, transporting the same full kernel and preserving this intermediate failure. Complete Jacobian maps, faithful global formalization, strict replay/CI and calibrated computational comparison remain open.

#text(size:7.6pt)[Exact quartic coefficients in the original15-monomial order: 1,164,176,127,109,75,91,157,56,179,142,133,28,43,94. P0=(1:0:181). Fixed transported mask1155175778390933505.]

#text(size:7.6pt)[Sources: source87b61e80; original checkpoint492150; native27fb3a; NONDUAL13_MODEL_NEGATIVE_DERIVATION_01.md; original odd-product-models quotient formulas; Howe–Leprévost–Poonen math/9809210 Proposition15 and following remark, printed24–26. All whole raw/actual binaries retained; large217960B/150556B XZ await genuine18. Primary PDF/text already genuine17. No signed execution, novelty or calibrated advantage.]
''');typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Unsupported matched model on the fixed second hop

Native27fb3a fixes the entire transported kernel before model admissibility. Its unique HLP(2,1) match is smooth with D=12, nonsquare in the frozen cubic field. The smooth F223 quartic exists; its identification with the specified E2 product is unsupported. The original endpoint requirement stays open. All six outcomes remain retained, with no retwist or alternate selection. [pcc:unverified]

The native census passes one unfiltered test, all64 actual coordinate transports,4096 addition/pairing rows,135 independent original masks, both old full model panels and starting J1 original constructor identity. All six whole records compare exactly; omission of the entire actual matched record rejects101/no output. A separate Rust prime-field diagnostic retains all223 squares and excludes12. These are unsigned observations, not signed execution. [pcc:unverified]

[PDF](report.pdf) · [editable diagram](flow.dot) · [SVG](flow.svg) · [Rust projected diagnostics including all223 square rows](data.json) · [written derivation and exact scope](../../NONDUAL13_MODEL_NEGATIVE_DERIVATION_01.md) · [native custody](../../evidence/nondual13-model-native-01/scope.json). Whole large native data and actual binaries are preserved pending new genuine publication18. [pcc:unverified]

The phaseA report is a historical elliptic preflight. This report resolves its proposed full product/model step negatively for the fixed route. No second Jacobian map, universal nonexistence, ECDLP advantage or novelty claim is established. [pcc:unverified]
''');shutil.copyfile(__file__,p/'original-render.py');print('PDF bytes',(p/'report.pdf').stat().st_size,flush=True)
