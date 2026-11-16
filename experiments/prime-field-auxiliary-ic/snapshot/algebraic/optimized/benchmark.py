"""Serial complete attacks: preserved v1, fused v2, batched v2, shared-core rho."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent.parent))
from prepare import Curve,chain

# Load by file path to avoid a name collision when importing this benchmark.
import importlib.util
spec=importlib.util.spec_from_file_location('complete_attack_audit',ROOT.parent/'end_to_end/benchmark.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);audit_ic=old.audit


def build():
    binaries={}
    for label,source,binary in [('v1_chain',ROOT.parent/'end_to_end/native_ic.cpp',ROOT.parent/'end_to_end/native31'),
                                ('v2_chain',ROOT/'native_v2.cpp',ROOT/'native31'),
                                ('rho',ROOT/'rho.cpp',ROOT/'rho31')]:
        dependencies=[source]+([ROOT/'native_v2.cpp'] if label=='rho' else [])
        if not binary.exists() or binary.stat().st_mtime<max(p.stat().st_mtime for p in dependencies):
            temporary=binary.with_suffix('.new')
            subprocess.run(['g++','-O3','-march=native','-std=c++17','-Wall','-Wextra','-DFIELD_BITS=31',
                            '-o',str(temporary),str(source)],check=True)
            temporary.replace(binary)
        digest=hashlib.sha256(b''.join(p.read_bytes() for p in dependencies)).hexdigest()
        binaries[label]=(binary,digest)
    binaries['v2_batch']=binaries['v2_chain']
    return binaries


def prepare_folder():
    folder=ROOT/'results/field31_s5_base0';folder.mkdir(parents=True,exist_ok=True)
    original=ROOT.parent/'end_to_end/field31_s5_base0'
    if not (folder/'public.json').exists():
        for name in ['chain.txt','same_base.txt','random.txt','expected.json']:
            shutil.copy2(original/name,folder/name)
        manifest=json.loads((original/'public.json').read_text());pub=manifest['public']
        E=Curve(pub['p'],a4=pub['a'],a6=pub['b'])
        started=time.perf_counter();aux,V=chain(pub['p'],manifest['depth'],enumerate_all=True)
        points=[]
        for x in V:
            rhs=(x**3+pub['a']*x+pub['b'])%E.p;y=pow(rhs,(E.p+1)//4,E.p)
            if y*y%E.p==rhs:points.append([x,min(y,E.p-y)])
        basis_seconds=time.perf_counter()-started
        assert sorted(points)==manifest['factor_base'] and aux['maps']==manifest['auxiliary']['maps']
        assert V==manifest['structured_roots']
        manifest['auxiliary_basis_seconds']=basis_seconds
        (folder/'public.json').write_text(json.dumps(manifest,indent=2)+'\n')
        fields=[pub[k] for k in ['p','n','a','b']]+pub['P']+pub['Q']
        (folder/'rho_public.txt').write_text(' '.join(map(str,fields))+'\n')
    return folder


def audit_rho(folder,prefix):
    public=json.loads((folder/'public.json').read_text())['public']
    data=json.loads(prefix.with_suffix('.json').read_text());n=public['n']
    E=Curve(public['p'],a4=public['a'],a6=public['b']);P,Q=tuple(public['P']),tuple(public['Q'])
    a1,b1,a2,b2=[data[k] for k in ['collision_a1','collision_b1','collision_a2','collision_b2']]
    left=E.add(E.mul(a1,P),E.mul(b1,Q));right=E.add(E.mul(a2,P),E.mul(b2,Q))
    R=None if data['collision_infinity'] else (data['collision_x'],data['collision_y'])
    assert left==right==R and (b1-b2)%n
    assert data['recovered']==-(a1-a2)*pow((b1-b2)%n,-1,n)%n
    assert E.mul(data['recovered'],P)==Q
    return dict(verified_collision=True,verified_public_key=True)


def run_one(folder,binaries,label,seed):
    binary,digest=binaries[label];prefix=folder/f'{label}_seed{seed}'
    if label=='rho':args=[str(binary),str(folder/'rho_public.txt'),str(prefix.with_suffix('.json')),str(seed)]
    else:
        mode='chain_batch' if label=='v2_batch' else 'chain'
        args=[str(binary),str(folder/'chain.txt'),mode,str(prefix),str(seed)]
    print('START',label,seed,flush=True);started=time.perf_counter()
    pid=os.posix_spawn(str(binary),args,os.environ,file_actions=[
        (os.POSIX_SPAWN_OPEN,1,str(prefix.with_suffix('.log')),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),
        (os.POSIX_SPAWN_DUP2,1,2)])
    _,status,usage=os.wait4(pid,0);wall=time.perf_counter()-started
    if os.waitstatus_to_exitcode(status):raise RuntimeError(prefix.with_suffix('.log').read_text())
    data=json.loads(prefix.with_suffix('.json').read_text())
    audit=audit_rho(folder,prefix) if label=='rho' else audit_ic(folder,'chain',prefix)
    manifest=json.loads((folder/'public.json').read_text());basis=0 if label=='rho' else manifest['auxiliary_basis_seconds']
    data.update(label=label,seed=seed,process_wall_seconds=wall,basis_seconds=basis,
                end_to_end_seconds=wall+basis,source_sha256=digest,audit=audit,
                cpu_seconds=usage.ru_utime+usage.ru_stime,max_rss_kib=usage.ru_maxrss)
    prefix.with_suffix('.audited.json').write_text(json.dumps(data,indent=2)+'\n')
    print(f"DONE {label} {seed}: {data['end_to_end_seconds']:.6f}s, {data.get('queries',data.get('walk_steps'))} queries/steps; verified",flush=True)
    return data


def summarize(folder):
    rows=[json.loads(p.read_text()) for p in folder.glob('*_seed*.audited.json')]
    summaries={}
    for label in ['v1_chain','v2_chain','v2_batch','rho']:
        group=[r for r in rows if r['label']==label]
        if not group:continue
        summaries[label]=dict(runs=len(group),median_end_to_end_seconds=statistics.median(r['end_to_end_seconds'] for r in group),
            median_cpu_seconds=statistics.median(r['cpu_seconds'] for r in group),
            median_native_seconds=statistics.median(r['total_seconds'] for r in group),
            median_queries_or_steps=statistics.median(r.get('queries',r.get('walk_steps')) for r in group),
            all_verified=all(r['audit']['verified_public_key'] for r in group))
    data=dict(summary=summaries,runs=rows)
    (folder/'summary.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(summaries,indent=2),flush=True);return data


def verify(folder):
    checked=0
    source_hashes={
        'v1_chain':hashlib.sha256((ROOT.parent/'end_to_end/native_ic.cpp').read_bytes()).hexdigest(),
        'v2_chain':hashlib.sha256((ROOT/'native_v2.cpp').read_bytes()).hexdigest(),
        'v2_batch':hashlib.sha256((ROOT/'native_v2.cpp').read_bytes()).hexdigest(),
        'rho':hashlib.sha256((ROOT/'rho.cpp').read_bytes()+(ROOT/'native_v2.cpp').read_bytes()).hexdigest()}
    for path in folder.glob('*_seed*.audited.json'):
        data=json.loads(path.read_text());label,seed=data['label'],data['seed'];prefix=folder/f'{label}_seed{seed}'
        result=audit_rho(folder,prefix) if label=='rho' else audit_ic(folder,'chain',prefix)
        assert result==data['audit'] and data['source_sha256']==source_hashes[label]
        raw=json.loads(prefix.with_suffix('.json').read_text())
        for key,value in raw.items():assert data[key]==value
        assert data['end_to_end_seconds']==data['process_wall_seconds']+data['basis_seconds'];checked+=1
    for p in folder.glob('v1_chain_seed*.json'):
        if p.name.endswith('.audited.json'):continue
        seed=p.stem.split('seed')[1];v2=folder/f'v2_chain_seed{seed}.json'
        if not v2.exists():continue
        a,b=json.loads(p.read_text()),json.loads(v2.read_text())
        assert a['queries']==b['queries'] and a['weights']==b['weights']
        assert p.with_suffix('.relations.jsonl').read_bytes()==v2.with_suffix('.relations.jsonl').read_bytes()
    print('Verified complete attack certificates:',checked,flush=True);return checked


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,nargs='+',default=[0,1,2])
    parser.add_argument('--labels',nargs='+',choices=['v1_chain','v2_chain','v2_batch','rho'],default=['v1_chain','v2_chain','v2_batch','rho'])
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args();folder=prepare_folder()
    if not args.verify_only:
        binaries=build()
        for seed in args.seeds:
            ordered=args.labels[seed%len(args.labels):]+args.labels[:seed%len(args.labels)]
            for label in ordered:run_one(folder,binaries,label,seed)
    verify(folder);summarize(folder)
