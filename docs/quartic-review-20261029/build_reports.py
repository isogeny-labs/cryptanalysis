from pathlib import Path
import json, subprocess, hashlib, re, textwrap, html, shutil, posixpath
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from svglib.svglib import svg2rlg
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config
from matplotlib import font_manager
rl_config.invariant = 1
plt.rcParams["svg.hashsalt"] = "quartic-review-20261029"
plt.rcParams["svg.fonttype"] = "none"
pdfmetrics.registerFont(TTFont("DejaVuSans", font_manager.findfont("DejaVu Sans")))
pdfmetrics.registerFont(TTFont("DejaVuSansBold", font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold"))))
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/quartic-review-20261029';OUT.mkdir(exist_ok=True)
manifest=json.loads((ROOT/'tools/ci/quartic_certificates.json').read_text());studies=json.loads((OUT/'study-map.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in manifest['inputs'].items()), 'frozen input mismatch'
assert {(p['number'],p['head']) for p in studies}=={(p['number'],p['head']) for p in manifest['source_prs']}
mechanisms={
1164:('Frobenius exchanges coprime conjugate factors', ['K = Q(alpha), degree 18','L = K(s), s^2 = 2','Q4 = u4 q2 q2-conjugate\nQ8 = u8 q4 q4-conjugate','Finite-field specialization:\n2 nonsquare + denominators nonzero\n+ coprime specialized pairs','Frobenius-fixed root would belong\nto both conjugates: contradiction']),
1167:('A denominator exclusion is not a rational point', ['83,047 prime cells\np < 10,000,000; p = 11 mod 24','Exact norm/denominator gate','83,036 certified gate cells','11 excluded cells:\nrequires direct source-fiber classification','New exception p = 1,237,499:\n2 rational C points, zero E roots']),
1170:('Norm divisors and the nearby control', ['Pinned octic resultant cube root','21-digit divisor splits exactly:\n414340033 x 431435018569','Both primes: 18 C points each\n426 C-E point pairs each','Nearby control 414340153:\n18 C points, zero E-point lifts','Finite-field equation checks;\nno scalar recovery or speedup claim']),
1171:('Repeated roots locate branch-zero values', ['Specialized q4 and q8;\n499 saved rational factor roots','Derivative gcd within each factor','7 repeated x-roots\nacross four certified fields','7 branch-zero x-values\n(same saved roots)','Original cross-factor-overlap\nprediction failed; retained mismatch']),
1173:('Projection through the exact cubic resultant', ['P_B(T) over pinned K = Q(alpha)\nT^3 - z T^2 - 64','Res_T(cubic, P_B)\n= -16 R_E(z) = -16 u q4(z)q8(z)','Universal 5x5 Sylvester determinant\nproved over a commutative ring','56 saved C points x 13 coefficients\n= 728 finite coefficient comparisons','Concrete number-field interpretation\nremains separate from the ring identity'])}
problem_links={1174:['hecke432-discriminant-field-bridge'],1176:['hecke432-field-index-integral-basis-bridge'],1177:['hecke432-relative-ideal-encoding-bridge'],1184:['hecke432-local-hensel-frobenius-bridge'],1186:['hecke432-galois-partition-kummer-bridge']}
charts={}
def read(pr,name):
 s=next(s for s in studies if s['number']==pr);p=ROOT/s['roots'][0]/name;return json.loads(p.read_text()),str(p.relative_to(ROOT)),hashlib.sha256(p.read_bytes()).hexdigest()
d,p,h=read(1164,'holdout_result.json');charts[1164]={'labels':['C rows checked','C rows passing'],'values':[len(d['rows']),sum(r['prediction_pass'] for r in d['rows'])],'unit':'source C rows','source':p,'sha256':h,'scope':'Six saved C rows at primes 8123, 8147 and 8171. Retrospective verification.'}
d,p,h=read(1167,'scan_result.json');charts[1167]={'labels':['Eligible primes','Gate certified','Excluded primes'],'values':[d['cumulative_prime_cells'],d['cumulative_certified_good_cells'],d['cumulative_prime_cells']-d['cumulative_certified_good_cells']],'unit':'prime cells','source':p,'sha256':h,'scope':'7 <= p < 10,000,000; p congruent 11 mod 24. Excluded does not imply a rational pair.'}
d,p,h=read(1170,'audit_result.json');charts[1170]={'labels':[r['prime'] for r in d['rows']],'values':[r['rational_CE_pairs'] for r in d['rows']],'unit':'C-E point pairs','source':p,'sha256':h,'scope':'Two saved primes, 18 rational source points per prime. The nearby control is documented separately.'}
d,p,h=read(1171,'audit_result.json');charts[1171]={'labels':[str(r.get('prime','field')) for r in d['results']],'values':[r['branch_zero_roots'] for r in d['results']],'unit':'branch-zero x-roots','source':p,'sha256':h,'scope':'Four saved finite fields; seven total branch-zero x-roots among 499 rational roots.'}
d,p,h=read(1173,'result.json');charts[1173]={'labels':['Matched coefficients','Mismatched coefficients'],'values':[d['source_points_checked']*13,0 if d['coefficient_identities_match'] else d['source_points_checked']*13],'unit':'coefficient comparisons','source':p,'sha256':h,'scope':'13 coefficients for each of 56 saved source points. All coefficient identities match.'}
# Keep quantities with different units in separate panels.
for pr,c in charts.items():
 fig,ax=plt.subplots(figsize=(8,3.8));bars=ax.bar(range(len(c['values'])),c['values'],color='#155e75');ax.set_xticks(range(len(c['labels'])),c['labels'],fontsize=9);ax.set_ylabel(c['unit']);ax.set_title('Retained exact census: PR #'+str(pr),fontsize=12)
 for b,v in zip(bars,c['values']):ax.annotate(f'{v:,}',(b.get_x()+b.get_width()/2,v),xytext=(0,5),textcoords='offset points',ha='center',fontsize=10)
 ax.set_ylim(0,max(c['values'])*1.2 if max(c['values']) else 1);ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(OUT/f'{pr}-counts.svg',metadata={'Date':None});plt.close(fig)
(OUT/'quantitative-sources.json').write_text(json.dumps(charts,indent=2)+'\n')
styles=getSampleStyleSheet()
for sty in styles.byName.values():sty.fontName='DejaVuSansBold' if sty.name.startswith('Heading') or sty.name=='Title' else 'DejaVuSans'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;styles['BodyText'].wordWrap='CJK'
for entry in studies:
 pr=entry['number'];root=entry['roots'][0];result=ROOT/root/'RESULT.md';text=result.read_text();paragraphs=[p.strip() for p in text.split('\n\n') if p.strip() and not p.lstrip().startswith('#')];summary=paragraphs[0]
 def rebase_link(match):
  label,target=match.groups()
  if '://' in target:return match.group(0)
  if target.startswith('#'):target='RESULT.md'+target
  return '['+label+'](../../'+posixpath.normpath(posixpath.join(root,target))+')'
 summary=re.sub(r'\[([^]]+)\]\(([^)]+)\)',rebase_link,summary)
 if pr in (1164,1190):summary=re.sub(r'\bprospective(?:ly)?\b','retrospective',summary,flags=re.I)
 title,nodes=mechanisms.get(pr,('Evidence and proof boundaries for this study',['Pinned inputs: original source and protocols',entry['title'],'Submitted exact arithmetic / algebra certificates','Pinned Lean project and theorem axiom audit','Full concrete field / ideal / transport bridge:\nonly established where separately proved']))
 dot=['digraph evidence {','graph [rankdir=TB, bgcolor="white", pad="0.25"];','node [shape=box, style="rounded,filled", fillcolor="#eff6ff", color="#155e75", fontname="DejaVu Sans", fontsize=12, margin="0.18"];','edge [fontname="DejaVu Sans", fontsize=10, color="#475569"];']
 for i,n in enumerate(nodes):dot.append(f'n{i} [label={json.dumps('\n'.join(textwrap.fill(line,width=52) for line in n.splitlines()),ensure_ascii=False)}];')
 edges={1167:[(0,1),(1,2),(1,3),(3,4)],1170:[(0,1),(1,2),(0,3),(2,4),(3,4)],1171:[(0,1),(1,2),(2,3),(0,4)],1173:[(0,1),(2,1),(1,3),(1,4)]}.get(pr,[(i,i+1) for i in range(len(nodes)-1)])
 for a,b in edges:dot.append(f'n{a} -> n{b} [label="scope condition / recorded check", style='+('dashed' if b==4 else 'solid')+'];')
 dot.append('}');(OUT/f'{pr}.dot').write_text('\n'.join(dot)+'\n');subprocess.run(['dot','-Tsvg',str(OUT/f'{pr}.dot'),'-o',str(OUT/f'{pr}.svg')],check=True)
 formal=[e['path'] for e in manifest['formal'] if e['path'].startswith(root+'/')];frozen={p:h for p,h in manifest['inputs'].items() if p.startswith(root+'/')};problems=problem_links.get(pr,[])
 prose=f'''# Review addendum: PR #{pr}\n\nDate: 2026-10-29. {entry['title']}.\n\nOriginal author head: `{entry['head']}`. The original study and every frozen source, protocol, result, failed attempt and timing cap are preserved. This addendum takes precedence over unqualified experimental-status language in the archived report.\n\n## Recorded finding and its scope\n\n{summary}\n\nThe paragraph above describes the retained certificate record, not a new experiment. Source: [{root}/RESULT.md](../../{root}/RESULT.md). This review treats publication of protocol and results together as retrospective/exploratory unless an independent earlier publication witness is supplied. An archived PASS_PROSPECTIVE status is a literal historical label, not evidence of pre-observation registration. In particular, PR #1164's six-row holdout and PR #1190's 62/62 correctness checks retain their numerical results with this qualification.\n\n## Evidence-linked explanation\n\n{title}. Symbols C, B, E and K denote the frozen coordinate models or coefficient field, not newly registered subgroup instances. This diagram records algebra/certificate dependencies; it does not introduce a verified isogeny edge, EC1 identity, ISO1 route, or ECDLP transport claim.\n\n![{title}]({pr}.svg)\n\nEditable source: [{pr}.dot]({pr}.dot). Report and visual: [{pr}.pdf]({pr}.pdf).\n\n## Replay and proof map\n\nThe exact manifest binds {len(frozen)} files in this study. The shared project pins Lean {manifest['toolchain']} and Mathlib `{manifest['mathlib']}`. All 37 original modules, 113 requested declaration reports and 142 noninternal theorems passed the integrated proof replay; this does not formalize every concrete Sage/PARI field or ideal interpretation. The source manifest and proof map are [tools/ci/quartic_certificates.json](../../tools/ci/quartic_certificates.json) and [the original integration report](../ci-repair-quartic-20261027.md).\n\nThis study's original modules: {', '.join('`'+p+'`' for p in formal) or 'see the shared manifest; no new theorem is introduced by this addendum'}.\n\nA new portable replay ran all 42 original integer auditors successfully in a disposable canonical-layout container. The checkout was read-only and all 1,404 original input hashes were verified before and after replay. See [portable replay evidence](portable-replay/results.json). The separate field-index successor runner uses new output directories, unchanged source/protocol bytes, original timeout limits and the checked Sage launcher. Preparation and I/O controls are not a new Sage experiment.\n\n## Remaining obligations and graph review\n\nArithmetic table certificates and universal ring/permutation identities retain their precise hypotheses. Concrete number-field encodings, integral bases, ideals, Hensel lifting and Frobenius interpretation require their own bridges. No security, speedup, prospective-validation or general impossibility claim is added.\n'''
 if problems:prose+='\n'+ '\n'.join(f'- Open, indexed obligation: [{p}](../../problems/{p}.md).' for p in problems)+'\n'
 prose+='\nThe candidate catalog, volcano-IC figure set and paper figures were checked for affected links. This is a review and portability correction with no new surviving graphable mathematical fact; canonical graphs remain unchanged. The precise checked-path inventory is [graph-review.json](graph-review.json).\n'
 if pr in charts:
  c=charts[pr];prose+=f'''\n## Retained exact counts\n\n{c['scope']} Units: {c['unit']}. These are exact finite-census counts with no statistical error bars; extrapolation beyond the saved domain is not established. No new timings were collected. Data: [{c['source']}](../../{c['source']}), SHA-256 `{c['sha256']}`; [plotted values](quantitative-sources.json).\n\n![Retained counts]({pr}-counts.svg)\n'''
 (OUT/f'{pr}.md').write_text(prose)
 # The PDF contains the complete new addendum plus its explanatory visual.
 story=[]
 for block in prose.split('\n\n'):
  block=block.strip()
  if not block:continue
  if block.startswith('!['):
   name=f'{pr}-counts.svg' if 'Retained counts' in block else f'{pr}.svg';drawing=svg2rlg(str(OUT/name));iw,ih=drawing.width,drawing.height;scale=min(460/iw,420/ih,1);drawing.scale(scale,scale);drawing.width=iw*scale;drawing.height=ih*scale
   story.extend([Spacer(1,8),drawing,Spacer(1,10)]);continue
  level=3 if block.startswith('### ') else 2 if block.startswith('## ') else 1 if block.startswith('# ') else 0
  clean=block.lstrip('# ').replace('`','');clean=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'\1 (\2)',clean);clean=html.escape(clean).replace('\n','<br/>');story.append(Paragraph(clean,styles[f'Heading{level}'] if level else styles['BodyText']))
  if not level:story.append(Spacer(1,7))
 SimpleDocTemplate(str(OUT/f'{pr}.pdf'),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=38,title=f'Quartic review addendum #{pr}').build(story)
 (ROOT/root/'REVIEW_20261029.md').write_text(f'''# Dated review and replay addendum\n\nThe frozen report, protocols and receipts remain unchanged. Read the [2026-10-29 review addendum](../../docs/quartic-review-20261029/{pr}.md), [explanatory visual](../../docs/quartic-review-20261029/{pr}.svg), and [PDF](../../docs/quartic-review-20261029/{pr}.pdf).\n\nThe addendum records retrospective/exploratory publication status, the exact pinned proof project, portable replay and remaining formalization boundaries. It takes precedence over unqualified prospective-registration wording in archived receipts.\n''')
for svg in OUT.glob('*.svg'):
 svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
for entry in studies:
 for name in (f"{entry['number']}.png", f"{entry['number']}-counts.png"):
  (OUT/name).unlink(missing_ok=True)
print('generated dated reports, editable diagrams and PDFs',len(studies))
