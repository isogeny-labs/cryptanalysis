// Exact N131 W29 source-edge census for ten monomial half-trace seeds.
#define main archived_w23_geometry_main
#include "../../koblitz-s5-invariant-20260924/lowpoly_w23_geometry.cpp"
#undef main
#include <chrono>
#include <iostream>
#include <stdexcept>

int main() {
  try {
    const Fe trace = trace_mask();
    auto start = std::chrono::steady_clock::now();
    std::cout << "{\"status\":\"COMPLETE_MONOMIAL_PREFIX_SWEEP\",\"rows\":[";
    for (int k = 5; k <= 14; ++k) {
      const uint32_t seed = (1u << (k-1)) | (1u << (2*k-1));
      const int canonical = 2*k-1;
      uint64_t left=0,right=0,edges=0;
      uint32_t first=0,last=0;
      for (uint32_t index=0; index<(1u<<20); ++index) {
        uint32_t a=3, v=index;
        for (int bit=8; bit<29; ++bit) {
          if (bit==canonical) continue;
          a |= (v&1u)<<bit;
          v >>= 1;
        }
        if (v || (a&(1u<<canonical))) throw std::runtime_error("canonical mapping");
        uint32_t b=a^seed;
        if (a>=b || b>=(1u<<29) || (a&255)!=3)
          throw std::runtime_error("canonical masks");
        Fe wa{uint64_t(a)<<1,0,0}, wb{uint64_t(b)<<1,0,0};
        if (trace_bit(wa,trace) || trace_bit(wb,trace))
          throw std::runtime_error("source trace");
        Fe ia=inverse(wa), ib=inverse(wb);
        if (!(mul(wa,ia)==Fe{1,0,0}) || !(mul(wb,ib)==Fe{1,0,0}))
          throw std::runtime_error("inverse replay");
        bool va=!trace_bit(ia,trace), vb=!trace_bit(ib,trace);
        left+=va; right+=vb;
        if (va&&vb) {
          first=edges?first:a; last=a; ++edges;
        }
      }
      if (k>5) std::cout << ',';
      std::cout << "{\"k\":"<<k<<",\"seed_mask\":"<<seed
                <<",\"canonical_bit\":"<<canonical
                <<",\"canonical_masks\":1048576,\"inverse_checks\":2097152"
                <<",\"left_inverse_trace_zero\":"<<left
                <<",\"right_inverse_trace_zero\":"<<right
                <<",\"eligible_edges\":"<<edges
                <<",\"first_eligible\":"<<first
                <<",\"last_eligible\":"<<last<<'}' << std::flush;
    }
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    std::cout << "],\"self_wall_seconds\":"<<sec<<"}\n";
    return 0;
  } catch(const std::exception& e) {
    std::cerr << "ERROR " << e.what() << '\n'; return 2;
  }
}
