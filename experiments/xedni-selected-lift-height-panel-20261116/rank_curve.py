"""One isolated checked-Sage rank/generator arm; called by rank_panel.py."""
import json
import sys

from sage.all import EllipticCurve, QQ

A, B = map(QQ, sys.argv[1:])
E = EllipticCurve(QQ, [A, B])
rank = E.rank(proof=True)
generators = E.gens(proof=True)
print(json.dumps({"A": str(A), "B": str(B), "rank": int(rank),
                  "generators": [str(g) for g in generators],
                  "generator_heights": [str(g.height(precision=128, algorithm="pari")) for g in generators]},
                 sort_keys=True))
