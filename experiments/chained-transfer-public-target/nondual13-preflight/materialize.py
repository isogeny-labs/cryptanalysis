"""Literal source assembly and custody only; all research arithmetic is Rust."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
original=p.parent/'odd-source/src/lib.rs'
s=original.read_bytes();marker=b'\n#[cfg(test)]\nmod tests {'
assert s.count(marker)==1
prefix=s.split(marker)[0]
out=p/'generated';out.mkdir(exist_ok=False)
body=prefix+b'\n\ninclude!("../src/append.rs");\n'
(out/'lib.rs').write_bytes(body)
assert (out/'lib.rs').read_bytes()[:len(prefix)]==prefix
(out/'custody.json').write_text(json.dumps({'protocol':'../NONDUAL13_PREFLIGHT_PROTOCOL_01.md','published_protocol_commit':'cf9ca8f5eee66745848fae2673f655561b1de90f','original':str(original),'whole_original_sha256':hashlib.sha256(s).hexdigest(),'literal_prefix_bytes':len(prefix),'literal_prefix_sha256':hashlib.sha256(prefix).hexdigest(),'only_added_suffix':'include!("../src/append.rs");','restored_prefix_exact':True,'generated_sha256':hashlib.sha256(body).hexdigest(),'scope':'original tests excluded by prospective scope, original sources unchanged, new phase comprehensive test in appended Rust body'},indent=2)+'\n')
print('literal original prefix assembled; no arithmetic executed')
