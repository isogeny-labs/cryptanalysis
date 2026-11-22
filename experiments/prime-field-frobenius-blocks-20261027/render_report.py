"""Render a source-linked archival report; reads existing records, runs no solver.

Dependency: ReportLab. Every timing point comes from the preserved JSON.
"""
from hashlib import sha256
from pathlib import Path
import json
import statistics
import textwrap

import reportlab
from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Polygon
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parent
INK = colors.HexColor('#1f2937')
BLUE = colors.HexColor('#dbeafe')
GREEN = colors.HexColor('#dcfce7')
GRAY = colors.HexColor('#64748b')


def label(drawing, x, y, text, size=12, color=INK, anchor='start'):
    drawing.add(String(x, y, text, fontName='Helvetica', fontSize=size,
                       fillColor=color, textAnchor=anchor))


def box(drawing, x, y, width, height, lines, fill):
    drawing.add(Rect(x, y, width, height, rx=6, ry=6, fillColor=fill,
                     strokeColor=GRAY, strokeWidth=0.8))
    for i, line in enumerate(lines):
        label(drawing, x+width/2, y+height-20-18*i, line, anchor='middle')


def arrow(drawing, x1, y1, x2, y2):
    drawing.add(Line(x1, y1, x2, y2, strokeColor=GRAY, strokeWidth=1.2))
    drawing.add(Polygon([x2, y2, x2-7, y2+3, x2-7, y2-3],
                        fillColor=GRAY, strokeColor=GRAY))


def pipeline():
    d = Drawing(720, 420)
    box(d, 0, 270, 170, 70, ['Known labels', 'T = uP + vQ'], BLUE)
    box(d, 210, 320, 170, 85,
        ['Quadratic orbit', 'N(x(R)) = nu', 'Tr2(R) = T'], GREEN)
    box(d, 210, 205, 170, 85,
        ['Cubic orbit', 'Two fixed coefficients', 'Tr3(R) = T'], GREEN)
    box(d, 425, 250, 285, 120,
        ['Actual chosen-base membership', 'Tr(sum R_i) = O',
         'Trace-zero sums are allowed', 'Complete cost gap remains open'], BLUE)
    arrow(d, 170, 315, 210, 355)
    arrow(d, 170, 290, 210, 245)
    arrow(d, 380, 355, 425, 340)
    arrow(d, 380, 245, 425, 280)
    box(d, 0, 40, 205, 90,
        ['Labeled progression', 'T + [j]P, 0 <= j < M', 'M = 2*b*g'], BLUE)
    box(d, 255, 40, 205, 90,
        ['Binomial constraint Z^B = c', 'Quadratic resultant chain', 'Reduce modulo giant polynomial'], GREEN)
    box(d, 510, 40, 205, 90,
        ['Recover signed indices', 'Handle poles and identity', 'Verify points and labels'], BLUE)
    arrow(d, 205, 85, 255, 85)
    arrow(d, 460, 85, 510, 85)
    label(d, 0, 5, 'No isogeny edge is asserted. Diagram describes the archived algorithms.', 11)
    return d


def chart(records):
    d = Drawing(720, 370)
    names = [('binomial_chain', 'Binomial chain'),
             ('coordinate_products', 'Coordinate products'),
             ('sequential', 'Sequential scan'),
             ('interval_bsgs', 'Reused-table BSGS')]
    limit = max(r['complete_cpu_s'] for r in records)*1.08
    x0, width = 195, 500
    label(d, 195, 351, 'Recorded CPU components per 33-coordinate collection (s)', 12)
    for index, (key, title) in enumerate(names):
        values = [r['complete_cpu_s'] for r in records if r['algorithm'] == key]
        assert len(values) == 8
        y = 295-index*72
        label(d, 0, y+4, title, 12)
        label(d, 0, y-13, '8 trials; range shown', 10, GRAY)
        lo, hi = min(values), max(values)
        d.add(Line(x0+width*lo/limit, y, x0+width*hi/limit, y,
                   strokeColor=GRAY, strokeWidth=1))
        for j, value in enumerate(values):
            d.add(Circle(x0+width*value/limit, y+(j-3.5)*3.2, 3,
                         fillColor=colors.HexColor('#2563eb'), strokeColor=None))
        median = x0+width*statistics.median(values)/limit
        d.add(Line(median, y-16, median, y+16, strokeColor=INK, strokeWidth=1.5))
    d.add(Line(x0, 45, x0+width, 45, strokeColor=INK, strokeWidth=0.8))
    for i in range(6):
        value = limit*i/5; x = x0+width*i/5
        d.add(Line(x, 45, x, 40, strokeColor=INK))
        label(d, x, 24, f'{value:.2f}', 10, anchor='middle')
    label(d, 195, 4, 'Partial sums; collection/recovery excluded. Dots: trials; tick: median; span: range.', 10)
    return d


def main():
    raw_path = ROOT/'archive/experiments/ideas/block_benchmark.json'
    data = json.loads(raw_path.read_text())
    records = data['complete_constructions']
    summary = json.loads((ROOT/'archive/results.json').read_text())
    diagram, timing = pipeline(), chart(records)
    renderSVG.drawToFile(diagram, str(ROOT/'pipeline.svg'))
    renderSVG.drawToFile(timing, str(ROOT/'timings.svg'))
    c = Canvas(str(ROOT/'REPORT.pdf'), pagesize=(595.28, 841.89), invariant=1)
    c.setTitle('Fixed-invariant Frobenius lifts and binomial block certificates')

    def text(y, message, size=10):
        c.setFont('Helvetica', size); c.setFillColor(INK)
        for line in textwrap.wrap(message, width=96 if size <= 10 else 78):
            c.drawString(42, y, line); y -= size+4
        return y-4

    def heading(y, message):
        c.setFillColor(INK); c.setFont('Helvetica-Bold', 14)
        c.drawString(42, y, message)
        return y-23

    def figure(drawing, y):
        c.saveState(); c.translate(42, y); c.scale(0.71, 0.71)
        renderPDF.draw(drawing, c, 0, 0); c.restoreState()

    def footer(page):
        c.setFont('Helvetica', 8); c.setFillColor(GRAY)
        c.drawString(42, 25, f'Retrospective exploratory import | 2026-10-27 | page {page}')

    y = heading(792, 'Frobenius lifts and progression certificates')
    y = text(y, 'ARCHIVAL REPORT / PRE-GATE. Three prototypes, their original records and written arguments are published for review. No complete ECDLP cost improvement or qualified timing speedup is established.')
    y = text(y, 'Quadratic: fixed coordinate norm with known elliptic trace; reciprocal sextic divisors. Cubic: two fixed orbit coefficients; a quartic finds lifts, and formal quotients avoid unnecessary common-field embeddings for trace-only computations.')
    y = text(y, 'Progression blocks: preserve the raw binomial through homogeneous quadratic resultants, recover signed indices, and check actual points and labels.')
    figure(diagram, 255)
    y = text(235, 'The original combined requirement remains open: a cheap known-label construction into a small usable coordinate domain, together with lower total time to verified relations. Auxiliary trace labels do not give labels for each extension point in the original prime-order group.')
    y = text(y, 'The six/nine-point identities retain actual chosen-base membership and the full condition Tr(sum R_i)=O. In the quadratic checks, 302 of 304 conjugate choices had a nonidentity extension sum in the trace-zero kernel.')
    text(y, 'Sources: archive/WRITEUP.md; archive/experiments/ideas/lift_benchmark.json; archive/experiments/ideas/lift_witnesses.json. No new scientific experiment was run for this report.')
    footer(1); c.showPage()

    y = heading(792, 'Historical partial construction components')
    text(y, 'Input: y^2=x^3+2*x+25 over F_65537, full prime order 65,371. Each trial collects all 33 usable abscissae of a 64-coordinate coset, using blocks of length 2,048. All methods receive identical starts and stopping rules.')
    figure(timing, 425)
    y = heading(400, 'Recorded component sums: eight trials per method')
    c.setFont('Helvetica-Bold', 9)
    for x, title in [(42, 'Method'), (235, 'Partial CPU seconds'), (350, 'Counted group operations')]:
        c.drawString(x, y, title)
    y -= 20
    for key, title in [('binomial_chain', 'Binomial chain'),
                       ('coordinate_products', 'Coordinate products'),
                       ('sequential', 'Sequential scan'),
                       ('interval_bsgs', 'Reused-table interval BSGS')]:
        totals = summary['complete_labeled_domain_construction'][key]
        c.setFont('Helvetica', 9)
        c.drawString(42, y, title)
        c.drawString(235, y, f"{totals['complete_cpu_s']:.9f}")
        c.drawString(350, y, f"{totals['construction_group_ops']:,}")
        y -= 18
    y = text(y-12, 'CORRECTION: these partial sums omit sorting hits, maintaining known coordinates, termination and transcript work, and antipodal scalar recovery/verification. Each method has 353 antipodal opportunities; the recovery E.mul() calls are uncounted. Complete construction costs and their ratios are unknown. Archive bytes and numbers are unchanged; see ERRATA.md.')
    y = text(y, 'Counted: charged setup, sampling, successful/failed solves, solver index recovery, and scalar_verify() hit/identity checks. Per arm: 515 blocks, 58 empty. BSGS reuses a 2,048-point table. CPU-only; isolation/placement and qualified uncertainty receipts are absent. No qualified speedup is assigned.')
    text(y, 'All trials and sample ranges are shown. Raw source: archive/experiments/ideas/block_benchmark.json. The chain retains M-scale field work; the conjectural O~(B+sqrt(M)) total bound was not achieved.')
    footer(2); c.showPage()

    y = heading(792, 'Small prescribed domains: the scoped restriction')
    y = text(y, 'Statement (written proof, not Lean-checked): with fixed nonzero norm and nonrational quadratic abscissae, B prescribed values of the orbit trace coordinate cover at most 2B nonzero elliptic traces. The same bound holds for B prescribed h values in irreducible cubic polynomials Z^3+h*Z^2+d*Z-c, with c,d fixed.')
    y = text(y, 'Proof: a prescribed quadratic orbit polynomial determines one conjugate pair of abscissae. At one root, the curve equation has at most two ordinates; Frobenius determines the other ordinate. The resulting traces are T and -T. A prescribed irreducible cubic similarly determines one orbit of three abscissae, with at most two ordinate orbits and opposite traces. Taking a union over B parameters proves the bound.')
    y = text(y, 'Therefore independent uniform labeled rejection sampling has nonzero restricted-lift success probability at most 2B/r. This does not rule out nonuniform constructions, adaptive domains, higher-degree chains, or a better direct relation solver. The unrestricted auxiliary norm domain still has about p abscissae.')
    y = heading(y-7, 'Checks, provenance and remaining obligations')
    y = text(y, 'The stored audit verifies 1,664 known labels, 2,496 extension representations, 78 principal divisors, 588 divisor zeros and 1,163,264 progression indices. The extension verifier uses separate field arithmetic; prime-field group/scalar primitives are shared with the producer. No fully independent implementation of every layer is claimed.')
    y = text(y, 'The 34-file archive is preserved byte-for-byte from local commit 820693c998f88b4f7ee213c70c8b99be23734f1b. Its manifest and PROVENANCE.json bind the import. Available original logs are retained. Historical timings are exploratory and are not promoted to current lab validation or candidate records.')
    y = text(y, 'Lean formalization remains open; no Lean executable was available on the publication host. A faithful proof must establish the geometric/Frobenius orbit fiber statement, not assume the fiber bound as an axiom. The report keeps the full written statement and scope.')
    y = text(y, 'Next implementation obligation: solve the reciprocal coefficient surface while retaining chosen-base membership, or reduce the progression certificate below its present field-work cost. A future measurement must use frozen inputs, full failures/extraction/verification accounting and current lab controls.')
    text(y, 'References: Petit-Kosters-Messeng, PKC 2016 (rational-map factor bases); Amadori-Pintore-Sala, ePrint 2017/609 (known-label setting). General map families and classical resultant tools are not claimed as new. See README.md and archive/WRITEUP.md for links, formulas and exact limitations.')
    footer(3); c.save()
    files = ['pipeline.svg', 'timings.svg', 'REPORT.pdf']
    receipt = {'kind': 'document-render-only', 'reportlab_version': reportlab.Version,
               'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
               'input_sha256': sha256(raw_path.read_bytes()).hexdigest(),
               'outputs': {name: {'sha256': sha256((ROOT/name).read_bytes()).hexdigest(),
                                   'bytes': (ROOT/name).stat().st_size} for name in files}}
    (ROOT/'RENDER_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
