from pathlib import Path
import json,hashlib,platform,subprocess,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
P=Path(__file__).resolve().parent
a=json.loads((P/'summary.json').read_text());b=json.loads((P/'m2/summary.json').read_text())
plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})
def save(fig,name):
 fig.savefig(P/(name+'.svg'),bbox_inches='tight');fig.savefig(P/(name+'.png'),dpi=150,bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(9.4,3.4));xs=list(range(5))
for arm,label,color,mark in [('selected-aa0','m2, B=256 primary','#087f8c','o'),('selected-aa1','m2 A/A repeat','#7ab6bd','x'),('m3-reference','m3, B=512','#d28e00','s'),('m4-reference','m4, B=512','#7656a2','^')]:
 ax.plot(xs,[r[arm]['cold_ms'] for r in b['rows']],marker=mark,label=label,color=color,lw=1)
ax.set(xticks=xs,xlabel='Fresh target index (m2 follow-up only)',ylabel='Cold time (ms)',ylim=(0,330),title='Direct pair lookup: all four IC arms recover 5/5 targets')
ax.legend(ncol=2,loc='upper right',fontsize=9);ax.grid(axis='y',alpha=.2);fig.tight_layout();save(fig,'m2-cold')
fig,axs=plt.subplots(1,2,figsize=(9.4,3.0),gridspec_kw={'width_ratios':[1,1.2]})
for key,label,col in [('selected_cold_ms','m4 primary','#7656a2'),('aa_cold_ms','m4 A/A','#b4a0cc'),('m3_cold_ms','m3 reference','#d28e00')]:axs[0].plot(xs,[r[key] for r in a['rows']],marker='o',label=label,color=col)
axs[0].set(xticks=xs,ylabel='Cold time (ms)',xlabel='First-panel fresh target index',title='First frozen panel: 5/5 per indexed arm');axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
colors=['#cedce1','#d28e00','#087f8c','#7656a2','#cccccc'];keys=['base_construction_ns','pair_index_ns','online_ns','extra_certificate_replay_ns'];labs=['Base + group prep','Pair table','Search + elimination + replay','Extra full replay','Serialization + teardown']
for i,row in enumerate(b['rows']):
 r=json.loads((P/'m2/raw'/f'heldout-T{i}-selected-aa0.json').read_text());v=[(r['base_construction_ns']+r['group_preparation_ns'])/1e6]+[r[k]/1e6 for k in keys[1:]];v.append(r['cold_to_report_ns']/1e6-sum(v));left=0
 for j,x in enumerate(v):axs[1].barh(i,x,left=left,color=colors[j],label=labs[j] if i==0 else None);left+=x
axs[1].set(yticks=xs,ylabel='Follow-up target index',xlabel='Cold time (ms)',title='Full costs: no amortized or free setup');axs[1].legend(fontsize=7,loc='lower right');axs[1].grid(axis='x',alpha=.2)
fig.tight_layout();save(fig,'costs')
fig,ax=plt.subplots(figsize=(9.4,2.0));ax.set_xlim(0,10);ax.set_ylim(0,2);ax.axis('off')
labels=['Public Q only\nfixed E, G, N','Batched walk\naG + bQ','Signed pair index\nx key + all witnesses','Signed elimination\nwᵀH = 0','Full certificate\nreplay; return d']
for i,label in enumerate(labels):
 x=i*2;ax.add_patch(FancyBboxPatch((x+.05,.65),1.75,.95,boxstyle='round,pad=.05',fc='#edf4f5',ec='#087f8c'));ax.text(x+.925,1.125,label,ha='center',va='center',fontsize=9)
 if i<4:ax.annotate('',xy=(x+2.02,1.125),xytext=(x+1.83,1.125),arrowprops={'arrowstyle':'->','color':'#444'})
ax.text(5,.25,'All table construction, relation collection, elimination, and certificate replay are charged.',ha='center',fontsize=9)
fig.tight_layout();save(fig,'pipeline')
# Compact committed evidence retains native clock/counter outputs and original hash bindings.
small={'schema':'m31-e2e-delivery/v1','standing':'pcc:unverified','original_panel':{k:v for k,v in a.items() if k not in ('profile','rows')},'followup_panel':{k:v for k,v in b.items() if k!='profile'},'source_refs':{'worker_execution':'bfa695d0c5963a2bbdb6a59766683188a40df8f4','original_selection':'a52ce2f71a2348eaedb887244f6437e7df8fffd4','followup_protocol':'c94c0b7','followup_runner':'0f5ec2dd351b8e3c2e839f56b930d6268e94319e','followup_selection_analysis':'67f5e90'},'artifact':'/workspace/isogeny-m31-e2e.zip','binary_sha256':json.loads((P/'manifest.json').read_text())['binary_sha256'],'bindings':{str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [P/'manifest.json',P/'summary.json',P/'replay.json',P/'m2/manifest.json',P/'m2/summary.json',P/'m2/replay.json']}}
(P/'RESULTS.json').write_text(json.dumps(small,indent=2)+'\n')
# Record observable host details without asserting physical-host isolation or RAM technology.
def command(cmd):return subprocess.run(cmd,capture_output=True,text=True).stdout
host={'schema':'m31-e2e-host/v1','recorded_after_evaluation':True,'host':platform.platform(),'lscpu':command(['lscpu','-J']),'affinity':sorted(os.sched_getaffinity(0)),'numa_policy':'single pinned exposed CPU; default first-touch allocation; no enforced node binding or placement capture','physical_ram_technology':'unknown','isolation':'shared container; no admitted tier or exclusivity','compiler':command(['bash','-lc','source "$HOME/.cargo/env"; rustc +1.88.0 -Vv']),'cgroup':{}}
for path in ('/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/memory.max','/sys/fs/cgroup/memory.events','/sys/fs/cgroup/cpuset.cpus.effective','/sys/fs/cgroup/cpuset.mems.effective'):
 try:host['cgroup'][path]=Path(path).read_text()
 except OSError:host['cgroup'][path]=None
(P/'hardware.json').write_text(json.dumps(host,indent=2)+'\n')
