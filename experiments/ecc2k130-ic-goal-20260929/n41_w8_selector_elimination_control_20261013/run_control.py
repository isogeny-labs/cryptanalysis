"""Monitored frozen constructed-control build for selector elimination."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
import psutil
HERE=Path(__file__).resolve().parent
record=json.loads((HERE/'control_run_protocol.json').read_text())
for path,digest in record['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
command=['python3','-B',str(HERE/'experiment.py'),'control']
parent=psutil.Process(os.getpid());start=time.monotonic_ns();peak=0;degraded=False;stop=None
with (HERE/'control.stdout').open('x') as out,(HERE/'control.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:peak=max(peak,parent.memory_info().rss+proc.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:degraded=True
        if peak>record['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic_ns()-start>record['wall_cap_seconds']*10**9:stop='WALL_CAP'
        if stop:os.killpg(child.pid,signal.SIGTERM);break
        time.sleep(.05)
    child.wait()
result={'status':'EXIT_0' if child.returncode==0 else stop or 'EXIT_ERROR',
        'exit_code':child.returncode,'command':command,
        'wall_ns':time.monotonic_ns()-start,'stop_reason':stop,
        'sampled_peak_combined_rss_bytes':peak,'monitor_degraded':degraded,
        'protocol_sha256':hashlib.sha256((HERE/'control_run_protocol.json').read_bytes()).hexdigest(),
        'sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                  for name in ('control.stdout','control.stderr','public.xcnf','control_result.json')
                  if (HERE/name).exists()}}
with (HERE/'control_run_result.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'],result['wall_ns']/1e9)
