#define _POSIX_C_SOURCE 200809L
#include <time.h>
#include "product.h"

uint64_t timed_products(const uint32_t *a,const uint32_t *b,uint32_t *out,size_t n,size_t reps) {
    struct timespec start,stop;
    clock_gettime(CLOCK_MONOTONIC,&start);
    for(size_t i=0;i<reps;++i) m31_products(a,b,out,n);
    clock_gettime(CLOCK_MONOTONIC,&stop);
    return (uint64_t)(stop.tv_sec-start.tv_sec)*1000000000 + stop.tv_nsec-start.tv_nsec;
}
