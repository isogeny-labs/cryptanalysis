extern "C" void repeat_inverse(const uint32_t *src, uint32_t *dst, size_t n, size_t count) {
    for (size_t i=0; i<count; ++i) {
        m31_batch_inverse(src+i*n,dst+i*n,n);
        asm volatile("" ::: "memory");
    }
}
