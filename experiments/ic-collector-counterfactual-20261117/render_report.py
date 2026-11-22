#!/usr/bin/env python3
"""Render the complete frozen panel, preserving controls and claim boundaries."""
import json
from pathlib import Path
import statistics
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image, PageBreak
from fresh_common import MODES, CONTRASTS, INTERACTION

P = Path(__file__).resolve().parent
a = json.loads((P/'analysis-fresh.json').read_text())
ar = json.loads((P/'independent-arithmetic-fresh.json').read_text())
st = json.loads((P/'independent-states-fresh.json').read_text())
diag = json.loads((P/'analysis-n24.json').read_text())
prep = json.loads((P/'build-001/receipt.json').read_text())
readback = json.loads((P/'readback-timing-optimized-001.json').read_text())
assert all(x['status'] == 'pass' for x in [a, ar, st, diag, readback])
assert len(a['rows']) == 210 and ar['checks'] == 2310 and st['checks'] == 10240
assert readback['rows'][0]['files'] == 2413
CASES = a['cases']
NAMES = {c['n']: c for c in CASES}
assert len(a['aa_failed_rows']) == 13
assert all(c['through_cleanup_contrasts']['remedy_vs_indexed']['bootstrap95'][0] <= 1 <= c['through_cleanup_contrasts']['remedy_vs_indexed']['bootstrap95'][1] for c in CASES)
assert all(NAMES[24]['contrasts'][key]['bootstrap95'][1] < 1 for key in ['indexing_present', 'indexing_absent'])
LABELS = {'indexing_present': 'SP / IP', 'indexing_absent': 'SA / IA',
          'counter_staged': 'SP / SA', 'counter_indexed': 'IP / IA',
          'vs_anchor': 'A / IP', 'vs_compact': 'CI / IP',
          'rebuilt_indexed': 'II / IP', 'remedy_vs_indexed': 'II / IA',
          'setup_interaction': '(SP*IA)/(IP*SA)'}
KEYS = [c[0] for c in CONTRASTS]+[INTERACTION[0]]
FOCUS = ['indexing_present', 'indexing_absent', 'counter_indexed', 'remedy_vs_indexed']
WINDOWS = [('through_cleanup_contrasts', 'native-primary', 'Primary: context + pipeline through owned oracle cleanup'),
           ('contrasts', 'native-collector', 'Collector through owned collector/matrix cleanup'),
           ('table_setup_contrasts', 'native-setup', 'Pair-table preparation, included in primary')]
plt.rcParams.update({'font.size': 9, 'svg.fonttype': 'none', 'svg.hashsalt': 'collector-setup-20261117',
                     'axes.spines.top': False, 'axes.spines.right': False})
for window, name, title in WINDOWS:
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.0))
    for ax, key in zip(axes.flat, FOCUS):
        xs = [c['n'] for c in CASES]
        vals = [c[window][key] for c in CASES]
        ax.vlines(xs, [v['bootstrap95'][0] for v in vals], [v['bootstrap95'][1] for v in vals], color='#235f79')
        ax.scatter(xs, [v['median'] for v in vals], color='#235f79', s=21, zorder=3)
        ax.axhline(1, color='#996b2f', linestyle='--', linewidth=.8)
        ax.set_xticks(xs)
        ax.set_title(LABELS[key], fontsize=10)
        ax.grid(axis='y', alpha=.16)
        ax.set_xlabel('Field degree (frozen cases)', fontsize=8)
        ax.set_ylabel('Time ratio', fontsize=8)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    for ext in ['png', 'svg']:
        fig.savefig(P/(name+'.'+ext), dpi=180, metadata={'Date': None} if ext == 'svg' else None)
    plt.close(fig)
fig, ax = plt.subplots(figsize=(7.2, 2.6))
for c in CASES:
    rows = [r for r in a['rows'] if r['index'] == c['index']]
    ax.scatter([r['fixture'] for r in rows], [r['aa_ratio'] for r in rows], label='N'+str(c['n']), s=13, alpha=.65)
bad = [r for r in a['rows'] if r['aa_pass'] is False]
ax.scatter([r['fixture'] for r in bad], [r['aa_ratio'] for r in bad], marker='x', color='#ac3131', s=30, label='Failed control')
for y in [.85, 1.15]:
    ax.axhline(y, color='#996b2f', linestyle='--', linewidth=.8)
ax.set_xlabel('Panel fixture')
ax.set_ylabel('IP ordinary pre / post collector time')
ax.set_title('All 210 A/A controls; failures retained')
ax.legend(ncol=3, fontsize=7, loc='best')
fig.tight_layout()
for ext in ['png', 'svg']:
    fig.savefig(P/('aa-controls.'+ext), dpi=180, metadata={'Date': None} if ext == 'svg' else None)
plt.close(fig)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='SmallBody', fontName='Helvetica', fontSize=9, leading=12, spaceAfter=5))
styles.add(ParagraphStyle(name='Cell', fontName='Helvetica', fontSize=7.2, leading=9))
styles.add(ParagraphStyle(name='Tiny', fontName='Helvetica', fontSize=7.5, leading=10))
story, md = [], []
def para(text, style='SmallBody'):
    if '[pcc:' not in text:
        text += ' [pcc:unverified]'
    story.extend([Paragraph(escape(text), styles[style]), Spacer(1, 5)])
    md.extend([text, ''])
def page(title):
    if story:
        story.append(PageBreak())
    story.extend([Paragraph(escape(title), styles['Heading1']), Spacer(1, 8)])
    md.extend(['# '+title, ''])
def table(rows, widths=None):
    widths = widths or [520/len(rows[0])]*len(rows[0])
    cells = [[Paragraph(escape(str(v)).replace(' /CI/ ', '<br/>'), styles['Cell']) for v in row] for row in rows]
    t = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e6edf1')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 0), (-1, 0), .5, colors.HexColor('#b8c7d0'))])
    story.extend([t, Spacer(1, 8)])
    md.append('| '+' | '.join(map(str, rows[0]))+' |')
    md.append('| '+' | '.join('---' for _ in rows[0])+' |')
    md.extend('| '+' | '.join(str(v).replace(' /CI/ ', ' ') for v in r)+' |' for r in rows[1:])
    md.append('')
def image(name, height):
    story.extend([Image(str(P/(name+'.png')), width=520, height=height), Spacer(1, 6)])
    md.extend(['!['+name+']('+name+'.svg)', ''])
def ratio(c, window, key):
    v = c[window][key]
    return f"{v['median']:.5f} /CI/ [{v['bootstrap95'][0]:.5f}, {v['bootstrap95'][1]:.5f}]"
def full_table(window):
    table([['Effect', *['N'+str(c['n']) for c in CASES]]]+
          [[LABELS[key], *[ratio(c, window, key) for c in CASES]] for key in KEYS], [70]+[90]*5)

page('Collector setup counterfactual')
para('Outcome: omitting the indexed metadata entry did not establish a primary improvement over the frozen indexed control in any field. N24 reproduces a collector slowdown from indexed preparation within one binary, with or without that entry. The physical cause remains open.')
para('Standing: unsigned producer evidence, claim PCC-20261117-262375. Invalid for promotion: all 13 failed A/A rows are retained. Native preparation is separately recorded as unsigned PCC-20261117-b8257b. No independently signed speedup verdict or mathematical-novelty conclusion follows.')
table([['Field', 'Blocks', 'Failed A/A', 'II / IA primary, paired median [95%]']]+
      [['N'+str(c['n']), c['attempted'], c['aa_failures'], ratio(c, 'through_cleanup_contrasts', 'remedy_vs_indexed')] for c in CASES], [45, 50, 65, 360])
para(f"The panel completed 210 blocks: {ar['pipeline_answers']} IC, {ar['rho_answers']} same-target rho and {ar['aa_answers']} A/A answers. Existing independent Python arithmetic checked all {ar['checks']} answers and {st['checks']} exported walk states. There were {a['capped_arms']} capped IC arms.")
para('A = frozen anchor ordinary; CI = compact inverse; II = frozen indexed inverse. SP/SA = staged preparation with metadata present/absent. IP/IA = indexed preparation with metadata present/absent. The four new paths use one binary and the same inverse-vector query body. Default behavior stays IP; absence is an experimental control.')
para('Primary includes context plus pipeline through owned oracle cleanup: base/table setup, collector, matrix and scalar check. Prior fixture/calibration/spec/empty allocation, startup/JSON and later context/report destruction are excluded. Collector has its own cleanup boundary. Full-process cold remains open.')

for window, name, title in WINDOWS:
    page(title)
    image(name, 289)
    full_table(window)
    para('Each cell is median reference/candidate time and a pointwise 95% paired bootstrap interval, 10000 resamples, seed 20261116, all 42 rows per field. Above 1 favors the denominator for pairwise effects. The interaction is neutral: it measures relative setup effects, not a standalone optimization direction. No familywise coverage, filtering, host pooling or cross-panel products.', 'Tiny')
    if window == 'contrasts':
        para('N24 SP/IP and SA/IA intervals lie below 1. The collector slowdown persists without the counter entry; the counter-removal and interaction intervals do not establish a remedy. N27 indexing-effect intervals contain1. These effects identify declared preparation choices in this build, not a cache, allocator or historical cross-binary cause.', 'Tiny')

page('Mean costs and matched same-point rho')
table([['Field', 'A ms', 'CI ms', 'II ms', 'SP ms', 'SA ms', 'IP ms', 'IA ms']]+
      [['N'+str(c['n']), *[f"{1000*c['methods'][m]['mean_context_plus_computation_s']:.4f}" for m in MODES]] for c in CASES], [38]+[482/7]*7)
para('Primary arithmetic means in milliseconds; these are separate from the paired median-ratio estimands. Earlier optimizations shared by the new cells explain their comparison with the older anchor. An anchor comparison is not a newly isolated gain from omitting metadata.')
table([['Field', 'Plain rho / IP', 'Negation rho / IP', 'Plain rho / IA', 'Negation rho / IA']]+
      [['N'+str(c['n']), *[f"{c['methods'][m]['median_context_rho_over_pipeline'][kind]:.5f}" for m in [MODES[5], MODES[6]] for kind in ['rho-plain', 'rho-negation']]] for c in CASES], [40, 120, 120, 120, 120])
para('Reference entries are paired medians of context-plus-rho compute / IC primary on the exact same Q/G/r/seed. Ratios below 1 favor rho. Original compact-control rho arithmetic is retained. No setup-reused-rho or full-process-cold crossover is established.')
table([['Field', 'II mean RSS MiB', 'IP mean RSS MiB', 'IA mean RSS MiB']]+
      [['N'+str(c['n']), *[f"{statistics.mean(r['methods'][m]['peak_rss_kib'] for r in a['rows'] if r['index']==c['index'])/1024:.3f}" for m in [MODES[2], MODES[5], MODES[6]]]] for c in CASES], [40, 160, 160, 160])
para('RSS is complete-child GNUtime peak RSS, averaged over 42 targets. It includes startup/reporting and does not measure heap allocations or diagnose the collector mechanism.')

page('Instruction evidence and native admission')
table([['Cell', 'Whole guest Ir', 'Collector own Ir', 'Walker own Ir', 'Probe own Ir', 'Lookup own Ir']]+
      [[r['tag'].upper(), f"{r['whole_guest_ir']:,}", *[f"{r['selected_exclusive_function_ir'][k]:,}" for k in ['collector_function', 'walker_function', 'pair_probe_function', 'witness_lookup_function']]] for r in diag['rows']], [30, 100, 100, 100, 95, 95])
para('Separate pre-generation N24 fixture 0 captures use synthetic cost units 1 and pinned Callgrind tools. All four use the same binary. Selected generic-dispatch exclusive Ir is 0. Whole counts include setup/reporting; selected function-exclusive counts exclude callees. Neither is a native collector clock, hardware retirement count or complete physical-cost explanation.')
insts = json.loads((P/'instances.json').read_text())
table([['Field', 'Complete maps', 'Staged maps', 'Staged compact', 'Indexed pairs', 'Const pairs']]+
      [[insts[i]['field']['degree'], r['complete_map_comparisons'], r['staged_map_comparisons'], r['staged_compact_map_comparisons'], r['indexed_prepare_pairs'], r['vector_const_pairs']] for i, r in enumerate(prep['native_table_smoke'])], [35, 90, 85, 95, 110, 105])
para('Native preparation passed strict library/probe Clippy, 29 framework tests and the existing walker/vector/inverse/compact/packed/guard controls plus staged first-witness checks. Positive native AVX2/PCLMUL128 use was admitted. Independent arithmetic checked 20 four-cell pipeline answers, 2,560 walk states and 4 diagnostic answers before fresh identities.')
para('Pair/chunk order, first witnesses, compact 8 byte payload, field arithmetic, direct m2 probe, query schedule and inverse counters are preserved. Counter absence never constructs and then removes the entry; accumulation remains. Native table map controls separately establish staged/indexed selection.')

page('Every failed A/A control retained')
image('aa-controls', 188)
table([['Field', 'Controls', 'Failed', 'Minimum ratio', 'Maximum ratio']]+
      [['N'+str(c['n']), 42, c['aa_failures'], f"{min(r['aa_ratio'] for r in a['rows'] if r['index']==c['index']):.5f}", f"{max(r['aa_ratio'] for r in a['rows'] if r['index']==c['index']):.5f}"] for c in CASES], [40, 70, 70, 170, 170])
table([['Field', 'Fixture', 'Pre / post ratio']]+
      [['N'+str(CASES[r['index']]['n']), r['fixture'], f"{r['ratio']:.8f}"] for r in a['aa_failed_rows']], [70, 100, 350])
para('A/A is IP ordinary fixture 0 before/after each block, acceptance band 0.85..1.15. All failures remain in all 42 row estimates. No replacement host or filtered panel was used. N24/N27 have no failed A/A rows, but the full panel remains unsigned and invalid for promotion.', 'Tiny')

page('Source identity and raw custody')
for name in ['anchor-input.json', 'prepared-input.json', 'indexed-input.json', 'optimized-input.json']:
    b = json.loads((P/name).read_text())
    para(f"{name}: binary {b['binary_sha256']}; source {b['source_commit']}; preparation {b['source_job']}.", 'Tiny')
para('Native preparation source 5623753791bd66e01056ecb8bd901b5f6caf352e reconstructs the exact indexed sixteen-source recipe, including its archived Cargo manifest, with three declared Rust overlays. Compiler/root/environment match. Later main integration does not relabel the frozen native binary or source.')
para('Timing source 0c3e791087b39b273f7cc0d5d01d1494a9130c18 and all 35 candidate / 210 workload identities were published before launch. Fresh-generation.json records the contemporaneous ARM identity-probe hash, prior build receipt and generator/controller hashes. The probe hash matched before/after generation; it is an identity generator, not the x86 timing binary.')
para('The completed job snapshot matches all 15 declared controller/input hashes and the published identities. Every native target matched its workload. See fresh-snapshot-binding.json for full snapshot, runner-status, metadata and generation-receipt SHA256 values.')
para('All 130 preparation files and 2,413 timing files were uploaded through scoped default/us-west-2/crypto-autoresearcher in lossless bundles. Fresh downloads checked every member size/hash. Per-file absolute URIs, bundle receipts and readback receipts are retained. No earlier raw arm, failed local check or checkpoint attempt was overwritten.')
para('Ledger bookkeeping limitation: the benchmark record was initialized after native execution. Its original creation time and coordinator capture are retained; native source/hardware/command timestamps come from the original runner receipt. Protocols, controllers, identities and the generation receipt were prospectively published. The ledger entry is not backdated.')

page('Reproduction, limits and next falsifier')
para('Timing job 20261117-154829-472b uses one Modal L4 / 4 CPU / 8 GiB / 900 s allocation, CPU arithmetic on one exposed CPU. Startup preceded actual execution, which completed in 373 seconds. GPU arithmetic was not measured. Physical placement, memory technology/speed/channels and a qualified isolation tier remain unknown.')
para('Fixtures 726..767 per field; fourteen Williams orders repeated 3, every method position and ordered adjacent pair 6 times. Matched plain/negation rho use separate compact-control processes. Controller 780 s, child 12 s / preflight 30 s, and 8 GiB native virtual cap. No observer subprocess or extra instrumentation ran on the timing worker.')
para('Use a fresh verification checkout for analysis/binding regeneration. Existing replay receipts include invocation timings and are immutable evidence; write new replay outputs when checking the same data.')
for command in ['python3 analyze_fresh.py', 'python3 replay_fresh_answers.py --stem independent-arithmetic-check',
                'python3 replay_fresh_states.py timing-optimized-001 --out independent-states-check.json',
                'python3 seal_fresh_provenance.py 20261117-154829-472b --identities-revision 0c3e791087b39b273f7cc0d5d01d1494a9130c18']:
    para('From this study directory: '+command, 'Tiny')
para('The record/export plan remains 203 metrics and 25 raw references. Nine effects are reported separately for primary, collector and table setup; within-block interaction is computed before aggregation. The raw analysis retains every method cost, reference, failed control and diagnostic. All intervals are pointwise and exploratory.')
para('Next discriminating experiment: retain indexed arithmetic/table contents and independently vary the old scratch reservations and old gather writes. A repeatable restored collector cost would narrow the preparation-state mechanism; no effect rejects that factor. Any candidate remedy must lower the charged primary against the frozen control on separately fresh targets.')
para('The original extra general-dispatch work was fixed earlier. The later indexed collector regression remains unresolved at the physical-mechanism level. No new primary improvement over frozen indexed, qualified speedup, full-cold result, GPU throughput or broader mathematical breakthrough is established here. The broader performance objective remains open.')

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#52616b'))
    canvas.drawString(36, 22, 'Unverified producer evidence | invalid for promotion | all controls retained')
    canvas.drawRightString(A4[0]-36, 22, str(doc.page))
    canvas.restoreState()

doc = SimpleDocTemplate(str(P/'REPORT.pdf'), pagesize=A4, rightMargin=36, leftMargin=36,
                        topMargin=32, bottomMargin=36, title='Collector setup counterfactual', author='Cryptanalysis research')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
(P/'REPORT.md').write_text('\n'.join(md)+'\n')
print('Rendered REPORT.pdf, source Markdown and four plot families; inspect every page before delivery')
