"""Literal generalized geometry and elliptic helpers; no arithmetic."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;s=p.parent;g=p/'generated';g.mkdir();rows=[]
for source,destination,patches in [
 ('odd-product-maps/src/adapter.rs','adapter.rs',[('chained_n4_odd_product_models','chained_n4_paired_fourth_preflight::models',3)]),
 ('odd-product-maps/src/norm.rs','norm.rs',[])]:
 whole=(s/source).read_bytes();body=whole
 for before,after,count in patches:
  assert body.count(before.encode())==count
  body=body.replace(before.encode(),after.encode())
 (g/destination).write_bytes(body);rows.append(dict(source=source,source_sha256=hashlib.sha256(whole).hexdigest(),destination=destination,body_sha256=hashlib.sha256(body).hexdigest(),explicit_patches=patches))
for source,start,end,destination in [
 ('odd-source/src/lib.rs','fn er(','fn digest(','encoding.rs'),
 ('odd-source/src/lib.rs','fn cubic(','fn identity_residual(','polynomial.rs'),
 ('odd-source/src/lib.rs','fn homogeneous(','fn multiplication_13(','rational.rs'),
 ('nondual13-preflight/src/append.rs','fn rational_curve_residual(','pub struct SecondHop','curve_residual.rs'),
 ('twisted-pair-preflight/src/twist_append.rs','fn eval_rational(','fn compare_degree13_recipe(','eval_rational.rs'),
 ('norm-halving-evaluator/src/lib.rs','fn parse_packet(','#[derive(Clone, Copy)]','parse_packet.rs')]:
 whole=(s/source).read_bytes();a=start.encode();b=end.encode();assert whole.count(a)==1 and whole.count(b)==1
 body=whole[whole.index(a):whole.index(b)];(g/destination).write_bytes(body)
 rows.append(dict(source=source,source_sha256=hashlib.sha256(whole).hexdigest(),start=start,end_before=end,destination=destination,body_sha256=hashlib.sha256(body).hexdigest(),explicit_patches=[]))
(g/'custody.json').write_text(json.dumps(dict(protocol='38b827 publishedbd603d0 before code',literal_sources=rows,scope='Two original geometry bodies and six literal helper sections; only three declared nominal import replacements'),indent=2)+'\n')
print('Eight literal original geometry/helper units; no arithmetic run')
