#!/usr/bin/env python3
"""Render the preserved whole-guest instruction attribution, separately from timing."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, PageBreak
from xml.sax.saxutils import escape

P = Path(__file__).resolve().parent
a = json.loads((P/'analysis-profile-001.json').read_text())
row = a['rows'][1]
functions = row['functions'][:10]
labels = ['Table flush', 'Cached point kernel', 'Table builder', 'Batch inverse products',
          'Walker', 'Full-point SIMD', 'Field inverse', 'Collector', 'Seen-point insert', 'Table probe']
plt.rcParams.update({'svg.fonttype':'none', 'font.size':9})
fig, ax = plt.subplots(figsize=(7.6, 3.6))
ax.barh(labels[::-1], [100*x['fraction'] for x in functions][::-1], color='#246b81')
ax.set_xlabel('Exclusive guest Ir / whole guest Ir (%)');ax.set_title('N27 development point; first vector capture')
fig.tight_layout()
for ext in ['svg','png']: fig.savefig(P/f'profile-exclusive.{ext}', dpi=170)
plt.close(fig)
claim = '[pcc:unverified] PCC-20261116-503112; unsigned producer analysis. No signed performance verdict.'
paragraphs = [
 'Instruction profile after shared inversion and full-point SIMD',
 claim,
 'Job 20261116-144118-ab03: six completed captures, ABBA batch16/vector16 then plain and negation rho. Fixed N27 development fixture0, dimension10,531columns; one public target per solve. Binary dab1240e459c95551e1a558a25f57f4f8d40497a3cdf1e0482217df8efc19f7e, source5cb366343. Current as_chunks style changes are outside this binary.',
 'Whole-guest Ir: batch16 122445015 and122445008; vector16 119553350 and119553343. Ratio of median totals1.024187236. Plain rho10358849; negation rho11374055, same point and seed. These are interpreted instruction-read events across startup, inputs/fixture, context/base/table preparation, collector/matrix/check, JSON output and executed cleanup. They are not native time, hardware retired instructions, cycles or the primary online interval. Two repeats give a repeat range, not a confidence interval.',
 'Raw headers, footers, exclusive sums and annotated PROGRAM TOTALS agree for every capture. Six answers and512exported coefficient states pass producer invocations of the existing independent Python arithmetic. Table/stream Nulgrind admission passed; actual backend is avx2-pclmul128 with positive vector pairs. The allocation used one L4,4CPU,8GiB900s; arithmetic ran on one pinned CPU. Physical placement/memory details and unavailable hardware counters remain unknown.',
 'Attribution and next controlled change',
 'First vector capture: disjoint table builder body, flush and cached helper total57590428exclusiveIr, about48.17% of the whole guest. Batch-inverse product function10152364Ir, about8.49%; field inverse5438160Ir, about4.55%. Inlined work limits attribution. The3451point-kernel context constructors cost821338inclusiveIr, about0.687%; inclusive edges overlap callees and must not be summed with exclusive totals.',
 'The preceding packed-square study and this binary use rustc1.98.1/LLVM22.1.8 and matching recorded build environment. Static cached-narrow false disassembly grows from457to642instruction lines; the new exclusive count is higher, but changed inlining prevents treating that isolated count as a cross-source runtime regression. Keep both binaries and receipts. The next proposed control specializes exact polynomial reduction at compile time, retains the general kernel and fallback, and measures fresh paired targets after correctness controls. No performance result for that proposal is established.',
 'Reproduction: PROFILE_PROTOCOL.md, profile-input.json, run_profile.py, analyze_profiles.py, replay_profiles.py, replay_profile_walk.py, analysis-profile-001.json, replay-profile-001.json, replay-profile-walk-001.json and profile-bundle-receipt.json. Raw83files have lossless bundle SHA/URI pins. Existing native timing REPORT.pdf remains unchanged. Known engineering; curve catalog and volcano/isogeny-route graph sources have no changed mathematical facts. Qualificationnull, invalid for promotion; custody fork retained without ledger rewrite or waiver. Broad optimization remains active.',
 'Sources: owning koblitz_fast.rs, semaev_decomp.rs, ic_boundary/batched_walk.rs and ic_framework/batch_mitm.rs; the preceding ic-native-profile study; official Callgrind manual https://valgrind.org/docs/manual/cl-manual.html. Ir does not establish native latency. Larger fields, GPU execution and complete-process cold improvement remain open.'
]
md=['# '+paragraphs[0], '', *sum(([x+' [pcc:unverified]',''] for x in paragraphs[1:]),[])]
md += ['![Exclusive instruction costs](profile-exclusive.svg)', '', '![Same-target flow](flow.svg)']
(P/'REPORT-profile001.md').write_text('\n'.join(md)+'\n')
styles=getSampleStyleSheet();story=[]
for i,t in enumerate(paragraphs):
 if i==5:story.append(PageBreak())
 style='Title' if i==0 else 'Heading2' if i==5 else 'BodyText'
 story += [Paragraph(escape(t),styles[style]),Spacer(1,10)]
 if i==3:story += [Image(str(P/'profile-exclusive.png'),width=510,height=242)]
 if i==6:story += [Image(str(P/'flow.png'),width=510,height=146)]
SimpleDocTemplate(str(P/'REPORT-profile001.pdf'),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=30).build(story)
print(json.dumps({'report':str(P/'REPORT-profile001.pdf'),'standing':'unsigned'}))
