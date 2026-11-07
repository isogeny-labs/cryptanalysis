import gzip,json,math,hashlib,collections,pathlib
root=pathlib.Path(__file__).parent
D={}
for arm in ('main','c12'):
 p=root/f'rows_{arm}.jsonl.gz'
 rows={}
 with gzip.open(p,'rt') as f:
  for line in f:
   z=json.loads(line); key=(z['family'],z['bits'],z['curve'],z['target'])
   if key in rows: raise ValueError(('duplicate',arm,key))
   rows[key]=z
 D[arm]=rows
M,C=D['main'],D['c12']
assert set(M)==set(C)
assert len(M)==80000 and len(C)==80000
assert all(z['correct'] and z['rho_correct'] for z in M.values())
assert all(z['correct'] for z in C.values())
assert all((M[k]['p'],M[k]['a'],M[k]['b'],M[k]['N'],M[k]['r'],M[k]['k'])==(C[k]['p'],C[k]['a'],C[k]['b'],C[k]['N'],C[k]['r'],C[k]['k']) for k in M)
assert all(len({k[2] for k in M if k[0]==f and k[1]==b})==200 for f in ('j1728','j0') for b in range(26,41,2))
assert all(sum(1 for k in M if k[0]==f and k[1]==b)==5000 for f in ('j1728','j0') for b in range(26,41,2))
def table(r,m,c):
 budget=(math.isqrt(r//m)+1)//(c*r.bit_length())
 return 8 if budget<16 else 16 if budget<32 else 32
same=[k for k in M if table(M[k]['r'],4 if k[0]=='j1728' else 6,48)==table(M[k]['r'],4 if k[0]=='j1728' else 6,12)]
assert len(same)==45700
assert all(M[k]['ops']==C[k]['ops'] for k in same)
result={'rows_per_arm':len(M),'rho_rows':len(M),'identity_control_equal_table':len(same),'identity_control_mismatched':0,'cells':{},'primary':{}}
for family in ('j1728','j0'):
 primary=[]
 for bits in range(26,41,2):
  keys=[k for k in M if k[0]==family and k[1]==bits]
  a=sum(C[k]['ops'] for k in keys); b=sum(M[k]['ops'] for k in keys); rho=sum(M[k]['rho_ops'] for k in keys)
  ratio=a/b
  result['cells'][f'{family}:{bits}']={'c12_over_main':ratio,'main_over_rho':b/rho,'c12_over_rho':a/rho,'main_ops':b,'c12_ops':a,'rho_ops':rho}
  if bits in (28,30,32,34): primary.append(ratio)
 result['primary'][family]=math.exp(sum(map(math.log,primary))/4)
(root/'independent-point-recompute.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'rows_per_arm':result['rows_per_arm'],'identity_control':len(same),'primary':result['primary'],'cells':{k:v['c12_over_main'] for k,v in result['cells'].items()}},indent=2))
