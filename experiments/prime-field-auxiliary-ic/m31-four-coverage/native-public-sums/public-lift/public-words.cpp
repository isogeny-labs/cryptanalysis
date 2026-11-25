#include <charconv>
#include <cstdint>
#include <cstring>

#if defined(__APPLE__) && !defined(M31_USE_OPENSSL)
#include <CommonCrypto/CommonDigest.h>
#else
#include <openssl/evp.h>
#include <memory>
#endif

// Hash prefix || decimal(counter) and return the first big-endian word
// with the top bit cleared. Callers handle the noncanonical word 2^31-1.
// On failure the caller must discard the batch. Prefix length is in bytes.
extern "C" int public_words(const char *prefix, size_t length, uint64_t start,
                            size_t count, uint32_t *out) {
    char message[128];
    constexpr size_t counter_digits = 20;
    if (length > sizeof(message) - counter_digits || (length && !prefix) ||
        (count && (!out || count - 1 > UINT64_MAX - start))) return -1;
    if (!count) return 0;

    if (length) std::memcpy(message, prefix, length);
#if !defined(__APPLE__) || defined(M31_USE_OPENSSL)
    std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)> ctx(EVP_MD_CTX_new(), EVP_MD_CTX_free);
    if (!ctx) return -1;
#endif
    for (size_t i = 0; i < count; ++i) {
        const auto end = std::to_chars(message + length, message + sizeof(message), start + i);
        const size_t size = static_cast<size_t>(end.ptr - message);
        unsigned char digest[32];
#if defined(__APPLE__) && !defined(M31_USE_OPENSSL)
        if (!CC_SHA256(message, static_cast<CC_LONG>(size), digest)) return -1;
#else
        if (!EVP_DigestInit_ex(ctx.get(), EVP_sha256(), nullptr) ||
            !EVP_DigestUpdate(ctx.get(), message, size) ||
            !EVP_DigestFinal_ex(ctx.get(), digest, nullptr)) return -1;
#endif
        out[i] = (uint32_t(digest[0] & 127) << 24) | (uint32_t(digest[1]) << 16) |
                 (uint32_t(digest[2]) << 8) | digest[3];
    }
    return 0;
}
