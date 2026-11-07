"""Execute the frozen D_K=-39 class-walk holdout with retained receipts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

HERE = Path(__file__).resolve().parent
SAGE = Path('/Volumes/SSD990/cryptanalysis/sage')
SCRIPT = HERE / 'tools' / 'exp11_class_walk.py'
DEPENDENCY = HERE / 'tools' / 'hecke11.py'
EXPECTED = {
    SCRIPT.name: '17a2a87c86206644e4d9f6e64735f97f5e56c2526fe20a3b54807c193685ba09',
    DEPENDENCY.name: '7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb',
}
for source in (SCRIPT, DEPENDENCY):
    assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED[source.name]

attempt_id = f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{time.time_ns()}-{uuid.uuid4().hex[:8]}"
attempt = HERE / 'runs' / attempt_id
(attempt / 'tools').mkdir(parents=True, exist_ok=False)
(attempt / 'data').mkdir()
attempt_script = attempt / 'tools' / SCRIPT.name
shutil.copyfile(SCRIPT, attempt_script)
shutil.copyfile(DEPENDENCY, attempt / 'tools' / DEPENDENCY.name)

runtime = subprocess.run([str(SAGE), '--runtime-info'], capture_output=True, text=True, check=True)
(attempt / 'runtime-info.json').write_text(runtime.stdout)
env = os.environ.copy()
env.update(PFS_WALK_DK='-39', PFS_WALK_F='6', PFS_WALK_L='2,3', PFS_WALK_PMIN='367')
cmd = [str(SAGE), '-python', str(attempt_script)]
start = time.monotonic()
try:
    result = subprocess.run(cmd, cwd=attempt, env=env, capture_output=True, text=True, timeout=180)
    status = {'exit_code': result.returncode, 'timeout': False}
    out, err = result.stdout, result.stderr
except subprocess.TimeoutExpired as exc:
    status = {'exit_code': None, 'timeout': True}
    out = (exc.stdout or b'').decode(errors='replace')
    err = (exc.stderr or b'').decode(errors='replace')
(attempt / 'producer.stdout').write_text(out)
(attempt / 'producer.stderr').write_text(err)
status.update(command=cmd, environment={k: env[k] for k in ('PFS_WALK_DK', 'PFS_WALK_F', 'PFS_WALK_L', 'PFS_WALK_PMIN')},
              cap_seconds=180, wall_seconds=time.monotonic()-start,
              attempt_directory=str(attempt.relative_to(HERE)),
              output='data/exp11_class_walk_D39_f6.json')
(attempt / 'launch.json').write_text(json.dumps(status, indent=2) + '\n')
print(json.dumps(status, indent=2))
