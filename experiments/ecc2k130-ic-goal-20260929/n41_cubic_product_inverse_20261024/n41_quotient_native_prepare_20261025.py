import hashlib,json
from pathlib import Path

root=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
geo_path=root/'n41_w8_fixed_sum_table_20261009/geometry.json'
table_path=root/'n41_four_code_suffix_quotient_20261024/target_table.json'
cases_path=root/'n41_w8_two_code_affine_span_20261013/cases.jsonl'
expected={geo_path:'d100282312b509a4e93dd8896b8d79f7c664537e224e25b607eab28e6c87dcae',
 table_path:'277d78c82d008d128c5ffa7d9444ea2f7d27899d3ed1a6b3d3163aef854611b4',
 cases_path:'5865314886c6d777c2827074f3917485d40d76fad7d93cda6aac47b5f97d82d6'}
for path,digest in expected.items():assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
geo=json.loads(geo_path.read_text());table=json.loads(table_path.read_text())
cases=[json.loads(line) for line in cases_path.read_text().splitlines()]
assert len(cases)==1554 and len(table['rows'])==40
third=geo['blocks'][2]
def insert(piv,x):
 while x:
  bit=x.bit_length()-1
  if piv[bit]:x^=piv[bit]
  else:piv[bit]=x;return True
 return False
piv=[0]*41;basis=[]
for b in third['product_basis']:
 if insert(piv,b):basis.append(b)
assert len(basis)==7
products=[]
for code in range(40):
 state=third['states'][4*code];value=0
 for bit,b in enumerate(third['product_basis']):
  if (state['a']>>bit)&1:value^=b
 products.append(value)
assert len(set(products))==40
out=Path(__file__).with_name('n41_quotient_native_input_20261025.tsv')
with out.open('w') as f:
 print('N41Q',7,40,160,1554,third['s'],file=f)
 for b in basis:print('B',b,file=f)
 for code,p in enumerate(products):print('P',code,p,file=f)
 for row in table['rows']:
  for chart in row:print('T',chart['state_id'],chart['chart'],file=f)
 for case in cases:
  assert len(case['reciprocal_coordinates'])==8
  print('C',case['left_code'],case['right_code'],*case['reciprocal_coordinates'],file=f)
print(json.dumps({'status':'PASS_N41_QUOTIENT_INPUT','sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
 'bytes':out.stat().st_size,'source_rank':len(basis),'products':len(products),
 'charts':160,'families':len(cases)}))
