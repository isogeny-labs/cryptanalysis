"""Small independent arithmetic and information-accounting correctness controls."""
import unittest
from flint import nmod_poly as Poly
from modular import Curve,Field,extension_trace
from study import BSGS,reduced
from verify import ShortCurve,rank


class CoreTests(unittest.TestCase):
    def test_known_torsion_and_independent_short_model(self):
        curve=Curve(367);other=ShortCurve(367);P=(5,5)
        expected=[None,(5,5),(16,306),(16,60),(5,361),None]
        self.assertEqual([curve.mul(k,P) for k in range(6)],expected)
        for k,value in enumerate(expected):self.assertEqual(other.original(other.times(k,other.point(P))),value)

    def test_nonrational_quadratic_orbit_trace(self):
        # In F7[i], i²=-1: P=(i,2+2i), P+Frob(P)=(5,1).
        result=extension_trace(Poly([0,1],7),Poly([2,2],7),Poly([1,0,1],7),7)
        self.assertEqual(result,(5,1))
        self.assertTrue(Curve(7).contains(result))

    def test_eliminating_new_columns(self):
        # x+y=0 and y-z=0 constrain old coordinates x,z by x+z=0.
        rows=[{0:1,2:1},{1:-1,2:1}]
        full=len(reduced(rows,3,11)[1]);new=len(reduced([{0:1},{0:1}],1,11)[1])
        self.assertEqual((full,new,full-new),(2,1,1))
        self.assertEqual(rank(rows,3,11),2)

    def test_reusable_bsgs_and_character_count(self):
        curve=Curve(367);P=(5,5);solver=BSGS(curve,P,5)
        self.assertEqual([solver.log(curve.mul(k,P)) for k in range(5)],list(range(5)))
        self.assertEqual(Field(367).curve_order(),385)


if __name__=='__main__':unittest.main()
