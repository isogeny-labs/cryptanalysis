"""Replay the k5 branch formula and capped solver receipt from frozen files."""
import gzip,hashlib,json,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'terminal_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_TERMINAL_REPLAY'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
result=json.loads((HERE/'k5_branch_result.json').read_text())
branch=json.loads((HERE/'k5_branch_protocol.json').read_text())
assert result['status']=='BOUNDED_UNKNOWN' and result['stop_reason']=='PARENT_WALL_CAP'
assert result['candidate_id'] is None and result['monitor_error'] is None
assert result['protocol_sha256']==sha(HERE/'k5_branch_protocol.json')
assert result['sampled_peak_combined_rss_bytes']<branch['combined_rss_cap_bytes']
assert result['solver_exit_code']==-9 and result['status_lines']==[] and result['model_line_count']==0
assert branch['branch_prefix_value']==3 and branch['mask_variable_ids']==list(range(1,9))
original=HERE/'n131_k5_public.xcnf'
with tempfile.TemporaryDirectory(prefix='k5_branch_replay_',dir='/private/tmp') as name:
    formula=Path(name)/'branch.xcnf'
    with original.open() as inp,formula.open('w') as out:
        assert inp.readline().strip()=='p cnf 119909 271656'
        out.write('p cnf 119909 271664\n')
        for i,variable in enumerate(branch['mask_variable_ids']):
            literal=variable if branch['branch_prefix_value']>>i&1 else -variable
            out.write(f'{literal} 0\n')
        for line in inp:out.write(line)
    assert sha(formula)==result['formula_sha256']
    assert formula.stat().st_size==result['formula_bytes']
stdout=gzip.open(HERE/'k5_solver.stdout.gz','rb').read()
stderr=gzip.open(HERE/'k5_solver.stderr.gz','rb').read()
assert hashlib.sha256(stdout).hexdigest()==result['raw_stdout_sha256']
assert hashlib.sha256(stderr).hexdigest()==result['raw_stderr_sha256']
assert not stderr
lines=stdout.decode(errors='replace').splitlines()
restarts=[line for line in lines if line.startswith('c rst')]
assert len(restarts)==result['restart_rows']
assert not any(line.startswith(('s ','v ')) for line in lines)
assert len(restarts)==3008
record={'status':'PASS_TERMINAL_REPLAY','candidate_id':None,'branch_formula_sha256':result['formula_sha256'],
        'solver_stdout_sha256':result['raw_stdout_sha256'],'restart_rows':len(restarts),
        'last_restart':restarts[-1],'terminal_protocol_sha256':sha(HERE/'terminal_protocol.json'),
        'verifier_sha256':sha(Path(__file__))}
(HERE/'terminal_result.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps(record,sort_keys=True))
