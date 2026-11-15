"""Render only native Rust record projections and the explicitly conditional proof."""
from pathlib import Path
import json,subprocess,shutil,textwrap,typst
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/nondual13-phaseA-01';p.mkdir();raw=Path('/workspace/scratch/ct76-nondual13-audit-01');shutil.copyfile(raw/'report-inputs.json',p/'data.json');d=json.loads((p/'data.json').read_text())
def label(name):return name+' / K\\n'+'\\n'.join(textwrap.wrap(d[name+'_id'],35))
nodes='\n'.join(name+' [label='+json.dumps(label(name))+',color="'+('#347d83'if name=='E2'else'#295477')+'"];'for name in ['E0','E1','E2'])
(p/'flow.dot').write_text('''digraph actual {graph[rankdir=LR,bgcolor="white",fontname="DejaVu Sans",nodesep=.17,ranksep=.35];node[shape=box,style="rounded",fontname="DejaVu Sans",fontsize=9,margin=.1];edge[fontname="DejaVu Sans",fontsize=8];\n'''+nodes+'''
 E0->E1[dir=both,label="gamma1 / delta1\\neach degree13; both[13]"];E1->E2[dir=both,label="gamma2 / delta2\\neach degree13; both[13]"];
 E0->E2[label="Gamma degree169; gcd12",color="#347d83"];
 next[label="Phase B: all64 actual product2-torsion\\ntransport full gluing kernel\\nmatched F223 J2 UNKNOWN",color="#a57535"];
 E2->next[style=dashed,label="proposed model preflight"];
}''');subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':9});fig,ax=plt.subplots(figsize=(8.8,1.45));vals=[d['candidate_gcd_degree'],d['backtracking_gcd_degree']];ax.barh(['actual gamma2 gamma1','old dual delta1 gamma1'],vals,color=['#347d83','#b57b34']);ax.invert_yaxis();ax.set_xlabel('Degree of gcd(x denominator, psi13(E0)²) · no cost interpretation');ax.set_xticks([0,12,84,168]);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);fig.tight_layout();fig.savefig(p/'kernel-gcd.svg',bbox_inches='tight');plt.close(fig)
(p/'report.typ').write_text(r'''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.45em)
#set heading(numbering:none)
#let d=json("data.json")
#text(size:17pt,weight:"bold")[A nondual second elliptic hop]
#v(3pt)
#text(fill:rgb("#347d83"),weight:"bold")[UNSIGNED NATIVE RESULT · prime-field Jacobian model still open]

The actual second lambda2 kernel on E1 yields a separable degree13 map to E2 over K=F223[z]/(z³−3). Both new dual[13] identities and all five literal public-target controls pass. The degree169 composite passes the whole nondual kernel criterion; substituting the existing dual rejects101. This is elliptic preflight, not another completed Jacobian transfer or a computational advantage.

#image("flow.svg",width:100%,height:56mm,fit:"contain")
#image("kernel-gcd.svg",width:100%,height:32mm,fit:"contain")

== Exact maps and a discriminating negative
Original Frobenius, Elkies, Kohel, curve and division-polynomial engines are unchanged. Retain both complete new degree13 curve identities and both signed[13] rational comparisons. The composite has reduced x degrees169/168, zero whole curve residual and nonzero derivative. Its gcd with psi13² equals the first degree12 denominator. The old dual backtrack instead has the entire degree168 gcd and actually fails the same acceptance gate. No count or JSON field is edited to simulate that rejection.

== Global argument, with its hypotheses visible
For a separable odd-degree isogeny, each nonzero kernel pair contributes a double x-denominator root. The degree12 intersection therefore gives13 points including infinity in ker(Gamma) intersect E0[13]. A kernel of order169 with only13 elements killed by13 is cyclic169; it cannot be the scalar[13] kernel. This uses the standard projective-extension, pole, torsion and finite-group classification bridges stated in the derivation. Native polynomial equality does not formalize them. Both individual dual pairs imply the reversed composite[169], hence injectivity on prime ell2773073.

== Implementation checks and formal scope
One unfiltered library test passes, with36 source points,36 target points,1024 addition pairs each way, actual four2-torsion images and all five public targets checked through original source answers. Every one of the four whole records compares exactly with no masks; omitting the public record rejects101/no output. Both original Lean gates audit the general norm-product theorem and its169 specialization with zero trusted declarations. Actual curves and the cyclic geometric kernel are not Lean objects here. Failed first proof and its explicit associativity correction are retained.

== Next decisive task
Transport all64 actual product2-torsion points through gamma2 and both coefficient conjugates; check Frobenius, addition and4096 pairings. Carry the full current J1 gluing kernel and select its exact new mask before square-D or smoothness. Preserve an unsupported matched outcome instead of retwisting or selecting a different case. An admissible F223 model is required before a second complete Jacobian-map implementation.

#text(size:7.4pt)[E2: #d.E2_id]

#text(size:7.4pt)[E2 equation coefficients in basis(1,z,z²): a=(12,143,39), b=(115,82,144). Native three-conjugate j sets are disjoint from both E0 and E1; this does not classify an unconstructed J2.]

#text(size:8pt)[Sources: prospective23ab48/cf9ca8f5 before code; native252fd8/source9a30773a and checkpoint9a75e6; NONDUAL13_PREFLIGHT_DERIVATION_01.md; faithful NondualComposition module and both original proof gates; primary/source review448588, Sutherland2025Lectures4/5/22. Whole raw records, source and actual binaries remain retained pending genuine publication17. No timing price, ECDLP gain, signed execution or novelty claim.]
''');typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Actual second degree13 elliptic hop

Native252fd8 passes one unfiltered comprehensive phaseA test, both new signed[13] rational identities, the complete169 curve/separability/kernel gate, all point/addition/public checks and actual old-dual rejection101. Its actual E2 overK has a=(12,143,39),b=(115,82,144). Four whole native records compare exactly without masks; entire-public-record omission rejects101/no output. These are unsigned observations. [pcc:unverified]

[Written derivation](../../NONDUAL13_PREFLIGHT_DERIVATION_01.md) exposes every standard geometric/degree/pole/torsion/classification bridge for the cyclic169 kernel implication. The Lean norm-product and169-specialization lemmas retain individual dual-pair and scalar-linearity hypotheses; actual curves and cyclic kernel remain outside that formalization. Prior scalar recovery and F101degree7 work are reused, with no aggregate novelty count. [pcc:unverified]

[PDF](report.pdf) · [complete native report fields](data.json) · [editable actual route](flow.dot) · [SVG](flow.svg) · [kernel-gcd diagnostic](kernel-gcd.svg) · [native custody](../../evidence/nondual13-phaseA-native-01/whole-native-audit-index.json). Whole large JSON/native XZ require genuine publication17; no source outputs are truncated. [pcc:unverified]

Existing first-hop mathematical and source-arithmetic graphs remain frozen at their scope. This adds the actual elliptic E2 route and a polynomial-degree control graph. Full64product transport, matched prime-field J2, second Jacobian maps and calibrated advantage remain open. [pcc:unverified]
''')
shutil.copyfile(__file__,p/'original-render.py');print('phaseA PDF bytes',(p/'report.pdf').stat().st_size)
