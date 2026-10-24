"""Save one private new-column witness per translated Hecke row."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def main():
    raw=(HERE/'result.json').read_bytes();data=json.loads(raw)
    new=set(data['new_column_indices']);rows=data['accepted_rows']
    counts=Counter(int(j) for row in rows for j,v in row['coefficients'].items()
                   if int(j) in new and v)
    witnesses=[]
    for i,row in enumerate(rows):
        private=sorted((int(j),v) for j,v in row['coefficients'].items()
                       if int(j) in new and v and counts[int(j)]==1)
        assert private
        column,coefficient=private[0]
        assert coefficient==1
        witnesses.append({'accepted_row_index':i,'full_row_index':len(data['base_rows'])+i,
                          'new_column_index':column,
                          'orbit_representative':data['column_representatives'][column],
                          'coefficient':coefficient})
    assert len(witnesses)==len(rows)==40
    assert len({r['new_column_index'] for r in witnesses})==40
    assert all(str(w['new_column_index']) not in row for row in data['base_rows']
               for w in witnesses)
    out={'status':'PRIVATE_NEW_COLUMN_WITNESS_FOR_EVERY_CROSS_CLASS_ROW',
         'result_sha256':sha256(raw).hexdigest(),
         'script_sha256':sha256((HERE/'certify_private.py').read_bytes()).hexdigest(),
         'witnesses':witnesses,'private_new_column_count':sum(v==1 for v in counts.values()),
         'candidate_id':None,'timing_claim':None}
    (HERE/'private_witness.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'witnesses':len(witnesses),
                      'private_new_columns':out['private_new_column_count']},sort_keys=True))

if __name__=='__main__':main()
