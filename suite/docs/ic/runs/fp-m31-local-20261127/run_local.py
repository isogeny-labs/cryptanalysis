"""Run existing native M31 CLI arms; no elliptic arithmetic implemented here."""
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
WORKSPACE=REPO.parent.parent
spec=importlib.util.spec_from_file_location('lead_watch',WORKSPACE/'tools/lead_sweep.py')
watch=importlib.util.module_from_spec(spec);spec.loader.exec_module(watch)
CLI=REPO/'suite/target/debug/ca-ic'
FIXTURE=REPO/'crates/prime-field-auxiliary-ic/target/release/examples/m31_public_fixture'
ORDER=2147505293

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def fixture(*args):
    return json.loads(subprocess.check_output([str(FIXTURE),*map(str,args)],text=True))
def flags(arm):
    if arm=='torus':return ['--torus-depth','7','--backend','auto']
    if arm=='torus-direct':return ['--torus-depth','7','--without-auxiliary','--backend','scalar']
    return ['--without-auxiliary','--backend','scalar']

def main():
    raw=HERE/'raw';raw.mkdir(exist_ok=False)
    inputs=HERE/'inputs';inputs.mkdir(exist_ok=False)
    custody=HERE/'evaluator';custody.mkdir(exist_ok=False)
    seeds=json.loads((HERE/'seeds.json').read_text())
    expected={};publics={};controls={}
    for rep in seeds['replicates']:
        number=rep['replicate'];scalar=rep['streams']['target-private']%(ORDER-1)+1
        public=fixture('target',scalar)
        assert public['public']['p']==2147483647
        path=inputs/f'target-{number}.json';path.write_text(json.dumps(public,sort_keys=True)+'\n')
        expected[number]=scalar;publics[number]=(path,public)
    (custody/'scalars.json').write_text(json.dumps(expected,indent=2))
    for m in (2,3,4):
        for arm in ('torus','torus-direct','interval'):
            public=fixture('pdp',m,arm)
            path=inputs/f'pdp-{m}-{arm}.json';path.write_text(json.dumps(public,sort_keys=True)+'\n')
            controls[m,arm]=(path,public)
        assert controls[m,'torus'][1]==controls[m,'torus-direct'][1]
    manifest={'scope':'Native prime-field M31 CPU-only diagnostic; producer assertions pcc:unverified',
      'p':2147483647,'scalar_modulus':ORDER,'curve':{'a':2,'b':14,'G':[1,814455902]},
      'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
      'binary_sha256':digest(CLI),'fixture_binary_sha256':digest(FIXTURE),
      'protocol_sha256':digest(HERE/'PROTOCOL.md'),'seeds_sha256':digest(HERE/'seeds.json'),
      'platform':platform.platform(),'cpu_count':os.cpu_count(),
      'inputs':{p.name:digest(p) for p in inputs.glob('*.json')},'planned_cells':56,'cells':[]}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2))
    jobs=[]
    for replay in (0,1):
        for m in (2,3,4):
            for arm in ('torus','torus-direct','interval'):
                jobs.append(('pdp',replay,m,arm))
    for mode in ('yield','solve'):
        for rep in (0,1):
            for m in (2,3,4):
                for arm in (('torus','torus-direct','interval') if rep==0 else ('interval','torus-direct','torus')):
                    jobs.append((mode,rep,m,arm))
    jobs += [('rho',rep,2,'interval') for rep in (0,1)]
    replays={}
    for mode,rep,m,arm in jobs:
        name=f'{mode}-rep{rep}-m{m}-{arm}'
        path,public=controls[m,arm] if mode=='pdp' else publics[rep]
        sampler=seeds['replicates'][rep]['streams']['sampler'] if mode!='pdp' else 1
        output=raw/(name+'.json')
        command=[str(CLI),'--json','--out',str(output),'auxiliary','--input',str(path),
                 '--summands',str(m),'--seed',str(sampler),'--walk-lanes','4',
                 '--max-proof-nodes','1048576',*flags(arm)]
        if mode=='pdp':command+=['--decompose-only']
        elif mode=='yield':command+=['--relation-yield-only','--max-queries','512','--max-millis','1500']
        elif mode=='solve':command+=['--max-queries','65536','--max-millis','2000','--profile-phases']
        else:command+=['--max-queries','1','--max-millis','1','--rho','--rho-max-ops','200000']
        status=watch.watched_run(command,raw/(name+'.txt'),2,20,cwd=REPO)
        row={'case':name,'mode':mode,'replicate':rep,'summands':m,'arm':arm,
             'input_sha256':digest(path),'command':command,**status}
        if output.exists():
            report=json.loads(output.read_text());row['native_status']=report.get('status')
            row['native_report']=report;row['output_sha256']=digest(output)
            if report.get('public',{}).get('p')!=2147483647:
                row['status']='invalid';row['reason']=report.get('message','missing/wrong prime field')
            elif report.get('status') in ('solved','relation_found','no_relation','incomplete','complete'):
                row['process_status']=row['status'];row['status']='native_'+report['status']
            if mode=='pdp' and report.get('status')=='relation_found':
                d=report['decomposition']
                terms=d['terms'] if m>2 else [{'column':d['i'],'sign':-1 if d['negative_i'] else 1},
                                              {'column':d['j'],'sign':-1 if d['negative_j'] else 1}]
                encoded=','.join(f"{t['column']}:{t['sign']}" for t in terms)
                q=public['public']['Q'];check=fixture('verify',m,arm,*q,encoded)
                row['native_row_replay']=check['replay_passed']
                key=(m,arm)
                if rep==0:replays[key]=d
                else:row['repeat_same_mathematical_output']=replays.get(key)==d
            if mode!='pdp' and report.get('status')=='solved':
                row['expected_scalar_match']=report['certificate']['scalar']==expected[rep]
                assert row['expected_scalar_match']
            if mode=='rho' and report.get('rho',{}).get('status')=='solved':
                row['rho_expected_scalar_match']=report['rho']['scalar']==expected[rep]
                assert row['rho_expected_scalar_match'] and report['rho']['producer_check_passed']
        manifest['cells'].append(row)
        (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2))
        print(json.dumps({k:v for k,v in row.items() if k not in ('native_report','command')}),flush=True)

if __name__=='__main__':main()
