"""Bind the frozen source, two target queries, Lean log, and Sage audit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as inp:
        for block in iter(lambda:inp.read(8<<20),b''):h.update(block)
    return h.hexdigest()

def main():
    source=json.loads((HERE/'produce.receipt.json').read_text())
    old=(ROOT/'n131_w29_native_pair_source_prefix_20261019'/'n131_full.stdout').read_text().splitlines()
    previous=next(line for line in old if line.startswith('RESULT COMPLETE ')).split()
    assert source['status']=='COMPLETE'
    assert source['stream_bytes']==134219672*17
    assert source['stream_sha256']==sha(HERE/'all.bin')
    producer=source['terminal_line'].split()
    assert producer[:5]==['PRODUCE','COMPLETE','67109836','134219672','0']
    assert producer[5]==previous[-1]
    queries={}
    for label in ('baseline','linear','public_baseline','public_linear'):
        cfg=json.loads((HERE/f'{label}.protocol.json').read_text())
        receipt=json.loads((HERE/f'{label}.receipt.json').read_text())
        assert cfg['status']=='FROZEN_BEFORE_'+label.upper()
        for rec in cfg['inputs'].values():assert sha(rec['path'])==rec['sha256']
        assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
        assert receipt['protocol_sha256']==sha(HERE/f'{label}.protocol.json')
        assert receipt['stdout_sha256']==sha(HERE/f'{label}.stdout')
        assert receipt['stderr_sha256']==sha(HERE/f'{label}.stderr')
        fields=receipt['terminal_line'].split()
        assert fields[:3]==['QUERY','COMPLETE','134219672']
        assert fields[3:6]==['134219672','0','268439344']
        assert receipt['sampled_peak_combined_rss_bytes']<=4294967296
        assert receipt['wall_seconds']<=590
        queries[label]={'roots':int(fields[5]),'hits':int(fields[6]),
                        'digest':fields[7],'native_seconds':int(fields[8])/1e9,
                        'parent_wall_seconds':receipt['wall_seconds'],
                        'sampled_peak_combined_rss_bytes':receipt['sampled_peak_combined_rss_bytes']}
    assert queries['baseline']['hits']==queries['linear']['hits']==1
    assert queries['public_baseline']['hits']==queries['public_linear']['hits']==0
    assert queries['baseline']['digest']==queries['linear']['digest']
    assert queries['public_baseline']['digest']==queries['public_linear']['digest']
    audit=json.loads((HERE/'audit_result.json').read_text())
    assert audit['status']=='PASS_FULL_TERMINAL_SAGE_AUDIT'
    assert audit['prefix_outputs_replayed']==2128 and audit['linear_map_controls']==256
    assert len(audit['queries']['linear']['valid_source_hits'])==1
    assert audit['queries']['linear']['valid_source_hits'][0]['left_code']==22
    assert audit['queries']['linear']['valid_source_hits'][0]['right_code']==29
    for label in queries:
        assert len(audit['queries'][label]['valid_source_hits'])==queries[label]['hits']
    n41=json.loads((HERE/'n41_linear_control_result.json').read_text())
    assert n41['status']=='PASS_N41_LINEAR_TERMINAL_CONTROL'
    assert n41['left_outputs']==562 and n41['s3_roots']==1124
    assert n41['product_image_hits']==1 and n41['hit'][1:3]==[253,63]
    lean=(HERE/'lean.stdout').read_text()
    assert 'sorryAx' not in lean and lean.count('depends on axioms:')==4
    assert not (HERE/'lean.stderr').read_text()
    result={'status':'PASS_FULL_STREAM_TERMINAL_REPLAY','candidate_id':None,
            'source_valid_codes':67109836,'source_outputs':134219672,
            'stream_bytes':source['stream_bytes'],'stream_sha256':source['stream_sha256'],
            'source_setup_parent_seconds':source['wall_seconds'],
            'queries':queries,
            'constructed_observed_stage_ratio':queries['baseline']['parent_wall_seconds']/queries['linear']['parent_wall_seconds'],
            'public_observed_stage_ratio':queries['public_baseline']['parent_wall_seconds']/queries['public_linear']['parent_wall_seconds'],
            'sage_audit_sha256':sha(HERE/'audit_result.json'),
            'n41_control_sha256':sha(HERE/'n41_linear_control_result.json'),
            'lean_stdout_sha256':sha(HERE/'lean.stdout')}
    (HERE/'verification_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
