#pragma once
#include <array>
#include <cstdint>

namespace m31_exceptional {
constexpr uint32_t modulus = 2147483647;
constexpr std::array<uint32_t,32> coordinates = {
    0, 1, 33359769, 139984982,
    177504693, 244425803, 321862516, 478064842,
    508369663, 637231878, 705231622, 746452052,
    849551769, 952675664, 1040047656, 1063718422,
    1174338953, 1516123271, 1575660783, 1623230299,
    1668578532, 1729373102, 1753716560, 1825752205,
    1903942232, 1948130974, 1965083199, 1983108407,
    2074043423, 2085125131, 2106326137, 2127360844
};
constexpr unsigned bucket(uint32_t x) { return (x ^ (x >> 4)) & 255; }
constexpr auto lookup = [] {
    std::array<uint32_t,256> table{};
    for (auto& slot : table) slot = modulus;
    for (auto x : coordinates) table[bucket(x)] = x;
    return table;
}();

constexpr bool contains(uint32_t x) { return x < modulus && lookup[bucket(x)] == x; }
static_assert([] {
    for (auto x : coordinates) if (!contains(x)) return false;
    return true;
}());
}
