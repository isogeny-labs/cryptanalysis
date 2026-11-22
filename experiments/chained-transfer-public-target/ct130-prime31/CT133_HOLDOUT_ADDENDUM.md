# CT133 prospective holdout repair — 2026-11-15

[pcc:unverified]. Initial frozen seeds 20261201–20261204 ran locally: min(source BSGS, source neg rho)/target GLV rho = 1.38138, 1.56662, 1.48754, 1.28952. **Evidence defect:** each raw row contains known scalar k, not recovered solver scalar; the code checks equality internally but an independent verifier cannot recheck recovery from the raw record. These files remain exploratory and unadmitted, with their original hashes preserved.

**Frozen amendment BEFORE remeasurement:** each row now writes known_k **and** recovered_k with public x,y, ns, EC additions/inversions, iterations/cycles/table width. Independently recompute all public scalar multiples, mapping, source scalar verification, 64 distinct Q and all 384 ordered runs/panel; reject tampering under normal and -O Python. No case removal.

**Fresh preregistered seeds:** 20261210, 20261211, 20261212, 20261213, each 64 targets; otherwise identical original CT133 C++17 -O3, cold ABCCBA/CBAABC, group and verification overhead. Retain earlier four sample files without relabeling them. Report all ratios and uncertainty.

Still not a strongest rho/IC/full 701-Jacobian comparison, execution PCC, or general ECDLP speedup. No paid compute.
