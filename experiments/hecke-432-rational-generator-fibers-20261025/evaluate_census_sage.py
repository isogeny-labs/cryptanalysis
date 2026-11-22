"""Evaluate every rational-generator X0(432) class in the F883 census."""
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, sage_eval

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


moduli=load_module('quarter_shift_moduli',ROOT/'hecke-432-moduli-shift-evaluator-20261025'/'produce_sage.py')
bridge=load_module('quarter_shift_bridge',ROOT/'hecke-27-coordinate-bridge-20261025'/'evaluate_sage.py')


def evaluate(row, P_xy, maps, F, K, C, E, B):
    record={'prime':883,'field_degree':2,'curve_ainvs':row['curve_ainvs'],
            'generator':P_xy,'curve_order':864}
    mod=moduli.case(record, [])
    u=K.gen()
    points=[]
    coordinate_counts=[]
    for output in mod['outputs']:
        js=sage_eval(output['curve_j'],locals={'u':u})
        jt=sage_eval(output['level27_quotient_j'],locals={'u':u})
        _, candidates=bridge.roots_for_pair(C,maps,js,jt)
        coordinate_counts.append(len(candidates))
        if len(candidates)!=1:
            return {'status':'COORDINATE_FIBER_NOT_UNIQUE',
                    'coordinate_counts':coordinate_counts,'moduli':mod}
        points.append(candidates[0])
    plus,minus=points
    if plus == minus:
        return {'status':'ZERO_DIFFERENCE','coordinate_counts':coordinate_counts,'moduli':mod}
    assert plus[0]**883==minus[0] and plus[1]**883==minus[1]
    D=plus-minus
    i=sage_eval(mod['chosen_i'],locals={'u':u})
    xe,ye=-4*D[0],-8*i*(D[1]+K(1)/2)
    assert xe**883==xe and ye**883==ye
    H=E(F(xe),F(ye))
    preimages=bridge.dual_preimages(H,B,E)
    if len(preimages)!=1:
        return {'status':'DUAL_FIBER_NOT_UNIQUE','dual_fiber_size':len(preimages),
                'coordinate_counts':coordinate_counts,'moduli':mod}
    Q=preimages[0]
    assert bridge.dual_image(Q,E)==H
    return {'status':'PASS_FULL_FORWARD','coordinate_counts':coordinate_counts,
            'C_plus':[str(plus[0]),str(plus[1])],
            'C_minus':[str(minus[0]),str(minus[1])],
            'B_point':[int(Q[0]),int(Q[1])] if not Q.is_zero() else 'O',
            'moduli_j_pairs':[[o['curve_j'],o['level27_quotient_j']] for o in mod['outputs']]}


def main():
    census=json.loads((HERE/'class_census.json').read_text())
    maps=json.loads((ROOT/'hecke-27-coordinate-bridge-20261025'/'coordinate_map.json').read_text())
    assert census['status']=='COMPLETE_F883_CLASS_CENSUS'
    F=GF(883)
    K=GF(883**2,'u')
    C=EllipticCurve(K,maps['curve_ainvs'])
    E=EllipticCurve(F,[0,0,0,0,432])
    B=EllipticCurve(F,[0,0,0,0,-16])
    image={}
    rows=[]
    attempted=0
    for row in census['classes']:
        for P_xy in row['subgroup_generators']:
            attempted+=1
            result=evaluate(row,P_xy,maps,F,K,C,E,B)
            result.update({'input_j':row['j'],'input_twist':row['twist'],
                           'input_ainvs':row['curve_ainvs'],'input_generator':P_xy})
            rows.append(result)
            if result['status']=='PASS_FULL_FORWARD':
                key=str(result['B_point'])
                image[key]=image.get(key,0)+1
            print(f'{attempted}/{census["rational_order_432_subgroups"]} '
                  f'j={row["j"]} status={result["status"]}',flush=True)
    assert attempted==census['rational_order_432_subgroups']
    out={'status':'COMPLETE_RATIONAL_GENERATOR_FORWARD_CENSUS',
         'prime':883,'B_point_count':int(B.cardinality()),
         'rational_generator_subgroups_attempted':attempted,
         'forward_pass_count':sum(r['status']=='PASS_FULL_FORWARD' for r in rows),
         'distinct_B_images':len(image),'B_image_fiber_counts':image,
         'rows':rows}
    (HERE/'forward_census.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','B_point_count',
          'rational_generator_subgroups_attempted','forward_pass_count','distinct_B_images')},sort_keys=True))


if __name__=='__main__':
    main()
