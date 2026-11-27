"""Native command/proof regression controls; Python performs no group arithmetic."""
import argparse,json,subprocess,tempfile
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',required=True,type=Path);parser.add_argument('--verifier',required=True,type=Path);args=parser.parse_args()
    worker=args.worker.resolve();verifier=args.verifier.resolve();checks=[]
    def run(command,code):
        p=subprocess.run(list(map(str,command)),capture_output=True,text=True,timeout=30)
        assert p.returncode==code,(command,p.returncode,p.stderr[:500]);assert 'panicked at' not in p.stderr
        checks.append({'command':list(map(str,command)),'expected_exit':code,'actual_exit':p.returncode})
        return p
    run([worker,'--help'],0)
    for argv in [[],['--qx'],['--qx','-1','--qy','0'],['--qx','0','--qy','0'],['--qx','2147483648','--qy','814455902'],['--qx','1','--qy','814455902','--lanes','0'],['--qx','1','--qy','814455902','--chunk','0'],['--qx','1','--qy','814455902','--columns','2049'],['--qx','1','--qy','814455902','--summands','1'],['--surprise','1']]:run([worker,*argv],2)
    p=run([worker,'--qx','2144058214','--qy','807222724','--max-queries','0'],1);incomplete=json.loads(p.stdout);assert incomplete['status']=='incomplete' and incomplete['certificate'] is None
    with tempfile.TemporaryDirectory(prefix='m31-delivery-') as directory:
        root=Path(directory);report=root/'report.json'
        p=run([worker,'--qx','2144058214','--qy','807222724','--seed','1'],0);report.write_text(p.stdout);r=json.loads(p.stdout)
        assert r['status']=='solved' and r['p']==2147483647 and r['scalar']==345912577 and r['columns']==256 and r['summands']==2
        checked=json.loads(run([verifier,report,'--qx','2144058214','--qy','807222724'],0).stdout);assert checked['status']=='checked' and checked['scalar']==r['scalar']
        run([verifier,report,'--qx','1','--qy','814455902'],1)
        for name,mutate in [
            ('reported-scalar',lambda r:r.update(scalar=0)),
            ('proof-scalar',lambda r:r['certificate'].update(scalar=0)),
            ('dependency-weight',lambda r:r['certificate']['weights'].__setitem__(0,(r['certificate']['weights'][0]+1)%r['n'])),
            ('signed-column',lambda r:r['certificate']['relations'][0]['terms'][0].update(sign=0)),
            ('target-substitution',lambda r:r.update(Q=r['G'])),
            ('truncated-dependency',lambda r:r['certificate']['relations'].pop()),
            ('duplicate-row',lambda r:r['certificate']['relations'].__setitem__(1,r['certificate']['relations'][0])),
        ]:
            bad=json.loads(p.stdout);mutate(bad);path=root/(name+'.json');path.write_text(json.dumps(bad));run([verifier,path],1)
        (root/'incomplete.json').write_text(json.dumps(incomplete));run([verifier,root/'incomplete.json'],1)
        (root/'malformed.json').write_text('{');run([verifier,root/'malformed.json'],1)
    print(json.dumps({'schema':'m31-delivery-controls/v1','status':'passed','checks':checks,'count':len(checks),'standing':'pcc:unverified','scope':'Native correctness and CLI controls only; no performance measurement or signed independent verdict'},indent=2))
if __name__=='__main__':main()
