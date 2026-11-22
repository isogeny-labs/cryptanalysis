#define main archived_fouratom_main
#include "../n131_w15_rotated_fouratom_inverse_20261010/native.cpp"
#undef main
#include <unordered_map>
#include <algorithm>

using PolyBool = std::unordered_map<uint64_t,Fe>;

static PolyBool multiply_bool(const Field& f,const PolyBool& a,const PolyBool& b) {
    PolyBool out;out.reserve(a.size()*b.size());
    for(const auto& [ma,ca]:a)for(const auto& [mb,cb]:b){
        uint64_t key=ma|mb;
        Fe value=f.mul(ca,cb);
        auto [it,inserted]=out.try_emplace(key,value);
        if(!inserted)it->second=xo(it->second,value);
    }
    for(auto it=out.begin();it!=out.end();){if(zero(it->second))it=out.erase(it);else ++it;}
    return out;
}
static std::array<PolyBool,9> powers_bool(const Field& f,const std::vector<Fe>& basis,int offset){
    std::array<PolyBool,9> out;
    out[0][0]={1,0,0};
    std::array<PolyBool,4> squares;
    for(size_t i=0;i<basis.size();++i)squares[0][1ULL<<(offset+i)]=basis[i];
    for(int k=1;k<4;++k)
        for(const auto& [mask,value]:squares[k-1])squares[k][mask]=f.sq(value);
    for(int exponent=1;exponent<=8;++exponent){
        PolyBool current=out[0];
        for(int k=0;k<4;++k)if(exponent>>k&1)current=multiply_bool(f,current,squares[k]);
        out[exponent]=std::move(current);
    }
    return out;
}
static uint32_t coordinates(Fe value,const std::vector<Fe>& basis){
    std::array<Fe,131> pivots{};std::array<uint32_t,131> masks{};
    for(size_t i=0;i<basis.size();++i){
        Fe x=basis[i];uint32_t bits=1U<<i;
        while(!zero(x)){
            int k=highbit(x);
            if(zero(pivots[k])){pivots[k]=x;masks[k]=bits;break;}
            x=xo(x,pivots[k]);bits^=masks[k];
        }
        if(zero(x))throw std::runtime_error("dependent basis");
    }
    uint32_t result=0;
    while(!zero(value)){
        int k=highbit(value);
        if(zero(pivots[k]))throw std::runtime_error("positive product outside image");
        value=xo(value,pivots[k]);result^=masks[k];
    }
    return result;
}
static Fe evaluation(const PolyBool& anf,uint64_t assignment){
    Fe result{};
    for(const auto& [mask,value]:anf)if((mask&assignment)==mask)result=xo(result,value);
    return result;
}
static Fe direct(const Field& f,const std::array<std::array<Fe,9>,9>& rows,Fe p,Fe q){
    auto polynomial=evaluate_h(f,rows,p);
    Fe out{};
    for(int j=polynomial.degree;j>=0;--j)out=xo(f.mul(out,q),polynomial.c[j]);
    return out;
}
static int degree(uint64_t mask){return __builtin_popcountll(mask);}

int main(int argc,char**argv){
try {
    if(argc!=3)throw std::runtime_error("usage: anf input.txt output.json");
    auto started=ticks();
    std::ifstream input(argv[1]);if(!input)throw std::runtime_error("input missing");
    int n,dimension,s0,s1,r0,r1,m0,m1,m2,m3;
    std::string zword;
    input>>n>>dimension>>s0>>s1>>r0>>r1>>zword>>m0>>m1>>m2>>m3;
    std::string tail;if(!input||input>>tail)throw std::runtime_error("bad input");
    if(!((n==41&&dimension==8&&r0==14&&r1==21)||
         (n==131&&dimension==15&&r0==26&&r1==39)))throw std::runtime_error("field or source drift");
    Field f(n);Fe z=decimal(zword),seed0{uint64_t(s0)<<1,0,0},seed1{uint64_t(s1)<<1,0,0};
    Fe a=seed0,b=seed1;
    for(int k=0;k<r0;++k)a=f.sq(a);
    for(int k=0;k<r1;++k)b=f.sq(b);
    auto basis0=product_basis(f,dimension,seed0,r0);
    auto basis1=product_basis(f,dimension,seed1,r1);
    if(basis0.size()!=size_t(dimension-1)||basis1.size()!=basis0.size())
        throw std::runtime_error("basis rank drift");
    const int d=dimension-1;
    auto pp=powers_bool(f,basis0,0),qq=powers_bool(f,basis1,d);
    auto rows=resultant_rows(f,a,b,z);
    PolyBool anf;
    uint64_t products=0;
    for(int j=0;j<=8;++j)for(int i=0;i<=8;++i){
        Fe scalar=rows[j][i];if(zero(scalar))continue;
        for(const auto& [pm,pc]:pp[i]){
            Fe scaled=f.mul(scalar,pc);
            for(const auto& [qm,qc]:qq[j]){
                Fe value=f.mul(scaled,qc);uint64_t key=pm|qm;
                auto [it,inserted]=anf.try_emplace(key,value);
                if(!inserted)it->second=xo(it->second,value);
                ++products;
            }
        }
    }
    for(auto it=anf.begin();it!=anf.end();){if(zero(it->second))it=anf.erase(it);else ++it;}
    std::array<uint64_t,35> histogram{};for(const auto& [mask,value]:anf)++histogram[degree(mask)];
    Fe wa{uint64_t(m0)<<1,0,0},wb{uint64_t(m1)<<1,0,0};
    Fe wc{uint64_t(m2)<<1,0,0},wd{uint64_t(m3)<<1,0,0};
    Fe p=f.mul(wa,wb),q=f.mul(wc,wd);
    for(int k=0;k<r0;++k)p=f.sq(p);
    for(int k=0;k<r1;++k)q=f.sq(q);
    uint32_t pm=coordinates(p,basis0),qm=coordinates(q,basis1);
    uint64_t assignment=uint64_t(pm)|(uint64_t(qm)<<d);
    Fe witness_anf=evaluation(anf,assignment),witness_direct=direct(f,rows,p,q);
    if(!eq(witness_anf,witness_direct))throw std::runtime_error("witness ANF mismatch");
    uint64_t rng=0x92635a17d4ULL;unsigned checks=0;
    for(int t=0;t<32;++t){
        rng^=rng>>12;rng^=rng<<25;rng^=rng>>27;
        uint32_t x=rng&((1U<<d)-1),y=(rng>>d)&((1U<<d)-1);
        Fe px{},qy{};
        for(int k=0;k<d;++k){if(x>>k&1)px=xo(px,basis0[k]);if(y>>k&1)qy=xo(qy,basis1[k]);}
        if(!eq(evaluation(anf,uint64_t(x)|(uint64_t(y)<<d)),direct(f,rows,px,qy)))
            throw std::runtime_error("sample ANF mismatch");
        ++checks;
    }
    std::ofstream out(argv[2]);if(!out)throw std::runtime_error("output missing");
    out<<"{\"status\":\"PASS_EXACT_PRODUCT_ANF\",\"field_degree\":"<<n
       <<",\"product_bits_each\":"<<d<<",\"anf_monomials\":"<<anf.size()
       <<",\"raw_tensor_terms\":"<<products<<",\"degree_histogram\":[";
    for(size_t i=0;i<histogram.size();++i){if(i)out<<",";out<<histogram[i];}
    out<<"],\"positive_product_masks\":["<<pm<<","<<qm<<"]"
       <<",\"witness_anf_zero\":"<<(zero(witness_anf)?"true":"false")
       <<",\"sample_direct_checks\":"<<checks
       <<",\"elapsed_ns_exploratory\":"<<(ticks()-started)
       <<",\"peak_rss_bytes\":"<<rss()<<"}\n";
    std::cout<<"PASS_EXACT_PRODUCT_ANF n="<<n<<" monomials="<<anf.size()
             <<" raw="<<products<<" witness_zero="<<zero(witness_anf)<<"\n";
} catch(const std::exception& e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
