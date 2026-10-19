// Concatenate arithmetic.h before this file when compiling with NVRTC.
#ifndef CERTICOM_ARITHMETIC_H
#include "arithmetic.h"
#endif
extern "C" __global__ void certicom_add(CcCurve c,const CcPoint *a,
                                        const CcPoint *b,CcPoint *out,unsigned n) {
    unsigned i=blockIdx.x*blockDim.x+threadIdx.x;
    if (i<n) out[i]=cc_point_add(c,a[i],b[i]);
}
extern "C" __global__ void certicom_mul(CcCurve c,const CcPoint *a,
                                        const CcInteger *k,CcPoint *out,unsigned n) {
    unsigned i=blockIdx.x*blockDim.x+threadIdx.x;
    if (i<n) out[i]=cc_point_mul(c,a[i],k[i]);
}
extern "C" __global__ void certicom_rho(CcCurve c,const CcRho *in,
                                        CcRho *out,unsigned n,unsigned steps) {
    unsigned i=blockIdx.x*blockDim.x+threadIdx.x;
    if (i<n) out[i]=cc_rho_advance(c,in[i],steps);
}
