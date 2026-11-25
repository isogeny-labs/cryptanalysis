"""Summarize every native cell, including incomplete and killed processes."""
import collections
import json
from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas

HERE=Path(__file__).resolve().parent

def main():
    manifest=json.loads((HERE/'manifest.json').read_text())
    summaries=[]
    for cell in manifest['cells']:
        row=next(iter(cell.get('native_rows',[])),{})
        decomposition=row.get('decomposition',{})
        solver=decomposition.get('solver') or {}
        summaries.append({'label':cell['label'],'degree':cell['degree'],'seed':cell['seed'],
             'arm':cell['arm'],'status':cell['status'],'native_status':cell.get('native_status'),
             'relations':decomposition.get('relations_found'),
             'trials':decomposition.get('trials'),
             'recovered_log':row.get('recovered'),'native_self_check':row.get('verified'),
             'solver_calls':solver.get('calls'),'solver_conflicts':solver.get('ops'),
             'solver_budget_exceeded':solver.get('budget_exceeded'),
             'wall_seconds':cell['wall_seconds'],'peak_rss_gib':cell['peak_rss_gib']})
    result={'scope':manifest['scope'],'planned':24,'attempted':len(summaries),
            'status_counts':dict(collections.Counter(x['status'] for x in summaries)),
            'cells':summaries}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2))
    lines=['# Native m=31 local feasibility results','',
      'Producer assertions only: [pcc:unverified]. CPU-only debug build; local runs authorized by the user. No speedup or promotion claim.',
      '',f"Source commit: `{manifest['commit']}`. Binary SHA256: `{manifest['binary_sha256']}`.",
      '', 'Each process had 20 seconds and 2 GiB. SAT calls had a 1000-conflict cap; m31 cells had four target trials.',
      'Native incomplete means the capped pipeline did not recover a logarithm. A timeout has no completed native report; its relation count is unknown, not zero.',
      '', '| Cell | Process outcome | Relations | Solver capped calls | Native log self-check | Wall s |',
      '|---|---|---:|---:|---|---:|']
    for r in summaries:
        value=lambda k:'unknown' if r[k] is None else str(r[k])
        lines.append(f"| {r['label']} | {r['status']} | {value('relations')} | {value('solver_budget_exceeded')} | {value('native_self_check')} | {r['wall_seconds']:.3f} |")
    lines+=['','The m2 arms are controls, not matched m31 speed comparisons. Some setup and solver costs are converted using local measured timing; S is not a qualified performance result.',
       'Leaf membership uses the actual native factor base. Every returned row is checked by native group addition. SAT chart UNSAT excludes identity intermediate sums and is not a proof of global non-decomposability.',
       'Raw reports, console logs, commands, source/lock/binary hashes and process statuses are retained locally beside this report. Signed independent PCC validation is absent.']
    (HERE/'REPORT.md').write_text('\n'.join(lines)+'\n')
    pdf=canvas.Canvas(str(HERE/'REPORT.pdf'),pagesize=landscape(A4));width,height=landscape(A4)
    pdf.setFont('Helvetica-Bold',14);pdf.drawString(30,height-30,'Native m=31 feasibility - producer assertions, PCC unverified')
    pdf.setFont('Helvetica',9);pdf.drawString(30,height-48,'Local CPU/debug run. S3 upload waived by user. No speedup or promotion claim.')
    pdf.drawString(30,height-63,'Native fields -> local S3 blocks -> native XOR/CDCL -> tree sign lift -> native group-law check')
    y=height-90
    for r in summaries:
        if y<40:pdf.showPage();pdf.setFont('Helvetica',9);y=height-35
        relation='unknown' if r['relations'] is None else str(r['relations'])
        pdf.drawString(30,y,f"{r['label']:<35} {r['status']:<20} relations={relation:<7} log-check={str(r['native_self_check']):<7} wall={r['wall_seconds']:.3f}s")
        y-=15
    pdf.save()
    print(json.dumps({k:v for k,v in result.items() if k!='cells'},indent=2))

if __name__=='__main__':main()
