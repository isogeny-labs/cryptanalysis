#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Canonical M31 input and output. Either input may exactly alias out.
   Partial overlap is unsupported. For n=0 all pointers may be null. */
void m31_products(const uint32_t *a, const uint32_t *b, uint32_t *out, size_t n);
#ifdef __cplusplus
}
#endif
