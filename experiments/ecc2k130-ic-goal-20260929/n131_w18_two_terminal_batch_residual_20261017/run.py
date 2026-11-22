"""Matched N131 residual replay with batch and archived scalar inversion paths."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT/'n131_w18_two_terminal_bilinear_20261015'
ARITH_DIR = ROOT/'n131_fixed_seed_halftrace_cubic_20261011'
sys.path.insert(0,str(ARITH_DIR))
import verify as arithmetic  # noqa: E402
import batch  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    signal.alarm(300)
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BATCH_RESIDUAL_COMPARISON'
    paths = {'batch.py': HERE/'batch.py', 'run.py': HERE/'run.py',
             'freeze.py': HERE/'freeze.py', 'arithmetic.py': ARITH_DIR/'verify.py',
             'pool.json': OLD/'pool.json', 'query_result.json': OLD/'query_result.json',
             'control_result.json': OLD/'control_result.json',
             'old_terminal.py': OLD/'terminal.py', 'old_protocol.json': OLD/'protocol.json'}
    assert protocol['input_sha256'] == {name:sha(path) for name,path in paths.items()}
    pool = json.loads(paths['pool.json'].read_text())
    states = pool['joint_states']
    assert len(states) == 2080
    records = []
    for label, prior_name, target_key in [('public','query_result.json','raw_target'),
                                          ('constructed','control_result.json','control_raw_target')]:
        prior = json.loads(paths[prior_name].read_text())
        raw_target = prior[target_key]
        start = time.monotonic_ns()
        updated, phases = batch.residuals(raw_target,states,arithmetic)
        batch_ns = time.monotonic_ns()-start
        assert updated == prior['residuals']
        row = {'label':label,'raw_target':raw_target,
               'batch_ns':batch_ns,'batch_phase_ns':phases,
               'archived_residuals_sha256':sha(paths[prior_name]),
               'residual_count':len(updated),
               'ordered_residuals_sha256':hashlib.sha256(
                   json.dumps(updated,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
        if label == 'public':
            start = time.monotonic_ns()
            scalar=[]
            for state in states:
                joint=state['raw_sum']
                negated=((joint[0],joint[1]^joint[0]) if joint is not None else None)
                point=arithmetic.point_add(tuple(raw_target),negated)
                recip=(None if point is None or point[0] in (0,1) else arithmetic.inverse(point[0]))
                scalar.append({'left_state_id':state['left_state_id'],
                               'right_state_id':state['right_state_id'],
                               'point':list(point) if point is not None else None,
                               'standard_reciprocal':recip})
            row['matched_scalar_ns']=time.monotonic_ns()-start
            assert scalar == updated
        records.append(row)
        print(label,'batch_seconds',round(batch_ns/1e9,6),
              'matched_scalar_seconds',round(row.get('matched_scalar_ns',0)/1e9,6),flush=True)
    result={'status':'PASS_N131_BATCH_RESIDUAL_EXACT_REPLAY','candidate_id':None,
            'protocol_sha256':sha(protocol_path),'rows':records,
            'peak_self_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],flush=True)


if __name__=='__main__':
    main()
