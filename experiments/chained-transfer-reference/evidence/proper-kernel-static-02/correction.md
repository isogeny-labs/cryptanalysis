# Sum-table index correction before attempt02

The original native even_kernel_certificates.rs builds kernel_sum_indices
from point_indices of the complete49-point E7 list,not from positions in
its seven kernel rows. Attempt01/f0c793 retained the incorrect local-index
assumption and failed the positive original record. Attempt02 requires
next<49 AND actual membership in the seven-point kernel,then compares
actual Cantor sums to pulls[next]. All49 table checks remain required.
No producer field,cryptographic formula or acceptance criterion changed.
StrictClippy02 passes. No functional02 result yet. [pcc:unverified]
