"""Amortized GCD root extraction for a fixed, explicitly known factor base."""
from resultant_solver import nmod_poly,product_tree,signed_base


class KnownRootGCD:
    """Replace one large HGCD with remainder descent and small leaf GCDs.

    The product tree is built once per factor base. No target or pair sums
    enter preprocessing. Repeated roots are rejected after reduction modulo p.
    """
    def __init__(self,roots,p,block_size=256):
        self.p=p;self.roots=tuple(int(x)%p for x in roots)
        if not self.roots or len(set(self.roots))!=len(self.roots):
            raise ValueError('Distinct nonempty roots required')
        if block_size<1:raise ValueError('Positive block size required')
        blocks=[self.roots[i:i+block_size] for i in range(0,len(self.roots),block_size)]
        self.blocks=blocks
        self.levels=[[product_tree((nmod_poly([-x,1],p) for x in block),p) for block in blocks]]
        while len(self.levels[-1])>1:
            level=self.levels[-1]
            self.levels.append([level[i]*level[i+1] if i+1<len(level) else level[i]
                                for i in range(0,len(level),2)])
        self.polynomial=self.levels[-1][0]
        self.membership_polynomial=self.polynomial
        self.liftable_only=False
        self.curve=None

    @classmethod
    def for_model(cls,model,roots,block_size=256):
        """Discard coordinates that cannot represent rational target points.

        This is target-independent preparation. Every actual point relation
        uses liftable coordinates, including at degenerate S3 specializations.
        """
        points=signed_base(model,roots)
        plan=cls(sorted({x for x,y in points}),model.curve['p'],block_size)
        plan.membership_polynomial=model.polynomial
        plan.liftable_only=True
        plan.curve=dict(model.curve)
        return plan

    def candidates(self,resultant):
        if resultant.modulus()!=self.p:raise ValueError('Polynomial field mismatch')
        remainders=[resultant%self.polynomial]
        for level in reversed(self.levels[:-1]):
            remainders=[remainders[i//2]%poly for i,poly in enumerate(level)]
        roots=set()
        for block,poly,remainder in zip(self.blocks,self.levels[0],remainders):
            if not remainder:roots.update(block)
            elif remainder.degree()>0:
                roots.update(int(x) for x,_ in poly.gcd(remainder).roots())
        return roots
