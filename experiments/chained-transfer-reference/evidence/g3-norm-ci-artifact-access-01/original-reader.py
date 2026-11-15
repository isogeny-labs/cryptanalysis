"""Read original GitHub artifact ZIPs; never forward GitHub auth to blob hosts."""
from pathlib import Path
import json,os,urllib.request,urllib.parse,urllib.error,hashlib
o=Path('/workspace/scratch/ct56-g3-norm-own-ci-raw-01');assert o.is_dir()
token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN');assert token
api='https://api.github.com/repos/isogeny-labs/cryptanalysis'
headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
with urllib.request.urlopen(urllib.request.Request(api+'/actions/runs/43400864083/artifacts?per_page=100',headers=headers),timeout=60) as r:data=json.load(r)
(o/'artifacts-api.json').write_text(json.dumps(data,indent=2)+'\n');assert len(data['artifacts'])==data['total_count']==7
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,hdrs,newurl):return None
opener=urllib.request.build_opener(NoRedirect)
out=o/'original-artifacts';out.mkdir();receipts=[]
for artifact in data['artifacts']:
    assert not artifact['expired']
    req=urllib.request.Request(artifact['archive_download_url'],headers=headers)
    try:
        with opener.open(req,timeout=60) as response:payload=response.read();host='api.github.com';status=response.status
    except urllib.error.HTTPError as response:
        assert response.code in [301,302,303,307,308]
        location=response.headers['Location'];parsed=urllib.parse.urlparse(location);assert parsed.scheme=='https'
        # Signed redirect is used in memory only. No GitHub Authorization header.
        with urllib.request.urlopen(urllib.request.Request(location,headers={'Accept':'application/octet-stream'}),timeout=60) as download:payload=download.read();status=download.status;host=parsed.hostname
    target=out/(str(artifact['id'])+'.zip');target.write_bytes(payload);actual=hashlib.sha256(payload).hexdigest();expected=artifact.get('digest')
    receipt=dict(id=artifact['id'],name=artifact['name'],bytes=len(payload),sha256=actual,API_declared_digest=expected,download_status=status,blob_host=host,GitHub_authorization_forwarded_to_blob=False,signed_location_persisted=False)
    if expected:receipt['declared_digest_matches']=expected=='sha256:'+actual
    receipts.append(receipt);(o/'artifact-download-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n');print(artifact['name'],artifact['id'],len(payload),receipt.get('declared_digest_matches'),flush=True)
assert all(x.get('declared_digest_matches',True) for x in receipts)
