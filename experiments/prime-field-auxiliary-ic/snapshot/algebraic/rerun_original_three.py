"""Reproduce the original positive three-point fixture with both encodings."""
import json
from resultant_solver import ROOT,prepare,solve_three,signed_base


def main():
    source=ROOT/'benchmarks/field31_s10_m3_seed0/case.json'
    case=json.loads(source.read_text())
    folder=ROOT/'structure_results/original_three_point_case'
    folder.mkdir(parents=True,exist_ok=True)
    manifest=dict(curve=case['curve'],target=case['target'],roots=case['structured_roots'],
                  auxiliary=case['auxiliary'],
                  note='historical known-positive fixture; identical base/target for both encodings')
    (folder/'case.json').write_text(json.dumps(manifest,indent=2)+'\n')
    answers=[]
    for encoding in ['chain','expanded']:
        model=prepare(case['curve'],auxiliary=case['auxiliary'],roots=case['structured_roots'],encoding=encoding)
        points=signed_base(model,case['structured_roots'])
        answer=solve_three(model,case['target'],points)
        output=folder/encoding;output.mkdir(exist_ok=True)
        (output/'result.json').write_text(json.dumps(answer,indent=2)+'\n')
        answers.append(answer)
        print(json.dumps(answer),flush=True)
    assert answers[0]['relations']==answers[1]['relations']
    assert answers[0]['two_sum_calls']==answers[1]['two_sum_calls']


if __name__=='__main__':main()
