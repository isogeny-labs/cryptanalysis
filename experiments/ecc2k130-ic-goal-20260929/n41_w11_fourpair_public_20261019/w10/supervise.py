"""One-worker N41 four-pair join under frozen wall and combined-RSS caps."""
import hashlib,json,os,subprocess,time
from pathlib import Path
import psutil
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'query_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_W10_FOURPAIR_QUERY'
for k,v in cfg['sources'].items():assert sha(v['path'])==v['sha256'],k
assert cfg['worker_count']==1
out=H/'join4.stdout';err=H/'join4.stderr';receipt=H/'query_result.json'
assert not out.exists() and not err.exists() and not receipt.exists()
cmd=[cfg['binary'],cfg['sources']['join_input']['path'],str(cfg['target_orientations'])]
start=time.monotonic();parent=psutil.Process(os.getpid());peak=samples=0;stop=monitor_error=None
with out.open('xb') as fo,err.open('xb') as fe:
 child=subprocess.Popen(cmd,stdout=fo,stderr=fe,cwd=H,start_new_session=True)
 (H/'query_handle.json').write_text(json.dumps({'pid':child.pid,'command':cmd,'started_monotonic':start},sort_keys=True,indent=2)+'\n')
 proc=psutil.Process(child.pid)
 while child.poll() is None:
  try:
   peak=max(peak,parent.memory_info().rss+proc.memory_info().rss)
   samples+=1
  except psutil.NoSuchProcess:
   if child.poll() is not None:break
   stop='MONITOR_FAILURE';monitor_error='NoSuchProcessWhileLive';break
  except (psutil.AccessDenied,PermissionError) as exc:
   if child.poll() is None:
    stop='MONITOR_FAILURE';monitor_error=type(exc).__name__;break
  if peak>cfg['rss_cap_bytes']:stop='RSS_CAP';break
  if time.monotonic()-start>cfg['wall_cap_seconds']:stop='WALL_CAP';break
  time.sleep(.02)
 if stop and child.poll() is None:child.terminate()
 code=child.wait()
lines=out.read_text().splitlines();terminal=next((x for x in reversed(lines) if x.startswith('HIT ') or x.startswith('NO_HIT ')),None)
status=('COMPLETE_HIT' if not stop and code==0 and terminal and terminal.startswith('HIT ') else
        'COMPLETE_NO_HIT' if not stop and code==0 and terminal and terminal.startswith('NO_HIT ') else
        stop or 'PRODUCER_FAILURE')
result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],'command':cmd,
 'exit_code':code,'stop_reason':stop,'monitor_error':monitor_error,
 'wall_seconds':time.monotonic()-start,'sampled_peak_combined_rss_bytes':peak,
 'rss_samples':samples,'terminal_line':terminal,'worker_lines':lines,
 'stdout_sha256':sha(out),'stderr_sha256':sha(err),
 'protocol_sha256':sha(H/'query_protocol.json'),'supervisor_sha256':sha(Path(__file__))}
receipt.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','exit_code','wall_seconds','sampled_peak_combined_rss_bytes','terminal_line')},sort_keys=True))
