"""Render a prospective report; no mathematical search or calculation."""
from pathlib import Path
import hashlib,json,shutil,subprocess,typst
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/twisted-pair-proposal-01';p.mkdir()
raw=Path('/workspace/scratch/ct80-twist-primary-review-01');raw.mkdir();sources=[]
for name in ['ct59-HLP-Split-Jacobians.pdf','ct59-HLP-Split-Jacobians.txt']:
 src=Path('/workspace/scratch')/name;shutil.copyfile(src,raw/name);sources.append(dict(source=str(src),bytes=src.stat().st_size,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),reference='arXiv:math/9809210v1; section4.1 Proposition15 and following remark'))
(p/'primary-sources.json').write_text(json.dumps(sources,indent=2)+'\n');(raw/'primary-sources.json').write_text(json.dumps(sources,indent=2)+'\n')
text=(raw/'ct59-HLP-Split-Jacobians.txt').read_text();lines=text.splitlines();(p/'primary-excerpts.txt').write_text('\n'.join(lines[1080:1100]+['\n[Exact separate excerpt: Proposition15 and field qualification]\n']+lines[1278:1306]+['\n[Exact separate excerpt: following remark]\n']+lines[1364:1379])+'\n')
(p/'flow.dot').write_text('''digraph fixedpair {
graph[rankdir=TB,bgcolor="white",ranksep=.32,nodesep=.4];
node[shape=box,style=rounded,fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=9];
old[label="RETAINED: original matched-source negatives\\nE2 / D12 and E3 / D24\\nsmooth F223 quartics; source identifications unsupported",color="#8b3434"];
fixed[label="PROPOSED NEW INSTANCE ONLY\\nnu=12; exactly E2^nu -> E3^nu\\nfixed old rational-map recipe; no alternate candidate",color="#a57535",style="rounded,dashed"];
cert[label="REQUIRED before model acceptance\\nnew order / nonzero prime-order point / Hasse certificate\\nwhole rational identities + actual64-point transport\\nfreeze rescaled G2/G3 BEFORE all12 model rows",color="#295477"];
test[label="TEST, do not assume\\nH'=nu H; adj'=nu^2 adj; D'=nu^3 D\\nunique fixed-kernel matches + full old coefficient parity\\nall controls / Lean / whole ordered records",color="#295477"];
outcome[label="Outcome UNKNOWN\\nsupported pair or preserved new negative\\ncomplete Jacobian evaluator needs subsequent protocol\\nNO old-to-twist logarithm transfer or cost claim",color="#a57535",style="rounded,dashed"];
old->fixed[style=invis];fixed->cert[style=dashed];cert->test[style=dashed];test->outcome[style=dashed];}''')
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
(p/'report.typ').write_text(r'''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.4pt)
#set par(leading:.4em)
#text(size:17pt,weight:"bold")[A fixed twist pair for a separate ECDLP instance]
#v(4pt)
#text(fill:rgb("#a57535"),weight:"bold")[PROSPECTIVE · no new source, order, model or map result]

The original nondual continuation has two smooth prime-field quartics with unsupported supplied-source identifications, at D12 and D24. Keep both negatives. Test one fixed quadratic twist of both already-fixed elliptic endpoints, nu=12, using the standard HLP twisting construction. This changes the ECDLP instance; it supplies no map carrying the original logarithm to the twist.

#image("flow.svg",width:100%,height:121mm,fit:"contain")

== What must be checked independently
Prove the homogeneous scalar identities and actual finite-field witnesses with both original Lean gates, retaining field and geometry bridges. Certify the new prime subgroup using an actual nonzero point and a unique Hasse multiple. Twist the complete existing rational map and signed dual; check every coefficient, composition, point and addition control. Transport all64 actual2-torsion points with their coordinate permutations and4096 addition/original alternating-pairing rows. Fix both full kernels before examining allsix HLP cases at each endpoint. Keep every outcome and compare matched normalized coefficients exactly to the frozen old rows.

== Source and boundary
Howe–Leprevost–Poonen, arXiv:math/9809210v1, section4.1 Proposition15 identifies the quotient with the plane-quartic Jacobian over k(sqrt(T)). Its following remark explains the additional quadratic character of a nonhyperelliptic Jacobian. This is standard prior work; the new proposal tests its application to this fixed pair. A supported model is not a complete rational Jacobian evaluator or an ECDLP speedup.

#text(size:8pt)[Protocol: TWISTED_PAIR_PREFLIGHT_PROTOCOL_01.md. Original evidence27fb3a/6d2c97 and finite residue68cd8c/ee88e7 stay unchanged. Source hashes and exact primary excerpts are beside this report; complete primary files remain at ct80-twist-primary-review-01 for NEW19. Existing model-negative and source-vector diagrams remain current because no new mathematical edge is accepted. KB/ecdb unavailable, vault8edec422 locked: no novelty/absence inference.120s wrappers/explicit900s engine preparation; one900s2GiB native preflight after exact checkpoint. No paid launch, signed execution or benchmark claim.]
''')
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Fixed-twist pair preflight for a separate instance

[Protocol01](../../TWISTED_PAIR_PREFLIGHT_PROTOCOL_01.md) fixes nu12 and both existing E2/E3 endpoints before new code, with unchanged old D12/D24 negatives. The homogeneous HLP formulas are hypotheses to prove and check. All new orders, subgroup points, fixed-kernel matches and complete maps are unknown. No original-logarithm transport to the twist, computational advantage or novelty is claimed. [pcc:unverified]

[PDF](report.pdf) · [editable diagram](flow.dot) · [SVG](flow.svg) · [primary hashes](primary-sources.json) · [exact excerpts](primary-excerpts.txt). Complete primary files are retained at /workspace/scratch/ct80-twist-primary-review-01. [pcc:unverified]

Graphs checked: the existing nondual13-model-negative-01 and nondual13-next-negative-01 diagrams, and norm-arithmetic-partial-01 source-vector graph. They retain actual old outcomes; no new mathematical edge or quantitative result is accepted in this proposal. Geometry, full rational evaluation, current main/root gates, admitted performance references and signed standing remain open. [pcc:unverified]
''')
shutil.copyfile(__file__,p/'original-render.py');print('PDF bytes', (p/'report.pdf').stat().st_size)
