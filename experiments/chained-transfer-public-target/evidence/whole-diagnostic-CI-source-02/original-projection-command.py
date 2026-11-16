"""Version checkpoint checkout plumbing; preserve all mathematical inputs and old proofs."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess

repo=Path('/workspace/cryptanalysis');study=repo/'experiments/chained-transfer-public-target'
old=study/'ci_original_relation';ci=repo/'experiments/chained-transfer-relation-diagnostics-02'
entry='''# Versioned full diagnostic CI02 scope before source edits

## What was done
ce239f preserves both entire failed01 CI archives and exact successful checkpoint/readbacks with finalstatus1/no native work. b76887 preserves the inspected primary-review proposal. No new algorithm, proof or experimental result yet. [pcc:unverified]

## Decisions made
Reserve new experiments/chained-transfer-relation-diagnostics-02 and single workflow chained-transfer-original-relation-02.yml plus named sparse-checkpoint-status problem/index, existing project evidence/review/log/PCC/Resume scopes. Keep every b1f07d/5c5c9b source subject and old01 workflow byteexact. Use original fetch-depth0 setup in new02, capture original finalstatus actualexit0, and require the unchanged whole99-phase/native/proof contract. No original tool, criterion or failedsource is replaced. [pcc:unverified]

## Open threads
Source02/static checks/governance/publication and actual freshCI, new unassisted protocol beforecode, fullNEW28, Root4347held metadata originalmigration and original3877 ledger-prefixblock. [pcc:unverified]

## Errors
Conductor unavailable, scope expansion recorded here before edits. The shallow-checkout explanation is a hypothesis grounded in originalsource and successful full-history transport; actual02run must confirm it. [pcc:unverified]
'''
with(repo/'docs/session-logs/2026-11-15.md').open('a')as out:out.write('\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+entry+'\n---\n')
ci.mkdir()
for name in ['phase-plan-01.txt','kernel-declarations-01.txt','kernel-statement-bindings-01.txt','validate_receipts_01.py']:
    shutil.copyfile(old/name,ci/name)
driver=(old/'check-01.sh').read_text()
driver=driver.replace('reference=$ci/reference-01.sha256','reference=$ci/reference-02.sha256')
driver=driver.replace('study=experiments/chained-transfer-public-target\n','study=experiments/chained-transfer-public-target\noriginal_ci=$repo/$study/ci_original_relation\n')
for name in ['frozen-comparator-inputs-03.sha256','audit-03/Cargo.toml','historical-whole-fixture-pins-01.json','historical-passive-acceptance-01.json']:
    driver=driver.replace('$ci/'+name,'$original_ci/'+name)
(ci/'check-02.sh').write_text(driver)
accept=(old/'accept_completed_01.py').read_text().replace("ci = repo / 'experiments/chained-transfer-public-target/ci_original_relation'", "ci = repo / 'experiments/chained-transfer-relation-diagnostics-02'").replace('reference-01.sha256','reference-02.sha256')
(ci/'accept_completed_02.py').write_text(accept)
workflow=(repo/'.github/workflows/chained-transfer-original-relation.yml').read_text()
workflow=workflow.replace('name: Whole original relation diagnostics and historical replay','name: Whole original relation diagnostics and historical replay02',1)
workflow=workflow.replace("      - '.github/workflows/chained-transfer-original-relation.yml'", "      - 'experiments/chained-transfer-relation-diagnostics-02/**'\n      - '.github/workflows/chained-transfer-original-relation-02.yml'")
workflow=workflow.replace('          path: cryptanalysis\n', '          fetch-depth: 0\n          path: cryptanalysis\n',1)
workflow=workflow.replace('            experiments/chained-transfer-public-target\n','            experiments/chained-transfer-public-target\n            experiments/chained-transfer-relation-diagnostics-02\n',1)
workflow=workflow.replace('cryptanalysis/experiments/chained-transfer-public-target/ci_original_relation/check-01.sh','cryptanalysis/experiments/chained-transfer-relation-diagnostics-02/check-02.sh')
workflow=workflow.replace('cryptanalysis/experiments/chained-transfer-public-target/ci_original_relation/accept_completed_01.py','cryptanalysis/experiments/chained-transfer-relation-diagnostics-02/accept_completed_02.py')
workflow=workflow.replace('          bash ../artifact-tools/scripts/checkpoint.sh status > "$out/original-final-status.log" 2>&1', '''          set +e
          bash ../artifact-tools/scripts/checkpoint.sh status > "$out/original-final-status.log" 2>&1
          status_code=$?
          set -e
          printf '%s\\n' "$status_code" > "$out/original-final-status.exit"
          cat "$out/original-final-status.log"
          exit "$status_code"''')
path=repo/'.github/workflows/chained-transfer-original-relation-02.yml';assert not path.exists();path.write_text(workflow)
guards={}
for line in(old/'reference-01.sha256').read_text().splitlines():
    digest,name=line.split('  ',1);guards[name]=digest
for p in [*sorted(ci.iterdir()),path]:
    if p.is_file():guards[p.relative_to(repo).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
reference=ci/'reference-02.sha256';reference.write_text(''.join(digest+'  '+name+'\n'for name,digest in sorted(guards.items())))
evidence=study/'evidence/whole-diagnostic-CI-source-02';evidence.mkdir()
shutil.copyfile(__file__,evidence/'original-projection-command.py')
commands=[('entire-reference',['sha256sum','--check',str(reference)]),('original1598-reference',['sha256sum','--check',str(old/'reference-01.sha256')]),('shell',['bash','-n',str(ci/'check-02.sh')]),('actionlint',['/workspace/scratch/actionlint-bin/actionlint',str(path)]),('operational-syntax',['python3','-m','py_compile',str(ci/'validate_receipts_01.py'),str(ci/'accept_completed_02.py')]),('wiring',['python3','tools/artifacts/wire_workflows.py','--check'])]
for name,command in commands:
    q=subprocess.run(command,cwd=repo,capture_output=True);(evidence/(name+'.txt')).write_bytes(q.stdout+q.stderr);(evidence/(name+'.exit')).write_text(str(q.returncode)+'\n');print(name,q.returncode,flush=True);assert q.returncode==0
assert(ci/'phase-plan-01.txt').read_bytes()==(old/'phase-plan-01.txt').read_bytes()
assert(ci/'validate_receipts_01.py').read_bytes()==(old/'validate_receipts_01.py').read_bytes()
(evidence/'source-custody.json').write_text(json.dumps(dict(original_subjects_kept='b1f07d and5c5c9b byteexact; original1598 guard0',new_entire_guard_count=len(guards),complete_phase_count=99,only_checkout_semantics_change='fetch-depth0 exactly as existing originalcheckpoint transport; no fake remote refs',actual_original_status_exit_now_retained=True,mathematical_producers_auditors_controls_proofs_original_tools_unchanged=True,no_new_diagnostic_run=True,old01_negative_runs='ce239f; entire ZIPs/allmembers retained',scope='unsigned source/static-check custody only'),indent=2)+'\n')
problem=repo/'problems/chained-transfer-diagnostic-checkpoint-sparse-status.md'
problem.write_text('''# Original checkpoint final status in shallow sparse diagnostic checkout

Status: investigating. The complete diagnostic run is blocked before any native math/proof phase. ce239f retains two whole failedCI attempts:43761331865/source8a3 and43761567486/sourcef136. Each genuine original gate and all three complete checkpoint readbacks pass0, then original finalstatus exits1 after its spec listing; the native/proof step is skipped. Both complete199MBZIPs/all28members/pack/metadata/logs are retained. [pcc:unverified]

The newworkflow01 omitted the successful original transport's fetch-depth0 checkout. Its detached shallow exact-source checkout reports1unpushed and scans the complete tree, including sparse paths. Original spec_files has a direct pipeline whose final absent candidate can trigger errexit before its return0. This is an evidence-backed hypothesis, not a mathematical obstruction or an accepted fix. [pcc:unverified]

Next discriminating action: separatelyversioned workflow02 uses the exact original fetch-depth0 setup, captures the original finalstatus exit and requires0, then runs every unchanged whole diagnostic phase/control/proof at fixed limits. Do not change the immutable checkpoint script or bypassstatus. Preserve all b1f07d/source01 proofs and failed attempts. [pcc:unverified]

Exit criteria: actual exact-source original checkpoint/readbacks/status0; complete unchanged99-phase plan plus inherited102phases, all mathematical/historical controls, original proof gates, source/runtime/prepared/raw/partial custody, completed-run final exits and independent whole-artifact inspection. A setup-only pass does not accept the fullCI. [pcc:unverified]
''')
index=repo/'problems/README.md';content=index.read_text();position=content.index('\n',content.index('|---'))+1 if '|---'in content else None
row='| [Diagnostic checkpoint sparse status](chained-transfer-diagnostic-checkpoint-sparse-status.md) | investigating | Original checkpoint/readbacks0 then finalstatus1; native step skipped | Version02 exact original fetch-depth0 setup, actualstatus0 and complete whole diagnostic run; failuresce239f retained. [pcc:unverified] |\n'
if position is None:
    lines=content.splitlines(keepends=True);position=next(i for i,line in enumerate(lines)if line.startswith('|')and'---'in line)+1;lines.insert(position,row);index.write_text(''.join(lines))
else:index.write_text(content[:position]+row+content[position:])
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',f'Versioned complete diagnosticCI02 source after ce239f two whole checkpoint-status failures: new separateexperiments/chained-transfer-relation-diagnostics-02/singleworkflow02, exact originalfetch-depth0 setup and captured finaloriginalstatus exit requiring0. Keep all b1f07d/5c5c9b source01subjects/oldworkflow/1598guards byteexact; extend entire reference to{len(guards)}files. Same99phaseplan/identical operationalprefixvalidator/allinherited102phases/native-rank-character-historicalcontrols/proofgates/caps/fullretention; no originaltool or science criterion changed. Wholeold/newsourceguards/shell/actionlint/operational syntax/wiring0. New02freshCI UNEXECUTED, checkoutexplanationhypothesisawaitsactualrun. Namedproblemrecordsfullcriteria without freezingliveproblemupdates. Inspectedreviewb76887 isproposalonly; no unassistedalgorithm implemented/trialed and no paidbuild/job. Unsigned source/staticdata only.']
for p in [*sorted(ci.iterdir()),path,*sorted(evidence.iterdir())]:
    if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(repo).as_posix()]
claim=subprocess.check_output(cmd,cwd=repo,text=True).strip();Path('/workspace/scratch/ct124-diagnostic-CI02-source.claim').write_text(claim+'\n')
entry=f'''# Complete source02 uses original full-history checkpoint checkout; source01 retained

## What was done
{claim}: separate diagnosticCI02/newworkflow02 uses originalfetch-depth0 setup and captured originalfinalstatus requiring0. All b1f07d/5c5c9b source01subjects and1598guards unchanged; extended reference{len(guards)}files. Identical99phaseplan/prefixvalidator and fullinherited102phases/math-historicalcontrols/proofs/caps/wholecustody. Old/newguards/shell/actionlint/operationalsyntax/wiring0. Namedcheckpointstatusproblem indexed; liveproblemnotpinned. [pcc:unverified]

## Decisions made
Publishsource02 before a newrun. The actual exact-source checkpoint/readbacks/status0 plus every fullscientific/control/proof/final exit remain required; no originaltool change orstatusbypass. Old01 and bothwholefailedattemptsce239f retained. Group sourcefix with inspectedreviewb76887 and completefailurerecords inonepublication. [pcc:unverified]

## Open threads
Governance/sourcepublication andactual02CI; freezeunassisted wholepopulation successorprotocol beforecode; fullNEW28; Root4347originalartifacttransport sourcec019hold and original3877ledgerprefixblock; existingmath/cost/reference/admission gates. [pcc:unverified]

## Errors
Original01 omitted originaltransportfetch-depth0; two metadata-only failuresremain. Source02fixhypothesis not accepteduntilactualrun. No new mathematical outcome. [pcc:unverified]
'''
with(repo/'docs/session-logs/2026-11-15.md').open('a')as out:out.write('\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+entry+'\n---\n')
resume=repo/'.resume/RESUME.md';resume.write_text(entry+'\n---\n\n'+resume.read_text())
print(claim,len(guards),flush=True)
