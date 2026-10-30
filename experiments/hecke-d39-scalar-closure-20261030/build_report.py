"""Render the research report and its vector evidence diagram (ReportLab)."""
from html import escape
from pathlib import Path
import re
import subprocess
import tempfile

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, Image

HERE = Path(__file__).resolve().parent
BASE = 'https://github.com/isogeny-labs/cryptanalysis/blob/research/hecke-d39-scalar-closure-20261030/experiments/hecke-d39-scalar-closure-20261030/'


def inline(text):
    text = escape(text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  lambda m: '<link color="blue" href="' +
                  (m[2] if m[2].startswith('https://') else BASE+m[2]) + '">' + m[1] + '</link>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    return re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)


def main():
    subprocess.run(['dot', '-Tsvg', str(HERE/'evidence.dot'), '-o', str(HERE/'evidence.svg')], check=True)
    styles = getSampleStyleSheet()
    styles['BodyText'].fontSize = 9
    styles['BodyText'].leading = 13
    story, pending, code = [], [], None

    def flush():
        if pending:
            story.append(Paragraph(inline(' '.join(pending)), styles['BodyText']))
            story.append(Spacer(1, 6))
            pending.clear()

    for line in (HERE/'REPORT.md').read_text().splitlines():
        if line.startswith('```'):
            flush()
            if code is None:
                code = []
            else:
                story.append(Preformatted('\n'.join(code), styles['Code'], maxLineLength=90))
                code = None
        elif code is not None:
            code.append(line)
        elif line.startswith('#'):
            flush()
            level = len(line)-len(line.lstrip('#'))
            story.append(Paragraph(inline(line.lstrip('# ')), styles['Title' if level == 1 else 'Heading2']))
        elif not line.strip():
            flush()
        elif line.startswith('|'):
            flush()
            if not re.fullmatch(r'[| :\-]+', line):
                story.append(Paragraph(inline(line.strip('|').replace('|', ' / ')), styles['BodyText']))
        else:
            pending.append(line)
    flush()
    story.extend([PageBreak(), Paragraph('Evidence map: saved ranks and unexecuted proposal', styles['Heading1'])])
    temp = tempfile.TemporaryDirectory()
    png = Path(temp.name)/'evidence.png'
    subprocess.run(['dot', '-Tpng', '-Gdpi=160', str(HERE/'evidence.dot'), '-o', str(png)], check=True)
    drawing = Image(str(png))
    scale = min(6.5*inch/drawing.imageWidth, 8.5*inch/drawing.imageHeight)
    drawing.drawWidth = drawing.imageWidth*scale
    drawing.drawHeight = drawing.imageHeight*scale
    story.append(drawing)
    story.append(Paragraph('Exact saved rank observations: 40 and 52, one finite fixture; new-arm ranks unknown.', styles['BodyText']))
    SimpleDocTemplate(str(HERE/'report.pdf'), title='Hecke D39 scalar-closure discriminator',
                      author='Research report', leftMargin=0.7*inch, rightMargin=0.7*inch).build(story)
    temp.cleanup()


if __name__ == '__main__':
    main()
