#include <metal_stdlib>
using namespace metal;
#include "arithmetic.h"
kernel void certicom_add(constant CcCurve &c [[buffer(0)]],
                         device const CcPoint *a [[buffer(1)]],
                         device const CcPoint *b [[buffer(2)]],
                         device CcPoint *out [[buffer(3)]],
                         constant uint &n [[buffer(4)]],
                         uint i [[thread_position_in_grid]]) {
    if (i<n) out[i]=cc_point_add(c,a[i],b[i]);
}
kernel void certicom_mul(constant CcCurve &c [[buffer(0)]],
                         device const CcPoint *a [[buffer(1)]],
                         device const CcInteger *k [[buffer(2)]],
                         device CcPoint *out [[buffer(3)]],
                         constant uint &n [[buffer(4)]],
                         uint i [[thread_position_in_grid]]) {
    if (i<n) out[i]=cc_point_mul(c,a[i],k[i]);
}
kernel void certicom_rho(constant CcCurve &c [[buffer(0)]],
                         device const CcRho *in [[buffer(1)]],
                         device const uint *unused [[buffer(2)]],
                         device CcRho *out [[buffer(3)]],
                         constant uint &n [[buffer(4)]],
                         constant uint &steps [[buffer(5)]],
                         uint i [[thread_position_in_grid]]) {
    (void)unused;
    if (i<n) out[i]=cc_rho_advance(c,in[i],steps);
}
