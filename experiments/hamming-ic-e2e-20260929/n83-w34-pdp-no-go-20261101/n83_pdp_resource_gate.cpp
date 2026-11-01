#include <algorithm>
#include <cstdint>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

using u128 = unsigned __int128;

struct Factor {
    std::string prime;
    unsigned exponent;
    std::string witness;
};

struct PrimeCertificate {
    std::string value;
    std::vector<Factor> factors_of_value_minus_one;
};

u128 parse(const std::string &decimal) {
    u128 value = 0;
    for (char digit : decimal) {
        if (digit < '0' || digit > '9') {
            throw std::runtime_error("non-decimal integer");
        }
        value *= 10;
        value += digit - '0';
    }
    return value;
}

u128 gcd(u128 left, u128 right) {
    while (right != 0) {
        u128 remainder = left % right;
        left = right;
        right = remainder;
    }
    return left;
}

u128 addmod(u128 left, u128 right, u128 modulus) {
    // Both inputs are reduced.  This form cannot overflow even near 2^128.
    return left >= modulus - right ? left - (modulus - right) : left + right;
}

u128 mulmod(u128 left, u128 right, u128 modulus) {
    u128 result = 0;
    left %= modulus;
    while (right > 0) {
        if ((right & 1) != 0) result = addmod(result, left, modulus);
        left = addmod(left, left, modulus);
        right >>= 1;
    }
    return result;
}

u128 powmod(u128 base, u128 exponent, u128 modulus) {
    u128 result = 1;
    base %= modulus;
    while (exponent > 0) {
        if ((exponent & 1) != 0) {
            result = mulmod(result, base, modulus);
        }
        base = mulmod(base, base, modulus);
        exponent >>= 1;
    }
    return result;
}

bool small_prime(std::uint64_t value) {
    if (value < 2) return false;
    for (std::uint64_t divisor = 2; divisor * divisor <= value; ++divisor) {
        if (value % divisor == 0) return value == divisor;
    }
    return true;
}

u128 power(u128 base, unsigned exponent) {
    u128 result = 1;
    for (unsigned i = 0; i < exponent; ++i) result *= base;
    return result;
}

void verify_prime_certificate(
    const std::string &value_key,
    const std::map<std::string, PrimeCertificate> &certificates,
    std::map<std::string, bool> &verified) {
    if (verified[value_key]) return;
    const u128 value = parse(value_key);
    if (value <= 109) {
        const auto word = static_cast<std::uint64_t>(value);
        if (!small_prime(word)) throw std::runtime_error("small factor is not prime");
        verified[value_key] = true;
        return;
    }
    const auto found = certificates.find(value_key);
    if (found == certificates.end()) throw std::runtime_error("missing Pocklington node");
    u128 product = 1;
    for (const Factor &factor : found->second.factors_of_value_minus_one) {
        verify_prime_certificate(factor.prime, certificates, verified);
        const u128 prime = parse(factor.prime);
        product *= power(prime, factor.exponent);
        const u128 witness = parse(factor.witness);
        if (powmod(witness, value - 1, value) != 1) {
            throw std::runtime_error("Fermat condition failed");
        }
        u128 residue = powmod(witness, (value - 1) / prime, value) - 1;
        if (gcd(residue, value) != 1) {
            throw std::runtime_error("Pocklington gcd condition failed");
        }
    }
    if (product != value - 1) {
        throw std::runtime_error("factorization of n-1 is incomplete");
    }
    // Complete factorization gives F=n-1>sqrt(n), the strict Pocklington bound.
    if (product <= value / product) {
        throw std::runtime_error("Pocklington product is too small");
    }
    verified[value_key] = true;
}

u128 choose_with_repetition(u128 base_size, unsigned count) {
    u128 result = 1;
    for (unsigned i = 1; i <= count; ++i) {
        result *= base_size + i - 1;
        result /= i;
    }
    return result;
}

u128 ceil_div(u128 numerator, u128 denominator) {
    return (numerator + denominator - 1) / denominator;
}

std::string decimal(u128 value) {
    if (value == 0) return "0";
    std::string out;
    while (value > 0) {
        out.push_back(static_cast<char>('0' + value % 10));
        value /= 10;
    }
    std::reverse(out.begin(), out.end());
    return out;
}

}  // namespace

int main() {
    const std::string subgroup_order_decimal = "2417851639230796216685689";
    const u128 subgroup_order = parse(subgroup_order_decimal);
    const u128 base_size = 423964;
    const u128 folded_columns = 2554;
    const u128 signed_frobenius_orbit_ceiling = 166;
    const u128 memory_bytes = 2147483648ULL;
    const u128 optimistic_entry_bytes = 16;
    const u128 concrete_triple_test_cap = parse("300000000000");

    const std::map<std::string, PrimeCertificate> certificates = {
        {"5051", {"5051", {{"2", 1, "2"}, {"5", 2, "2"}, {"101", 1, "2"}}}},
        {"11119", {"11119", {{"2", 1, "3"}, {"3", 1, "2"}, {"17", 1, "2"}, {"109", 1, "3"}}}},
        {"19395841", {"19395841", {{"2", 8, "7"}, {"3", 1, "2"}, {"5", 1, "2"}, {"5051", 1, "2"}}}},
        {"1012327725929069161", {"1012327725929069161", {
            {"2", 3, "7"}, {"3", 2, "2"}, {"5", 1, "2"}, {"13", 1, "2"},
            {"17", 1, "2"}, {"59", 1, "2"}, {"11119", 1, "2"}, {"19395841", 1, "2"}}}},
        {subgroup_order_decimal, {subgroup_order_decimal, {
            {"2", 3, "17"}, {"3", 1, "2"}, {"11", 1, "2"}, {"83", 1, "2"},
            {"109", 1, "2"}, {"1012327725929069161", 1, "2"}}}},
    };
    std::map<std::string, bool> verified;
    verify_prime_certificate(subgroup_order_decimal, certificates, verified);

    const u128 pair_multisets = choose_with_repetition(base_size, 2);
    const u128 five_multisets = choose_with_repetition(base_size, 5);
    const u128 expected_five_multisets = parse("114149470796697230602971808");
    if (five_multisets != expected_five_multisets) {
        throw std::runtime_error("five-sum geometry mismatch");
    }
    const u128 pair_state_loops = 83 * folded_columns * folded_columns;
    if (pair_state_loops != 541402028) {
        throw std::runtime_error("folded pair-state count mismatch");
    }

    const u128 resident_entry_cap = memory_bytes / optimistic_entry_bytes;
    const u128 represented_pairs_by_memory = std::min(
        pair_multisets,
        resident_entry_cap * signed_frobenius_orbit_ceiling);
    const u128 bounded_join_numerator = represented_pairs_by_memory * concrete_triple_test_cap;
    const u128 all_pairs_join_numerator = pair_multisets * concrete_triple_test_cap;
    const bool bounded_join_below_half = 2 * bounded_join_numerator < subgroup_order;
    const bool all_pairs_join_below_half = 2 * all_pairs_join_numerator < subgroup_order;
    if (!bounded_join_below_half || !all_pairs_join_below_half) {
        throw std::runtime_error("pair/triple admission bound unexpectedly passed");
    }

    const u128 triple_tests_for_half_with_memory =
        ceil_div(subgroup_order, 2 * represented_pairs_by_memory);
    const u128 triple_tests_for_half_with_all_pairs =
        ceil_div(subgroup_order, 2 * pair_multisets);
    const u128 concrete_pairs_needed_at_test_cap =
        ceil_div(subgroup_order, 2 * concrete_triple_test_cap);
    const u128 pair_orbit_entries_needed_at_test_cap =
        ceil_div(concrete_pairs_needed_at_test_cap, signed_frobenius_orbit_ceiling);

    // A planted control can always be made to pass: choose one stored pair and one
    // scheduled triple, define T as their sum, and replay those five points.  For a
    // uniform target the same single comparison covers at most one pair orbit, i.e.
    // at most 166 concrete target values.
    const u128 planted_control_comparisons = 1;
    const u128 planted_control_uniform_target_numerator = signed_frobenius_orbit_ceiling;

    std::cout
        << "{\n"
        << "  \"schema_version\": 1,\n"
        << "  \"kind\": \"n83_w34_five_sum_predata_resource_gate_result\",\n"
        << "  \"status\": \"NO_GO_CERTIFIED_FOR_FROZEN_FAMILIES\",\n"
        << "  \"experiment_admitted\": false,\n"
        << "  \"curve_id\": \"EC1N83Ckb1h2bcb59d56ad6\",\n"
        << "  \"subgroup_order\": \"" << decimal(subgroup_order) << "\",\n"
        << "  \"subgroup_order_prime_pocklington\": true,\n"
        << "  \"quotient_separator\": {\n"
        << "    \"proper_nontrivial_subgroup_exists\": false,\n"
        << "    \"reason\": \"prime-order cyclic subgroup: a quotient homomorphism is injective or trivial\"\n"
        << "  },\n"
        << "  \"geometry\": {\n"
        << "    \"usable_projected_points_B\": " << decimal(base_size) << ",\n"
        << "    \"folded_columns_K\": " << decimal(folded_columns) << ",\n"
        << "    \"signed_frobenius_orbit_ceiling\": " << decimal(signed_frobenius_orbit_ceiling) << ",\n"
        << "    \"pair_multisets\": \"" << decimal(pair_multisets) << "\",\n"
        << "    \"five_multisets\": \"" << decimal(five_multisets) << "\",\n"
        << "    \"pair_state_loops_83K2\": \"" << decimal(pair_state_loops) << "\"\n"
        << "  },\n"
        << "  \"resource_gate\": {\n"
        << "    \"memory_bytes\": \"" << decimal(memory_bytes) << "\",\n"
        << "    \"optimistic_pair_certificate_bytes\": \"" << decimal(optimistic_entry_bytes) << "\",\n"
        << "    \"resident_pair_orbit_entry_cap\": \"" << decimal(resident_entry_cap) << "\",\n"
        << "    \"represented_concrete_pair_cap\": \"" << decimal(represented_pairs_by_memory) << "\",\n"
        << "    \"concrete_triple_test_cap\": \"" << decimal(concrete_triple_test_cap) << "\",\n"
        << "    \"bounded_join_success_upper_numerator\": \"" << decimal(bounded_join_numerator) << "\",\n"
        << "    \"bounded_join_success_upper_denominator\": \"" << decimal(subgroup_order) << "\",\n"
        << "    \"bounded_join_below_one_half\": true,\n"
        << "    \"all_pairs_join_success_upper_numerator\": \"" << decimal(all_pairs_join_numerator) << "\",\n"
        << "    \"all_pairs_join_success_upper_denominator\": \"" << decimal(subgroup_order) << "\",\n"
        << "    \"all_pairs_join_below_one_half\": true,\n"
        << "    \"triple_tests_needed_for_half_with_memory_cap\": \"" << decimal(triple_tests_for_half_with_memory) << "\",\n"
        << "    \"triple_tests_needed_for_half_with_all_pairs\": \"" << decimal(triple_tests_for_half_with_all_pairs) << "\",\n"
        << "    \"concrete_pairs_needed_for_half_at_test_cap\": \"" << decimal(concrete_pairs_needed_at_test_cap) << "\",\n"
        << "    \"pair_orbit_entries_needed_for_half_at_test_cap\": \"" << decimal(pair_orbit_entries_needed_at_test_cap) << "\"\n"
        << "  },\n"
        << "  \"positive_control_sanity\": {\n"
        << "    \"constructible\": true,\n"
        << "    \"scheduled_pair_triple_comparisons\": \"" << decimal(planted_control_comparisons) << "\",\n"
        << "    \"uniform_target_success_upper_numerator_for_same_single_comparison\": \"" << decimal(planted_control_uniform_target_numerator) << "\",\n"
        << "    \"uniform_target_success_upper_denominator_for_same_single_comparison\": \"" << decimal(subgroup_order) << "\",\n"
        << "    \"interpretation\": \"a deterministic planted pass would validate arithmetic and replay only, not ordinary-query coverage\"\n"
        << "  },\n"
        << "  \"claim_boundary\": \"Certified for exact quotient separators and explicit target-independent pair-certificate/concrete-triple joins under the frozen envelope. It is not a proof that no structured non-generic algebraic PDP exists.\"\n"
        << "}\n";
}
