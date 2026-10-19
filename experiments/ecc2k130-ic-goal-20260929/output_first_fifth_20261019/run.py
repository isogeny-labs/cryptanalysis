"""Target-conditioned fifth-code inversion for frozen N41/N131 four-slot panels."""
import hashlib,itertools,json,resource,signal,sys,time
from collections import Counter
from pathlib import Path
from output_first_math import FixedSeed
H=Path(__file__).resolve().parent
case=sys.argv[1];assert case in ('n41','n131')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/(case+'_protocol.json')).read_text())
assert cfg['status']=='FROZEN_BEFORE_OUTPUT_FIRST_FIFTH_'+case.upper()
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
assert cfg['worker_count']==1
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('output-first wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
start=time.monotonic()
if case=='n41':
    fixed=FixedSeed(41,[0,3],56,11);rotation=24
    panel=json.loads(Path(cfg['sources']['panel']['path']).read_text())
    states={}
    for line in Path(cfg['sources']['join_input']['path']).read_text().splitlines()[2:]:
        c=line.split()
        if c[0]=='S':
            slot,sid,code,branch,a,b,ca,cb,x,y=map(int,c[1:])
            states[(slot,sid)]={'point':(x,y),'code':code,'columns':[ca,cb]}
    boxes=[]
    for box in panel['boxes']:
        choices=[[states[(slot,sid)] for pair in box['root_choices'][slot] for sid in pair]
                 for slot in range(4)]
        boxes.append({'kind':box['kind'],'choices':choices,'target':tuple(panel['target_point'])})
else:
    fixed=FixedSeed(131,[0,1,2,13],898618,33);rotation=72
    panel=json.loads(Path(cfg['sources']['panel']['path']).read_text())
    boxes=[]
    for box in panel['boxes']:
        choices=[]
        for slot in range(4):
            choices.append([{'point':tuple(xy),'code':choice['code'],'columns':choice['columns']}
                            for choice in box['choices'][slot] for xy in choice['signed_points']])
        boxes.append({'kind':box['kind'],'choices':choices,'target':tuple(box['target_point'])})
load_seconds=time.monotonic()-start
rows=[];run_status='COMPLETE_OUTPUT_FIRST_FIFTH'
for box_index,box in enumerate(boxes):
    t=time.monotonic();counts=Counter();hits=[]
    target=box['target'];assert fixed.e.on_curve(target)
    for ids in itertools.product(range(4),repeat=4):
        selected=[box['choices'][j][ids[j]] for j in range(4)]
        columns=[col for choice in selected for col in choice['columns']]
        assert len(set(columns))==8
        assert len({choice['code'] for choice in selected})==4
        prefix=None
        for choice in selected:
            point=choice['point'];assert fixed.e.on_curve(point)
            prefix=fixed.e.add(prefix,point)
        residual=fixed.e.sub(target,prefix)
        found=fixed.recover(residual,rotation)
        counts[found['status']]+=1
        if found['status']=='VERIFIED_PAIR_OUTPUT':
            all_cols=columns+found['columns']
            if len(set(all_cols))<10 or found['code'] in [x['code'] for x in selected]:
                counts['COLUMN_OR_CODE_COLLISION']+=1
                continue
            assert fixed.e.add(prefix,tuple(found['output_point']))==target
            hits.append({'prefix_choice_indices':list(ids),
                         'first_four_codes':[x['code'] for x in selected],
                         'last_code':found['code'],
                         'last_source_masks':found['source_masks'],
                         'last_product':found['product'],
                         'factor_columns':all_cols,
                         'residual_point':found['output_point'],
                         'target_point':list(target)})
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
            run_status='RSS_CAP_PARTIAL';break
    rows.append({'box_index':box_index,'kind':box['kind'],'target_point':list(target),
                 'prefix_assignments':sum(counts.values())-counts['COLUMN_OR_CODE_COLLISION'],
                 'status_counts':dict(sorted(counts.items())),
                 'verified_relations':hits,'box_seconds':time.monotonic()-t})
    if run_status!='COMPLETE_OUTPUT_FIRST_FIFTH':break
signal.alarm(0)
result={'status':run_status,'candidate_id':None,'curve_id':cfg['curve_id'],'case':case,
        'field_degree':fixed.n,'source_free_bits':len(fixed.bits),
        'source_product_rank':len(fixed.basis),'H':fixed.H,'C':fixed.C,
        'boxes_completed':len(rows),'rows':rows,
        'public_relations':sum(len(r['verified_relations']) for r in rows if r['kind'] in ('frozen_public_raw_point','frozen_random_source_family')),
        'source_load_seconds':load_seconds,'wall_seconds':time.monotonic()-start,
        'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(H/(case+'_protocol.json')),'script_sha256':sha(Path(__file__)),
        'math_sha256':sha(H/'output_first_math.py')}
(H/(case+'_result.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'case':case,'boxes_completed':len(rows),
                  'public_relations':result['public_relations'],
                  'positive_relations':len(rows[0]['verified_relations']),
                  'wall_seconds':result['wall_seconds']},sort_keys=True),flush=True)
