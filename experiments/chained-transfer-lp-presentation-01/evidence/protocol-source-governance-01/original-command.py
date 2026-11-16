"""Govern and publish prospective documentation; no numerical research execution."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,lzma,os,shutil,subprocess

repo=Path('/workspace/cryptanalysis');project=repo/'experiments/chained-transfer-lp-presentation-01';base='82617f14fb48843585137f0310f7d1fa9a5d8ea6'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==base
gov=project/'evidence/protocol-source-governance-01';gov.mkdir(parents=True);shutil.copyfile(__file__,gov/'original-command.py')
scope=[project.relative_to(repo).as_posix(),'problems/chained-transfer-full-large-prime-presentation.md','problems/README.md','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-15.md','.resume/RESUME.md','.gitattributes']
def paths():
    return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=repo).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=repo).split(b'\0')))-{b''})
def run(name,command):
    q=subprocess.run(command,cwd=repo,capture_output=True);body=q.stdout+q.stderr
    compressed=len(body)>60000 or('whitespace'in name and q.returncode)
    (gov/(name+('.txt.xz'if compressed else'.txt'))).write_bytes(lzma.compress(body)if compressed else body)
    (gov/(name+'.exit')).write_text(str(q.returncode)+'\n');print(name,q.returncode,flush=True);assert q.returncode==0,body[:1000]
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','scripts','suite','.github/workflows','experiments/chained-transfer-public-target','experiments/chained-transfer-relation-diagnostics-02','.artifacts/config.json'],cwd=repo)
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[name.decode()for name in paths()if name.endswith(b'.md')]])
run('working-whitespace',['git','diff','--check','--',*scope])
run('entire1605-original-CI02-source-guards',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'])
run('report-Python',['python3','tools/ci/check_report_graph_python.py'])
run('wiring',['python3','tools/artifacts/wire_workflows.py','--check'])
def stage():
    names=paths();file=Path('/workspace/scratch/ct130-LP-protocol-source.paths0');file.write_bytes(b'\0'.join(p for p in names if p!=b'.resume/RESUME.md')+b'\0')
    subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(file),'--pathspec-file-nul'],cwd=repo,check=True)
    subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=repo,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=repo).split(b'\0'))-{b''};assert selected==set(names)
    for name in selected:
        if name.startswith(b'pcc/claims/'):
            for proof in json.loads((repo/name.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    value=proof['subject'];p=repo/value['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==value['sha256']
                    assert value['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+value['path']],cwd=repo,capture_output=True).returncode==0
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=repo,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(gov/'custody.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),base=base,all_recorded_governance_exits=0,every_new_subject_exact_staged_or_parented=True,original_science_workflows_tools_scripts_policy_unchanged=True,prospective_only=True,whole_original_queue_history_retained=True,no_algorithm_or_population_run=True,scope='unsigned source/documentation governance; native proof/unit development follows publication, actual new population requires full EKS admission'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Prospective LPpresentation protocol8f7bac/source-review correctionb10aea governance: whole60calls/fourA-P-C-Ucertificatespercall240/header60footer62/fullrawgraphoccurrences/projections-lifts-inclusions/privatefeedback-wholecontrols/old360replay/separatepostcharacterchecks frozen before implementation. Inspectedtwo-page47962Breport/source-KBreceipts/exactpriorwholequeuehistory retained; rows_multcyclecap correctionappended, alloldreports/science unchanged. Original1605guard/ledger/prose/workingcachedwhitespace/reportPython/wiring/artifact0, everynewsubject exactstagedorparented; no changesoriginaltools/scripts/native/workflows/policies. No newalgorithm/populationtrial/paidbuild/job/rank/solve/cost/global/numericalLean/noveltypromotion. SourcepublishednormallyonLPfeaturebranchandnewtag; newfullpopulationrequiresoriginalcheckpoint/liveknownbudgetcapacity/sourceimage/EKSadmission before launch. Unsigned source/dataonly.']
for p in sorted(gov.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(repo).as_posix()]
claim=subprocess.check_output(cmd,cwd=repo,text=True).strip();selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=repo,check=True)
subprocess.run(['git','commit','--quiet','-m','research: freeze complete large-prime presentation projection audit'],cwd=repo,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();print(claim,head,len(selected),flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115','/workspace/scratch/ct130-LP-protocol-normal-publication-01'],cwd=repo,capture_output=True);Path('/workspace/scratch/ct130-LP-protocol-normal-publication-caller01.txt').write_bytes(q.stdout+q.stderr);print('normalbranchpub',q.returncode,flush=True)
env=os.environ.copy();n=int(env.get('GIT_CONFIG_COUNT','0'));env.update({'GIT_CONFIG_COUNT':str(n+1),'GIT_CONFIG_KEY_'+str(n):'http.https://github.com/.extraheader','GIT_CONFIG_VALUE_'+str(n):'AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode(),'GIT_TERMINAL_PROMPT':'0'})
ref='refs/tags/chained-transfer-lp-protocol-20261115-'+head[:12];url='https://github.com/isogeny-labs/cryptanalysis.git';out=Path('/workspace/scratch/ct130-LP-protocol-new-tag-publication-01');out.mkdir()
before=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=repo,env=env,capture_output=True,timeout=60);(out/'before.txt').write_bytes(before.stdout+before.stderr);assert before.returncode==0 and not before.stdout
push=subprocess.run(['git','push','--no-force','--porcelain',url,head+':'+ref],cwd=repo,env=env,capture_output=True,timeout=180);(out/'push.txt').write_bytes(push.stdout+push.stderr);(out/'push.exit').write_text(str(push.returncode)+'\n');assert push.returncode==0
after=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=repo,env=env,capture_output=True,timeout=60);(out/'after.txt').write_bytes(after.stdout+after.stderr);assert after.returncode==0 and after.stdout.decode().split()[0]==head
(out/'receipt.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=head,new_tag_ref=ref,actual_normal_new_tag_push=0,exact_remote_readback=True,branch_publication_actual_exit=q.returncode,no_force_or_existing_ref_update=True,scope='unsigned normal source preservation; protocol precedes implementation'),indent=2)+'\n')
assert q.returncode==0,'branch publication refused; exact committed source is preserved by its genuinely new tag'
print('newtagpub0',ref,flush=True)
