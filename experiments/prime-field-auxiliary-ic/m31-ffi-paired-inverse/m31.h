#ifndef M31_FIELD_FFI_H
#define M31_FIELD_FFI_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Reduce each input modulo 2^31-1 and write its inverse, mapping zero to zero.
   Buffers may be identical or disjoint. For count == 0 both may be null. */
void m31_batch_inverse(const uint32_t *input, uint32_t *output, size_t count);
/* Elementwise product modulo 2^31-1 for arbitrary uint32_t inputs.
   Each buffer may be identical to or disjoint from each other buffer.
   For count == 0 all pointers may be null. */
void m31_batch_multiply(const uint32_t *left, const uint32_t *right,
                        uint32_t *output, size_t count);
#ifdef __cplusplus
}
#endif
#endif
