#include "region_core.hpp"

int main(int argc,char**argv) {
  if(argc!=2)return 2;
  std::vector<std::vector<u64>> families(4);
  for(int p=0;p<4;p++)families[p]=family_basis(p);
  auto basis=region_basis(families,2,0);
  auto result=screen(basis,basis,1000731834126ULL);
  assert(basis.size()==19 && result.cross_rank==40 && result.consistent);
  std::ofstream output(argv[1]);assert(output.good());
  output<<"{\"status\":\"PASS_EXCEPTIONAL_FOUR_FAMILY_REGION\",\"product_codes\":[0,1,2,3]"
    <<",\"output_union_rank\":"<<basis.size()<<",\"cross_rank\":"<<result.cross_rank
    <<",\"target_span_consistent\":true,\"target_reciprocal\":1000731834126}\n";
  std::cout<<"PASS_EXCEPTIONAL_FOUR_FAMILY_REGION cross_rank="<<result.cross_rank<<"\n";
}
