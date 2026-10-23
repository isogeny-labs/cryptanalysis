"""Compare frozen and regularized D1407 rows in point-string coordinates."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

P=Path(__file__).resolve().parent
old=P/'data/exp11_class_walk_D1407_f6.json'
new=P/'regularized/data/exp11_class_walk_D1407_f6.json'

def rows(data):
    points=data['column_points']
    return [tuple(sorted((points[int(k)],int(v)) for k,v in row.items() if v))
            for row in data['relation_rows']]

def main():
    before=json.loads(old.read_text());after=json.loads(new.read_text())
    old_points=set(before['column_points']);new_points=set(after['column_points'])
    before_rows=Counter(rows(before));after_rows=Counter(rows(after))
    removed_rows=list((before_rows-after_rows).elements())
    added_rows=list((after_rows-before_rows).elements())
    assert len(old_points)==383 and len(new_points)==384
    assert new_points-old_points=={'(16 : 60 : 1)'} and not old_points-new_points
    assert not removed_rows and len(added_rows)==2
    assert all(any(point=='(16 : 60 : 1)' for point,_ in row) for row in added_rows)
    result={'status':'EXACT_TWO_ROW_REGULAR_BRANCH_REPAIR',
            'old_sha256':sha256(old.read_bytes()).hexdigest(),
            'new_sha256':sha256(new.read_bytes()).hexdigest(),
            'script_sha256':sha256((P/'compare_repair.py').read_bytes()).hexdigest(),
            'added_point':'(16 : 60 : 1)','removed_row_count':0,
            'added_rows':[[{'point':point,'coefficient':value} for point,value in row]
                          for row in added_rows],
            'old_full_rank':before['rank'],'new_full_rank':after['rank'],
            'candidate_id':None,'timing_claim':None}
    (P/'repair_delta.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'added_rows':len(added_rows),
                      'old_full_rank':before['rank'],'new_full_rank':after['rank']}))

if __name__=='__main__':main()
