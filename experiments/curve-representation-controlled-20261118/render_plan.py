"""Render the pre-data design. No scientific measurements are generated."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib

HERE = Path(__file__).resolve().parent


def main():
    fonts = Path(matplotlib.get_data_path())/'fonts/ttf'
    pdfmetrics.registerFont(TTFont('PlanSans', str(fonts/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('PlanSans-Bold', str(fonts/'DejaVuSans-Bold.ttf')))
    target = HERE/'protocol-plan.pdf'
    c = canvas.Canvas(str(target), pagesize=(595, 842))
    c.setTitle('Controlled curve representation comparison — protocol only')
    ink, teal = HexColor('#24374A'), HexColor('#007F87')
    c.setFillColor(ink)
    c.setFont('PlanSans-Bold', 20)
    c.drawString(42, 790, 'Controlled representation comparison')
    c.setFont('PlanSans', 11)
    c.drawString(42, 766, 'Protocol only | 18 November 2026 | No panel data collected')
    c.setFillColor(teal)
    c.setFont('PlanSans-Bold', 11)
    c.drawString(42, 735, 'One geometry, one base, one target/query stream; four formulations')

    def box(x, y, w, h, lines):
        c.setStrokeColor(teal)
        c.setFillColor(HexColor('#F0F8F8'))
        c.roundRect(x, y, w, h, 5, stroke=1, fill=1)
        c.setFillColor(ink)
        c.setFont('PlanSans', 10)
        for i, line in enumerate(lines):
            c.drawCentredString(x+w/2, y+h-18-14*i, line)

    box(42, 650, 510, 58, ['Fixed growing toy fixtures and sign-folded factor bases',
                          'Separate same-field and same-subgroup-order cofactor-1 controls'])
    labels = [['Montgomery', 'eliminated S4'], ['Edwards', 'eliminated S4'],
              ['Torsion invariant', 'quotient-coordinate S4'], ['Retained point', 'S3 chain + infinity']]
    for i, lines in enumerate(labels):
        x = 42+i*130
        box(x, 535, 120, 65, lines)
        c.setStrokeColor(teal)
        c.line(x+60, 650, x+60, 602)
        c.line(x+60, 535, x+60, 490)
    box(42, 425, 510, 65, ['Lift coordinate roots to actual source-curve point relations',
                          'Reject false candidates; record all failures and timeouts',
                          'Update rank and attempt scalar replay at the stopping rank'])
    c.line(297, 425, 297, 398)
    box(42, 325, 510, 73, ['Record phase wall/CPU time and exact accepted-row denominator',
                          'OS peak RSS, rejected candidates, query/collector censoring',
                          'A/A baseline, planted/negative controls, same-point rho reference'])
    c.setFillColor(ink)
    c.setFont('PlanSans-Bold', 12)
    c.drawString(42, 289, 'Admission status')
    c.setFont('PlanSans', 10)
    for i, line in enumerate([
        'S3 bucket and normal checkpoint upload returned AllAccessDisabled.',
        'The repository requires checkpoint success and CUDA-host admission.',
        'A user-authorized Git-checkpoint / exploratory-CPU exception is pending.',
        'No exception, isolation receipt, signed verdict or run result is invented.',
        '',
        'Limits planned: 24 ordinary queries, 2 seconds per PDP, 60 seconds per cell.',
        'A zero accepted-row denominator stays null; incomplete collection stays censored.',
        'Cofactor-1 controls do not possess all four source-curve representations.',
        'Ordinary-host observations cannot establish a qualified timing advantage.'
    ]):
        c.drawString(42, 266-17*i, line)
    c.setFont('PlanSans', 8)
    c.drawString(42, 63, 'Editable source: render_plan.py | Full design: PLAN.md and protocol.json | PR #1767')
    c.drawString(42, 48, 'All scientific assertions remain unverified. [pcc:unverified]')
    c.save()
    print(target.name)


if __name__ == '__main__':
    main()
