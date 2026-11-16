"""Complete preflight388 with the whole guard stdout under original docs hydration."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,re,shutil,subprocess
r=Path('/workspace/cryptanalysis');base='adb8a8519990a3b85bf72267b23e984bdf9a57f2';branch='research/chained-transfer-lp-presentation-20261115'
env=os.environ.copy();env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0')
idx=Path('/workspace/scratch/ct388-Consumer-portable-source-whole-index');env['GIT_INDEX_FILE']=str(idx/'actual-current')
p=r/'experiments/chained-transfer-lp-presentation-01';g=p/'evidence/portable-source-whole-custody-publication-completion-09';g.mkdir();shutil.copyfile(__file__,g/'entire-original-completion-command.py')
scope=[str(p.relative_to(r)),'experiments/chained-transfer-relation-diagnostics-02/evidence/entire-CI02-source-guard-failure-01/entire-original-checkpoint-metadata','docs/chained-transfer-byte-custody-20261116','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-16.md','.resume/RESUME.md','.github/workflows/chained-transfer-lp-historical-development-01.yml','.gitattributes']
shutil.copyfile(r/'docs/chained-transfer-byte-custody-20261116/EXACT_ADDRESSES_02.json',g/'immutable-entire-exact-addresses-02.json')
def names():
 return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r,env=env).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r,env=env).split(b'\0')))-{b''})
def run(label,cmd,want=0):
 q=subprocess.run(cmd,cwd=r,env=env,capture_output=True,timeout=120);raw=q.stdout+q.stderr
 (g/(label+'.txt.xz')).write_bytes(lzma.compress(raw));(g/(label+'.exit')).write_text(str(q.returncode)+'\n');print(label,q.returncode,flush=True);assert q.returncode==want;return raw
run('original-current-parent-ledger-prefix',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('authored-prose',['python3','tools/pcc/pcc.py','lint-prose',*[n.decode()for n in names()if n.endswith(b'.md')]])
def stage():
 ns=names();selected=idx/'selected-paths0';selected.write_bytes(b'\0'.join(n for n in ns if n!=b'.resume/RESUME.md')+b'\0')
 subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(selected),'--pathspec-file-nul'],cwd=r,env=env,check=True)
 subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,env=env,check=True)
 actual=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r,env=env).split(b'\0'))-{b''};assert actual==set(ns)
 for n in actual:
  if n.startswith(b'pcc/claims/'):
   for proof in json.loads((r/n.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     s=proof['subject'];assert hashlib.sha256((r/s['path']).read_bytes()).hexdigest()==s['sha256']
     assert s['path'].encode()in actual or subprocess.run(['git','cat-file','-e',base+':'+s['path']],cwd=r,env=env,capture_output=True).returncode==0
stage();run('final-cached-whitespace',['git','diff','--cached','--check'])
tree=subprocess.check_output(['git','write-tree'],cwd=r,env=env,text=True).strip()
manifest=json.loads((r/'docs/chained-transfer-byte-custody-20261116/EXACT_ADDRESSES_02.json').read_text())
expected={(x['entire_regular_payload'],x['original_bytes'])for x in manifest['addresses']}
assert len(expected)==9
for label,reference in [('original-immediate-artifact-policy',base),('original-frozen826-artifact-policy','82617f14fb48843585137f0310f7d1fa9a5d8ea6')]:
 raw=run(label,['python3','tools/artifacts/artifacts.py','check',reference,tree],1)
 found={(m.group(2).decode(),int(m.group(1).replace(b',',b'')))for m in re.finditer(rb'^ +([0-9,]+)  (.+)$',raw,re.M)}
 assert found==expected and b'9 data file(s)'in raw
(g/'exact-eight-whole-artifact-payloads.json').write_text(json.dumps([{'path':n,'bytes':b}for n,b in sorted(expected)],indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Publish portable exact native2c runtime source helper with actual final1310-link/1663-whole-file/original1605/50/12/cleanGit/unpushed0/RESUME guards and3586-byte-record preservation349a6e; final metadata missing/expired deadlines reject1/125, first positiveb8a890/earlier full fresh-fetch repair08b4f7 retained. Entire consolidated fresh mode remains unrun. OCI context/CI captures helper, own9 guard, original50/12 path sets retain only exact workflow/transitive hash refresh; no native/protocol/limits/math/source-tool changes. Whole original docs-hydration layout00e6d1 gives13 source evidence addresses to9 entire regular raw/encoded payloads with exact unchanged original sizes/hashes; original frozen PCC gate/sign unchanged and already pull docs, original12 affected subject checks unsigned/no failures. Actual current-parent ledger/prose/all1605/50/12/9/benchrec/full workflow wiring/reportPython/actionlint/individual shell/cached0. Immediate and frozen826 original artifact checks both1 now name exactly9 complete docs payloads, replacing prior uncovered seven metadata paths through whole-data custody without policy/tool/guard exceptions. Full original upload/remote byte replay/genuine bot/current CI required before remote closure/merge; local hashes/source publication are not remote or signed/scientificNEW28 standing. Entire currentadb compiler/native/proof745-memberCI7b609c, clean context99ea57 and failed transport/first source records preserved. No local full LP/native benchmark/paid image/EKS/admission, no new role/provider/grant/network route, force/rechain/reset/admin bypass.']
for f in sorted(g.iterdir()):cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,env=env,text=True).strip()
entry='\n---\n\n'+datetime.now(timezone.utc).isoformat()+'\n# Publish exact portable source and whole-data original docs custody\n\n## What was done\n'+claim+': source helper/link/deadline component349a6e and whole-data local layout00e6d1 ready. Original prefix/prose/1605/50/12/9/benchrec/full wiring/reportPython/actionlint/individual shell/cached0; both immediate/frozen826 artifact1 name exactly9 complete docs payloads for12 original addresses. Frozen PCC workflow/tools/policy/native/protocol unchanged. [pcc:unverified]\n\n## Decisions made\nNormal FF existing owned PR1587 branch, immutable tag, current own CI/genuine whole remote migration and guarded bot integration before merge. Use original docs hydration rather than editing frozen PCC workflow. Preserve all raw bytes/failures; exact captured-whitespace attributes only if required by actual first check. [pcc:unverified]\n\n## Open threads\nRemote replay/current CI/bot, fresh combined helper/actual checkpoint/ABI/paid EKS admission/full historical population/full scientificNEW28 remain distinct. [pcc:unverified]\n\n## Errors\nAll original failures/empty draft upload attempts/source negatives retained. PaidSTOPe42949 remains; no metadata test promoted as scientific execution. [pcc:unverified]\n'
for name in ['docs/session-logs/2026-11-16.md','.resume/RESUME.md']:
 with(r/name).open('a')as f:f.write(entry)
stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,env=env,check=True)
subprocess.run(['git','-c','gc.auto=0','commit','--quiet','-m','research: prepare exact runtime source and preserve whole inputs under existing hydration'],cwd=r,env=env,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,env=env,text=True).strip();assert subprocess.check_output(['git','rev-parse','HEAD^'],cwd=r,env=env,text=True).strip()==base
shutil.copyfile(idx/'actual-current',r/'.git/index');assert(r/'.git/index').read_bytes()==(idx/'actual-current').read_bytes();print(claim,head,flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint_configured_connection.py','isogeny-labs/cryptanalysis',base,head,branch,str(idx/'normal-existing-branch-publication')],cwd=r,env=env,capture_output=True,timeout=240)
(idx/'entire-actual-publication-caller.txt').write_bytes(q.stdout+q.stderr);print('actual-normal-FF-publication',q.returncode,flush=True);assert q.returncode==0
ref='refs/tags/chained-transfer-portable-source-whole-custody-20261116-'+head[:12];out=idx/'normal-new-immutable-tag';out.mkdir();url='https://github.com/isogeny-labs/cryptanalysis.git'
q=subprocess.run(['git','ls-remote',url,ref],cwd=r,env=env,capture_output=True,timeout=60);(out/'entire-before.txt').write_bytes(q.stdout+q.stderr);assert q.returncode==0 and not q.stdout
q=subprocess.run(['git','push','--no-force','--porcelain',url,head+':'+ref],cwd=r,env=env,capture_output=True,timeout=180);(out/'entire-actual-push.log.xz').write_bytes(lzma.compress(q.stdout+q.stderr));(out/'actual-push.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
q=subprocess.run(['git','ls-remote',url,ref],cwd=r,env=env,capture_output=True,timeout=60);(out/'entire-after.txt').write_bytes(q.stdout+q.stderr);assert q.returncode==0 and q.stdout.decode().split()[0]==head
(out/'actual-receipt.json').write_text(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'head':head,'ref':ref,'actual_normal_new_push':0,'exact_readback':True,'force':False},indent=2)+'\n');print('actual-normal-new-tag',head,flush=True)
