#define main inherited_bilinear_screen_main
#include "../n41_bilinear_rank_screen_20261013/native.cpp"
#undef main

struct Witness {u64 c;int family;};
struct CrossWitness {u64 value,c,d;int left_family,right_family;};

bool add_pivot(u64 value,std::array<u64,N>& pivots) {
  u64 reduced=value;
  for(int bit=N-1;bit>=0;bit--)if(reduced&(1ULL<<bit)) {
    if(pivots[bit])reduced^=pivots[bit];
    else {pivots[bit]=reduced;return true;}
  }
  return false;
}

int main(int argc,char**argv) {
  if(argc!=2)return 2;
  const u64 target=1000731834126ULL;
  std::array<u64,N> union_pivots{},cross_pivots{},pairing_pivots{};
  std::vector<Witness> union_basis;
  std::vector<CrossWitness> cross_basis;
  int family_count=0,coordinate_vectors=0,trace_failures=0;
  auto began=Clock::now();
  for(int family=0;family<2048;family++) {
    auto basis=family_basis(family);family_count++;
    for(u64 c:basis) {
      coordinate_vectors++;
      if(add_pivot(c,union_pivots))union_basis.push_back({c,family});
    }
  }
  for(auto left:union_basis)for(auto right:union_basis) {
    u64 z=mul(mul(target,left.c),right.c);
    u64 value=sq(z)^z;
    if(tr(value)!=0)trace_failures++;
    if(add_pivot(value,cross_pivots))
      cross_basis.push_back({value,left.c,right.c,left.family,right.family});
  }
  // Nondegeneracy of the concrete trace pairing in the selected field basis.
  for(int i=0;i<N;i++) {
    u64 row=0;
    for(int j=0;j<N;j++)if(tr(mul(1ULL<<i,1ULL<<j)))row|=1ULL<<j;
    assert(add_pivot(row,pairing_pivots));
  }
  assert(family_count==2048 && coordinate_vectors>=2048*6);
  assert(union_basis.size()==40 && cross_basis.size()==40);
  assert(trace_failures==0);
  std::ofstream output(argv[1]);assert(output.good());
  output<<"{\"status\":\"PASS_COMPLETE_N41_GLOBAL_CROSS_SPAN\",\"target_reciprocal\":"<<target
    <<",\"product_families\":"<<family_count<<",\"coordinate_basis_vectors_examined\":"<<coordinate_vectors
    <<",\"coordinate_union_rank\":"<<union_basis.size()
    <<",\"cross_span_rank\":"<<cross_basis.size()
    <<",\"trace_pairing_rank\":"<<N<<",\"trace_failures\":"<<trace_failures
    <<",\"union_basis\":[";
  for(size_t i=0;i<union_basis.size();i++) {
    auto w=union_basis[i];output<<(i?",":"")<<"["<<w.c<<","<<w.family<<"]";
  }
  output<<"],\"cross_basis\":[";
  for(size_t i=0;i<cross_basis.size();i++) {
    auto w=cross_basis[i];output<<(i?",":"")<<"["<<w.value<<","<<w.c<<","<<w.d<<","<<w.left_family<<","<<w.right_family<<"]";
  }
  output<<"]}\n";
  auto seconds=std::chrono::duration<double>(Clock::now()-began).count();
  std::cout<<"PASS_COMPLETE_N41_GLOBAL_CROSS_SPAN rank="<<cross_basis.size()
    <<" families="<<family_count<<" seconds="<<seconds<<"\n";
}
