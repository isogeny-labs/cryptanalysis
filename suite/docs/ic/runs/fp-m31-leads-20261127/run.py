"""Orchestrate native implementations; all curve and solver work is Rust."""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
WORKSPACE=REPO.parent.parent
spec=importlib.util.spec_from_file_location('watch',WORKSPACE/'tools/lead_sweep.py')
watch=importlib.util.module_from_spec(spec);spec.loader.exec_module(watch)
BIN=REPO/'suite/target/debug/examples'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def final_report(path):
    reports=[]
    for line in path.read_text(errors='replace').splitlines():
        try:
            value=json.loads(line)
            if isinstance(value,dict):reports.append(value)
        except json.JSONDecodeError:pass
    final=[r for r in reports if r.get('status') or r.get('mode') in ('target_controls','signed_cancellation_controls')]
    return final[-1] if final else None,reports

def main():
    raw=HERE/'raw';raw.mkdir(exist_ok=False)
    cases=json.loads((HERE/'panel.json').read_text())['cases']
    seeds=json.loads((HERE/'seeds.json').read_text())
    for item in seeds['encoding_cases']:assert sha(HERE/'inputs'/(item['id']+'.json'))==item['input_sha256']
    manifest={'schema':'m31-five-lead-local-run/v1','p':2147483647,
      'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
      'protocol_sha256':sha(HERE/'PROTOCOL.md'),'seed_sha256':sha(HERE/'seeds.json'),
      'binary_sha256':{name:sha(BIN/name) for name in ('m31_relation_leads','m31_encoding_pilot')},
      'platform':platform.platform(),'planned':146,'cells':[],'transport':[]}
    def persist():(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    def execute(name,command,kind,**metadata):
        path=raw/(name+'.txt')
        status=watch.watched_run(list(map(str,command)),path,2,20,cwd=REPO)
        report,all_reports=final_report(path)
        if report is not None:(raw/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        row={'id':name,'kind':kind,'command':list(map(str,command)),**metadata,**status,
          'log_sha256':sha(path),'report':report,'preflight':[r for r in all_reports if r.get('stage')=='start']}
        if report is not None:row['report_sha256']=sha(raw/(name+'.json'))
        manifest['cells' if kind!='transport' else 'transport'].append(row);persist()
        small={k:v for k,v in row.items() if k not in ('command','report','preflight')}
        if report is not None:small['native_status']=report.get('status',report.get('mode'))
        print(json.dumps(small),flush=True)
        return row
    persist()
    # Native stdout has one owner. Deliberate failure must not skip later work.
    first=execute('transport-deliberate-failure',[BIN/'m31_relation_leads','invalid-control-command'],'transport')
    second=execute('transport-next-command',[BIN/'m31_relation_leads','panel'],'transport')
    assert first['exit_code']!=0 and second['exit_code']==0
    for mode in ('target','cancel'):
        row=execute('lead-'+mode,[BIN/'m31_relation_leads',mode],'control')
        assert row['exit_code']==0 and row['report'] is not None,'correctness control failed; retain logs and stop'
    # Root implementation and sign/partial correctness are checked before F4 cells.
    for c in cases:
        for schedule in ('global','staged'):
            encodings=['monolithic','serial','balanced','partial','explicit']
            if c['kind']=='ordinary1':encodings.reverse()
            for encoding in encodings:
                path=HERE/'inputs'/(c['id']+'.json')
                execute(c['id']+'-'+encoding+'-'+schedule,
                  [BIN/'m31_encoding_pilot','--input',path,'--m',c['m'],'--encoding',encoding,
                   '--schedule',schedule,'--budget-ms',2000,'--degree',8,'--construction-ms',10000],
                  'encoding',case=c['id'],m=c['m'],columns=len(c['base']),target_kind=c['kind'],
                  encoding=encoding,schedule=schedule,input_sha256=sha(path))
    for rep in (0,1):
        for m in (3,4):
            for arm in (('torus','interval','random') if rep==0 else ('random','interval','torus')):
                for method in (('full','partial') if rep==0 else ('partial','full')):
                    execute(f'collection-{arm}-{method}-rep{rep}-m{m}',
                      [BIN/'m31_relation_leads','collect',arm,method,rep,m,256,5000],
                      'collection',replicate=rep,m=m,arm=arm,method=method)
    assert len(manifest['cells'])==146
    persist()

if __name__=='__main__':main()
