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
    if(argc!=4)throw std::runtime_error("usage: native_norm support.tsv coefficients.tsv selected_count");
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
      std::vector<GF2EX> quartics;
      quartics.reserve(n);
      for(const auto& item:source) {
        std::array<GF2E,5> power;
        power[0]=NTL::to_GF2E(GF2X(1));
        for(int j=1;j<5;++j)power[j]=power[j-1]*item.q;
        GF2EX f;
        for(int i=0;i<5;++i) {
          GF2E c;
          for(int j=0;j<5;++j)if(seen[i][j])c+=coefficient[i][j]*power[j];
          NTL::SetCoeff(f,i,c);
        }
        quartics.push_back(std::move(f));
      }
      auto construction_done=Clock::now();
      GF2EX norm=product_tree(quartics);
      auto norm_done=Clock::now();
      GF2EX common=NTL::GCD(norm,vanisher);
      auto gcd_done=Clock::now();
      std::vector<unsigned> first_hits;
      int degree=NTL::deg(common);
      if(degree>0) {
        GF2E root;
        if(degree==1)root=NTL::coeff(common,0)/NTL::coeff(common,1);
        for(const auto& item:source)
          if(degree==1?(item.p==root):NTL::IsZero(NTL::eval(common,item.p)))
            first_hits.push_back(item.code);
        if(int(first_hits.size())!=degree)throw std::runtime_error("gcd root localization");
      }
      std::vector<std::pair<unsigned,unsigned>> pairs;
      for(unsigned code:first_hits) {
        auto it=std::lower_bound(source.begin(),source.end(),code,
          [](const Source& item,unsigned c){return item.code<c;});
        if(it==source.end()||it->code!=code)throw std::runtime_error("missing first code");
        for(size_t j=0;j<source.size();++j)
          if(NTL::IsZero(NTL::eval(quartics[j],it->p)))pairs.emplace_back(code,source[j].code);
      }
      auto row_done=Clock::now();
      struct rusage usage{};
      getrusage(RUSAGE_SELF,&usage);
      std::cout << "ROW " << target << " " << NTL::deg(norm) << " " << degree
                << " " << pairs.size();
      for(auto [a,b]:pairs)std::cout << " " << a << "," << b;
      std::cout << " " << seconds(row_start,construction_done)
                << " " << seconds(construction_done,norm_done)
                << " " << seconds(norm_done,gcd_done)
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
