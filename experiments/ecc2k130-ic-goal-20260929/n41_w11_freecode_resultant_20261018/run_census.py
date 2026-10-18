"""Execute frozen one-process native free-code resultant census."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'census_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
assert not (HERE / 'census_result.json').exists()
started = time.monotonic()
args = [str(HERE / 'census'), str(HERE / 'resultant_input.tsv'),
        str(ROOT / 'n41_w11_fivepair_native_join_20261018/join_input.tsv'),
        str(HERE / 'census_result.json')]
try:
    run = subprocess.run(args, capture_output=True, text=True,
                         timeout=cfg['wall_cap_seconds'])
    status = 'COMPLETE' if run.returncode == 0 else 'PRODUCER_FAILURE'
    stdout, stderr, exit_code = run.stdout, run.stderr, run.returncode
except subprocess.TimeoutExpired as exc:
    status = 'BOUNDED_UNKNOWN'
    stdout = (exc.stdout or b'').decode(errors='replace')
    stderr = (exc.stderr or b'').decode(errors='replace')
    exit_code = None
(HERE / 'census.stdout').write_text(stdout)
(HERE / 'census.stderr').write_text(stderr)
out = HERE / 'census_result.json'
receipt = {'status': status, 'candidate_id': None,
           'curve_id': cfg['curve_id'], 'worker_count': 1,
           'wall_cap_seconds': cfg['wall_cap_seconds'],
           'parent_wall_seconds': time.monotonic()-started,
           'exit_code': exit_code,
           'result_complete': status == 'COMPLETE' and out.exists(),
           'result_sha256': hashlib.sha256(out.read_bytes()).hexdigest()
                            if status == 'COMPLETE' and out.exists() else None,
           'protocol_sha256': hashlib.sha256((HERE / 'census_protocol.json').read_bytes()).hexdigest()}
(HERE / 'census_receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
print(json.dumps(receipt, sort_keys=True))
