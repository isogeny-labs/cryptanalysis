"""Same saved native worker, separately frozen direct-pair experiment."""
from pathlib import Path
import importlib.util,json,sys,subprocess
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('parent_e2e',HERE.parent/'run.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
b.HERE=HERE;b.SEEDS=json.loads((HERE/'seeds.json').read_text())
OLD=[[2144058214,807222724],[1764015007,688050509]]
def dev():
    (HERE/'raw').mkdir(exist_ok=False)
    original=json.loads((HERE.parent/'manifest.json').read_text());assert b.sha(b.BIN)==original['binary_sha256']
    m={'schema':'m31-e2e-m2-local/v1','p':2147483647,'source_commit':b.source(),'binary_sha256':b.sha(b.BIN),'reference_binary_sha256':b.sha(b.RHO),'protocol_sha256':b.sha(HERE/'PROTOCOL.md'),'seeds_sha256':b.sha(HERE/'seeds.json'),'planned':32,'cpu_affinity':b.PIN,'cells':[]}
    b.save(m);groups=[]
    for size in (128,256,512):
        config={'columns':size,'summands':2,'base':'interval','method':'indexed','max_queries':4000000}
        rows=[b.ic(m,f'dev-B{size}-T{rep}',q,b.SEEDS['development'][rep],config,stage='development',replicate=rep) for rep,q in enumerate(OLD)]
        groups.append(rows)
    chosen=min(groups,key=b.score);assert b.score(chosen)[0]==-2
    selection={'schema':'m31-e2e-m2-selection/v1','source_commit':b.source(),'binary_sha256':b.sha(b.BIN),'selected':chosen[0]['configuration'],'references':[{'columns':512,'summands':3,'base':'interval','method':'indexed','max_queries':4000000},{'columns':512,'summands':4,'base':'interval','method':'indexed','max_queries':4000000}],'criterion':'two complete old-target recoveries, then geometric mean cold time; no new heldout Q seen'}
    (HERE/'selection.json').write_text(json.dumps(selection,indent=2)+'\n');print(json.dumps(selection),flush=True)
def evaluate():
    m=b.load();s=json.loads((HERE/'selection.json').read_text());assert b.sha(b.BIN)==s['binary_sha256']==m['binary_sha256']
    frozen=subprocess.check_output(['git','show','HEAD:'+str((HERE/'selection.json').relative_to(b.REPO))],cwd=b.REPO);assert frozen==(HERE/'selection.json').read_bytes()
    (HERE/'inputs').mkdir(exist_ok=False);(HERE/'evaluator').mkdir(exist_ok=False)
    points={};scalars={}
    for stream in b.SEEDS['heldout']:
        i=stream['replicate'];raw=json.loads(subprocess.check_output([str(b.FIXTURE),str(stream['evaluator_only'])],text=True));scalars[i]=raw.pop('evaluator')['scalar'];points[i]=raw['public']['Q'];raw['structured_roots']=list(range(128));(HERE/'inputs'/f'target-{i}.json').write_text(json.dumps(raw,sort_keys=True)+'\n')
    (HERE/'evaluator/scalars.json').write_text(json.dumps(scalars,indent=2)+'\n')
    for stream in b.SEEDS['heldout']:
        i=stream['replicate'];arms=[('selected-aa0',s['selected']),('m3-reference',s['references'][0]),('m4-reference',s['references'][1]),('selected-aa1',s['selected'])]
        if i%2:arms.reverse()
        for arm,config in arms:
            row=b.ic(m,f'heldout-T{i}-{arm}',points[i],stream,config,stage='heldout',replicate=i,arm=arm)
            if row['report'] and row['report'].get('status')=='solved':assert row['report']['scalar']==scalars[i];row['expected_scalar_match']=True;b.save(m)
        path=HERE/'raw'/f'rho-T{i}-native.json'
        row=b.native(m,f'rho-T{i}',[b.RHO,'--json','--out',path,'auxiliary','--input',HERE/'inputs'/f'target-{i}.json','--without-auxiliary','--backend','scalar','--summands',2,'--seed',stream['sampler'],'--max-queries',1,'--max-millis',1,'--rho','--rho-max-ops',200000],stage='rho',replicate=i)
        if path.exists():
            row['report']=json.loads(path.read_text());row['native_rho_report_sha256']=b.sha(path);rho=row['report'].get('rho',{})
            if rho.get('status')=='solved':assert rho['scalar']==scalars[i] and rho['producer_check_passed'];row['expected_scalar_match']=True
            b.save(m)
    b.ic(m,'selected-phase-profile',OLD[0],b.SEEDS['development'][0],s['selected'],stage='profile',replicate=0)
    assert len(m['cells'])==32;b.save(m)
if __name__=='__main__':{'dev':dev,'evaluate':evaluate}[sys.argv[1]]()
