"""Checkpoint the additive proof replay and its complete local driver/control evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';ci=s/'ci_induced_transfer';raw=Path('/workspace/scratch/ct95-induced-proof-driver-local-01')
assert(raw/'actual-driver.exit').read_text().strip()=='0'
tests=json.loads((raw/'receipt-negative-controls.json').read_text());assert len(tests)==4 and all(v['actual_exit']==1 and v['no_accepted_output']for v in tests)
e=s/'evidence/induced-transfer-proof-CI-source-01';e.mkdir()
for name in ['original-command.py','outcome.json','actual-driver.txt','actual-driver.exit','prospective-local-uncommitted-driver-source.json','receipt-negative-controls.json','actual-negative-control-command.py']:
 shutil.copyfile(raw/name,e/name)
for name in [v['case']for v in tests]:
 for suffix in ['.txt','.exit']:shutil.copyfile(raw/(name+suffix),e/(name+suffix))
shutil.copytree(raw/'whole-output',e/'whole-local-original-driver')
for name in ['ct95_materialize_induced_proof_CI_guards_02.py','ct95-proof-driver-local-caller01.txt','ct95-proof-driver-local-caller01.exit','ct95-proof-receipt-negative-caller01.txt','ct95-proof-receipt-negative-caller01.exit']:
 shutil.copyfile('/workspace/scratch/'+name,e/name)
(e/'guard-materialization-failure-01.json').write_text(json.dumps(dict(operation='initial inline literal proof-closure guard materializer',actual_observation='AssertionError at the arbitrary len(paths)>100 assertion after25consumer+27producer tracked tool files were checked; subsequent batch bash/actionlint completed and the shell tool returned0',actual_input_files_modified_before_exception=['ci_induced_transfer/statement-bindings-01.txt'],reference_written_before_exception=False,corrected_operation='ct95_materialize_induced_proof_CI_guards_02.py freezes all73 actual input paths without arbitrary size requirement',scientific_code_or_CI_acceptance_criteria_changed=False,original_inline_source_available_in='session tool invocation; no separate original source file was created',scope='preserved materialization failure, no invented individual subprocess exit'),indent=2)+'\n')
(e/'REPORT.md').write_text('''# Additive induced-transfer proof CI source

The new standalone workflow and73-path frozen closure preserve the previous
CI03 workflow and all1440 guards. The complete driver ran locally with both
unchanged original proof gates:21 audited declarations and zero trusted under
each pinned Lean version, allnine exact original local statement bindings,
source guards before/after and whole source/log/phase custody. Consumer parent
5417e9d is explicitly accompanied by the exact untracked prospective driver/
workflow manifest; producer tools are checked out at original3d49af7. This local
precommit validation does not assert that those new files were in parent5417e9d.
[pcc:unverified]

The actual validator rejects all four modified complete receipt copies:
missing named root, missing structural declaration, missing exact binding and
altered binding verdict. Each returns1 with no accepted coverage output. All
original and modified receipt trees remain local forNEW26. The initial guard
materializer's arbitrary path-count assertion is preserved without inventing
a subprocess exit. No old source, claim, workflow or proof criterion changes.
[pcc:unverified]

Fresh GitHub proof execution remains pending after normal publication and
ordinary research-branch fast-forward. The proof derives the nine conditional
transfer conclusions; the actual HLP/field/Frobenius/Picard/order/program/lift
and calibrated-cost obligations remain explicit. Unsigned local proof-driver
and receipt-validation evidence only. [pcc:unverified]
''')
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Additive induced-transfer proofCI source01: separate newworkflow/checker/73actualclosureguards, alloriginalCI03workflow/1440guards/mathematicalsource/verifiers unchanged. Complete exactnewdriver local0 in sparseoriginaltool worktrees: producerpin3d49af7, consumerparent5417e9d with explicitlyuntrackedprospective driver-workflow byte manifest; bothoriginal434-435 gates21declarations0trusted/allnineexactlocalbindingspass/sourceguardsbefore-after0. Actualreceiptvalidator allfourmodifiedwholecopies(missingnamedroot/missingstructuraldeclaration/missingbinding/alteredverdict)1-noacceptance; allwholecopies/rawlogs retainedforNEW26. Initialarbitraryguardcount materializationassertion preservedwithoutinventedsubprocessexit. FreshGitHubexecutionpendingpublication/normalFF. Unsignedlocaldriveronly; no actualmodel-programbridge/calibratedadvantage/globalCI/signedpromotion.']
files=[f for f in e.rglob('*')if f.is_file()]+[f for f in ci.iterdir()if f.is_file()]+[r/'.github/workflows/chained-transfer-induced-proof.yml']
for f in sorted(files):cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct95-induced-proof-CI-source.claim.txt').write_text(claim+'\n');print(claim,flush=True)
state='# Original full CI accepted; new induced-proof replay ready for publication\n\nCIacceptancea93f80 at258: all749members/153phases/sevenwholepopulations/24omissions/both70module-declarationchecks/all70bindings/1440guards/actualruntime-preparedcustody anddownloadedsevenRustpositive0/24omissions101. NewproofCI '+claim+' locallypassescomplete driver0/both21declarations0trusted/allnineexactbindings/73guards/fouractualreceiptnegatives1-nooutput. Consumerparent5417e9d plusuntrackednewsourceexplicit; no freshGitHubproofexecutionclaim. [pcc:unverified]\n\n## What was done\nFrozenCI03/fullfailed-and-successfulrawretained; proofeddc37/resultd90ad1 remains conditionalquotientalgebra with geometric/fullkerneltransport/ellipticduality/perinputannihilator hypotheses. Everylocalfailedprojection/hostmissing-env/transport/materializationattemptretained. Cleanup12c9513d/136555ac excludeallheldinputs/subjects andpreserveactualscience/source/exes/fullpreparedcopies. [pcc:unverified]\n\n## Decisions made\nCommitandnormalpublish onsoleledgerwriter research/chained-transfer-induced-map-20261115; thenordinaryFF originalresearch/chained-transfer-public-target-20261113 from258 tothatcheckpoint BEFORE anyacceptanceappendthere. No rebase/rechain/force/mergerequirementwaiver. Newworkflowadditive, alloldtools/scripts/suite/workflows/sourcecriteriaunchanged. [pcc:unverified]\n\n## Open threads\nCollectnewproofCIafterFF withoutduplicatedispatch, mirrorproof-and-CIcheckpointtoRoot, genuineNEW26 wholecustody ofct92-95; nextoriginalfixedmodels prime-fieldIC reuseoldIC/normassistedbaseline withcompleteprimitive/setup/referencecensus. Cold12018complete102missing/124, root124/clock101/livebudget-capacity-isolation-image/mainledger/review/signing remain open. No calibrated/globalCI/ECDLPadvantage/signedpromotion. [pcc:unverified]\n\n## Errors\nOriginalfullnative693/test-onlyCRToraclecorrection andallpriornegativegeometry/proof/cold/globalresults retained; newreceiptnegativecontrols aredeliberatevalidationinputs, notmathematicalcounterexamples. No scientificcriterion wasweakened. [pcc:unverified]\n\n---\n\n'
for f in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:f.write_text(state+f.read_text())
f=r/'docs/session-logs/2026-11-15.md';f.write_text(f.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
