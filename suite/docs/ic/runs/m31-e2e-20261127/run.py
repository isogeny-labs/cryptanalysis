"""Frozen native recovery development and evaluation; no curve arithmetic here."""
from pathlib import Path
import hashlib,importlib.util,json,math,os,subprocess,sys,platform
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
WORKSPACE=REPO.parent.parent
BIN=REPO/'crates/prime-field-auxiliary-ic/target/release/examples/m31_e2e'
FIXTURE=BIN.with_name('m31_e2e_fixture')
RHO=REPO/'suite/target/debug/ca-ic'
spec=importlib.util.spec_from_file_location('watch',WORKSPACE/'tools/lead_sweep.py')
watch=importlib.util.module_from_spec(spec);spec.loader.exec_module(watch)
SEEDS=json.loads((HERE/'seeds.json').read_text())
CPU=min(os.sched_getaffinity(0))
PIN=['taskset','-c',str(CPU)] if subprocess.run(['which','taskset'],capture_output=True).returncode==0 else []

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
def save(m): (HERE/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
def load():return json.loads((HERE/'manifest.json').read_text())
def native(m,name,command,**meta):
    path=HERE/'raw'/(name+'.txt');assert not path.exists()
    status=watch.watched_run([*PIN,*map(str,command)],path,2,20,poll=.002,cwd=REPO)
    found=[]
    for line in path.read_text(errors='replace').splitlines():
        try:
            value=json.loads(line)
            if isinstance(value,dict):found.append(value)
        except json.JSONDecodeError:pass
    if not found:
        try:
            value=json.loads(path.read_text())
            if isinstance(value,dict):found.append(value)
        except json.JSONDecodeError:pass
    report=found[-1] if found else None
    if report is not None:(path.with_suffix('.json')).write_text(json.dumps(report,indent=2)+'\n')
    row={'id':name,'command':[*PIN,*map(str,command)],**meta,**status,'report':report,'log_sha256':sha(path)}
    if report is not None:row['report_sha256']=sha(path.with_suffix('.json'))
    m['cells'].append(row);save(m)
    print(json.dumps({'id':name,'process':row['status'],'native':report.get('status') if report else None,'cold_ms':report.get('cold_to_report_ns',0)/1e6 if report else None,'queries':report.get('work',{}).get('queries') if report else None}),flush=True)
    return row
def ic(m,name,q,stream,config,**meta):
    command=[BIN,'--qx',q[0],'--qy',q[1],'--columns',config['columns'],'--summands',config['summands'],'--base',config['base'],'--method',config.get('method','indexed'),'--seed',stream['sampler'],'--base-seed',stream['base'],'--max-ms',5000,'--max-queries',config.get('max_queries',2000000),'--lanes',64,'--chunk',64]
    if meta.get('stage')=='profile':command+=['--profile']
    return native(m,name,command,configuration=config,**meta)
def score(rows):
    ok=[r['report']['cold_to_report_ns'] for r in rows if r['report'] is not None and r['report'].get('status')=='solved']
    return (-len(ok),math.exp(sum(math.log(t) for t in ok)/len(ok)) if ok else float('inf'),rows[0]['configuration']['columns']**2)
def dev():
    (HERE/'raw').mkdir(exist_ok=False)
    m={'schema':'m31-e2e-local-run/v1','p':2147483647,'source_commit':source(),'binary_sha256':sha(BIN),'fixture_binary_sha256':sha(FIXTURE),'rho_binary_sha256':sha(RHO),'protocol_sha256':sha(HERE/'PROTOCOL.md'),'seeds_sha256':sha(HERE/'seeds.json'),'cpu_affinity':PIN,'host':platform.platform(),'planned':46,'cells':[]}
    save(m)
    points=[[2144058214,807222724],[1764015007,688050509]]
    groups=[]
    for b in (64,128,256,512):
        for arity in (3,4):
            config={'columns':b,'summands':arity,'base':'interval','method':'indexed'}
            rows=[ic(m,f'dev-B{b}-m{arity}-interval-T{rep}',q,SEEDS['development'][rep],config,stage='development',replicate=rep) for rep,q in enumerate(points)]
            groups.append(rows)
    best=min(groups,key=score)
    assert score(best)[0]==-2,'No configuration completes both development targets; preserve all outcomes and diagnose'
    structural=dict(best[0]['configuration']);base_groups=[best]
    for base in ('torus','random'):
        config={**structural,'base':base}
        base_groups.append([ic(m,f'dev-selected-{base}-T{rep}',q,SEEDS['development'][rep],config,stage='base-selection',replicate=rep) for rep,q in enumerate(points)])
    chosen=min(base_groups,key=score)
    m3=min([g for g in groups if g[0]['configuration']['summands']==3],key=score)
    assert score(m3)[0]==-2,'No completed optimized m3 reference'
    selection={'schema':'m31-e2e-selection/v1','source_commit':source(),'binary_sha256':sha(BIN),'selected':chosen[0]['configuration'],'m3_reference':m3[0]['configuration'],'criterion':'completed count then geometric mean cold time on two development targets; no heldout inputs seen','development_cells':len(m['cells'])}
    (HERE/'selection.json').write_text(json.dumps(selection,indent=2)+'\n');print(json.dumps(selection),flush=True)
def evaluate():
    m=load();s=json.loads((HERE/'selection.json').read_text());assert sha(BIN)==s['binary_sha256']==m['binary_sha256']
    m['reference_binary_sha256_at_evaluation']=sha(RHO)
    m.setdefault('evaluation_source_commit',source())
    m.setdefault('resume_source_commits',[]).append(source())
    save(m)
    frozen=subprocess.check_output(['git','show','HEAD:'+str((HERE/'selection.json').relative_to(REPO))],cwd=REPO)
    assert frozen==(HERE/'selection.json').read_bytes(),'Commit selection before heldout fixture generation'
    scalar_map={};points={}
    if (HERE/'inputs').exists():
        scalar_map={int(k):v for k,v in json.loads((HERE/'evaluator/scalars.json').read_text()).items()}
        points={rep:json.loads((HERE/'inputs'/f'target-{rep}.json').read_text())['public']['Q'] for rep in range(5)}
    else:
        (HERE/'inputs').mkdir();(HERE/'evaluator').mkdir()
        for stream in SEEDS['heldout']:
            rep=stream['replicate'];fixture=json.loads(subprocess.check_output([str(FIXTURE),str(stream['evaluator_only'])],text=True))
            scalar_map[rep]=fixture['evaluator']['scalar'];points[rep]=fixture['public']['Q']
            fixture.pop('evaluator');fixture['structured_roots']=list(range(128));(HERE/'inputs'/f'target-{rep}.json').write_text(json.dumps(fixture,sort_keys=True)+'\n')
        (HERE/'evaluator/scalars.json').write_text(json.dumps(scalar_map,indent=2)+'\n')
    for stream in SEEDS['heldout']:
        rep=stream['replicate'];q=points[rep]
        arms=[('selected-aa0',s['selected']),('direct',{**s['selected'],'method':'direct'}),('m3-reference',s['m3_reference']),('selected-aa1',s['selected'])]
        if rep%2:arms.reverse()
        for arm,config in arms:
            if any(c['id']==f'heldout-T{rep}-{arm}' for c in m['cells']):continue
            row=ic(m,f'heldout-T{rep}-{arm}',q,stream,config,stage='heldout',replicate=rep,arm=arm)
            if row['report'] and row['report'].get('status')=='solved':
                assert row['report']['scalar']==scalar_map[rep],'Wrong recovered scalar'
                row['expected_scalar_match']=True;save(m)
        path=HERE/'raw'/f'rho-T{rep}-native.json';input_path=HERE/'inputs'/f'target-{rep}.json'
        previous=next((c for c in m['cells'] if c['id']==f'rho-T{rep}'),None)
        if previous is None:
            row=native(m,f'rho-T{rep}',[RHO,'--json','--out',path,'auxiliary','--input',input_path,'--without-auxiliary','--backend','scalar','--summands',2,'--seed',stream['sampler'],'--max-queries',1,'--max-millis',1,'--rho','--rho-max-ops',200000],stage='rho',replicate=rep)
        else:
            row=previous
            if not isinstance(row['report'],dict):
                row['stdout_parse_fragment']=row['report'];row['parser_recovery']='Use original complete native --out report; no process repeated'
        if path.exists():
            row['report']=json.loads(path.read_text());row['native_rho_report_sha256']=sha(path)
            ref=row['report'].get('rho',{})
            if ref.get('status')=='solved':assert ref['scalar']==scalar_map[rep] and ref['producer_check_passed'];row['expected_scalar_match']=True
            save(m)
    if not any(c['id']=='selected-phase-profile' for c in m['cells']):
        ic(m,'selected-phase-profile',[2144058214,807222724],SEEDS['development'][0],s['selected'],stage='profile',replicate=0)
    assert len(m['cells'])==46
    save(m)
if __name__=='__main__':
    {'dev':dev,'evaluate':evaluate}[sys.argv[1]]()
