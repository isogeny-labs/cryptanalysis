"""Strong direct-pair control: batch inversion and global sign quotient."""
from itertools import combinations
from zero_fiber import canonical_pm


def inverses(values,p):
    prefixes=[];acc=1
    for value in values:
        prefixes.append(acc);acc=acc*value%p
    reciprocal=pow(acc,-1,p);result=[0]*len(values)
    for i in range(len(values)-1,-1,-1):
        result[i]=reciprocal*prefixes[i]%p
        reciprocal=reciprocal*values[i]%p
    return result


def zero_pairs(E,xs):
    p=E.p;points=[]
    for x in sorted(set(xs)):
        P=E.lift(x)
        if P is not None:points.append(P)
    allowed={x for x,y in points};relations=set()
    for i,(x,y) in enumerate(points):
        tail=points[i+1:]
        reciprocals=inverses([(xx-x)%p for xx,yy in tail],p)
        for (xx,yy),reciprocal in zip(tail,reciprocals):
            for sign in [1,-1]:
                slope=(sign*yy-y)*reciprocal%p
                third=(slope*slope-x-xx)%p
                # Each relation is generated once using its two smallest x's.
                if third<=xx or third not in allowed:continue
                P=(x,y);Q=(xx,sign*yy%p);R=(third,(y+slope*(third-x))%p)
                relation=canonical_pm(E,[P,Q,R])
                assert all(E.contains(T) for T in relation) and E.sum(relation) is None
                relations.add(relation)
    return relations
