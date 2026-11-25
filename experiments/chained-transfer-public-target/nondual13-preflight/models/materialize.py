"""Literal source assembly only. Native code performs every research calculation."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;s=p.parent.parent;g=p/'generated';g.mkdir();rows=[]
def copy(src,name,suffix=b'',marker=None):
 b=src.read_bytes();prefix=b if marker is None else b.split(marker)[0];assert marker is None or b.count(marker)==1
 body=prefix+suffix;(g/name).write_bytes(body);assert(g/name).read_bytes()[:len(prefix)]==prefix
 rows.append({'original':str(src),'whole_original_sha256':hashlib.sha256(b).hexdigest(),'literal_prefix_bytes':len(prefix),'literal_prefix_sha256':hashlib.sha256(prefix).hexdigest(),'only_added_suffix':suffix.decode(),'generated':name,'generated_sha256':hashlib.sha256(body).hexdigest()})
copy(s/'odd-product-models/src/lib.rs','lib.rs',b'\n#[path="torsion_original.rs"]\npub mod transported;\ninclude!("../src/model_append.rs");\n',b'\n#[cfg(test)]\nmod tests;')
copy(s/'odd-product-models/src/source.rs','source.rs',b'\ninclude!("../src/source_append.rs");\n')
copy(s/'odd-product-models/src/even.rs','even.rs')
copy(s/'odd-product-refinements/src/kernels.rs','torsion_original.rs',b'\ninclude!("../src/torsion_append.rs");\n',b'pub fn audit_all(')
(g/'custody.json').write_text(json.dumps({'protocol':'23ab48, published cf9ca8f5 before phaseA/B source','scope':'literal original generic model/source/even and pure torsion helper prefixes; original tests audit_all not included, new comprehensive phaseB test appended','original_bytes_unchanged':rows},indent=2)+'\n')
