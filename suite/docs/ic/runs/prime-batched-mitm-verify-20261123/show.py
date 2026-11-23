import sys,json,subprocess,glob
for c in sys.argv[1:]:
    out=subprocess.run(['python3','analyze.py']+sorted(glob.glob(c+'/*.json')) if False else ['python3','analyze.py',c+'/baseline.json']+[a for a in sorted(glob.glob(c+'/lead-*.json')) if not a.endswith('status.json')],capture_output=True,text=True)
    print(c.split('/')[-1]); 
    if out.returncode: print(out.stderr[-300:])
    for l in out.stdout.splitlines():
        r=json.loads(l); print('  %-12s n=%d S %.2f [%.2f,%.2f] | wallS %.2f [%.2f,%.2f] | gae %.2f | sameTrials=%s | baseS %.1f armS %.1f S/rho %.1f'%((r['arm'],r['n'])+tuple(r['S'])+tuple(r['wallS'])+(r['gae'][0],r['same_trials'],r['base_S'],r['arm_S'],r['S_over_rho'])))
