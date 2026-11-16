"""Literal model/helper source assembly only; research arithmetic is native Rust."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;s=p.parent.parent;g=p/'generated';g.mkdir();rows=[]
def copy(src,name,suffix=b'',marker=None):
 b=src.read_bytes();prefix=b if marker is None else b.split(marker)[0];assert marker is None or b.count(marker)==1
 body=prefix+suffix;(g/name).write_bytes(body);assert(g/name).read_bytes()[:len(prefix)]==prefix
 rows.append(dict(original=str(src),whole_sha256=hashlib.sha256(b).hexdigest(),literal_prefix_bytes=len(prefix),literal_prefix_sha256=hashlib.sha256(prefix).hexdigest(),generated=name,generated_sha256=hashlib.sha256(body).hexdigest(),added_suffix=suffix.decode()))
copy(s/'odd-product-models/src/lib.rs','lib.rs',b'\n#[path="torsion_original.rs"]\npub mod transported;\ninclude!("../src/model_append.rs");\n',b'\n#[cfg(test)]\nmod tests;')
copy(s/'odd-product-models/src/source.rs','source.rs',b'\ninclude!("source_second_literal.rs");\ninclude!("../src/source_append.rs");\n')
copy(s/'nondual13-preflight/models/src/source_append.rs','source_second_literal.rs')
copy(s/'odd-product-models/src/even.rs','even.rs')
copy(s/'odd-product-refinements/src/kernels.rs','torsion_original.rs',b'\ninclude!("torsion_second_literal.rs");\ninclude!("../src/torsion_append.rs");\n',b'pub fn audit_all(')
copy(s/'nondual13-preflight/models/src/torsion_append.rs','torsion_second_literal.rs')
(g/'custody.json').write_text(json.dumps(dict(protocol='bbfd74 published9038f2b9 before new code',literal_sources=rows,scope='original generic/source/even/finite-space prefixes plus entire prior second-source/transport appendices; third source/transport/test are explicit additive code'),indent=2)+'\n')
print('literal model and previous phaseB appendices assembled; no arithmetic executed')
