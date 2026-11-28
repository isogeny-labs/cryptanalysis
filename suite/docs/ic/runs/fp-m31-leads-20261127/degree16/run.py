"""Selected diagnostic on the saved, original native worker binary."""
import hashlib,importlib.util,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[5]
spec=importlib.util.spec_from_file_location('lead_watch',REPO.parent.parent/'tools/lead_sweep.py')
watch=importlib.util.module_from_spec(spec);spec.loader.exec_module(watch)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    raw=HERE/'raw';raw.mkdir(exist_ok=False)
    binary=Path('/workspace/scratch/m31-five-leads-binaries/m31_encoding_pilot')
    inp=HERE.parent/'inputs/k4-m4-planted.json'
    parent=json.loads((HERE.parent/'manifest.json').read_text())
    assert sha(binary)==parent['binary_sha256']['m31_encoding_pilot']
    result={'p':2147483647,'source_commit':parent['source_commit'],'orchestrator_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'input_sha256':sha(inp),'binary_sha256':sha(binary),'protocol_sha256':sha(HERE/'PROTOCOL.md'),'planned':4,'cells':[]}
    for e in ('monolithic','partial'):
        for s in ('global','staged'):
            name=e+'-'+s;path=raw/(name+'.txt')
            command=list(map(str,[binary,'--input',inp,'--m',4,'--encoding',e,'--schedule',s,'--budget-ms',2000,'--degree',16,'--construction-ms',10000]))
            status=watch.watched_run(command,path,2,20,cwd=REPO)
            parsed=[]
            for line in path.read_text(errors='replace').splitlines():
                try:parsed.append(json.loads(line))
                except json.JSONDecodeError:pass
            reports=[x for x in parsed if isinstance(x,dict) and x.get('status')]
            report=reports[-1] if reports else None
            if report is not None:(raw/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
            row={'id':name,'kind':'encoding','case':'k4-m4-planted','encoding':e,'schedule':s,'command':command,'log_sha256':sha(path),'report':report,**status}
            if report is not None:row['report_sha256']=sha(raw/(name+'.json'))
            result['cells'].append(row);(HERE/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({'cell':name,'process':row['status'],'native':report.get('status') if report else None,'f4_steps':sum(x['steps'] for x in report['stages']) if report else None}),flush=True)
if __name__=='__main__':main()
