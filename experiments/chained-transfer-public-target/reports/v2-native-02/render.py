"""Render native observations and written scope; no cryptographic computation."""
from pathlib import Path
import json,subprocess,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/v2-native-02';d.mkdir()
records=json.loads((s/'evidence/v2-native-02/native-records.json').read_text());by={x['kind']:x['data'] for x in records}
(d/'native-records.json').write_text(json.dumps(records,indent=2)+'\n')
dot='''digraph V2 {
graph [rankdir=LR,bgcolor="transparent",nodesep=.25,ranksep=.35];
node [shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];
edge [fontname="DejaVu Sans",fontsize=9];
E [label="Original E(K)\nK = F223[z] / (z^3 - 3)\nell = 2773073"];
S [label="Short source E'(K)\nS(v,w) = -(v + a2/3,w)\nactual common quartic sign"];
J [label="Jac(C)(F223)\nall15 actual N4 coefficients\nP0 = [1,74,153]"];
T [label="Complete old raw origin\nfibre at T = kappa(infinity-)\nnonzero at actual legacy P0",fillcolor="#fff3da"];
E -> S [label="signed source isomorphism"];
S -> J [label="complete Phi\nthree conjugate fibre ideals"];
J -> S [label="canonical Norm\nR2/R4 length3 algebra",color="#18794e"];
T -> J [label="subtract geometric origin",style=dashed];
}'''
(d/'flow.dot').write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/'flow.dot'),'-o',str(d/'flow.svg')],check=True)
labels=['Source panel','Actual C point classes','P0 addition pairs','Finite branch controls','Infinity controls','Line offsets']
values=[by['N4_V2_COMPOSITIONS']['source_panel'],by['N4_V2_COMPOSITIONS']['all_rational_point_classes'],by['N4_V2_BASEPOINT']['addition_pairs'],by['N4_V2_EXCEPTIONAL']['all_three_quadratic_branch_pairs'],by['N4_V2_EXCEPTIONAL']['four_infinity_sign_controls'],by['N4_V2_EXCEPTIONAL']['plane_line_offsets']]
fig,ax=plt.subplots(figsize=(7.3,2.35));ax.barh(labels[::-1],values[::-1],color='#477a9c')
for i,v in enumerate(values[::-1]):ax.text(v+3,i,str(v),va='center',fontsize=9)
ax.set(xlim=(0,260),xlabel='Actual cases in different correctness panels; no timing comparison')
ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(d/'panels.svg');plt.close(fig)
p1=[
'Observed unsigned a5a4a6: one comprehensive unfiltered Rust test passes, zero failed/ignored/filtered, all2203 input guards unchanged. The additive V2 constructors rebuild the actual q223 field, plane quartic, P0, normal forms and complete origin. Original V1 and all q5/7/11 controls remain unchanged. Four original N4 files and the frozen P1 algorithm remain byte exact.',
'Exact source: K=F223[z]/(z³−3), ell2773073, #E(K)=11092292=4ell. All basis products/Frobenius and all15 normalized quartic coefficients match the actual N4 source. Canonical P0=[1,0,0]; the original winning FB at seed102/nfb36 actually chooses [1,74,153]. Both completed constructors use their own true P0 and model tags. Source j is outside F223; this is a restricted extension-field family.',
'The entire actual four-element 2-Sylow subgroup is checked, including all three original cubic two-torsion roots. Eight odd multiples crossed with it give32 source controls. Both [2] compositions hold on the stated source/class panels, and Phi(G) is nonzero with exact prime order2773073. These are bounded native checks, not enumeration of the11092292 source or Jacobian elements.'
]
p2=[
'Actual sign/origin: completed kappa and legacy lambda use opposite quartic ordinates. I(v,w)=(v+a2/3,w), T=kappa(negative infinity), and kappa(lambda⁻¹P)=T−I(P). After subtracting the actual old infinity fibre, Phi_old=Phi_new∘(-I). Here T=((116,126,164),(133,115,44));2T is nonzero. All16 admitted split fibres in the panel equal completed raw fibres at each actual P0. At the winning legacy P0 the raw origin is nonzero; it is constructed geometrically, never fitted.',
'Reference divisors: Dinf=K_C−P0. A fixed final divisor key shifts by delta=[Pnew−Pold], while the same raw degree-six space shifts by2delta. Native controls check zero/inverse,100 addition pairs, the raw-degree6 formula and the complete map bridge at distinct actual P0. Fresh norm at the legacy P0 checks32 source points, all five public point half-inverses and all five affine three-point cancellations; the ratio base is nonzero.',
'Exceptional controls: all224 plane-line offsets agree, all12 geometric roots from the three quadratics and all four infinity signs pass. The actual3P scheme at[1,1,52] retains multiplicity3; discarding multiplicity changes its norm, and an alternate affine chart agrees with the correct result. The first3P at[1,0,0] is a retained null control: omission gives the same norm there. No claim turns that null into a discriminating negative control.',
'Written proof and formal boundary: pi_i* pi_i^*=[2]; cross terms vanish by the other Ciani involutions. The sum of three pull-push projectors is2 plus the V4 norm, which factors through Pic^0(P1)=0. Hence both compositions are[2]; on the odd subgroup, inverse2=1386537 recovers points and preserves DLP scalars. V2_MAPS_01.md spells out the actual divisor/model origins. Existing9+5 Lean bindings prove conditional module/ring identities, not the actual Picard, Hasse, cover or N4 solver objects. Full formal geometry remains open.',
'Independent controls now settled at their scopes: full replay67baa2 passes all43 phase pairs (29positive0/0+14intentional2/0), both original9+5 proof gates,14 exact bindings and435 guards. Exact68d ownCI43432174569/job131908108813 succeeds;13 native records match after excluding only recorded wall/wall_total values,14 canonical claim digests match (a5a143). Rho accessor e5d852 checks all five recovered native/actualCLI answers; the walk is unchanged by its three output-only substitutions.',
'Failures and next action: whole full01 consumer-path failure080841 and rho01 counter-boundary/timestamp failure638d96 remain, with corrected passes and all original sources. Seven complete closed captures and seven full member indices are retained; genuine remote publication is separately evidenced. The active prospective protocol74e00a/COMPLETED_DESCENT_PROTOCOL_02.md replaces only split-transfer triple admission in individual descent, after normal publication. Map overhead may outweigh avoided rejection; original counters omit arithmetic in the separate completed-map engine. No benchmark, computational advantage, generic prime-field coverage or signed execution is established.'
]
(d/'page1.json').write_text(json.dumps(p1,indent=2)+'\n');(d/'page2.json').write_text(json.dumps(p2,indent=2)+'\n')
(d/'REPORT.md').write_text('# Actual q223 completed maps and checked baseline answers\n\n2026-11-13. All standing unsigned.\n\n'+'\n\n'.join(x+' [pcc:unverified]' for x in p1+p2)+'\n\nSources: evidence/v2-native-02/native-records.json and acceptance.json; evidence/independent-full-02; evidence/independent-CI-02; evidence/rho-acceptance-02; V2_MAPS_01.md; frozen DERIVATION.md/PROOF_MAP.md and existing original proof maps. Editable diagram, plot and native records accompany this report. Canonical q5/7/11 graphs were checked and remain valid at those unchanged scopes; this new q223 diagram is an additive bounded-evidence view, not a new globally formal edge.\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.42em)
#text(size:18pt,weight:"bold")[Actual q223 completed maps]
#parbreak()
2026-11-13 · bounded native evidence · all standing unsigned
#parbreak()
#image("flow.svg",width:100%)
#image("panels.svg",width:98%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:18pt,weight:"bold")[Origins, proofs and independent checks]
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
#text(size:9pt,weight:"bold")[Source-linked evidence:]
#parbreak()
a5a4a6/V2 native02;67baa2/full02;a5a143/ownCI;e5d852/rho02;7da26d/extension freeze;V2_MAPS_01.md;existing f68241+d71088 partial formal bindings. Whole failed and passed captures/member indices remain separate immutable evidence.
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
