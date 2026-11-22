"""Unpinned ordinary N41 relation control for the four-fiber selector law."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
N41=ROOT/'n41_w8_fixedseed_ordinary_join_20261013'
N41_ARITH=ROOT/'n41_w8_fixed_sum_table_20261009/audit.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit_path=N41/'audit_result.json'
    query_path=N41/'query_result.json'
    audit=json.loads(audit_path.read_text())
    query=json.loads(query_path.read_text())
    assert audit['status']=='PASS_INDEPENDENT_SAGE_ORDINARY_N41_SEVEN_PAIR_RELATION'
    assert query['status']=='PASS_ORDINARY_RAW_RELATION'
    assert audit['group_replay_pass'] and audit['raw_sum_pass']
    spec=importlib.util.spec_from_file_location('n41_checked_curve',N41_ARITH)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    curve,elem,integer=old.sage_curve()
    def decode(pair):
        return curve(elem(pair[0]),elem(pair[1]))
    def encode(point):
        return None if point==curve(0) else [integer(point[0]),integer(point[1])]
    states=[decode(row['raw_pair_sum']) for row in audit['states']]
    assert len(states)==7
    free=sum(states[:5],curve(0))
    terminal=sum(states[5:],curve(0))
    raw=decode(audit['raw_target'])
    public=decode(audit['public_target'])
    assert free+terminal==raw and 4*raw==public
    offsets=[curve(0),curve(elem(0),elem(1)),curve(elem(1),elem(0)),
             curve(elem(1),elem(1))]
    assert len(set(offsets))==4
    assert all(4*point==curve(0) for point in offsets)
    targets=[raw+point for point in offsets]
    assert len(set(targets))==4 and all(4*point==public for point in targets)
    residuals=[point-terminal for point in targets]
    assert residuals[0]==free
    assert all(point!=free for point in residuals[1:])
    rows=[]
    for index,(target,residual) in enumerate(zip(targets,residuals)):
        recip=(None if residual==curve(0) or integer(residual[0]) in (0,1)
               else integer(residual[0]**-1))
        rows.append({'raw_preimage_index':index,'raw_target':encode(target),
                     'terminal_sum':encode(terminal),'residual':encode(residual),
                     'standard_reciprocal':recip,
                     'matches_unpinned_free_five':residual==free})
    receipt={'status':'PASS_UNPINNED_N41_FOURFIBER_SELECTOR_CONTROL',
             'curve_id':audit['curve_id'],'public_target':audit['public_target'],
             'relation_state_ids':[row['state_id'] for row in audit['states']],
             'free_five_sum':encode(free),'terminal_two_sum':encode(terminal),
             'raw_fibers':rows,'source_sha256':{
                 'script':sha(Path(__file__)),'n41_audit':sha(audit_path),
                 'n41_query':sha(query_path),'n41_arithmetic':sha(N41_ARITH),
                 'sage_runtime_info':sha(HERE/'sage_runtime_info.json')}}
    (HERE/'n41_control_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],flush=True)


if __name__=='__main__':
    main()
