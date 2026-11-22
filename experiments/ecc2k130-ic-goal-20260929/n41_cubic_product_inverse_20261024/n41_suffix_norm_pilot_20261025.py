import hashlib,json,random,time
from pathlib import Path
from sage.all import PolynomialRing

root=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
geo_path=root/'n41_w8_fixed_sum_table_20261009/geometry.json'
table_path=root/'n41_four_code_suffix_quotient_20261024/target_table.json'
cases_path=root/'n41_w8_two_code_affine_span_20261013/cases.jsonl'
audit_path=root/'n41_w8_fixed_sum_table_20261009/audit.py'
expected={geo_path:'d100282312b509a4e93dd8896b8d79f7c664537e224e25b607eab28e6c87dcae',
 table_path:'277d78c82d008d128c5ffa7d9444ea2f7d27899d3ed1a6b3d3163aef854611b4',
 cases_path:'5865314886c6d777c2827074f3917485d40d76fad7d93cda6aac47b5f97d82d6',
 audit_path:'9a0b4b8c97e0b4d8102d175e511cc19f5b751354c3a7d04540646f6498a60b0e'}
for path,digest in expected.items():assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
import importlib.util
spec=importlib.util.spec_from_file_location('curve_audit',audit_path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
curve,elem,integer=module.sage_curve();F=elem(0).parent()
PR=PolynomialRing(F,'T');T=PR.gen();zero=F.zero();one=F.one()
geo=json.loads(geo_path.read_text());table=json.loads(table_path.read_text())
cases=[json.loads(x) for x in cases_path.read_text().splitlines()]
third=geo['blocks'][2];S=elem(third['s'])**2
products=[]
for code in range(40):
 state=third['states'][4*code];p=zero
 for i,b in enumerate(third['product_basis']):
  if (state['a']>>i)&1:p+=elem(b)
 products.append(p)
assert len({integer(p) for p in products})==40
charts={integer(elem(row['chart'])):row['state_id'] for group in table['rows'] for row in group}
assert len(charts)==160
def product_tree(polys):
 while len(polys)>1:
  polys=[polys[2*i]*polys[2*i+1] if 2*i+1<len(polys) else polys[2*i]
         for i in range((len(polys)+1)//2)]
 return polys[0]
setup=time.monotonic();chart_vanisher=product_tree([T+elem(t) for t in charts])
assert chart_vanisher.degree()==160
fixture_case=next(row for row in cases if (row['left_code'],row['right_code'])==(24,37))
def u_from(row,index):
 v=elem(row['reciprocal_coordinates'][index]);return v/(v+one)
tasks=[(fixture_case,2)]
rng=random.Random(20261025)
for _ in range(99):tasks.append((cases[rng.randrange(len(cases))],rng.randrange(8)))
setup_s=time.monotonic()-setup
records=[];build_s=gcd_s=0
for idx,(case,ui) in enumerate(tasks):
 u=u_from(case,ui);h=u*(u+one);B=h*(T*T+T);D=T*T+u*u
 start=time.monotonic()
 factors=[D*D+S*S+(S*S+S)*B*B+p*B*(D+S)+p*p*D*(D+1) for p in products]
 norm=product_tree(factors)
 build_s+=time.monotonic()-start
 assert norm.degree()==160
 start=time.monotonic();g=norm.gcd(chart_vanisher)
 gcd_s+=time.monotonic()-start
 if g.degree():
  hits=[]
  for rawt,sid in charts.items():
   t=elem(rawt)
   if g(t)==zero:
    for pi,p in enumerate(products):
     if factors[pi](t)==zero:hits.append([sid,case['left_code'],case['right_code'],ui,pi])
  records.append({'task':idx,'degree':int(g.degree()),'hits':hits})
assert records==[{'task':0,'degree':1,'hits':[[0,24,37,2,10]]}],records
print(json.dumps({'status':'PASS_N41_SUFFIX_NORM_PILOT','candidate_id':None,
 'tasks':len(tasks),'source_products':len(products),'charts':len(charts),
 'setup_s':setup_s,'norm_build_s':build_s,'gcd_s':gcd_s,
 'retained':records},sort_keys=True))
