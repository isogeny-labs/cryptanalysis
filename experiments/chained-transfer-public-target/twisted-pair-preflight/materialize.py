"""Literal source/fixture I/O only. No mathematical calculation or selection."""
from pathlib import Path
import hashlib,json,lzma
p=Path(__file__).resolve().parent;s=p.parent;g=p/'generated';g.mkdir();(g/'models').mkdir();rows=[]
def copy(src,dst,suffix=b'',marker=None,patch=None):
 b=src.read_bytes();v=b if marker is None else b.split(marker)[0];assert marker is None or b.count(marker)==1
 original=v
 if patch:
  old,new=patch;assert v.count(old)==1;v=v.replace(old,new)
 body=v+suffix;(g/dst).write_bytes(body)
 rows.append(dict(source=str(src),whole_sha256=hashlib.sha256(b).hexdigest(),literal_prefix_bytes=len(original),literal_prefix_sha256=hashlib.sha256(original).hexdigest(),explicit_patch=None if patch is None else [x.decode() for x in patch],appended=suffix.decode(),generated=dst,generated_sha256=hashlib.sha256(body).hexdigest()))
copy(s/'odd-source/src/lib.rs','lib.rs',b'\ninclude!("second_literal.rs");\ninclude!("third_literal.rs");\n#[path="models/mod.rs"]\npub mod models;\n#[path="torsion.rs"]\npub mod twisted_torsion;\ninclude!("../src/twist_append.rs");\n#[cfg(test)]\ninclude!("../src/tests.rs");\n',b'\n#[cfg(test)]\nmod tests {')
copy(s/'nondual13-preflight/src/append.rs','second_literal.rs',marker=b'\n#[cfg(test)]\nmod second_hop_tests {')
copy(s/'nondual13-next-preflight/src/append.rs','third_literal.rs',marker=b'\n#[cfg(test)]\ninclude!("../src/tests.rs");')
copy(s/'odd-product-models/src/lib.rs','models/mod.rs',marker=b'\n#[cfg(test)]\nmod tests;')
copy(s/'odd-product-models/src/source.rs','models/source.rs',b'\ninclude!("../../src/source_twist.rs");\n',patch=(b'actual nonzero prime-ell generator plus unique Hasse multiple4;original arithmetic and written Hasse bridge',b'actual nonzero prime-ell generator plus unique Hasse multiple equal to declared order/ell; original arithmetic and written Hasse bridge'))
copy(s/'odd-product-models/src/even.rs','models/even.rs')
copy(s/'odd-product-refinements/src/kernels.rs','torsion.rs',b'\ninclude!("../src/torsion_twist.rs");\n',b'pub fn audit_all(')
for name,src in [('old-second-model.json',s/'nondual13-preflight/models/expected-native-01.json.xz'),('old-third-model.json',s/'nondual13-next-preflight/models/expected-native-01.json.xz')]:
 b=lzma.decompress(src.read_bytes());(g/name).write_bytes(b);rows.append(dict(source=str(src),generated=name,whole_decompressed_sha256=hashlib.sha256(b).hexdigest(),method='entire original genuine18 fixture, no field extraction'))
(g/'custody.json').write_text(json.dumps(dict(protocol='f10846 published3fad107a before proof/native code',literal_sources=rows,scope='original helpers and all prior hop bodies; only SourceE metadata text generalized to describe explicit new Hasse certificate, original cofactor4 checker unchanged; new source constructor separate'),indent=2)+'\n')
print('literal original helpers, prior hops, models and whole old fixtures assembled; no mathematics executed')
