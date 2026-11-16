"""Rendering/I/O projection of frozen native results; no field or group math."""
from pathlib import Path
import hashlib,json,shutil,subprocess,typst
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/twisted-pair-result-01';p.mkdir()
raw=Path('/workspace/scratch/ct80-twisted-pair-native-02/expected-whole-native-01.json');records=json.loads(raw.read_text());d={x['kind']:x['data'] for x in records};pair=d['N4_TWIST_MATCHED_PAIR'];maps=d['N4_TWIST_MAPS_AND_CERTIFICATES'];panels=[]
for side in ['source','target']:
 body=pair[side];rows=[]
 for item in body['all6_homogeneity_and_whole_coefficient_parity']:
  old=item['whole_old_model_row'];new=item['whole_new_model_row'];rows.append(dict(old_case=[old['root_index'],old['sign_index']],new_case=[new['root_index'],new['sign_index']],old_D=old['D'],new_D=new['D'],old_square=old['D_square_in_Fp_and_K'],new_square=new['D_square_in_Fp_and_K'],fixed_match=new['kernel_mask']==body['fixed_mask_before_model_builder']))
 rows.sort(key=lambda x:x['old_case']);panels.append(dict(endpoint=side,rows=rows,matched_case=[body['unique_matched_row']['root_index'],body['unique_matched_row']['sign_index']],D=body['unique_matched_row']['D'],sqrt=body['unique_matched_row']['sqrt_D_in_K'],fixed_mask=body['fixed_mask_before_model_builder'],normalized_coefficients=body['unique_matched_row']['normalized_Fp_coefficients']))
data=dict(source_file=str(raw),source_bytes=raw.stat().st_size,source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),native_claim='2a0549',order=d['N4_TWIST_ORDER_CANDIDATE'],source_id=maps['source_id'],target_id=maps['target_id'],source_certificate=maps['source_certificate'],target_certificate=maps['target_certificate'],panels=panels,scope='rendering projection only; all nine WHOLE native records and all12 complete model rows retained at source path for NEW19; never used as an acceptance comparator')
(p/'render-data.json').write_text(json.dumps(data,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(10.5,3.0));fig.patch.set_facecolor('white')
for ax,panel in zip(axes,panels):
 ax.set_xlim(0,3);ax.set_ylim(-.5,6.5);ax.axis('off');ax.text(1.5,6.2,panel['endpoint'].capitalize()+' endpoint: all six correspondences',ha='center',fontsize=10,weight='bold')
 for j,label in enumerate(['Old case / D','New case / D','Fixed kernel']):ax.text(j+.5,5.7,label,ha='center',fontsize=8.5)
 for i,row in enumerate(panel['rows']):
  y=5.2-i*.85
  for j,prefix in [(0,'old'),(1,'new')]:
   color='#dcebdc' if row[prefix+'_square'] else '#f0dddd';ax.add_patch(plt.Rectangle((j+.07,y-.31),.87,.62,facecolor=color,edgecolor='white'))
   ax.text(j+.5,y,f"{tuple(row[prefix+'_case'])} / {row[prefix+'_D'][0]}",ha='center',va='center',fontsize=8.4)
  ax.text(2.5,y,'MATCH' if row['fixed_match'] else '',ha='center',va='center',fontsize=8.4,weight='bold',color='#235b72')
fig.text(.5,.01,'Green: square D. Red: nonsquare D. Correspondences and MATCH labels come from the full native transport; no square-case selection.',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.035,1,1]);fig.savefig(p/'all-six-correspondences.svg',bbox_inches='tight');plt.close(fig)
(p/'flow.dot').write_text('''digraph actualpair {graph[rankdir=TB,bgcolor="white",ranksep=.3,nodesep=.4];node[shape=box,style=rounded,fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=9];
e2[label="E2 twist12 / K\\nnew prime2771711; full order11086844",color="#235b72"];
e3[label="E3 twist12 / K\\nnew prime2771711; full order11086844",color="#235b72"];
j2[label="Fixed F223 quartic C2\\nmatched HLP(1,1), D220, sqrt79\\nold normalized coefficients retained",color="#46754a"];
j3[label="Fixed F223 quartic C3\\nmatched HLP(2,0), D217, sqrt70\\nold normalized coefficients retained",color="#46754a"];
{rank=same;e2;e3}{rank=same;j2;j3}
e2->e3[label="actual degree13 / both[13] identities"];
e2->j2[label="HLP quotient of Weil restriction\\nglobal geometry bridge",style=dashed];
e3->j3[label="HLP quotient of Weil restriction\\nglobal geometry bridge",style=dashed];
j2->j3[label="induced degree13^3: conditional factorization\\ncomplete rational evaluator NOT IMPLEMENTED",style=dashed,color="#a57535"];}''')
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
(p/'report.typ').write_text(r'''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.4em)
#text(size:17pt,weight:"bold")[A supported fixed-twist pair, on a new subgroup]
#v(4pt)
#text(fill:rgb("#235b72"),weight:"bold")[NATIVE PREFLIGHT PASSES · unsigned · complete Jacobian evaluation remains open]

Exactly nu12 twists both fixed E2/E3 endpoints. The actual new order11086844=4·2771711 is certified by nonzero prime-order points and a unique Hasse multiple4 on both curves. All generator attempts and wrong-order/zero-generator rejections are retained. The old2773073-order instance is different. No logarithm is carried from that old subgroup to its twist.

#image("flow.svg",width:100%,height:70mm,fit:"contain")

== The kernel is fixed before model admissibility
Actual64-point coordinate/Frobenius transport,4096 addition/original alternating-form rows and135 masks fix both new full kernels before either model builder. Allsix cases at each endpoint remain. The unique matches are(1,1),D220,sqrt79 and(2,0),D217,sqrt70. Every old/new HLP scalar/matrix identity and allsix normalized quartic arrays per endpoint agree exactly. Old matched source failures at D12/D24 remain negative.

#image("all-six-correspondences.svg",width:100%,height:65mm,fit:"contain")

== Native evidence and limit
One unfiltered test0; actual Kohel maps versus complete twisted signed recipes; both[13] rational identities, separability/coprimality, SEA11/9,36points each way,1024 addition pairs each way, allfour2-torsion and five NEW public-target controls pass. Allnine whole ordered records compare without masks/deduplication. Removing the actual whole matched-pair record rejects101/no output. All981 original guards and actual full compiled/runtime source/binary custody pass.

#text(size:8pt)[2a0549 at source0db58cf0; prospectivef10846 was published3fad107a before code. Original checkpointc22371 and immediate gate0 precede native02. Earlier helper-wiring failurefe3785 is preserved. Complete raw and source/binaries are at ct80-twisted-pair-native-02/build-02 for NEW19; render-data.json pins the WHOLE native packet file. This is a model/source preflight, not a complete Jacobian evaluator, two-hop chain, timing result, novelty or ECDLP advantage.]

#pagebreak()
#text(size:16pt,weight:"bold")[Why this pair does not carry the original prime-field log]
#v(5pt)
The two fixed quartic equations already existed. Their new supplied-source identifications use the twisted elliptic order11086844. The original prime2773073 is coprime to that order. If HLP/Frobenius descent and isogeny-cardinality identify the fixed F223 Jacobian group order with11086844, Lagrange implies every target point is killed by it. A point also killed by2773073 must be zero. This is a scoped group obstruction for these fixed targets, not a statement about arbitrary reductions or other curves.

== The checked annihilator calculation
The exact Bezout relation is2163237·2773073−541075·11086844=1. Thus, when both integers annihilate a point a, applying their linear combination gives a=0. OldPrimeObstruction.lean proves this general module argument, the exact numerical gcd and its conditional specialization. Both original gates accept allthree roots with zero trusted declarations; three exact local statement bindings pass. The actual Jacobian/cardinality/Lagrange interpretation remains explicit.

== The checked HLP algebra
Over an extension containing s with s²=nu, the scaling(x,y)↦(nu·x,nu·s·y) gives the twist. Conjugating the fixed isogeny yields x↦nu·phi_x(x/nu), y↦y·phi_Y(x/nu); native checks the whole rational identities independently.

A scales by nu, B and Delta by nu², h and H by nu, adj(H) and the Ciani coefficients by nu², and T=det(H),D=16T by nu³. The fixed linear Moore descent preserves the common coefficient factor, explaining the unchanged normalized quartics. TwistHomogeneity.lean checks eight ring/modular roots. TwistingFactor.lean separately checks three roots for explicit denominator inverse witnesses, full primary-factor homogeneity and equality to the symmetric determinant polynomial. Both original gates and all exact local bindings pass; this formalizes scalar algebra, not actual varieties or Rust execution.

== Conditional geometric factorization
Under the HLP/Frobenius source identifications, the three conjugate13 maps carry the entire fixed kernel and factor through the two degree8 quotient isogenies. Degree multiplicativity gives8·deg(beta)=8·13³; compatible polarizations give dual(beta)·beta=[13]. Actual rational Jacobian evaluation, origins/exceptional inputs and direct-composite cost comparison are still missing. The native preflight does not fill those program/geometric bridges.

== What remains next
Preserve the original D12/D24 negatives and pursue the original prime-order chain through a separately frozen composite continuation that can skip unsupported intermediate Jacobian models. No fourth-edge code or outcome is included here. The observer census concerns the earlier original norm-halving transfer, not this new pair: its cold900 cap fails and both reuse streams complete. Its vectors remain unpriced and cannot be applied to this beta. No calibrated advantage, paid launch or signed standing is established.

#text(size:8pt)[Sources: TWISTED_PAIR_DERIVATION_01.md; native2a0549; primary Howe–Leprevost–Poonen arXiv:math/9809210v1 section4.1 Proposition15 and following remark; proof71014e / inverse-factorf2d901 / annihilator215bcc. Field encoding, constructor matching, global HLP/Frobenius, finite cardinality and Rust bridges remain scoped. Original source-model and arithmetic-vector graphs were checked and retain their old outcomes; no unsupported old-to-twist edge is added.]
''')
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Supported fixed-twist pair on a separate subgroup

Native2a0549 supports the fixed new-instance pair after all64/4096/135 transported-kernel checks and allsix models each; originalD12/D24 negatives stay unchanged. New prime2771711/order11086844 differs from old2773073. Full nine-record/control/source custody passes. [pcc:unverified]

[PDF](report.pdf) · [flow source](flow.dot) · [actual allsix correspondence matrix](all-six-correspondences.svg) · [render-only native projection/hash](render-data.json) · [written derivation and proof map](../../TWISTED_PAIR_DERIVATION_01.md). No complete rational Jacobian evaluator, original-log twist transport, chain or cost advantage is claimed. [pcc:unverified]

Proof71014e covers eight ring/residue roots, f2d901 covers three inverse-factor roots, and215bcc covers three conditional annihilator roots. Both original gates and exact local bindings pass with zero trusted; actual encoded-field/geometric/cardinality/program bridges remain explicit. These are standard mathematical formalizations, not an aggregate novelty count. [pcc:unverified]

Graphs checked: original nondual13-model-negative-01, nondual13-next-negative-01 and norm-arithmetic-partial-01. Their actual old outcomes are unchanged. The new diagram labels the hypothetical induced Jacobian evaluator as pending and includes no old-to-twist transfer. [pcc:unverified]
''')
shutil.copyfile(__file__,p/'original-render.py');print('PDF bytes',(p/'report.pdf').stat().st_size)
