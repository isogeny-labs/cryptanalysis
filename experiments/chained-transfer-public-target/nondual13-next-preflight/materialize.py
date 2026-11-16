"""Literal source assembly only, without research arithmetic."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;s=p.parent;out=p/'generated';out.mkdir();rows=[]
def prefix(path,marker):
 b=path.read_bytes();assert b.count(marker)==1;v=b.split(marker)[0]
 rows.append(dict(original=str(path),whole_sha256=hashlib.sha256(b).hexdigest(),literal_prefix_bytes=len(v),literal_prefix_sha256=hashlib.sha256(v).hexdigest()))
 return v
original=prefix(s/'odd-source/src/lib.rs',b'\n#[cfg(test)]\nmod tests {')
second=prefix(s/'nondual13-preflight/src/append.rs',b'\n#[cfg(test)]\nmod second_hop_tests {')
(out/'second_literal.rs').write_bytes(second)
body=original+b'\ninclude!("second_literal.rs");\ninclude!("../src/append.rs");\n'
(out/'lib.rs').write_bytes(body);assert(out/'lib.rs').read_bytes()[:len(original)]==original
(out/'custody.json').write_text(json.dumps(dict(protocol='bbfd74 published9038f2b9 before third-edge code',literal_original_and_second_body=rows,generated_sha256=hashlib.sha256(body).hexdigest(),scope='literal engine and existing SecondHop bodies, original test modules excluded; new comprehensive unfiltered test appended'),indent=2)+'\n')
print('literal original engine and existing SecondHop assembled; no arithmetic executed')
