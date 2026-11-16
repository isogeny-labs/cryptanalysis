"""Stream the exact complete GitHub artifact; whole-byte transport only."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,urllib.request,zipfile
out=Path('/workspace/scratch/ct94-additive-original-full-CI-acceptance-01')
api=json.loads(Path('/workspace/scratch/private-ct94-CI-download-api.json').read_text());data=api.get('structuredContent',api)
if 'file_uri'not in data:data=data['structuredContent']
target=out/'whole-original-GitHub-artifact.zip';expected='06104f175a79f38aa22961cabb6467e33838724e9e87f9b037e3477defa970fb'
assert not target.exists();partial=out/'whole-original-GitHub-artifact.zip.partial';assert not partial.exists()
h=hashlib.sha256();count=0
with urllib.request.urlopen(data['file_uri']['download_url'],timeout=120)as response,partial.open('xb')as dest:
    while chunk:=response.read(1048576):
        dest.write(chunk);h.update(chunk);count+=len(chunk);assert count<=99483928
assert count==99483928 and h.hexdigest()==expected
partial.rename(target);members=[]
with zipfile.ZipFile(target)as z:
    assert len(z.namelist())==len(set(z.namelist()))
    for info in z.infolist():
        p=PurePosixPath(info.filename);assert not p.is_absolute()and '..'not in p.parts and '\\'not in info.filename
        assert not info.is_dir();members.append(dict(path=info.filename,bytes=info.file_size,compressed_bytes=info.compress_size,CRC=info.CRC,external_attr=info.external_attr,compression=info.compress_type))
(out/'zip-members-original-index.json').write_text(json.dumps(dict(all_members=members,all_paths_unique_safe=True),indent=2)+'\n')
(out/'download-transport.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),run=43700115169,job=132769186550,artifact=14156900587,source='25801fe6aaba49674ef010e814dc7c9a58c28247',bytes=count,sha256=h.hexdigest(),all_members=len(members),uncompressed_bytes=sum(row['bytes']for row in members),remote_job_conclusion='success',scientific_acceptance='PENDING entiremember/custody/phase/proof/auditor checks',scope='unsigned complete transport only; private signedmetadata retained separately'),indent=2)+'\n')
print(json.dumps(dict(bytes=count,sha256=h.hexdigest(),members=len(members),uncompressed_bytes=sum(row['bytes']for row in members))),flush=True)
