"""Check the signed source-pair involution in the frozen six-slot input."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'
data=(OLD/'join_input.tsv').read_text().splitlines()
slots={i:{} for i in range(6)}
for line in data[1:]:
    tag,slot,sid,a,b,sa,sb,ca,cb,x,y=line.split()
    assert tag=='S'
    slot,sid,a,b,sa,sb,ca,cb,x,y=map(int,(slot,sid,a,b,sa,sb,ca,cb,x,y))
    slots[slot][(a,b,sa,sb)]=(sid,ca,cb,x,y)
checks=0
for slot,states in slots.items():
    assert len(states)==160
    for (a,b,sa,sb),(sid,ca,cb,x,y) in states.items():
        nsid,nca,ncb,nx,ny=states[(a,b,sa^1,sb^1)]
        assert nsid!=sid and (nca,ncb)==(ca,cb)
        assert (nx,ny)==(x,y^x)
        checks+=1
result={'status':'PASS','source_input_sha256':hashlib.sha256((OLD/'join_input.tsv').read_bytes()).hexdigest(),
        'signed_states_checked':checks,'involution_pairs':checks//2,
        'negation_rule':'(x,y) -> (x,y xor x)'}
(D/'state_audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
