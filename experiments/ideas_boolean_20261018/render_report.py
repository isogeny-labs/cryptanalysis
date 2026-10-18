#!/usr/bin/env python3
"""Render recorded values only; no experiment or cryptographic computation."""
from pathlib import Path
from collections import Counter
import hashlib
import html
import json
import shutil
import subprocess
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE=Path(__file__).resolve().parent
RUNS=HERE/'runs'


def read(path):return json.loads((HERE/path).read_text())


def main():
    cases=read('runs/cpu-correctness-r1/inputs.json')
    f5=read('runs/cpu-correctness-r1/f5-results.json')
    dinur=read('runs/cpu-correctness-r1/dinur-results.json')
    scalar_orders=read('runs/native-orders-r1/results.json')
    matrix_orders=read('runs/m4ri-orders-r1/results.json')
    m4ri=read('runs/m4ri-correctness-r1/results.json')
    decision=read('runs/lptwy-correctness-r1/results.json')
    search=read('runs/lptwy-search-r1/results.json')
    replay=read('runs/cpu-correctness-r1/degree4-trace.json')
    counts={
        'original_scalar_F5':dict(Counter(r['status'] for r in f5)),
        'instrumented_native_six_orders':dict(Counter(r['status'] for r in scalar_orders)),
        'M4RI_six_orders':dict(Counter(r['status'] for r in matrix_orders)),
        'existing_F5_M4RI_signature_budget_arms':dict(Counter(r['status'] for r in m4ri)),
        'Dinur_multiple_parity':dict(Counter(r['status'] for r in dinur)),
        'LPTWY_decision':dict(Counter(r['status'] for r in decision)),
        'LPTWY_full_search':dict(Counter(r['status'] for r in search))}
    assert all(r['status']=='verified' for r in matrix_orders)
    assert all(r['status']=='verified' for r in search+decision+dinur)
    assert all(r['basis_certificate']['verified'] for r in m4ri)
    # Fixed generator/product rule must give an order-invariant matrix row
    # count and rank, despite a different elimination priority.
    invariant=[]
    for case in cases:
        rows=[r for r in matrix_orders if r['case_id']==case['case_id']]
        shape={(r['counters']['matrix_rows'],r['counters']['matrix_rank']) for r in rows}
        assert len(shape)==1 and len(rows)==6
        invariant.append({'case_id':case['case_id'],'six_orders_same_matrix_shape_and_rank':True,
                          'rows':next(iter(shape))[0],'rank':next(iter(shape))[1],
                          'all_exact_ideal_certificates_pass':True})
    summary={'schema':'ideas-boolean-execution-status/v1','counts':counts,
             'matrix_invariance':invariant,'fixed_degree4_replay':replay,
             'items':[
                 {'item':3,'status':'partial','executed':'Dinur Algorithm 2 parity component; primary LPTWY q2 decision plus charged full search on exact 6/9/12-variable descended systems; positives and natural certified negatives',
                  'remaining':'Full Dinur isolation/search; realistic n<=41 variable-count ladder; useful exponent fit with uncertainty and stronger baselines. LPTWY pilot partition parameter is not the asymptotic optimum.'},
                 {'item':5,'status':'partial','executed':'48 six-order M4RI+completion exact certificates, with actual elimination block orders, permutations clearly labeled, matrix rows/rank and product/criterion/zero/reduction counters',
                  'remaining':'Invariant F4 solving-degree scan and degree-restricted closure; fixed-degree matrix plus unbounded completion does not determine D. Realistic large descent cells need GPU/full IC runs.'},
                 {'item':6,'status':'partial','executed':'Existing Python/native/M4RI F5 compared on exact inputs; 0/64 signature budget matrix arms; tiny m4 chained D4 matrix; fixed-row trace divergence/fallback charged',
                  'remaining':'Full Joux-Vitse symbolic trace implementation and transfer grid; strongest external F4/F5 baseline (msolve unavailable); realistic nondegenerate m4 D4 cells; GPU end-to-end comparison.'}],
             'timing_claim':'none: shared unisolated CPU correctness runs',
             'registry_check':'Canonical curves.yaml inspected at 0ea8931d21d567f83de47c30bdaac0585f479c11; existing toy13_kb1 uses modulus 8219, our full-curve fixture uses 8231. Candidate/subgroup/EC1 IDs remain null; no registry identity is borrowed.',
             'graph_check':'No canonical IC/volcano graph changed: no new curve transport, candidate or full-DLP result. Existing pdp-scaling and candidate-registry sources were checked.'}
    (HERE/'execution-status.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')

    selected=[r for r in scalar_orders if r['case_id']=='direct-n13-m3-ell3-0']
    labels=[r['order']['name'].replace('grevlex-','').replace('block-eliminate-','block:') for r in selected]
    fig,axes=plt.subplots(1,2,figsize=(11.4,4.5),layout='constrained')
    axes[0].bar(range(6),[r['counters']['reductions'] for r in selected],color='#406c92')
    axes[0].set_xticks(range(6),labels,rotation=42,ha='right',fontsize=8)
    axes[0].set_ylabel('Counted native polynomial reductions')
    axes[0].set_title('Same positive 9-variable S4 input; six orders')
    positive=[r for r in search if r['exists']]
    axes[1].bar([str(r['nvars']) for r in positive],
                [r['charged_counts']['monomial_products'] for r in positive],color='#67947c')
    axes[1].set_yscale('log');axes[1].set_xlabel('Actual Boolean variables N')
    axes[1].set_ylabel('Counted naive ANF monomial-product visits')
    axes[1].set_title('LPTWY full search; every oracle call included')
    axes[1].text(0.02,0.96,'Input degrees: 6, 6, 12\nOne planted input per size; no fitted c',transform=axes[1].transAxes,va='top',fontsize=9)
    fig.suptitle('CPU correctness pilot: operation counts, not speedups',fontsize=13)
    for extension in ['svg','png']:
        fig.savefig(HERE/f'counted-work.{extension}',dpi=180)
    plt.close(fig)
    for extension in ['svg','png']:
        subprocess.run(['dot','-T'+extension,str(HERE/'pipeline.dot'),'-o',str(HERE/f'pipeline.{extension}')],check=True)

    table='\n'.join('| '+ ' | '.join(map(str,row))+' |' for row in [
        ['Fixture','N','ANF degree','Boolean roots','group-verified x tuples'],
        ['---','---:','---:','---:','---:']]+[
        [c['case_id'],c['nvars'],c['input_max_degree'],c['independent_group_root_check']['algebraic_root_count'],
         c['independent_group_root_check']['group_verified_factor_x_tuples']] for c in cases])
    count_table='| Arm | Recorded outcomes |\n|---|---|\n'+'\n'.join(f"| {name} | {json.dumps(status)} |" for name,status in counts.items())
    report=f'''# Boolean solver execution: items 3, 5 and 6

Date: 2026-10-18. Repository base: `0ea8931d21d567f83de47c30bdaac0585f479c11`.
Classification: engineering and exact toy correctness controls. CPU only; `F4_F2_ECHELON=host`, one worker per command. No full IC performance run, calibrated rho comparison, deployment conclusion or solver exponent c is claimed. Raw seconds are shared-host diagnostics.

## Executed result

LPTWY randomized decision passed eight controls and its fully charged decision-to-search reduction passed all six descended systems, including three natural certified negatives. Dinur multiple-parity counting passed six complete vector checks. The existing F5/M4RI engine passed sixteen signature-budget arms. All forty-eight M4RI plus completion order arms passed independent exact ideal certificates. The scalar Python reference and the instrumented scalar native engine each retained twelve 20-second timeouts at the 12-variable S5 cell.

{count_table}

The six orders comprise natural grevlex; reversed and interleaved variable permutations under grevlex; two genuine elimination block orders; and positive weighted grevlex. A block is compared before the other block, without an outer total-degree key. Weight and layout records are retained per trial. Every completed order passed full Boolean root-set equality, staircase dimension, reducedness, original-generator normal forms, and all ordinary and Boolean-field S-pairs.

## Frozen inputs and identities

{table}

Exact polynomials, targets, field moduli, curve coefficients, seeds and input digests are in `runs/cpu-correctness-r1/inputs.json`. These use the full curve `y^2+xy=x^3+1`, not a prime-order subgroup. Field moduli are 8231 at n=13, 131081 at n=17, and 11 at n=3. The canonical registry was checked: its toy13 alias uses modulus 8219 and a specified subgroup, so its EC1 ID is not reused. Candidate, subgroup and EC1 IDs remain null for these correctness fixtures.

The tiny chained m=4, n=3, ell=1 fixture has repeated points and includes 2-torsion. It exercises a real chained S3 encoding in ten Boolean variables, with input degree three, but cannot establish behavior of nondegenerate deployed-size decomposition systems.

## Polynomial-method applicability

Dinur's primary source, arXiv:2005.04800v2, gives the 0.6943 exponent specifically for quadratic degree d=2. These direct S4/S5 descents have measured ANF degrees six and twelve. Frobenius linearity of powers does not make their products quadratic. The implemented reference follows Algorithm 2 with random mixtures, recursive partial parity counting, downset Mobius interpolation/evaluation, and 48N+1 majority repetitions; it uses Equation (2)'s indicator product of (1+P_j) in the base case. Complete returned parity vectors are checked independently. The affine isolation/search reduction is not part of that implementation.

The primary LPTWY author manuscript's Lemma 3.3, q=2, is implemented in `lptwy_decision.cpp`: independent mixtures for each suffix; complement-polynomial products; independent random suffix weights; ANF construction; Mobius evaluation; and a 40% scoreboard threshold over 100N repetitions. The separately frozen search reduction charges the original decision and every variable-fixing decision, all restrictions and final verification. The pilot uses n0=max(1,floor(N/5)), rather than the asymptotic degree-dependent optimal partition. It is a reference implementation of the method with a declared finite parameter, not evidence for its optimized asymptotic exponent.

No credible c fit can be extracted from three tiny sizes that mix two arities and degrees six/twelve. Counting different polynomial operations as one unit would further hide their costs. The raw native counts are retained separately. Full n<=41 scaling at m*ell approximately n, auxiliaries included, and confidence-bounded c remain open. This pilot does not close the polynomial-method paradigm.

## Six-order and signature controls

M4RI release 20260122 was built in a workspace-local prefix because no installed library was available. Its upstream elimination test passed. Matrix-degree settings are N for the direct systems, and four for the tiny chained fixture. At each fixed input, all six orders generated the same matrix row count and rank; final ideals were independently certified. The scalar completion is unbounded and charged separately. A fixed degree-four matrix followed by scalar completion is not a degree-four solving-degree result. Maximum materialized product degree includes reducer-table products and is an observed allocation/work statistic, not a lower bound on the necessary solving degree.

For the planted nine-variable S4 input, the six scalar-native order arms used reductions ranging from {min(r['counters']['reductions'] for r in selected)} to {max(r['counters']['reductions'] for r in selected)}; criterion calls, product visits, nnz and zero outputs are separate axes in the raw results. This is not an online IC speedup. Existing F5 was already implemented in the source corpus; this campaign adds adapters and tests, not a claim of inventing or first building F5. Signature-budget arms 0 and 64 preserve exact roots; F5 rows and matrix ranks are retained rather than treating a stage count as a speedup.

## Charged trace replay

The degree-four trace control intentionally uses a smaller fixed row rule: each of nine S3 equations times every monomial of degree at most one. It has {replay['rows']} rows and {replay['columns']} possible columns. This differs from the existing M4RI generator's full admissible-product rule; their matrix sizes are not directly comparable.

Learning used {replay['learning']['xor_rows']} row XORs. On the distinct next target, replay diverged at zero-based row {replay['replay_attempt']['divergence_row']} after {replay['replay_attempt']['xor_rows']} row XORs, then paid {replay['fallback']['xor_rows']} for full fallback. Baseline alone paid {replay['baseline']['xor_rows']}. Learning plus one target paid {replay['charged_total_xor_rows_learning_plus_one_target']} XORs. Baseline and fallback have identical exact reduced row-space digests. Comparisons and zero rows are retained too. This refutes a saving for this one checked fixed-row replay transfer; it is not a Joux-Vitse symbolic F4 trace implementation or a universal trace-replay impossibility result.

## Remaining acceptance gates

- Item 3 is partial: complete Dinur isolation/search; actual n<=41 descent scaling with all auxiliaries counted; optimized partition parameters; fit uncertainty; and strongest matched baselines remain.
- Item 5 is partial: a genuine bounded F4 solving-degree scan, beyond the fixed-degree matrix plus completion used here, and realistic large cells remain.
- Item 6 is partial: Joux-Vitse symbolic trace learning/transfer, strongest external F4/F5 references, realistic nondegenerate m4 degree-four cells and GPU full IC comparison remain. msolve and Sage were unavailable. No configured GPU host was available.

Canonical graph review: no IC leaderboard, volcano or isogeny-route graph was changed, since this study produced no new candidate, curve transport or verified full DLP. Existing pdp-scaling and candidate-registry sources were checked. The supplied diagram and count graph explain only this correctness campaign.

## Reproduction and sources

The six frozen protocol files declare every arm; exact argv and hashes are recorded in every run's provenance. See `README.md` for executable commands. All failures are retained. Four adapter controls pass in `test_controls.py`. The M4RI source archive digest and upstream test log are retained in `sources/toolchain-build.json` and `sources/build-logs/`.

Primary papers: [Dinur, arXiv:2005.04800v2](https://arxiv.org/abs/2005.04800v2), Algorithms 2/3 and Equation (2); [Lokshtanov et al., SODA 2017 author manuscript](https://people.csail.mit.edu/rrw/polyEqSoda2017Submit.pdf), Lemma 3.3. Download identities and rejected retrievals are in `sources/primary-sources.json`. Existing engines and exact source hashes are pinned in run provenance. Prior fixed-row trace evidence was checked at `crypto-autoresearcher:experiments/EXP-CERTBIN-4e92d7/runs/RUN-CERTBIN-3b7e05/run-report.md`; its n=17,m=2 result is not repeated as a new result here.

![Execution and verification pipeline](pipeline.svg)

![Counted work, not speedups](counted-work.svg)
'''
    (HERE/'REPORT.md').write_text(report)
    font_dir=Path(matplotlib.get_data_path())/'fonts/ttf'
    pdfmetrics.registerFont(TTFont('EmbeddedDejaVu',str(font_dir/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('EmbeddedDejaVu-Bold',str(font_dir/'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('EmbeddedDejaVu',normal='EmbeddedDejaVu',bold='EmbeddedDejaVu-Bold')
    styles=getSampleStyleSheet()
    for name in ['BodyText','Title','Heading1','Heading2']:
        styles[name].fontName='EmbeddedDejaVu' if name=='BodyText' else 'EmbeddedDejaVu-Bold'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
    doc=SimpleDocTemplate(str(HERE/'REPORT.pdf'),pagesize=(8.27*inch,11.69*inch),rightMargin=45,leftMargin=45,topMargin=42,bottomMargin=42)
    story=[]
    for line in report.splitlines():
        if not line.strip():continue
        if line.startswith('!['):continue
        if line.startswith('|'):continue
        if line.startswith('# '):story.append(Paragraph(html.escape(line[2:]),styles['Title']))
        elif line.startswith('## '):story.append(Spacer(1,8));story.append(Paragraph(html.escape(line[3:]),styles['Heading2']))
        else:story.append(Paragraph(html.escape(line.replace('`','')),styles['BodyText']));story.append(Spacer(1,5))
    story.append(PageBreak());story.append(Paragraph('Recorded fixture and certificate counts',styles['Heading1']))
    cells=[['Fixture','N','degree','roots']]+[[c['case_id'],str(c['nvars']),str(c['input_max_degree']),str(c['independent_group_root_check']['algebraic_root_count'])] for c in cases]
    t=Table(cells,colWidths=[290,40,50,50],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8f1fb')),('FONTNAME',(0,0),(-1,-1),'EmbeddedDejaVu'),('FONTSIZE',(0,0),(-1,-1),8),('GRID',(0,0),(-1,-1),0.4,colors.lightgrey),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(t);story.append(Spacer(1,18));story.append(Image(str(HERE/'pipeline.png'),width=7.0*inch,height=1.49*inch));story.append(Spacer(1,16));story.append(Image(str(HERE/'counted-work.png'),width=7.0*inch,height=2.78*inch))
    doc.build(story)
    print(json.dumps(counts,sort_keys=True))


if __name__=='__main__':main()
