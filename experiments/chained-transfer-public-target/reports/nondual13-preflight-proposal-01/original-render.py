"""Render only the prospective protocol and already recorded primary/source review."""
from pathlib import Path
import json,subprocess,typst,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/nondual13-preflight-proposal-01';p.mkdir()
assert not(s/'nondual13-preflight').exists()
identity='N4-E13-short-936b863521fdce08d2724c468f27979cb39d9443d082b4be14209bb08f408414'
(p/'flow.dot').write_text('''digraph prospective {
 graph[rankdir=LR,bgcolor="white",fontname="DejaVu Sans",nodesep=.18,ranksep=.25];
 node[shape=box,style="rounded",fontname="DejaVu Sans",fontsize=9,margin=.10];
 edge[style=dashed,fontname="DejaVu Sans",fontsize=8,color="#a57535"];
 e1[label="Actual E1/K\\nN4-E13-short-\\n936b863521fdce08d2724c468f27979c\\nb39d9443d082b4be14209bb08f408414",color="#295477"];
 e2[label="Candidate E2/K: UNKNOWN\\ngamma2 kernel lambda2\\nold dual lambda4 is control",color="#a57535"];
 torsion[label="All64 actual product2-torsion points\\nFrobenius / addition / pairings\\ntransport full J1 gluing kernel"];
 model[label="Matched F223 model: UNKNOWN\\nchoose by transported mask first\\nretain nonsquare / unsupported",color="#a57535"];
 future[label="Future complete Jacobian hop\\nseparate protocol and implementation\\nno map or cost result yet"];
 e1->e2[label="proposed degree13"];e2->torsion;torsion->model;model->future;
}''')
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
(p/'flow.diagram.json').write_text(json.dumps({'status':'prospective; no new preflight implementation or result','protocol':'../../NONDUAL13_PREFLIGHT_PROTOCOL_01.md','source_review':'PCC-20261114-448588','source_revision':'5ac59843a0cc6546b0f007c0bd2f79212d169c43','producer':'3d49af7f3d0a28e76b79e4825c9d2324e85853d2','E1':identity,'J1':'Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4','E2':'unknown','J2':'unknown','all_new_arrows':'proposed, not completed native evidence','canonical_graphs_checked':['../norm-halving-results-01/flow.dot','../beta-complete-rational-01/complete-diagram.dot','../norm-arithmetic-proposal-01/flow.dot'],'graph_decision':'Existing accepted first-hop and census accounting graphs remain current at their scopes. This is a separate prospective continuation; no new quantitative graph before results.','scope':'elliptic/model preflight only; second complete Jacobian map and calibrated DLP comparison remain separate'},indent=2)+'\n')
(p/'report.typ').write_text(r'''#set page(paper: "a4", margin: 14mm)
#set text(font: "DejaVu Sans", size: 9.2pt)
#set par(leading: .48em)
#set heading(numbering: none)
#let d=json("flow.diagram.json")
#text(size: 17pt, weight: "bold")[A genuine second degree-13 hop]
#v(3pt)
#text(fill: rgb("#a57535"), weight: "bold")[PROSPECTIVE / UNSIGNED · elliptic and model preflight]

The existing first hop has complete rational Jacobian evaluators. The next construction must use an actual new kernel, preserve the DLP, and descend to an admissible prime-field model. This proposal tests that prerequisite; no second Jacobian map, endpoint or computational advantage has been established.

#image("flow.svg", width: 100%, height: 48mm, fit: "contain")

== Distinguish a real continuation from the dual
Use the actual E1 over K = F223[z]/(z³−3), frozen original order11092292 and prime ell2773073. Extract its lambda2 degree13 kernel with the original Frobenius/division-polynomial and Elkies routines. The existing dual uses lambda4. Retain whole maps and both[13] identities. For the degree169 composite, require the gcd with psi13(E0)² to retain exactly the first degree12 denominator; the backtracking[13] control retains degree168. This is a prediction with explicit separability, degree and pole obligations, not a result inferred from degrees or j values.

== Carry the actual gluing kernel before selecting a model
Apply gamma2 and both coefficient conjugates to every product2-torsion point. Check all64 coordinates, all addition pairs, Frobenius and4096 pairings. Transport the full current HLP(1,0) geometric kernel. Independently enumerate the product Lagrangians and match the new mask before observing square-D, smoothness or model admissibility. Keep every root/sign model and every nonsquare, singular, hyperelliptic-required or duplicate outcome. Do not retwist or choose a different square model after seeing the answer.

== Scope, controls and limits
New code is additive;929 original inputs, existing constructors, engines and21 workflows remain immutable. First replay the original model panel exactly. Preserve actual altered-target and dual-backtracking negatives, all five public targets and cofactor/odd controls. Each unfiltered serial native phase has900s build/native bounds and2GiB memory; these are correctness limits, not benchmark admission. Keep whole output, sources and actual binaries. Formalize feasible faithful implications, preserve the actual geometry bridges, and perform strict published-source replay/CI after completion.

== Next decision
An elliptic success alone does not complete the matched prime-field model requirement. An unsupported matched model remains a negative for this route. A supported endpoint leads to a separate protocol for complete second-hop Jacobian coordinates, dual compositions, inverse and source recovery, followed by full cold/online costs against the strongest ECDLP references. The current01e617 arithmetic census remains a separate running study; this proposal does not complete it.

#text(size: 7.4pt)[E1: #d.E1]

#text(size: 7.4pt)[J1: #d.J1]

#text(size: 8pt)[Sources: NONDUAL13_PREFLIGHT_PROTOCOL_01.md; original odd-source, odd-product-models and transported-kernel implementations; primary review448588 with Sutherland2025Lectures4§4.15,5§5.8/5.11 and Cor5.10,22 opening graph discussion. KB/atlas wrapper127 and locked vault limit prior-work access; no novelty or absence claim. Existing first-hop/census graphs remain unchanged at their frozen scopes.]
''')
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Prospective nondual13 elliptic/model preflight

This proposal accompanies [the prospective protocol](../../NONDUAL13_PREFLIGHT_PROTOCOL_01.md). It proposes an actual second lambda2 kernel on E1, an exact backtracking control, all64 two-torsion transports and selection of the prime-field model by the transported geometric kernel before model admissibility is observed. The endpoint and second Jacobian map are unknown; no cost result is claimed. [pcc:unverified]

[PDF](report.pdf) · [editable diagram](flow.dot) · [SVG](flow.svg) · [metadata and complete current IDs](flow.diagram.json) · [source and primary review448588](../../evidence/norm-halving-operation-review-01/sources-and-review.json). The protocol names complete polynomial/native/public/cofactor controls, written/formal obligations, immutable sources and900s/2GiB correctness limits. [pcc:unverified]

The accepted norm-halving, complete-beta and prospective census graphs were checked and remain current at their original scopes. New diagram arrows are proposed. No quantitative plot is appropriate before new results. Primary review includes Sutherland2025Lectures4,5,22; inaccessible KB/atlas/vault gives no novelty or absence inference. [pcc:unverified]
''')
(p/'render.py').write_text('''"""Rendering only; no research arithmetic or measurements."""
from pathlib import Path
import subprocess,typst
p=Path(__file__).resolve().parent
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
''')
shutil.copyfile(__file__,p/'original-render.py')
print('prospective PDF bytes',(p/'report.pdf').stat().st_size)
