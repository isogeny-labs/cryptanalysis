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
#ifdef __cplusplus
}
#endif
#endif
