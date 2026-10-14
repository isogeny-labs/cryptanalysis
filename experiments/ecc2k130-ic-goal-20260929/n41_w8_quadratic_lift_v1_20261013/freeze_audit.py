"""Freeze checked-Sage quadratic-lift replay."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
protocol=json.loads((HERE/'protocol.json').read_text())
sources=[HERE/x for x in ('protocol.json','result.json','run_result.json',
                            'audit_sage.py','run_audit.py','sage_runtime_info.json')]
sources.append(Path(protocol['source_table']))
record={'status':'FROZEN','kind':'n41_w8_quadratic_lift_sage_audit',
        'source_table':protocol['source_table'],'worker_count':1,
        'wall_cap_seconds':120,'rss_cap_bytes':4294967296,
        'sources':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in sources}}
with (HERE/'audit_protocol.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
