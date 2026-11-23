#include <ctime>
int main() {
  constexpr size_t n=1u<<20;
  std::mt19937 rng(4315);
  std::vector<Word> x(n),reference(n),out(n);
  for (auto& k:x) k=1+rng()%(prime-1);
  classify<false,Fold::minimum>(x,reference,nullptr);
  std::puts("round,position,signed,wall_ms,cpu_ms");
  for (int r=0;r<16;++r) for (int pos=0;pos<2;++pos) {
    bool sign=(pos+r)%2;
    auto start=std::chrono::steady_clock::now();
    auto cpu=std::clock();
    for (int k=0;k<4;++k) {
      if (sign) classify<false,Fold::signedFold>(x,out,nullptr);
      else classify<false,Fold::minimum>(x,out,nullptr);
      asm volatile("" : : "r"(out.data()) : "memory");
    }
    auto ticks=std::clock()-cpu;
    double wall=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    if (out!=reference) return 2;
    std::printf("%d,%d,%d,%.6f,%.6f\n",r,pos,int(sign),wall,1000.0*ticks/CLOCKS_PER_SEC);
  }
}
