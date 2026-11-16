"""Checkpoint tested generic foundation and inspected report; no population run."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,lzma,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01';base='6bb2516b64e7112356e58e45da590d60591c0461';assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
report=p/'report-foundation-01';raw=Path('/workspace/scratch/ct136-foundation-report-03');e=p/'evidence/foundation-report-rendering-01';e.mkdir()
for i in [1,2,3]:
 src=Path('/workspace/scratch/ct136-foundation-report-0'+str(i));dest=e/('attempt0'+str(i));dest.mkdir()
 for f in src.iterdir():
  if f.is_file()and f.suffix!='.png':shutil.copyfile(f,dest/f.name)
inspection=dict(at=datetime.now(timezone.utc).isoformat(),pages=1,all_pages_actually_opened=True,whole_PDF_bytes=(report/'report.pdf').stat().st_size,whole_PDF_sha256=hashlib.sha256((report/'report.pdf').read_bytes()).hexdigest(),raster=str(raw/'page-1.png'),raster_sha256=hashlib.sha256((raw/'page-1.png').read_bytes()).hexdigest(),observations='Final page legible; labels fit boxes, conditional hypotheses and unsigned/no-population scope readable. First successful render with overflowing labels and initial missing-typst import retained; corrected existing report virtualenv invocation and shorter explanatory labels.',scope='producing assistant visual inspection, unsigned')
(report/'visual-inspection.json').write_text(json.dumps(inspection,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','LPfoundation3d3f9a source-linked MD/proofmap/SVG/onepagePDF inspectedentirepage afterretainedfirstmissing-typstimportandfirstlayoutoverflow. Finalalllabelsinboxes/explicitspan-liftassumptions/knownidentity-only/unsigned/noq223claim. CompletefirstsuccessfulPDFandfigure/rawrenderfailures/exitsretained; finalreportactualbyteshashpinned. Originalmapsandrankgraphsunchangedbecause no newmaporpopulationrank. Thisreportdoesnotpromotegenericformalizationtonumerical/global/program/solve/costclaim.']
for f in [*sorted(report.iterdir()),p/'PROOF_MAP_01.md',*sorted(f for f in e.rglob('*')if f.is_file())]:cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
entry=f'''# Inspect and publish LP proof foundation report

## What was done
{claim}: complete one-page report/PDF and diagram actually inspected; proof map names all ten local bindings, both original13-declaration/zero-trust gates,24 native units and four complete positive/negative identity controls. Source mathematical checks are3d3f9a. [pcc:unverified]

## Decisions made
Checkpoint this foundation before new finite-matrix code. Keep native/ and lean/ source immutable; implement certificate development in a separate matrix-01 component. Full sixty-call computation remains EKS-admission gated. [pcc:unverified]

## Open threads
Native A/P/C/U certificates, independent Euclidean replay, lifts and synthetic graph cases; CI03 exact source hydration; Root4366 actual transport02; metadata sidecars/full scientific NEW28 and merge gates. [pcc:unverified]

## Errors
Initial default Python lacked typst; existing report virtualenv succeeds. First rendered figure overflowed box labels; full first PDF/source retained, labels shortened and final page opened. No mathematical data changed. [pcc:unverified]
'''
with(r/'docs/session-logs/2026-11-15.md').open('a')as out:out.write('\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+entry+'\n---\n')
f=r/'.resume/RESUME.md';f.write_text(entry+'\n---\n'+f.read_text())
# Literal Git porcelain is immutable raw metadata, with one exact-path attribute.
attrs=r/'.gitattributes';line='experiments/chained-transfer-lp-presentation-01/evidence/custody-checkpoint-publication-01/actual-publication/push.log -whitespace\n'
assert line not in attrs.read_text()
with attrs.open('a')as out:out.write(line)
g=p/'evidence/foundation-source-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[p.relative_to(r).as_posix(),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-15.md','.resume/RESUME.md','.gitattributes']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(n,c):
 q=subprocess.run(c,cwd=r,capture_output=True);b=q.stdout+q.stderr;(g/(n+('.txt.xz'if len(b)>60000 else'.txt'))).write_bytes(lzma.compress(b)if len(b)>60000 else b);(g/(n+'.exit')).write_text(str(q.returncode)+'\n');print(n,q.returncode,flush=True);assert q.returncode==0
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[n.decode()for n in paths()if n.endswith(b'.md')]]);run('whole1605-source-guards',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256']);run('benchrec',['python3','tools/benchrec.py','gate']);run('report-Python',['python3','tools/ci/check_report_graph_python.py']);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('native-format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',str(p/'native/src/lib.rs'),str(p/'native/src/bin/identities.rs')])
def stage():
 names=paths();f=Path('/workspace/scratch/ct137-foundation-source.paths0');f.write_bytes(b'\0'.join(n for n in names if n!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(names)
 for n in selected:
  if n.startswith(b'pcc/claims/'):
   for proof in json.loads((r/n.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     s=proof['subject'];assert hashlib.sha256((r/s['path']).read_bytes()).hexdigest()==s['sha256'];assert s['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+s['path']],cwd=r,capture_output=True).returncode==0
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree]);stage()
subprocess.run(['git','commit','--quiet','-m','research: prove finite LP projection and certify known cancellation identities'],cwd=r,check=True);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print('source',head,'report',claim,flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115','/workspace/scratch/ct137-foundation-source-normal-publication-01'],cwd=r,capture_output=True);Path('/workspace/scratch/ct137-foundation-source-normal-publication-caller01.txt').write_bytes(q.stdout+q.stderr);print('normalbranchpub',q.returncode,flush=True)
env=os.environ.copy();n=int(env.get('GIT_CONFIG_COUNT','0'));env.update({'GIT_CONFIG_COUNT':str(n+1),'GIT_CONFIG_KEY_'+str(n):'http.https://github.com/.extraheader','GIT_CONFIG_VALUE_'+str(n):'AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode(),'GIT_TERMINAL_PROMPT':'0'});url='https://github.com/isogeny-labs/cryptanalysis.git';out=Path('/workspace/scratch/ct137-foundation-source-new-tag-publication-01');out.mkdir();ref='refs/tags/chained-transfer-lp-foundation-20261115-'+head[:12]
before=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=r,env=env,capture_output=True,timeout=60);(out/'before.txt').write_bytes(before.stdout+before.stderr);assert before.returncode==0 and not before.stdout
push=subprocess.run(['git','push','--no-force','--porcelain',url,head+':'+ref],cwd=r,env=env,capture_output=True,timeout=180);(out/'actual-push.log.xz').write_bytes(lzma.compress(push.stdout+push.stderr));(out/'actual-push.exit').write_text(str(push.returncode)+'\n');assert push.returncode==0
after=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=r,env=env,capture_output=True,timeout=60);(out/'after.txt').write_bytes(after.stdout+after.stderr);assert after.returncode==0 and after.stdout.decode().split()[0]==head
(out/'receipt.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=head,new_tag=ref,new_tag_push=0,exact_readback=True,branch_publication_actual_exit=q.returncode,no_force=True,no_fixed_population_run=True),indent=2)+'\n');print('newsource-tag0',ref,flush=True)
