"""Copy exact prior finite-space helper bodies; no research calculations."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;s=p.parent
source=s/'odd-product-refinements/src/kernels.rs';whole=source.read_bytes()
first=b'fn vs(';last=b'fn original_all('
assert whole.count(first)==1 and whole.count(last)==1
body=whole[whole.index(first):whole.index(last)]
g=p/'generated';g.mkdir()
(g/'bits.rs').write_bytes(body)
(g/'custody.json').write_text(json.dumps(dict(prospective='0158c5 publishedc1cbc188 before implementation',source=source.relative_to(s).as_posix(),source_sha256=hashlib.sha256(whole).hexdigest(),start=first.decode(),end_before=last.decode(),literal_body_sha256=hashlib.sha256(body).hexdigest(),body_edits=[]),indent=2)+'\n')
