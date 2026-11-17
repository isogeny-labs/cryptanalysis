#!/usr/bin/env python3
"""CT169: live fixture mutations for the CT168 fail-closed independent census audit."""
import copy
import json
import sys
import tempfile
from pathlib import Path
from ct168_trace_audit import audit

def run_tests(primary_path, secondary_path):
    primary=json.loads(Path(primary_path).read_text())
    secondary=json.loads(Path(secondary_path).read_text())
    with tempfile.TemporaryDirectory() as temp:
        x,y=Path(temp)/'direct.json',Path(temp)/'generic.json'
        def run(a,b):
            x.write_text(json.dumps(a,separators=(',',':')))
            y.write_text(json.dumps(b,separators=(',',':')))
            return audit(x,y)
        expected=run(primary,secondary)
        cases=[
            ('extra secondary row',None,lambda b:b['counts'].append(copy.deepcopy(b['counts'][0]))),
            ('missing secondary row',None,lambda b:b['counts'].pop()),
            ('bool zero count',lambda a:a['twist_cubic'].__setitem__('zero_rhs_x',False),None),
            ('float zero count',lambda a:a['twist_cubic'].__setitem__('zero_rhs_x',0.0),None),
            ('float field size',lambda a:a.__setitem__('field_size',float(a['field_size'])),None),
            ('wrong direct schema',lambda a:a.__setitem__('schema','spoof'),None),
            ('wrong secondary schema',None,lambda b:b.__setitem__('schema','spoof')),
            ('extra top key',lambda a:a.__setitem__('unverified_extra',1),None),
            ('extra count key',None,lambda b:b['counts'][0].__setitem__('unverified_extra',1)),
            ('mutated point count direct',lambda a:a['source_cubic'].__setitem__('points',a['source_cubic']['points']+1),None),
            ('mutated point count both',lambda a:a['source_cubic'].__setitem__('points',a['source_cubic']['points']+1),lambda b:b['counts'][0].__setitem__('n',b['counts'][0]['n']+1)),
            ('missing field',lambda a:a['source_cubic'].pop('nonsquare_x'),None),
            ('false producer standing',lambda a:a.__setitem__('producer_standing','pcc:verified'),None),
        ]
        rejected=[]
        for name,change_a,change_b in cases:
            a,b=copy.deepcopy(primary),copy.deepcopy(secondary)
            if change_a:change_a(a)
            if change_b:change_b(b)
            try:run(a,b)
            except (ValueError,KeyError,TypeError):rejected.append(name)
            else:raise RuntimeError('audit accepted mutation: '+name)
        if len(rejected)!=len(cases):raise RuntimeError('incomplete negative controls')
        print(json.dumps({'status':'producer-selftest-only',
             'mutations_rejected':len(rejected),'cases':rejected,
             'canonical_extension':expected['minimal_isogeny_extension_degree_over_F223']},
             sort_keys=True,separators=(',',':')))

if __name__=='__main__':
    run_tests(sys.argv[1],sys.argv[2])
