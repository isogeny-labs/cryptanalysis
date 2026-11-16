"""Exhaustive signed-pair mask checks and independent public-target checks."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent


def validate():
    records=[]
    for bits,depth in [(19,5),(31,5),(31,6),(31,7),(31,8)]:
        folder=ROOT/f'field{bits}_s{depth}_base0'
        command=[str(ROOT/f'native{bits}'),str(folder/'chain.txt'),'chain',str(folder/'validation'),'0','validate']
        row=json.loads(subprocess.check_output(command,text=True))
        row.update(field_bits=bits,depth=depth);records.append(row)
        print(row,flush=True)
    data=dict(source_sha256=hashlib.sha256((ROOT/'native_ic.cpp').read_bytes()).hexdigest(),records=records,
              pair_targets=sum(r['validated_pair_targets'] for r in records),
              public_targets=sum(r['validated_public_targets'] for r in records))
    (ROOT/'native_validation.json').write_text(json.dumps(data,indent=2)+'\n')
    return data


if __name__=='__main__':validate()
