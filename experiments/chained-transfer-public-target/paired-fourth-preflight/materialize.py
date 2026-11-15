"""Literal source/fixture assembly only; all research arithmetic is Rust/Lean."""
from pathlib import Path
import hashlib,json,lzma
p=Path(__file__).resolve().parent;s=p.parent;g=p/'generated';g.mkdir();(g/'models').mkdir();rows=[]
def copy(src,dst,suffix=b'',marker=None,patch=None):
 b=src.read_bytes();v=b if marker is None else b.split(marker)[0];assert marker is None or b.count(marker)==1
 original=v
 if patch:
  old,new=patch;assert v.count(old)==1;v=v.replace(old,new)
 body=v+suffix;(g/dst).write_bytes(body)
 rows.append(dict(source=str(src),whole_sha256=hashlib.sha256(b).hexdigest(),literal_prefix_bytes=len(original),literal_prefix_sha256=hashlib.sha256(original).hexdigest(),explicit_patch=None if patch is None else [x.decode()for x in patch],appended=suffix.decode(),generated=dst,generated_sha256=hashlib.sha256(body).hexdigest()))
copy(s/'odd-source/src/lib.rs','lib.rs',b'\ninclude!("second_literal.rs");\ninclude!("third_literal.rs");\n#[path="models/mod.rs"]\npub mod models;\n#[path="torsion.rs"]\npub mod twisted_torsion;\ninclude!("../src/twist_append.rs");\ninclude!("../src/fourth_append.rs");\ninclude!("../src/fourth_tests.rs");\n#[cfg(test)]\ninclude!("extended_old_test.rs");\n',b'\n#[cfg(test)]\nmod tests {')
copy(s/'nondual13-preflight/src/append.rs','second_literal.rs',marker=b'\n#[cfg(test)]\nmod second_hop_tests {')
copy(s/'nondual13-next-preflight/src/append.rs','third_literal.rs',marker=b'\n#[cfg(test)]\ninclude!("../src/tests.rs");')
copy(s/'odd-product-models/src/lib.rs','models/mod.rs',marker=b'\n#[cfg(test)]\nmod tests;')
copy(s/'odd-product-models/src/source.rs','models/source.rs',b'\ninclude!("../../src/source_twist.rs");\ninclude!("../../src/fourth_source.rs");\n',patch=(b'actual nonzero prime-ell generator plus unique Hasse multiple4;original arithmetic and written Hasse bridge',b'actual nonzero prime-ell generator plus unique Hasse multiple equal to declared order/ell; original arithmetic and written Hasse bridge'))
copy(s/'odd-product-models/src/even.rs','models/even.rs')
copy(s/'odd-product-refinements/src/kernels.rs','torsion.rs',b'\ninclude!("../src/torsion_twist.rs");\ninclude!("../src/fourth_torsion.rs");\ninclude!("fourth_edge_transport.rs");\n',b'pub fn audit_all(')
for name,src in [('old-second-model.json',s/'nondual13-preflight/models/expected-native-01.json.xz'),('old-third-model.json',s/'nondual13-next-preflight/models/expected-native-01.json.xz')]:
 b=lzma.decompress(src.read_bytes());(g/name).write_bytes(b);rows.append(dict(source=str(src),generated=name,whole_decompressed_sha256=hashlib.sha256(b).hexdigest(),method='whole original genuine18 fixture, no field extraction'))
old=p/'src/tests.rs';b=old.read_bytes();closing=b'    }\n}\n';assert b.endswith(closing)
suffix=b'        crate::run_paired_fourth(&c, &pair, &all3, g3, &_transport);\n'+closing
prefix=b[:-len(closing)];(g/'extended_old_test.rs').write_bytes(prefix+suffix)
rows.append(dict(source=str(old),whole_sha256=hashlib.sha256(b).hexdigest(),literal_prefix_bytes=len(prefix),literal_prefix_sha256=hashlib.sha256(prefix).hexdigest(),explicit_additive_call=suffix.decode(),generated='extended_old_test.rs',generated_sha256=hashlib.sha256(prefix+suffix).hexdigest(),scope='entire previous test body and nine prints unchanged; append one call before its original two closing braces'))
src=s/'nondual13-next-preflight/models/src/torsion_append.rs';b=src.read_bytes();v=b
patches=[('pub fn audit_third(hop: &chained_n4_nondual13_next_preflight::ThirdHop','pub fn audit_edge4(hop: &crate::FourthBranch'),('"third_forward"','"fourth_forward"'),('"protocol":"23ab48"','"protocol":"paired-fourth01"'),('literal_current_J1_HLP10_mask','fixed_source_mask'),('actual transported mask fixed before E2 model builder is called','actual transported mask fixed before E4 model builder is called')]
for before,after in patches:
 expected=2 if before=='"third_forward"' else 1
 assert v.count(before.encode())==expected;v=v.replace(before.encode(),after.encode())
(g/'fourth_edge_transport.rs').write_bytes(v);rows.append(dict(source=str(src),whole_sha256=hashlib.sha256(b).hexdigest(),explicit_patches=patches,generated='fourth_edge_transport.rs',generated_sha256=hashlib.sha256(v).hexdigest(),scope='literal original full64/4096/135 algorithm; explicit signature/map-field/provenance-label changes only'))
(g/'custody.json').write_text(json.dumps(dict(protocol='PAIRED_FOURTH_EDGE_PROTOCOL_01 publishedfa3c50b5 BEFORE new code',literal_sources=rows,scope='additive derivative; original mathematical source and nine-record fixture unchanged'),indent=2)+'\n')
print('literal prior bodies and whole fixtures assembled; one additive fourth-edge call; no research arithmetic executed')
