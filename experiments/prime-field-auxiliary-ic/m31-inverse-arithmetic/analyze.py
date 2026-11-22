from pathlib import Path
import numpy as np

rows = np.loadtxt(Path(__file__).with_name("arm.csv"), dtype=int, delimiter=",")
assert rows.shape == (108, 3)
data = rows[np.lexsort((rows[:,1], rows[:,0]))].reshape(36, 3, 3)
assert np.all(data[:,:,0] == np.arange(36)[:,None])
assert np.all(data[:,:,1] == [0,1,2])
for offset in (0,1):
    ns = data[offset::2,:,2] / (64*2048)
    ratios = ns[:,1] / ns[:,2]
    indices = np.random.default_rng(291152).integers(0,len(ns),(10000,len(ns)))
    print("mixed zeros", bool(offset), "ns/element", np.median(ns,axis=0),
          "prefix/tree", np.median(ratios),
          "interval", np.quantile(np.median(ratios[indices],axis=1),[.025,.975]),
          "faster", np.count_nonzero(ratios>1))
