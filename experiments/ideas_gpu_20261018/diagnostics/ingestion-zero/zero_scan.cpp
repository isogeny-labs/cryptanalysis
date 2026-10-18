// Independent diagnostic loop over retained binary records; no GPU calls.
#include "hostcheck.h"
#include <fstream>
#include <iostream>
using namespace ec2k_gpu;
int main(int argc,char**argv){if(argc!=2)return 2;std::ifstream f(argv[1],std::ios::binary);if(!f)return 2;HostWalk w;ec2k_pt p,q;challengePoints(&p,&q);w.build(p,q);DpRecord r{};size_t index=0,zeros=0;while(f.read(reinterpret_cast<char*>(&r),sizeof r)){if(r.iters==0){ec2k_pt pt{feOf(r.x),feOf(r.y),0};bool golden=rewalk(w,r,nullptr);std::cout<<"{\"index\":"<<index<<",\"seed\":"<<r.seed<<",\"run\":"<<(r.seed>>48)<<",\"iters\":0,\"weight\":"<<ec2k_fe_weight(&pt.x)<<",\"on_curve\":"<<(ec2k_on_curve(&pt)?"true":"false")<<",\"golden_start_matches\":"<<(golden?"true":"false")<<"}\n";if(!golden)return 1;zeros++;}index++;}if(!f.eof()||f.gcount())return 2;std::cout<<"{\"records\":"<<index<<",\"zero_count\":"<<zeros<<",\"all_zeros_replayed\":true}\n";return 0;}
