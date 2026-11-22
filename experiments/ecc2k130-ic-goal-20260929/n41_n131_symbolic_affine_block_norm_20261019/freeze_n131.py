import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
coefficients = root / 'n131_w33_freecode_resultant_20261018/coefficients.json'
paths = [here/'n131_transfer_sage.py', here/'lean-toolchain',
         here/'sage_runtime_info.json', here/'compress_result.json',
         coefficients, root/'n131_w33_freecode_resultant_20261018/export_protocol.json']
protocol = {
    'status':'FROZEN_BEFORE_N131_SAMPLED_BLOCK_TRANSFER',
    'candidate_id':None,
    'curve_id':'EC1N131Ckb1heb5f1998f20b',
    'coefficients':str(coefficients),
    'sampled_prefixes':[0,1,2,3,5,7,11,13],
    'wall_cap_seconds':180,
    'worker_count':1,
    'memory_cap_bytes':4*1024**3,
    'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
    'test':'Both frozen constructed-positive and ordinary public N131 resultant; exact 16-code norm identity and full 32-dimensional right-source modular gcd on eight left prefixes',
}
dest=here/'n131_transfer_protocol.json'
assert not dest.exists()
dest.write_text(json.dumps(protocol,sort_keys=True,indent=2)+'\n')
print(hashlib.sha256(dest.read_bytes()).hexdigest())
