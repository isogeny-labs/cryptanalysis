"""Independently recheck every stored complete-attack certificate."""
import hashlib
import json
from pathlib import Path

from benchmark import audit,METHODS

ROOT=Path(__file__).resolve().parent


def verify():
    totals=dict(completed_attacks=0,verified_relations=0,matched_search_sequences=0)
    source_hash=hashlib.sha256((ROOT/'native_ic.cpp').read_bytes()).hexdigest()
    for folder in sorted(ROOT.glob('field*_base*')):
        checked={}
        for path in sorted(folder.glob('*_seed*.audited.json')):
            timing=json.loads(path.read_text());method=timing['method'];seed=timing['seed']
            prefix=folder/f'{method}_seed{seed}'
            result=audit(folder,method,prefix)
            assert result==timing['audit'] and timing['source_sha256']==source_hash
            assert timing['end_to_end_seconds']==timing['process_wall_seconds']+timing['basis_seconds']
            raw=json.loads(prefix.with_suffix('.json').read_text())
            for key,value in raw.items():assert timing[key]==value
            checked[method,seed]=raw
            totals['completed_attacks']+=1;totals['verified_relations']+=result['verified_relations']
        seeds={seed for method,seed in checked}
        for seed in seeds:
            if ('chain',seed) not in checked or ('same_base',seed) not in checked:continue
            a,b=checked['chain',seed],checked['same_base',seed]
            assert a['queries']==b['queries'] and a['weights']==b['weights']
            assert (folder/f'chain_seed{seed}.relations.jsonl').read_bytes()==(folder/f'same_base_seed{seed}.relations.jsonl').read_bytes()
            totals['matched_search_sequences']+=1
        if checked:print(folder.name,len(checked),'complete attacks verified',flush=True)
    (ROOT/'verification.json').write_text(json.dumps(totals,indent=2)+'\n')
    print(json.dumps(totals,indent=2));return totals


if __name__=='__main__':verify()
