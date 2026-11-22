"""Freeze source data and extraction script for compact certificates."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
base=here.parent/'n41_n131_pairroot_functional_20261018'
out=here/'certificate_protocol.json'
assert not out.exists()
paths=[here/'certificate.py',here/'result.json',
       base/'n41_result.json',base/'n131_result.json']
record={'status':'FROZEN_BEFORE_BRANCH_INVARIANT_CERTIFICATE_EXTRACTION',
        'candidate_id':None,
        'n41_source':str(base/'n41_result.json'),
        'n131_source':str(base/'n131_result.json'),
        'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in paths}}
out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
