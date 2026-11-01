"""Seal the pointwise transport experiment's sources and receipts."""
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PATHS=['PROTOCOL.md','RESULT.md','scan.py','run.py','runtime-info.json',
       'launch.json','scan.stdout','scan.stderr','scan.json','validate.py',
       'validation.json','validate.stdout','formal/AffineTransport.lean','formal/lean-toolchain',
       'formal/lakefile.toml','formal/lake-manifest.json','formal/build-output.txt','seal.py']
output={'status':'SEALED_D2631_ATKIN_COMMUTATION',
        'files':{path:hashlib.sha256((HERE/path).read_bytes()).hexdigest() for path in PATHS}}
encoded=json.dumps(output,indent=2,sort_keys=True)+'\n'
destination=HERE/'SEAL.json'
if '--check' in sys.argv:
    assert destination.read_text()==encoded
    print(output['status'],len(PATHS),'verified')
else:
    destination.write_text(encoded)
    print(output['status'],len(PATHS),'written')
