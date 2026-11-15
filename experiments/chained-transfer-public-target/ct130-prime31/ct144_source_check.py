#!/usr/bin/env python3
"""CT144 source-only custody gate: no execution; [pcc:unverified]."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parent
expected={
 'ct135_native.cpp':'5422e02524850bfb0f595901c063a07326079e9dd82a483e6085996ce97bbdb0',
 'ct136_native.cpp':'20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921',
 'ct144_projective_bsgs.cpp':'8cb98aa0285ef5dd084f0957fecfb3a97f995bb3eb8702402102d404ff4f19e9',
 'CT144_FROZEN_TARGETS.csv':'ea17d4ae6d39bbc61f834d50967cceae37f69fdf04806bfd80ff2750c439a7e3'
}
for path,digest in expected.items():
 if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest: raise SystemExit('CT144 invalid original '+path)
raw=(root/'ct136_native.cpp').read_text()
snip=raw.split('constexpr int LANES=32;',1)[1].split('int main(int argc,char**argv)',1)[0]
for w in (4,16):
 s='constexpr int LANES='+str(w)+';'+snip
 s=s.replace('6250;round++',str(200000//w)+';round++')
 for old,new in [('LANES',f'LANES{w}'),('StateArray',f'StateArray{w}'),('batch_plus',f'batch_plus{w}'),('rho_batch',f'rho_batch{w}')]:s=s.replace(old,new)
 if (root/f'ct144_batch{w}.inc').read_text()!=s: raise SystemExit('CT144 altered generated comparator '+str(w)
print('CT144 source, include and 128-point manifest hashes and full contents: OK [pcc:unverified]')
