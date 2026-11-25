"""Build current result PDF and rank chart from the retained exact receipts."""
from pathlib import Path
import json
import re
import subprocess
import tempfile

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.fonttype'] = 'none'
matplotlib.rcParams['svg.hashsalt'] = 'hecke-d39-rank-chart'
import matplotlib.pyplot as plt
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pypdf import PdfWriter
import build_report

HERE = Path(__file__).resolve().parent
build_report.BASE = 'https://github.com/isogeny-labs/cryptanalysis/blob/main/experiments/hecke-d39-scalar-closure-20261030/'


def main():
    first = json.loads((HERE/'runs/20261030T030848Z/receipt.json').read_text())
    control = json.loads((HERE/'runs/20261030-controls/receipt.json').read_text())
    rows = first['arms']+control['arms']
    labels = ['Hecke', 'Hecke + Atkin-Lehner', '+ equalities', '+ doubling',
              '+ doubling/tripling', '+ all additions', 'Equalities ONLY',
              'Doubling ONLY', 'Doubling/tripling ONLY']
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        fig, ax = plt.subplots(figsize=(8.5, 5.2), layout='constrained')
        bars = ax.barh(labels, [r['rank'] for r in rows], color=['#4679ad']*6+['#bd7d28']*3)
        ax.bar_label(bars, padding=3)
        ax.invert_yaxis()
        ax.set_xlim(0, 68)
        ax.set_xlabel('Rank modulo 11 on 64 original columns')
        ax.set_title('One saved D39 fixture: exact ranks, no sampling uncertainty')
        ax.axvline(63, color='gray', linestyle='--', linewidth=1)
        chart = HERE/'ranks.svg'
        fig.savefig(chart, metadata={'Date': None})
        chart.write_text('\n'.join(line.rstrip() for line in chart.read_text().splitlines())+'\n')
        fig.savefig(temp/'ranks.pdf')
        plt.close(fig)
        subprocess.run(['dot','-Tsvg',str(HERE/'result.dot'),'-o',str(HERE/'result.svg')],check=True)
        subprocess.run(['dot','-Tpdf',str(HERE/'result.dot'),'-o',str(temp/'diagram.pdf')],check=True)
        styles = getSampleStyleSheet()
        styles['BodyText'].fontSize=9
        styles['BodyText'].leading=13
        story, pending = [], []

        def flush():
            if pending:
                story.append(Paragraph(build_report.inline(' '.join(pending)),styles['BodyText']))
                story.append(Spacer(1,6))
                pending.clear()

        for line in (HERE/'RESULT.md').read_text().splitlines():
            if line.startswith('#'):
                flush()
                story.append(Paragraph(build_report.inline(line.lstrip('# ')), styles['Title' if line.startswith('# ') else 'Heading2']))
            elif not line.strip():
                flush()
            elif line.startswith('|'):
                flush()
                if not re.fullmatch(r'[| :\-]+',line):
                    story.append(Paragraph(build_report.inline(line.strip('|').replace('|',' / ')),styles['BodyText']))
            else:
                pending.append(line)
        flush()
        SimpleDocTemplate(str(temp/'body.pdf'),title='Hecke D39 closure and generic doubling control',
                          leftMargin=.7*inch,rightMargin=.7*inch).build(story)
        writer = PdfWriter()
        for filename in ('body.pdf', 'diagram.pdf', 'ranks.pdf'):
            writer.append(str(temp/filename))
        writer.add_metadata({'/Title': 'Hecke D39 closure and generic doubling control'})
        with (HERE/'result.pdf').open('wb') as output:
            writer.write(output)


if __name__ == '__main__':
    main()
