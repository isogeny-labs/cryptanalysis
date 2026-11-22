# Pointwise M31 products through a C ABI

m31_products accepts two arrays of canonical residues and writes their elementwise products. product.h specifies pointer and overlap requirements. The native ARM implementation uses four low-word products and four signed doubling high products per vector instruction pair. The maximum doubled product is below 2⁶³. The high word therefore gives floor(ab/2³¹). The residual sum is reduced with unsigned minimum and wrapping subtraction. Product.lean proves the high-word and final reduction identities. The one-fold identity and sum bound are in ../m31-field-ffi/Fold.lean. Non-ARM builds use the portable implementation.

Run python3 panel.py on the M4 Pro to compile and check the portable, widening and high-multiply paths. It checks exact aliasing on either side, zero length, vector tails, boundary values and random pairs against Python integer remainder. The C timer calls separately compiled functions with resident buffers. Block-level paired comparisons use six orders repeated six times. Times exclude Python dispatch and buffer construction.

| Size | First high-multiply ns/product | Repeat ns/product | Median widening/high, first | Repeat |
|---:|---:|---:|---:|---:|
| 32 | 0.1221 | 0.1211 | 1.2344 | 1.2441 |
| 4096 | 0.0982 | 0.0982 | 1.4951 | 1.4951 |

A separate direct ctypes check with already converted pointers included Python call and loop overhead. Median per-call times (widening/high) were 366.8/367.5 ns at 32 elements and 1018.6/831.1 ns at 4096. These descriptive measurements used 24 alternating-order pairs of 4096 calls and one shared host. Native assembly contains sqdmulh.4s and umin.4s. This panel measures general field products only.
