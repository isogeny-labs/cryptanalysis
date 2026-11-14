"""Native arithmetic source and custody governance; all scientific work is Rust/Lean."""
from pathlib import Path
import hashlib,json,lzma,subprocess,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='584ba997263904cc2b0f35f4dc1a2b5563eabb2a';d=s/'evidence/arithmetic-audit-source-governance-02'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scopes=[str(s.relative_to(r)),'.github/workflows/chained-transfer-arithmetic-audit.yml','docs/research-artifacts/chained-transfer/arithmetic-audit-01','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-14.md','.resume/RESUME.md','problems/chained-transfer-new-jacobian-ic-cost-coverage.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scopes],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(label,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr;(d/(label+'.txt.xz'if len(raw)>60000 else label+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(d/(label+'.exit')).write_text(str(p.returncode)+'\n');print(label,p.returncode,flush=True);assert p.returncode==0,raw[:1800]
run('original784',['sha256sum','--check','experiments/chained-transfer-public-target/ci_norm_sampling/reference-01.sha256']);run('new21',['sha256sum','--check','experiments/chained-transfer-public-target/arithmetic-audit/reference-02.sha256'])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','scripts','.github/workflows'],cwd=r)
run('shell',['bash','-n',str(s/'arithmetic-audit/check.sh')]);run('materializer-shell',['bash','-n',str(s/'arithmetic-audit/materialize.sh')]);run('canary-shell',['bash','-n',str(s/'arithmetic-audit/canary.sh')]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-arithmetic-audit.yml'])
run('format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',str(s/'arithmetic-audit/controls.rs'),str(s/'arithmetic-audit/taps/src/lib.rs'),*[str(p)for p in sorted((s/'arithmetic-audit/taps/src/bin').glob('*.rs'))]])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scopes]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate']);run('reportPython',['python3','tools/ci/check_report_graph_python.py'])
# Deliberately leave staging/commit for after genuine final-control publication.
(d/'preflight.json').write_text(json.dumps(dict(base=base,original784=0,new21=0,source_self_total=22,old17workflows_verifiers_engines_unchanged=True,all_recorded_preflight_exits=0,pending='genuinefinal75764Bcontrolarchive projection, thenstage/artifactgate/subjecthash+staging/commit',scope='unsigned native8d0c27+wholecensus58d3bb/report03cfb7; freshfull/own18CIstillowed'),indent=2)+'\n')
