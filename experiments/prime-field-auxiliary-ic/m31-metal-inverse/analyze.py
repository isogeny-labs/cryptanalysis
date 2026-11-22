from pathlib import Path
import numpy as np

rows = np.loadtxt(Path(__file__).with_name("rows.csv"),delimiter=",")
assert rows.shape == (18*6*3,5)
for n in np.unique(rows[:,1]):
    group = rows[rows[:,1] == n]
    data = group[np.lexsort((group[:,2],group[:,0]))].reshape(18,3,5)
    assert np.all(data[:,:,0] == np.arange(18)[:,None])
    assert np.all(data[:,:,2] == [0,1,2])
    wall = data[:,:,3]
    gpu = data[:,1:,4]
    assert np.all(wall>0) and np.all(gpu>0)
    ratios = wall[:,0]/wall[:,2]
    draws = np.random.default_rng(291156).integers(0,18,(10000,18))
    print(int(n),"wall us",np.round(np.median(wall,axis=0)*1e6,2),
          "device us",np.round(np.median(gpu,axis=0)*1e6,2),
          "CPU/batch8",round(np.median(ratios),3),
          "interval",np.round(np.quantile(np.median(ratios[draws],axis=1),[.025,.975]),3))
