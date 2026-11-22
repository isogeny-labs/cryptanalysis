"""Admission-gated controlled panel. No panel is launched by unit tests/imports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import resource
import signal
import subprocess
import sys
import time
from core import digest
from fixtures import make, workload, SEEDS
from host import snapshot

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def admission(protocol, path):
    data = json.loads(path.read_text())
    if data.get('mode') == 'pending':
        raise SystemExit('No launch admission: the exception question is still pending')
    freeze = protocol.get('freeze', {})
    if freeze.get('status') != 'frozen' or not freeze.get('filed_before_affected_data'):
        raise SystemExit('Refusing unfrozen or retrospective experiment protocol')
    manifest_path = HERE / protocol['links']['source_manifest']
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != protocol['links']['source_manifest_sha256']:
        raise SystemExit('Source manifest changed after protocol freeze')
    unsigned = {key: value for key, value in protocol.items() if key != 'freeze'}
    actual_hash = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    if actual_hash != freeze.get('protocol_sha256'):
        raise SystemExit('Protocol bytes changed after freeze')
    for name, sha in json.loads(manifest_path.read_text()).items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest() != sha:
            raise SystemExit('Source changed after protocol freeze: '+name)
    if data.get('mode') == 'user_authorized_exploratory_cpu_git':
        if data.get('user_authorization_received') is not True or not data.get('user_quote'):
            raise SystemExit('Missing explicit user exception for S3/GPU prerequisites')
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
        if data.get('source_commit') != head:
            raise SystemExit('Git checkpoint does not bind the current source commit')
        if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=REPO):
            raise SystemExit('Tracked source has uncommitted edits')
        return data
    subprocess.run(['bash', str(REPO/'scripts/checkpoint.sh'), 'gate'], cwd=REPO, check=True)
    subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], check=True, capture_output=True)
    if not data.get('cuda_host_admission_receipt') or not data.get('checkpoint_succeeded'):
        raise SystemExit('Standard checkpoint and CUDA host admission remain required')
    return data


def one(payload, directory, cpu, sequence):
    key = f'{sequence:04d}-{payload["instance"]["fixture_id"][:12]}-{payload["arm"]}-{payload["workload"]["seed"]}'
    source = directory.parent/'inputs'/f'{key}.json'
    output = directory/f'{key}.json'
    log = directory.parent/'logs'/f'{key}.txt'
    source.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(payload)+'\n')
    host_before = snapshot(cpu)
    start = time.perf_counter_ns()
    pid = os.fork()
    if pid == 0:
        try:
            os.setsid()
            os.sched_setaffinity(0, {cpu})
            resource.setrlimit(resource.RLIMIT_AS, (768 << 20, 768 << 20))
            resource.setrlimit(resource.RLIMIT_CPU, (65, 65))
            fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            os.dup2(fd, 1)
            os.dup2(fd, 2)
            os.close(fd)
            env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                       MKL_NUM_THREADS='1', PYTHONHASHSEED='0')
            os.execve(sys.executable, [sys.executable, str(HERE/'worker.py'), str(source), str(output)], env)
        except BaseException:
            os._exit(127)
    timed_out = False
    while True:
        done, status, usage = os.wait4(pid, os.WNOHANG)
        if done:
            break
        if (time.perf_counter_ns()-start) / 1e9 > 60:
            timed_out = True
            os.killpg(pid, signal.SIGKILL)
            _, status, usage = os.wait4(pid, 0)
            break
        time.sleep(0.05)
    elapsed = time.perf_counter_ns()-start
    data = json.loads(output.read_text()) if output.exists() else {
        'instance': payload['instance'], 'workload': payload['workload'],
        'arm': payload['arm'], 'queries': [], 'complete_collection_wall_ns': None}
    data['os_child_rusage'] = {'ru_utime': usage.ru_utime, 'ru_stime': usage.ru_stime,
                               'ru_maxrss': usage.ru_maxrss,
                               'ru_nvcsw': usage.ru_nvcsw, 'ru_nivcsw': usage.ru_nivcsw}
    data['supervised_process_wall_ns_including_import'] = elapsed
    data['selected_cpu'] = cpu
    data['host_before'] = host_before
    data['host_after'] = snapshot(cpu)
    data['exit_code'] = os.waitstatus_to_exitcode(status)
    if timed_out or data['exit_code']:
        data['status'] = 'cell_timeout' if timed_out else 'worker_error'
        data['complete_collection_wall_ns'] = None
    data['standing'] = 'unverified'
    output.write_text(json.dumps(data, indent=2)+'\n')
    return key, data['status']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol', type=Path, default=HERE/'protocol.json')
    parser.add_argument('--admission', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    authorization = admission(protocol, args.admission)
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out/'fixtures.json').exists():
        raise SystemExit('Output already contains fixtures; use a new run directory')
    cpu = min(os.sched_getaffinity(0))
    fixtures = make()
    (args.out/'fixtures.json').write_text(json.dumps(fixtures, indent=2)+'\n')
    (args.out/'host.json').write_text(json.dumps(snapshot(cpu), indent=2)+'\n')
    cells = args.out/'cells'
    cells.mkdir(exist_ok=True)
    sequence = 0
    for instance in fixtures['instances']:
        for seed in SEEDS:
            work = workload(instance, seed)
            arms = (['montgomery', 'edwards', 'invariant', 'retained', 'montgomery-aa']
                    if instance['kind'] == 'torsion'
                    else ['weierstrass', 'retained', 'weierstrass-aa'])
            random.Random(seed + int(instance['fixture_id'][:12], 16)).shuffle(arms)
            for arm in arms:
                payload = {'launch_authorized': True, 'instance': instance,
                           'workload': work, 'arm': arm, 'pdp_limit_s': 2}
                key, status = one(payload, cells, cpu, sequence)
                print(key, status, flush=True)
                sequence += 1
    subprocess.run([sys.executable, str(HERE/'analyze.py'), str(cells),
                    '--out', str(args.out/'summary.json')], check=True)


if __name__ == '__main__':
    main()
