// Exact N131 W20 target-conditioned source norm using NTL GF2EX.
#include "../n131_w20_paired_raw_quotient_20261016/field.hpp"
#include <NTL/GF2E.h>
#include <NTL/GF2EX.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <sys/resource.h>
#include <tuple>
#include <vector>

using Clock = std::chrono::steady_clock;
using NTL::GF2E;
using NTL::GF2EX;
using NTL::GF2X;

constexpr unsigned SEED = 898618;

double seconds(Clock::time_point a, Clock::time_point b) {
    return std::chrono::duration<double>(b-a).count();
}

unsigned code_of(unsigned a) {
    constexpr unsigned pivot=19;
    return (a&((1u<<pivot)-1))|((a>>(pivot+1))<<pivot);
}

GF2E ntl(Fe value) {
    GF2X x;
    for(int i=0;i<131;++i)if(bit(value,i))NTL::SetCoeff(x,i);
    return NTL::to_GF2E(x);
}

GF2EX product_tree(std::vector<GF2EX> layer) {
    if(layer.empty())return GF2EX(1);
    while(layer.size()>1) {
        std::vector<GF2EX> next;
        next.reserve((layer.size()+1)/2);
        for(size_t i=0;i<layer.size();i+=2) {
            if(i+1<layer.size())next.push_back(layer[i]*layer[i+1]);
            else next.push_back(std::move(layer[i]));
        }
        layer.swap(next);
    }
    return std::move(layer[0]);
}

struct Source {
    unsigned code;
    GF2E p,q;
};

int main(int argc,char**argv) {
  try {
    if(argc!=8)throw std::runtime_error("usage: block_norm_resume support.tsv coefficients.tsv selected_count block_size target_index begin_block end_block");
    auto process_start=Clock::now();
    GF2X modulus;
    for(int i:{0,1,2,13,131})NTL::SetCoeff(modulus,i);
    GF2E::init(modulus);
    Field field(131);
    std::ifstream input(argv[1]);
    if(!input)throw std::runtime_error("missing support");
    std::vector<int> col(1u<<20,-1);
    unsigned mask,column,shift,rows=0;
    while(input>>mask>>column>>shift) {
      if(mask>=col.size()||col[mask]!=-1)throw std::runtime_error("bad support row");
      col[mask]=int(column);++rows;
    }
    if(rows!=524493)throw std::runtime_error("support count");
    std::vector<std::pair<unsigned,unsigned>> valid;
    for(unsigned a=0;a<col.size();++a) {
      unsigned b=a^SEED;
      if(a<b&&col[a]>=0&&col[b]>=0&&col[a]!=col[b])valid.emplace_back(code_of(a),a);
    }
    std::sort(valid.begin(),valid.end());
    if(valid.size()!=132045)throw std::runtime_error("valid count");
    for(size_t i=1;i<valid.size();++i)
      if(valid[i-1].first==valid[i].first)throw std::runtime_error("duplicate code");
    unsigned n=std::stoul(argv[3]);
    if(n<2||n>valid.size())throw std::runtime_error("selected count");
    unsigned block_size=std::stoul(argv[4]);
    unsigned requested_target=std::stoul(argv[5]);
    if(requested_target>1)throw std::runtime_error("target index");
    unsigned begin_block=std::stoul(argv[6]),end_block=std::stoul(argv[7]);
    unsigned total_blocks=(n+block_size-1)/block_size;
    if(begin_block>=end_block||end_block>total_blocks)throw std::runtime_error("block interval");
    if(block_size<1||block_size>n)throw std::runtime_error("block size");
    std::vector<std::pair<unsigned,unsigned>> chosen(valid.begin(),valid.begin()+n);
    auto positive=std::lower_bound(chosen.begin(),chosen.end(),std::pair<unsigned,unsigned>{16722,0});
    if(positive==chosen.end()||positive->first!=16722) {
      auto all=std::lower_bound(valid.begin(),valid.end(),std::pair<unsigned,unsigned>{16722,0});
      if(all==valid.end()||all->first!=16722)throw std::runtime_error("positive code absent");
      chosen.back()=*all;
      std::sort(chosen.begin(),chosen.end());
    }
    if(chosen.front().first!=3)throw std::runtime_error("first code");
    std::vector<Source> source;
    source.reserve(n);
    std::set<std::tuple<uint64_t,uint64_t,uint64_t>> unique_p;
    for(auto [code,a]:chosen) {
      Fe p=field.mul(decimal(std::to_string(a<<1)),decimal(std::to_string((a^SEED)<<1)));
      Fe q=p;
      for(int i=0;i<18;++i)q=field.sq(q);
      if(!unique_p.emplace(p.lo,p.mid,p.hi).second)throw std::runtime_error("product collision");
      source.push_back(Source{code,ntl(p),ntl(q)});
    }
    auto source_ready=Clock::now();
    std::vector<GF2EX> linear;
    linear.reserve(n);
    for(const auto& item:source) {
      GF2EX f;
      NTL::SetCoeff(f,1,NTL::to_GF2E(GF2X(1)));
      NTL::SetCoeff(f,0,item.p);
      linear.push_back(std::move(f));
    }
    GF2EX vanisher=product_tree(std::move(linear));
    if(NTL::deg(vanisher)!=int(n))throw std::runtime_error("vanisher degree");
    auto vanisher_ready=Clock::now();
    std::ifstream coeffs(argv[2]);
    if(!coeffs)throw std::runtime_error("missing coefficients");
    std::cout << "SOURCE " << n << " " << valid.size() << " "
              << seconds(process_start,source_ready) << " "
              << seconds(source_ready,vanisher_ready) << "\n" << std::flush;
    for(unsigned target=0;target<2;++target) {
      auto row_start=Clock::now();
      std::string tag;
      unsigned index;
      coeffs>>tag>>index;
      if(tag!="T"||index!=target)throw std::runtime_error("target row");
      GF2E coefficient[5][5]{};
      bool seen[5][5]{};
      for(unsigned term=0;term<13;++term) {
        unsigned i,j;
        std::string value;
        coeffs>>tag>>index>>i>>j>>value;
        if(tag!="C"||index!=target||i>4||j>4||seen[i][j])
          throw std::runtime_error("coefficient row");
        coefficient[i][j]=ntl(decimal(value));
        seen[i][j]=true;
      }
      double construction_sum=0,norm_sum=0,gcd_sum=0;
      if(target!=requested_target)continue;
      std::vector<std::pair<unsigned,unsigned>> pairs;
      unsigned blocks=0;
      for(size_t start=0;start<source.size();start+=block_size) {
        if(blocks<begin_block||blocks>=end_block) {++blocks;continue;}
        size_t end=std::min(source.size(),start+block_size);
        auto block_start=Clock::now();
        std::vector<GF2EX> quartics;
        quartics.reserve(end-start);
        for(size_t j=start;j<end;++j) {
          const auto& item=source[j];
          std::array<GF2E,5> power;
          power[0]=NTL::to_GF2E(GF2X(1));
          for(int k=1;k<5;++k)power[k]=power[k-1]*item.q;
          GF2EX f;
          for(int i=0;i<5;++i) {
            GF2E c;
            for(int k=0;k<5;++k)if(seen[i][k])c+=coefficient[i][k]*power[k];
            NTL::SetCoeff(f,i,c);
          }
          quartics.push_back(std::move(f));
        }
        auto construction_done=Clock::now();
        GF2EX norm=product_tree(quartics);
        auto norm_done=Clock::now();
        GF2EX common=NTL::GCD(norm,vanisher);
        auto gcd_done=Clock::now();
        int degree=NTL::deg(common);
        std::vector<unsigned> first_hits;
        if(degree>0) {
          GF2E root;
          if(degree==1)root=NTL::coeff(common,0)/NTL::coeff(common,1);
          for(const auto& item:source)
            if(degree==1?(item.p==root):NTL::IsZero(NTL::eval(common,item.p)))
              first_hits.push_back(item.code);
          if(int(first_hits.size())!=degree)throw std::runtime_error("gcd root localization");
        }
        unsigned before=pairs.size();
        for(unsigned code:first_hits) {
          auto it=std::lower_bound(source.begin(),source.end(),code,
            [](const Source& item,unsigned c){return item.code<c;});
          if(it==source.end()||it->code!=code)throw std::runtime_error("missing first code");
          for(size_t j=0;j<quartics.size();++j)
            if(NTL::IsZero(NTL::eval(quartics[j],it->p)))
              pairs.emplace_back(code,source[start+j].code);
        }
        auto block_done=Clock::now();
        construction_sum+=seconds(block_start,construction_done);
        norm_sum+=seconds(construction_done,norm_done);
        gcd_sum+=seconds(norm_done,gcd_done);
        struct rusage block_usage{};
        getrusage(RUSAGE_SELF,&block_usage);
        std::cout << "BLOCK " << target << " " << blocks << " " << end-start
                  << " " << NTL::deg(norm) << " " << degree << " "
                  << pairs.size()-before << " " << seconds(block_start,block_done)
                  << " " << block_usage.ru_maxrss << "\n" << std::flush;
        ++blocks;
      }
      auto row_done=Clock::now();
      struct rusage usage{};
      getrusage(RUSAGE_SELF,&usage);
      std::sort(pairs.begin(),pairs.end());
      std::cout << "ROW " << target << " " << begin_block << " " << end_block << " " << pairs.size();
      for(auto [a,b]:pairs)std::cout << " " << a << "," << b;
      std::cout << " " << construction_sum
                << " " << norm_sum
                << " " << gcd_sum
                << " " << seconds(row_start,row_done)
                << " " << usage.ru_maxrss << "\n" << std::flush;
    }
    std::string trailing;
    if(coeffs>>trailing)throw std::runtime_error("trailing coefficient data");
    struct rusage usage{};
    getrusage(RUSAGE_SELF,&usage);
    std::cout << "DONE " << seconds(process_start,Clock::now()) << " " << usage.ru_maxrss << "\n";
    return 0;
  } catch(const std::exception& error) {
    std::cerr << "ERROR " << error.what() << "\n";
    return 1;
  }
}
