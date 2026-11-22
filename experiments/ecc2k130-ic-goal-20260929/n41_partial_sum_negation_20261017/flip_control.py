"""Construct and replay a public point that exercises the flipped lookup."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'
SOURCE=D.parent/'n41_w8_quotient_first_pair_20261015'
sys.path.insert(0,str(SOURCE))
import circuit
spec=importlib.util.spec_from_file_location('old_n41_builder',SOURCE/'build.py')
old_build=importlib.util.module_from_spec(spec);spec.loader.exec_module(old_build)
add=old_build.prior.add


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original=(OLD/'join_input.tsv').read_text().splitlines()
    audit=json.loads((OLD/'join_audit_result.json').read_text())
    rows=[[None]*160 for _ in range(6)]
    by_signature=[{} for _ in range(6)]
    for line in original[1:]:
        parts=line.split();assert parts[0]=='S'
        slot,sid,a,b,sa,sb,ca,cb,x,y=map(int,parts[1:])
        rows[slot][sid]={'point':(x,y),'cols':{ca,cb},
                         'signature':(a,b,sa,sb)}
        by_signature[slot][(a,b,sa,sb)]=sid
    negid=[]
    for slot in range(6):
        negid.append([by_signature[slot][(r['signature'][0],r['signature'][1],
                                          r['signature'][2]^1,r['signature'][3]^1)]
                      for r in rows[slot]])
    left_ids=[r['state_id'] for r in audit['pair_rows'][:3]]
    assert left_ids[0]<negid[0][left_ids[0]]
    left_points=[rows[i][sid]['point'] for i,sid in enumerate(left_ids)]
    left=add(add(left_points[0],left_points[1]),left_points[2])
    flipped_ids=[negid[i][sid] for i,sid in enumerate(left_ids)]
    flipped_points=[rows[i][sid]['point'] for i,sid in enumerate(flipped_ids)]
    flipped=add(add(flipped_points[0],flipped_points[1]),flipped_points[2])
    assert flipped==(left[0],left[1]^left[0])
    used=set().union(*(rows[i][sid]['cols'] for i,sid in enumerate(left_ids)))
    right_ids=None
    for a in range(160):
        A=rows[3][a]
        if A['cols']&used:continue
        for b in range(160):
            B=rows[4][b]
            if B['cols']&(used|A['cols']):continue
            for c in range(160):
                C=rows[5][c]
                if C['cols']&(used|A['cols']|B['cols']):continue
                right_ids=[a,b,c];break
            if right_ids is not None:break
        if right_ids is not None:break
    assert right_ids is not None
    rp=[rows[3+i][sid]['point'] for i,sid in enumerate(right_ids)]
    right=add(add(rp[0],rp[1]),rp[2])
    target=add(flipped,right)
    assert target is not None
    control=D/'flip_control.tsv'
    control.write_text(f'ECC2K41 6 160 {target[0]} {target[1]}\n'+
                       '\n'.join(original[1:])+'\n')
    binary=D/'negation_join'
    start=time.monotonic()
    proc=subprocess.run([str(binary),str(control)],capture_output=True,timeout=30)
    wall=time.monotonic()-start
    (D/'flip_control.stdout').write_bytes(proc.stdout)
    (D/'flip_control.stderr').write_bytes(proc.stderr)
    hits=[line for line in proc.stdout.decode().splitlines() if line.startswith('HIT ')]
    assert proc.returncode==0 and len(hits)==1
    hit=hits[0].split()
    assert list(map(int,hit[1:7]))==flipped_ids+right_ids
    assert int(hit[9])==1
    result={'status':'PASS_FLIPPED_LOOKUP','source_input_sha256':sha(OLD/'join_input.tsv'),
            'control_input_sha256':sha(control),'binary_sha256':sha(binary),
            'stdout_sha256':sha(D/'flip_control.stdout'),
            'stderr_sha256':sha(D/'flip_control.stderr'),
            'left_ids':left_ids,'flipped_left_ids':flipped_ids,
            'right_ids':right_ids,'raw_target':target,'hit_line':hits[0],
            'wall_s':wall}
    (D/'flip_control_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
