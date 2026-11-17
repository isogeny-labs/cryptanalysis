#!/usr/bin/env python3
"""Check source-level control invariants without inferring binary placement."""
import hashlib,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
name='suite/src/cryptanalysis/ic_framework/batch_mitm.rs'
old=subprocess.check_output(['git','show','bfd0e5062cbedccbc3b2a28856832dd434533510:'+name],cwd=ROOT,text=True)
new=(ROOT/name).read_text()
def query(text): return text[text.index('    fn decompose('):text.index('\n#[cfg(test)]')]
assert query(old)==query(new)
def array(text):
    start=text.index('BTreeMap::from([',text.index('    fn setup_native('))
    return text[start:text.index('])',start)+2]
original=array(old); current=array(new)
entry=re.search(r'\(\s*"mitm_indexed_prepare_pairs"\.into\(\),.*?\),\s*(?=\("mitm_scalar_prepare")',original,re.S).group()
expanded=current.replace('$($indexed,)?',entry)
normalize=lambda s:''.join(s.split())
assert normalize(expanded)==normalize(original)
out=dict(status='pass',query_method_source_sha256=hashlib.sha256(query(new).encode()).hexdigest(),present_constructor_expands_to_original_array=True,source_sha256=hashlib.sha256(new.encode()).hexdigest(),scope='Source equality and macro expansion only. No native binary, address, cache or timing equivalence claimed.')
(P/'source-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
