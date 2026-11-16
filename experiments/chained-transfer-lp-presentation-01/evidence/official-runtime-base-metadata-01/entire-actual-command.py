from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,urllib.request,subprocess
out=Path('/workspace/cryptanalysis/experiments/chained-transfer-lp-presentation-01/evidence/official-runtime-base-metadata-01');out.mkdir()
(out/'entire-actual-command.py').write_bytes(Path(__file__).read_bytes())
start=datetime.now(timezone.utc).isoformat()
def get(url,headers=None):
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=20) as reply:return reply.read(),dict(reply.headers)
try:
 auth,_=get('https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/debian:pull');registry_access_token=json.loads(auth)['token']
 headers={'Authorization':'Bearer '+registry_access_token,'Accept':'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json'}
 raw,returned_headers=get('https://registry-1.docker.io/v2/library/debian/manifests/bookworm-slim',headers);(out/'entire-official-bookworm-slim-index.json').write_bytes(raw);index=json.loads(raw);digest=returned_headers['docker-content-digest'] if 'docker-content-digest' in returned_headers else next(v for k,v in returned_headers.items() if k.lower()=='docker-content-digest');assert digest=='sha256:'+hashlib.sha256(raw).hexdigest()
 matches=[m for m in index['manifests'] if m.get('platform',{}).get('os')=='linux' and m.get('platform',{}).get('architecture')=='amd64'];assert len(matches)==1;platform_digest=matches[0]['digest']
 leaf,leaf_headers=get('https://registry-1.docker.io/v2/library/debian/manifests/'+platform_digest,headers);assert 'sha256:'+hashlib.sha256(leaf).hexdigest()==platform_digest;(out/'entire-official-linux-amd64-manifest.json').write_bytes(leaf);manifest=json.loads(leaf)
 cfg,_=get('https://registry-1.docker.io/v2/library/debian/blobs/'+manifest['config']['digest'],headers);assert 'sha256:'+hashlib.sha256(cfg).hexdigest()==manifest['config']['digest'];(out/'entire-official-linux-amd64-config.json').write_bytes(cfg);config=json.loads(cfg);assert config['architecture']=='amd64' and config['os']=='linux'
 (out/'actual-public-base-metadata.json').write_text(json.dumps(dict(start=start,finish=datetime.now(timezone.utc).isoformat(),source='official Docker library/debian bookworm-slim registry metadata',index_digest=digest,linux_amd64_manifest_digest=platform_digest,base_image='debian:bookworm-slim@'+platform_digest,config_digest=manifest['config']['digest'],actual_architecture=config['architecture'],scope='public manifest/config bytes only; no layers downloaded, container build, image execution, paid work or ABI qualification'),indent=2)+'\n')
 print(json.dumps(dict(public_metadata_exit=0,base_image='debian:bookworm-slim@'+platform_digest)))
except Exception as error:
 (out/'actual-failure.txt').write_text(type(error).__name__+': '+str(error)+'\n');print('public metadata read failed; entire noncredential diagnostic retained');raise SystemExit(1)
