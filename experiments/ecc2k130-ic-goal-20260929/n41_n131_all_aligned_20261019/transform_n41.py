"""Rotate every W11 pair slot to the same exact source-point domain."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    cfg=json.loads((HERE/'transform_protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_ALL_ALIGNED_N41_SOURCE'
    assert cfg['script_sha256']==sha(__file__)
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    source=Path(cfg['sources']['prior_join_input']['path'])
    lines=source.read_text().splitlines()
    assert lines[0]=='W11FIVE 5 1124 1'
    originals={}
    for row in lines:
        words=row.split()
        if words and words[0]=='S' and words[1]=='0':
            originals[int(words[2])]=words
    assert len(originals)==1124
    output=[];changed=0
    for row in lines:
        words=row.split()
        if words and words[0]=='S':
            slot,sid=int(words[1]),int(words[2])
            base=originals[sid]
            assert words[3:9]==base[3:9]
            if slot:
                words[-2:]=base[-2:]
                changed+=1
            row=' '.join(words)
        output.append(row)
    assert changed==4496
    path=HERE/'n41_join_input.tsv'
    path.write_text('\n'.join(output)+'\n')
    result={'status':'PASS_ALL_ALIGNED_N41_SOURCE_TRANSFORM','candidate_id':None,
            'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','rotations':[0]*5,
            'source_states_per_slot':1124,'changed_state_rows':changed,
            'target_row':next(row for row in output if row.startswith('T ')),
            'input_sha256':sha(path),'protocol_sha256':sha(HERE/'transform_protocol.json')}
    (HERE/'transform_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
