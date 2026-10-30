"""Build source-linked vector report and exact finite-count plots."""
from html import escape
import json
from pathlib import Path
import re
import subprocess
import tempfile

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.fonttype']='none'
matplotlib.rcParams['svg.hashsalt']='hecke-sparse-target-20261030'
import matplotlib.pyplot as plt
import numpy as np
from pypdf import PdfWriter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer

HERE=Path(__file__).resolve().parent
BASE='https://github.com/isogeny-labs/cryptanalysis/blob/research/hecke-sparse-target-20261030/experiments/hecke-sparse-target-20261030/'


def inline(text):
    text=escape(text)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:'<link color="blue" href="'+(m[2] if m[2].startswith('https://') else BASE+m[2])+'">'+m[1]+'</link>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)
    return re.sub(r'`([^`]+)`',r'<font name="Courier">\1</font>',text)


def main():
    rows=[json.loads((HERE/'runs'/cell/'receipt.json').read_text())
          for cell in ['f6-small-01','f6-medium-01','f6-large-01','f30-01']]
    with tempfile.TemporaryDirectory() as directory:
        temp=Path(directory)
        fig,axes=plt.subplots(2,1,figsize=(8.3,8.5),layout='constrained')
        x=np.arange(4);w=.36
        for offset,key,label,color in [(-w/2,'generic_bootstrap','Generic scalar-closure bootstrap','#bc812e'),
                                       (w/2,'bootstrap','Hecke + scalar bootstrap','#3977aa')]:
            bars=axes[0].bar(x+offset,[r[key]['free_logs_solved_generically'] for r in rows],w,label=label,color=color)
            axes[0].bar_label(bars)
        axes[0].set_xticks(x,[f"f{r['f']}, r={r['r']:,}" for r in rows],rotation=10)
        axes[0].set_ylabel('Required generic base-log queries')
        axes[0].set_title('Exact finite query counts; not total costs or speedups')
        axes[0].legend(fontsize=9)
        names=['Original base','Trace-grown201','Generic matched201']
        attempts=[256,3,10]
        bars=axes[1].barh(names,attempts,color=['#bd6565','#3977aa','#bc812e'])
        axes[1].bar_label(bars,labels=['failed at cap256','verified at3','verified at10'],padding=3)
        axes[1].set_xlim(0,330);axes[1].invert_yaxis()
        axes[1].set_xlabel('Queries on the same r=206,477 target')
        axes[1].set_title('Exploratory target continuation; index and growth setup charged separately')
        svg=HERE/'counts.svg';fig.savefig(svg,metadata={'Date':None})
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
        fig.savefig(temp/'counts.pdf');plt.close(fig)
        subprocess.run(['dot','-Tsvg',str(HERE/'evidence.dot'),'-o',str(HERE/'evidence.svg')],check=True)
        subprocess.run(['dot','-Tpdf',str(HERE/'evidence.dot'),'-o',str(temp/'diagram.pdf')],check=True)
        styles=getSampleStyleSheet();styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
        story=[];pending=[]
        def flush():
            if pending:
                story.extend([Paragraph(inline(' '.join(pending)),styles['BodyText']),Spacer(1,5)])
                pending.clear()
        for line in (HERE/'RESULT.md').read_text().splitlines():
            if line.startswith('#'):
                flush();story.append(Paragraph(inline(line.lstrip('# ')),styles['Title' if line.startswith('# ') else 'Heading2']))
            elif not line.strip():flush()
            elif line.startswith('|'):
                flush()
                if not re.fullmatch(r'[| :\-]+',line):story.append(Paragraph(inline(line.strip('|').replace('|',' / ')),styles['BodyText']))
            else:pending.append(line)
        flush()
        SimpleDocTemplate(str(temp/'body.pdf'),title='Sparse Hecke constraints and target connection',leftMargin=.65*inch,rightMargin=.65*inch).build(story)
        writer=PdfWriter()
        for name in ['body.pdf','diagram.pdf','counts.pdf']:writer.append(str(temp/name))
        writer.add_metadata({'/Title':'Sparse Hecke constraints and target connection'})
        for page in writer.pages:page.compress_content_streams()
        with (HERE/'report.pdf').open('wb') as output:writer.write(output)


if __name__=='__main__':main()
