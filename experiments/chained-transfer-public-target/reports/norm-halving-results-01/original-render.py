"""Render recorded Rust values only; no research calculations or inference."""
from pathlib import Path
import json,shutil,subprocess
import typst
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/norm-halving-results-01';p.mkdir()
shutil.copyfile('/workspace/scratch/ct74-norm-halving-audit-02/report-inputs-05.json',p/'recorded-inputs.json')
d=json.loads((p/'recorded-inputs.json').read_text())
rows=[('Shared packet parse','common_packet_parse'),('Shared complete norm / geometry','common_complete_norm_and_geometry_admission'),('Shared full-order Jacobian scalar','common_full_group_order_scalar'),('Transfer Jacobian CRT projection','transfer_jacobian_crt_projection'),('Transfer elliptic half-odd scalar','transfer_elliptic_half_odd_scalar'),('Transfer prime-field Phi','transfer_prime_field_phi'),('Transfer quartic factorization','transfer_quartic_root_factorization'),('Transfer ordinate recovery','transfer_generic_ordinate_recovery'),('Transfer explicit double check','transfer_explicit_double_check'),('Transfer quadratic source Phi','transfer_quadratic_source_phi'),('Transfer quadratic target Phi','transfer_quadratic_target_phi'),('Transfer source isogeny','transfer_source_isogeny')]
fig,ax=plt.subplots(figsize=(7.3,3.45));fig.subplots_adjust(left=.44,right=.97,bottom=.16,top=.91)
ys=list(range(len(rows)))
ax.barh([y-.17 for y in ys],[d['baseline_calls'].get(k,0)for _,k in rows],height=.31,color='#a57535',label='Strong scalar baseline')
ax.barh([y+.17 for y in ys],[d['direct_calls'].get(k,0)for _,k in rows],height=.31,color='#366c68',label='Direct norm-halving')
ax.set_yticks(ys,[name for name,_ in rows],fontsize=8);ax.invert_yaxis();ax.set_xticks(range(9));ax.set_xlabel('Recorded selected entries on one actual generic row',fontsize=8);ax.tick_params(axis='x',labelsize=8);ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True);ax.legend(fontsize=8,loc='lower right',frameon=False);ax.set_title('Call-site comparison — entry kinds have different costs',fontsize=10,loc='left')
fig.savefig(p/'selected-calls.svg');fig.savefig(p/'selected-calls.png',dpi=150);plt.close(fig)
dot=r'''digraph actual {
 graph [rankdir=LR,bgcolor="white",fontname="DejaVu Sans",nodesep=.19,ranksep=.25];
 node [shape=box,style="rounded",fontname="DejaVu Sans",fontsize=10,margin=.08];
 edge [fontname="DejaVu Sans",fontsize=8,color="#566970"];
 x[label="J0(F223): admitted x\nshared full norm + ORDER scalar",color="#295477"];
 q[label="Q=N0(x) in E(K)"];
 b[label="Strong scalar baseline\n[1386537]Q and x2=[ell]x",color="#a57535"];
 bp[label="Psi([1386537]Q)\nsubtract beta(x2)"];
 h[label="Direct norm-halving\nall four [2]a=Q in E(L)",color="#366c68"];
 c[label="actual E[2](K) correction t\nPhi0(t)=x-Phi0(a)\nreturn Psi(a)+Psi(t)"];
 y[label="J1(F223): beta(x)\nwhole outputs equal complete-C",color="#295477"];
 x->q; q->b; q->h; b->bp; h->c; bp->y; c->y;
}'''
(p/'flow.dot').write_text(dot);subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
meta={'status':'finite native equality / conditional formal algebra / unsigned','native_claim':'PCC-20261114-7ff793','lean_claim':'PCC-20261114-3ba28f','auxiliary_claim':'PCC-20261114-d91395','old_model':'Ciani-Jac-pi0-v2-3ba99ad5742ad62540f8addbbe153572696d2e595f64cd2c1b0b52e51ff351a4','new_model':'Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4','source':'../../NORM_HALVING_DERIVATION_01.md','dataset':'recorded-inputs.json','graph_scope':'arrows are native-tested evaluation routes; no execution standing or primitive pricing','prior_graphs_checked':['../norm-halving-proposal-01/flow.dot','../beta-complete-rational-01/complete-diagram.dot','../beta-rational-lift-01/lift-diagram.dot'],'prior_graph_decision':'prior frozen diagrams retain original scopes; this separate results diagram adds actual native results'}
(p/'flow.diagram.json').write_text(json.dumps(meta,indent=2)+'\n')
(p/'report.typ').write_text(r'''#set page(paper: "a4", margin: 13mm)
#set text(font: "DejaVu Sans", size: 9.1pt)
#set par(leading: 0.5em)
#set heading(numbering: none)
#let d=json("flow.diagram.json")
#text(size: 18pt, weight: "bold")[Complete norm-halving transfer]
#v(3pt)
#text(fill: rgb("#366c68"), weight: "bold")[FINITE CORRECTNESS / UNSIGNED · computational advantage open]

The new direct evaluator and stronger scalar baseline produce the immutable complete-C degree13 Jacobian transfer on the declared finite panel. Native05 passes all four unfiltered tests; all892 inputs stay unchanged. Entire prior three native JSON records are identical, with no ignored fields. (7ff793; earlier52c01c.)

#image("flow.svg", width: 100%, height: 60mm, fit: "contain")
#text(size: 8pt)[Solid arrows describe native-tested routes at the fixed instance. They do not certify a general geometric construction or a priced cost improvement.]

== Correct the half before evaluation
For every admitted x, the existing odd/cofactor decomposition supplies a full elliptic lift a0 in E(L), with Phi0(a0)=x and 2a0=N0(x). Every half a of N0(x) differs from a0 by E[2](K). Look up t with Phi0(t)=x−Phi0(a), then use the explicit quotient square beta Phi0=Psi:
#raw("Psi(a)+Psi(t)=Psi(a+t)=beta(x).", block: true)
Every four actual halves is checked. The runtime includes quadratic Phi/Psi, the source isogeny, dictionary, curve checks, origin subtraction and rational output check. The direct transfer core has no CRT or half-odd scalar. Common admission still includes the full-order Jacobian scalar. Full inverse still uses the Jacobian scalar3413013.

== Declared checks and negative controls
448 exceptional classes;48 mixed cases;40 public sector/direction rows;96 addition pairs; both new-map compositions equal[13]; full new inverse; original independent public source recovery. The48 coordinate targets match the literal selector, with infinity, nonzero two-torsion, generic and non-K halves. Changed quartic constant, zero denominator and incorrect coordinate-F controls are retained. Both deliberately shifted origins fail original odd-membership validation. The missing whole-record canary exits101. (7ff793/d91395.)

== Exact fields and models
K=F223[z]/(z³−3), L=F223[w]/(w⁶−3), z↦w²; K-Frobenius on L is F³. E: a=(214,144,205), b=(137,218,9); E13: a=(196,168,69), b=(8,82,207). Full quartics and origins retain the frozen complete-C identities.

#text(size: 7.7pt)[J0: #d.old_model]

#text(size: 7.7pt)[J1: #d.new_model]

#pagebreak()
#text(size: 17pt, weight: "bold")[Calls, proofs and remaining obligations]

#image("selected-calls.svg", width: 100%, height: 84mm, fit: "contain")
#text(size: 8pt)[The chart renders actual selected entries from one recorded generic input. Rows have different primitive costs; no totals, ratios or speedup inference. Complete literal-selector, context, field, Picard, admission and verification work remains included and unpriced.]

== Accounting that stays in scope
Both methods include packet parsing, complete validation norm and full-order Jacobian admission. The direct setup records two elliptic two-torsion factorizations, eight prime-field Phi calls, eight source-isogeny calls and two quadratic origin traces. The strong baseline includes immutable complete-C setup and its additional isogeny context. Direct generic evaluation has four ordinate recoveries and eight explicit double checks; literal-selector internal checks remain unpriced. The448 exceptional rows take446 generic branches and two infinity branches. Nonzero two-torsion coordinates are tested separately. No timing claim is made.

== Faithful conditional proofs
Both unchanged Lean4.34.1/4.35.0 gates accept ten declarations, zero trusted research axioms; named roots use standard foundations. Nine new exact statement bindings bring the partial count to82; the existing abscissa identity is reused. Proofs cover the universal ordinate identity, differences of halves, Frobenius-square fixing, odd lift, full lift from actual cofactor data, correction existence, evaluator equality, independence and the stronger scalar baseline. (3ba28f.)

The actual field/order/Weil-restriction/quotient/Picard/cofactor bridges remain written/native. The full lift is derived from odd plus actual cofactor lifts, not geometric surjectivity alone. Exact-Z expansion and the unchanged original certificate checker accept both polynomials; deleting −2B gives an actual original-checker counterexample101. The certificate's Lean pointer does not run Lean. (d91395.)

== Sources, preserved failures and next task
#link("https://math.mit.edu/classes/18.783/2025/LectureNotes2.pdf")[Sutherland2025, Lecture2 §2.2 (duplication)] and #link("https://math.mit.edu/classes/18.783/2025/LectureNotes5.pdf")[Lecture5, Theorems5.8/5.25]. The original project already had the halving quartic, selector and ring proof; no novelty claim. Local literal source, hashes, full derivation and proof map accompany this report.

Build01, constructor03, Lean01/02 and all earlier negative records remain retained. Native04/05 whole sources, outputs and actual binaries have complete indices. Complete primitive coverage, admitted matched algorithm references, full geometric bridges and a genuinely nondual degree13 continuation stay open. Live measurement admission, root regression, signing/merge requirements and locked KB/vault limits persist.
''')
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Complete norm-halving transfer results

The direct and strengthened scalar evaluators equal the immutable complete-C transfer across the declared448exceptional/48mixed/40publicsector-direction/96addition cases. All four halves, both new[13] compositions, full inverse and original source recovery are checked. Native05 passes four unfiltered tests, all892 guards, and all prior three whole records without masks (7ff793). Both original Lean gates pass ten declarations and nine new bindings (3ba28f); certificate and whole-record controls retain actual101 negatives (d91395). All results are unsigned. [pcc:unverified]

[PDF](report.pdf), [derivation](../../NORM_HALVING_DERIVATION_01.md), [proof map](../../NORM_HALVING_PROOF_MAP_01.md), [editable flow](flow.dot), [flow metadata](flow.diagram.json), [recorded Rust inputs](recorded-inputs.json), [selected-call graph](selected-calls.svg), [native evidence](../../evidence/norm-halving-complete-native-05/), [auxiliary evidence](../../evidence/norm-halving-identity-and-audit-01/). Render with `python render.py` in an environment with typst and matplotlib; scientific values come from the Rust audit, not Python. [pcc:unverified]

The call graph shows selected entry counts on one actual generic row. Complete common admission retains a full-order Jacobian scalar; context/field/Picard/validation/verification and literal-selector internal work are included and unpriced. Full inverse retains scalar3413013. No calibrated cost, stage or end-to-end improvement, or advantage over ECDLP algorithms is established. [pcc:unverified]

The existing prospective diagram and complete-C/A-B diagrams were checked and remain frozen at their original scopes. This report adds a separate actual-results diagram and a quantitative selected-call graph. Full field/model identities label the PDF; failed builds, proofs and controls remain indexed with their original bytes. Prior-art sources and unavailable KB/vault scope remain3da2fc, with no novelty or absence inference. [pcc:unverified]
''')
(p/'render.py').write_text('''"""Rendering only. Frozen values are native Rust audit output."""
from pathlib import Path
import subprocess
import typst
p=Path(__file__).resolve().parent
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
# The recorded-inputs.json and selected-call chart were generated by the retained
# original renderer; preserve that data when editing presentation sources.
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
''')
shutil.copyfile(__file__,p/'original-render.py')
print('PDF bytes',(p/'report.pdf').stat().st_size)
