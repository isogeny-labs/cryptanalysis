"""Public primary-source downloads and PDF text extraction; I/O only."""
from pathlib import Path
import urllib.request,subprocess,json,hashlib
p=Path(__file__).resolve().parent;sources=[]
for n in [4,5,22]:
 url=f'https://math.mit.edu/classes/18.783/2025/LectureNotes{n}.pdf'
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'ChainedECDLPResearch/1.0','Accept':'application/pdf'})
  with urllib.request.urlopen(req,timeout=45)as response:b=response.read();status=response.status
  f=p/f'LectureNotes{n}.pdf';f.write_bytes(b);subprocess.run(['pdftotext','-layout',str(f),str(p/f'LectureNotes{n}.txt')],check=True);sources.append({'url':url,'status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 except Exception as ex:sources.append({'url':url,'error':repr(ex),'source_not_read':True})
(p/'primary-downloads-02.json').write_text(json.dumps(sources,indent=2)+'\n');print(json.dumps(sources))
