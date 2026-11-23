#ifndef M31_CHECKED_ROOT_H
#define M31_CHECKED_ROOT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif
/* Each input is in [0, 2147483647). Output is the smaller square root,
 * or 2147483647 for a nonsquare. Buffers may coincide or be disjoint.
 * A count of zero accepts null pointers. */
void m31_checked_roots(const uint32_t* input, uint32_t* output, size_t count);
#ifdef __cplusplus
}
#endif
#endif
