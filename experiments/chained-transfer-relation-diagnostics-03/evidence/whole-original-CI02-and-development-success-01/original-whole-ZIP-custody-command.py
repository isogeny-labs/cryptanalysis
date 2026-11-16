"""Whole ZIP/CRC/hash and small-member custody; no mathematical extraction."""
from pathlib import Path,PurePosixPath
import hashlib,json,shutil,urllib.request,zipfile

base=Path('/dev/shm/ct183-B7-entire-CI-artifacts-01');base.mkdir()
specs=[(0,14192302267,340729140,'4972d58159bd44cfcb39daf29d8e3813c3c6ead85d928b281e022d1c15ec4de3'),(1,14192170203,1097635,'ad811044580ca01cdf8d3c345697f7f66142175bd04dc61865e3aa0930814a45'),(2,14191164098,201303822,'d97c9943f76b95857c77a691c834b948a231603de10537cbb82d6faa8d62c009')]
for index,artifact,size,digest in specs:
 out=base/str(artifact);out.mkdir()
 private=json.loads(Path('/workspace/scratch/private-ct182-B7-download-'+str(index)+'.json').read_text())
 url=private['structuredContent']['file_uri']['download_url']
 archive=out/'entire-original-artifact.zip'
 with urllib.request.urlopen(url,timeout=120) as source,archive.open('xb') as destination:shutil.copyfileobj(source,destination,1024*1024)
 assert archive.stat().st_size==size
 h=hashlib.sha256()
 with archive.open('rb')as source:
  for chunk in iter(lambda:source.read(1024*1024),b''):h.update(chunk)
 assert h.hexdigest()==digest
 inventory=[]
 with zipfile.ZipFile(archive)as whole:
  assert len(whole.namelist())==len(set(whole.namelist()))
  for member in whole.infolist():
   path=PurePosixPath(member.filename);assert not path.is_absolute() and '..'not in path.parts
   if member.is_dir():continue
   sha=hashlib.sha256();count=0
   # Keep all logical bytes in the complete original ZIP. Materialize every
   # small member for inspection; stream the entire large members for CRC/hash.
   materialize=member.file_size<=1024*1024
   target=out/'all-entire-small-members'/member.filename
   if materialize:target.parent.mkdir(parents=True,exist_ok=True);destination=target.open('xb')
   else:destination=None
   try:
    with whole.open(member)as source:
     for chunk in iter(lambda:source.read(1024*1024),b''):
      count+=len(chunk);sha.update(chunk)
      if destination is not None:destination.write(chunk)
   finally:
    if destination is not None:destination.close()
   assert count==member.file_size
   inventory.append(dict(member=member.filename,bytes=count,sha256=sha.hexdigest(),zip_CRC32=member.CRC,whole_stream_read_with_CRC=True,materialized_whole_regular_file=materialize))
 (out/'entire-member-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
 receipt=dict(artifact_id=artifact,whole_zip=str(archive),whole_bytes=size,whole_sha256=digest,all_members_streamed_complete_with_ZIP_CRC=True,member_count=len(inventory),logical_uncompressed_bytes=sum(x['bytes']for x in inventory),all_original_bytes_retained_in_whole_zip=True,large_members_not_separately_unpacked=True,reason='preserve complete archives within finite RAM; small-member inspection is not a truncated replacement',private_signed_URL_not_published=True)
 (out/'whole-archive-custody.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
