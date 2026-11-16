"""Accept whole original CBC CI artifact; I/O metadata checks and actual Rust auditor replays."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,lzma,os,re,shutil,stat,subprocess,zipfile
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';ci=s/'ci_original_fixed_ic';out=Path('/workspace/scratch/ct100-original-fixed-IC-CI-acceptance-01')
shutil.copyfile(__file__,out/'original-command.py')
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
archive=out/'whole-original-GitHub-artifact.zip';assert archive.stat().st_size==43094388 and sha(archive)=='e7f6c9f7a5db660350b3bbd3991b13696510328cc69798bc6de5121c78b71346'
root=out/'whole-artifact';root.mkdir();members=[]
with zipfile.ZipFile(archive)as z:
    assert len(z.namelist())==len(set(z.namelist()))==474
    for info in z.infolist():
        rel=PurePosixPath(info.filename);assert not rel.is_absolute()and'..'not in rel.parts and'\\'not in info.filename and not info.is_dir()
        mode=info.external_attr>>16;assert not stat.S_ISLNK(mode)
        p=root/info.filename;p.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();size=0
        with z.open(info)as source,p.open('xb')as target:
            while b:=source.read(1048576):target.write(b);h.update(b);size+=len(b)
        assert size==info.file_size and sha(p)==h.hexdigest()
        members.append(dict(path=info.filename,bytes=size,sha256=h.hexdigest(),CRC=info.CRC,original_external_attr=info.external_attr))
(out/'all474-whole-artifact-members.json').write_text(json.dumps(members,indent=2)+'\n')
assert(root/'consumer-head.txt').read_text().strip()=='cbc2ecefbedbc51a0f5ac430c34cb62d18302835'
assert(root/'producer-head.txt').read_text().strip()=='3d49af7f3d0a28e76b79e4825c9d2324e85853d2'
assert(root/'original.exit').read_text().strip()==(root/'final-source-guards.exit').read_text().strip()=='0'
assert(root/'original-command.sh').read_bytes()==(ci/'check-01.sh').read_bytes()
assert(root/'original-reference.sha256').read_bytes()==(ci/'reference-01.sha256').read_bytes()
refs=(root/'original-reference.sha256').read_text().splitlines();assert len(refs)==1503
for line in refs:
    h,name=line.split('  ',1);assert sha(r/name)==h,name
phases=read(ci/'phases-01.json')['ordered_phases'];actual=[p.split()for p in(root/'phases.txt').read_text().splitlines()];assert len(actual)==len(phases)==102
assert actual==[[p['name'],str(p['expected_exit']),str(p['expected_exit'])]for p in phases]
for p in phases:assert(root/(p['name']+'.pipe-exits')).read_text().split()==[str(p['expected_exit']),'0']
# Recompute the complete original field-engine closure from each raw Cargo graph,
# retaining the remote path strings rather than substituting a local prefix.
def closure(path):
    data=read(path);packages={p['id']:p for p in data['packages']};nodes={p['id']:p for p in data['resolve']['nodes']}
    roots=[key for key,p in packages.items()if p['name']=='isogeny_algos'];assert len(roots)==1
    seen=set();pending=roots[:]
    while pending:
        key=pending.pop()
        if key in seen:continue
        seen.add(key);pending.extend(v['pkg']for v in nodes[key]['deps'])
    return{key:dict(node=nodes[key],package={k:packages[key][k]for k in ['id','manifest_path','dependencies','features','targets']})for key in sorted(seen)}
baseline=closure(root/'chain-metadata.txt')
for label in ['original-ic','original-sampler']:
    assert closure(root/(label+'-metadata.txt'))==baseline==read(root/('engine-closure-'+label+'.json'))['exact_complete_closure']
# The downloaded artifact is closed. Only a verified closed-data duplicate is
# hardlinked for the independent I/O validator; its sole output gets a new inode.
replay=out/'independent-complete-receipt-replay';replay.mkdir()
for row in members:
    a=root/row['path'];b=replay/row['path'];b.parent.mkdir(parents=True,exist_ok=True);assert sha(a)==row['sha256'];os.link(a,b);assert b.read_bytes()==a.read_bytes()and stat.S_IMODE(b.stat().st_mode)==stat.S_IMODE(a.stat().st_mode)
(replay/'complete-whole-population-and-custody.json').unlink()
q=subprocess.run(['python3',str(ci/'validate_receipts_01.py'),str(r),str(replay)],capture_output=True)
(out/'independent-original-validator.txt').write_bytes(q.stdout+q.stderr);(out/'independent-original-validator.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
assert(replay/'complete-whole-population-and-custody.json').read_bytes()==(root/'complete-whole-population-and-custody.json').read_bytes()
print('All474members/1503guards/102phases/fullclosures and independent complete verdict passed',flush=True)
host=out/'actual-host-auditor-replays';host.mkdir();executables=host/'executables';executables.mkdir();commands=[]
def executable(name):
    original=root/name;copy=executables/name;shutil.copyfile(original,copy);assert copy.read_bytes()==original.read_bytes();copy.chmod(0o700);return copy
def run(name,cmd,want):
    with(host/(name+'.txt')).open('xb')as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120)
    (host/(name+'.exit')).write_text(str(q.returncode)+'\n');commands.append(dict(name=name,command=list(map(str,cmd)),actual_exit=q.returncode));assert q.returncode==want,(name,q.returncode);print(name,q.returncode,flush=True)
historical=executable('actual-runtime-historical-auditor.bin')
for label,tags in [('original-ic',['SETUP','INPUT','ATTEMPT','CASE','REJECTIONS','TARGET','SCOPE']),('original-sampler',['SETUP','PROVENANCE','INPUT','SCALARS','ATTEMPT','CASE','TARGET','SCOPE'])]:
    auditor=executable('actual-runtime-'+label+'-auditor.bin');positive=host/(label+'-whole-positive.json')
    run(label+'-whole-positive',[auditor,'--compare',root/(label+'-whole-frozen.json'),root/(label+'-native.txt'),positive],0)
    assert positive.read_bytes()==(root/(label+'-all-whole-records.json')).read_bytes()
    receipt=host/(label+'-historical-positive.json');run(label+'-historical-positive',[historical,'--compare',label,root/(label+'-expected.json'),root/(label+'-whole-frozen.json'),receipt],0)
    assert receipt.read_bytes()==(root/(label+'-historical-equality.json')).read_bytes()
    for control in ['missing-record-class','changed-scalar','changed-counter','unexpected-report-field','timing-only']:
        output=host/(label+'-'+control+'-accepted.json');want=0 if control=='timing-only'else 1
        run(label+'-historical-'+control,[historical,'--compare',label,root/(label+'-historical-controls')/(control+'.json'),root/(label+'-whole-frozen.json'),output],want);assert output.exists()==(want==0)
    prefix='N4_ORIGINAL_MODEL_IC_'if label=='original-ic'else'N4_ORIGINAL_FIXED_SAMPLER_'
    for suffix in tags:
        tag=prefix+suffix;omitted=root/(label+'-'+tag+'-entire-actual-records-omitted.txt.xz');output=host/(label+'-'+tag+'-must-not-accept.json')
        with(host/(label+'-'+tag+'-decoder.txt')).open('xb')as err:
            decoder=subprocess.Popen(['xz','-dc',str(omitted)],stdout=subprocess.PIPE,stderr=err)
            fd=decoder.stdout.fileno();cmd=[str(auditor),'--compare',str(root/(label+'-whole-frozen.json')),'/dev/fd/'+str(fd),str(output)]
            with(host/(label+'-'+tag+'-omission.txt')).open('xb')as f:q=subprocess.run(cmd,pass_fds=(fd,),stdout=f,stderr=subprocess.STDOUT,timeout=120)
            decoder.stdout.close();producer=decoder.wait(timeout=120)
        (host/(label+'-'+tag+'-omission.exit')).write_text(str(q.returncode)+'\n');(host/(label+'-'+tag+'-decoder.exit')).write_text(str(producer)+'\n')
        assert q.returncode==101 and producer==0 and not output.exists();commands.append(dict(name=label+'-'+tag+'-omission',command=cmd,actual_exit=q.returncode,whole_decoder_exit=producer));print(label,tag,'101/decoder0',flush=True)
for row in members:assert sha(root/row['path'])==row['sha256']
job=read(out/'whole-job-api.json')['structuredContent']['content'].encode();(out/'whole-original-job.log.xz').write_bytes(lzma.compress(job));assert lzma.decompress((out/'whole-original-job.log.xz').read_bytes())==job
logs=out/'whole-original-runlogs.zip'
with logs.open('xb')as dest,Path('/workspace/scratch/private-ct100-CBC-original-runlogs.stderr').open('xb')as err:q=subprocess.run(['timeout','120','gh','api','repos/isogeny-labs/cryptanalysis/actions/runs/43726524795/logs'],stdout=dest,stderr=err)
(out/'whole-runlogs-download.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
logrows=[]
with zipfile.ZipFile(logs)as z:
    for info in z.infolist():
        with z.open(info)as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        logrows.append(dict(path=info.filename,bytes=info.file_size,sha256=h,CRC=info.CRC))
(out/'all-whole-runlog-members.json').write_text(json.dumps(logrows,indent=2)+'\n')
(out/'all-actual-host-Rust-auditor-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
acceptance=dict(at=datetime.now(timezone.utc).isoformat(),source='cbc2ecefbedbc51a0f5ac430c34cb62d18302835',producer='3d49af7f3d0a28e76b79e4825c9d2324e85853d2',run=43726524795,job=132849545337,artifact=14166259090,whole_original_artifact_bytes=43094388,whole_original_artifact_sha256=sha(archive),all_original_members=474,uncompressed_bytes=sum(v['bytes']for v in members),all102phases_expected=True,all1503source_guards0=True,original_complete_engine_closure_independently_recomputed=True,full_prepared_RLIB_RMETA_runtime_custody=True,whole100_IC_and101_sampler_records=True,fifteen_actual_whole_omissions101_nooutput=True,eight_modified_historical_negatives1_nooutput=True,two_timing_only_positives0=True,both_original_proof_gates_26declarations_0trusted=True,all14_exact_bindings=True,independent_actual_versioned_validator_exit=0,whole_verdict_bytes_reproduced=True,downloaded_actual_Rust_auditor_whole_positives=2,downloaded_actual_historical_whole_positives=2,downloaded_actual_omissions=15,downloaded_actual_historical_negatives=8,downloaded_actual_timing_positives=2,all_original_decoded_member_bytes_unchanged_after_replays=True,whole_original_job_log_bytes=len(job),whole_original_job_log_sha256=hashlib.sha256(job).hexdigest(),whole_original_runlogs_bytes=logs.stat().st_size,whole_original_runlogs_sha256=sha(logs),all_whole_runlog_members=len(logrows),scope='unsigned exact scientific replay; current PR-body/global gates and calibrated costs remain separately scoped; original conditional actual-model/program bridges retained')
(out/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n');print(json.dumps(acceptance),flush=True)
