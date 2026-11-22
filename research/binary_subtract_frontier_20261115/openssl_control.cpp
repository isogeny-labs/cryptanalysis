// Independent full-point, first-witness control using OpenSSL's binary EC API.
// Input: degree modulus a b base_count target_count, then infinity/x/y triples.
// No timer, target generation, custom field arithmetic or summation formula.
#include <openssl/bn.h>
#include <openssl/ec.h>
#include <openssl/err.h>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <unordered_map>
#include <vector>

#ifdef OPENSSL_NO_EC2M
#error "OpenSSL binary-curve support is required by this control"
#endif

using Bn = std::unique_ptr<BIGNUM, decltype(&BN_free)>;
using Point = std::unique_ptr<EC_POINT, decltype(&EC_POINT_free)>;
static void require(bool ok, const char* what) {
    if (!ok) { ERR_print_errors_fp(stderr); throw std::runtime_error(what); }
}
static Bn number(std::uint64_t v) {
    unsigned char bytes[8];
    for (unsigned i=0;i<8;++i) bytes[i]=static_cast<unsigned char>(v>>(8*i));
    Bn out(BN_lebin2bn(bytes,8,nullptr),BN_free); require(bool(out),"BN allocation"); return out;
}
static Point input(const EC_GROUP* group,BN_CTX* ctx,unsigned degree) {
    unsigned infinity; std::uint64_t x,y;
    require(bool(std::cin>>infinity>>x>>y),"truncated point input");
    require(infinity<=1 && (x>>degree)==0 && (y>>degree)==0,"invalid point encoding");
    Point p(EC_POINT_new(group),EC_POINT_free); require(bool(p),"point allocation");
    if (infinity) { require(x==0 && y==0,"noncanonical infinity"); require(EC_POINT_set_to_infinity(group,p.get())==1,"set infinity"); }
    else { auto bx=number(x),by=number(y); require(EC_POINT_set_affine_coordinates(group,p.get(),bx.get(),by.get(),ctx)==1,"set point"); }
    require(EC_POINT_is_on_curve(group,p.get(),ctx)==1,"point is off curve");
    return p;
}
static std::uint64_t key(const EC_GROUP* group,const EC_POINT* p,BN_CTX* ctx) {
    if (EC_POINT_is_at_infinity(group,p)) return 0;
    Bn x(BN_new(),BN_free),y(BN_new(),BN_free); require(bool(x)&&bool(y),"coordinate allocation");
    require(EC_POINT_get_affine_coordinates(group,p,x.get(),y.get(),ctx)==1,"affine coordinates");
    require(BN_num_bits(x.get())<=62 && BN_num_bits(y.get())<=62,"coordinate too wide");
    auto xv=static_cast<std::uint64_t>(BN_get_word(x.get()));
    auto yv=static_cast<std::uint64_t>(BN_get_word(y.get()));
    return ((xv+1)<<1)|std::uint64_t(yv>(xv^yv));
}
int main(int argc,char** argv) {
    try {
        require(argc==2 && (std::string(argv[1])=="--check" || std::string(argv[1])=="--check-native-invert"),"requires --check or --check-native-invert (no timing mode)");
        const bool native_invert=std::string(argv[1])=="--check-native-invert";
        unsigned n; std::uint64_t modulus,a,b; std::size_t count,targets;
        require(bool(std::cin>>n>>modulus>>a>>b>>count>>targets),"missing header");
        require(n>1 && n<=62 && (modulus>>n)==1 && b!=0,"unsupported curve header");
        require(count<=65536 && targets<=65536,"control input cap");
        auto poly=number(modulus),ba=number(a),bb=number(b);
        std::unique_ptr<BN_CTX,decltype(&BN_CTX_free)> ctx(BN_CTX_new(),BN_CTX_free);
        require(bool(ctx),"context allocation");
        std::unique_ptr<EC_GROUP,decltype(&EC_GROUP_free)> group(EC_GROUP_new_curve_GF2m(poly.get(),ba.get(),bb.get(),ctx.get()),EC_GROUP_free);
        require(bool(group) && EC_GROUP_get_degree(group.get())==static_cast<int>(n),"binary group creation");
        std::vector<Point> negatives; negatives.reserve(count);
        std::unordered_map<std::uint64_t,std::size_t> index; index.reserve(count);
        for (std::size_t i=0;i<count;++i) {
            auto p=input(group.get(),ctx.get(),n);
            index[key(group.get(),p.get(),ctx.get())]=i; // Same duplicate-label rule as FactorBase.
            if (native_invert) {
                require(EC_POINT_invert(group.get(),p.get(),ctx.get())==1,"native negation");
            } else if (!EC_POINT_is_at_infinity(group.get(),p.get())) {
                // OpenSSL 3.5.7's ec2_smpl.c inversion returns early at Y=0,
                // although (x,0) negates to (x,x) when x is nonzero. Keep the
                // unmodified API as a separate negative control. The matched
                // comparator uses OpenSSL BN field addition to apply the
                // characteristic-two affine negation for every finite point.
                Bn x(BN_new(),BN_free),y(BN_new(),BN_free);
                require(bool(x)&&bool(y),"negation coordinate allocation");
                require(EC_POINT_get_affine_coordinates(group.get(),p.get(),x.get(),y.get(),ctx.get())==1,"negation coordinates");
                require(BN_GF2m_add(y.get(),x.get(),y.get())==1,"binary negation");
                require(EC_POINT_set_affine_coordinates(group.get(),p.get(),x.get(),y.get(),ctx.get())==1,"set negative point");
            }
            negatives.push_back(std::move(p));
        }
        Point rest(EC_POINT_new(group.get()),EC_POINT_free); require(bool(rest),"result allocation");
        for (std::size_t t=0;t<targets;++t) {
            auto target=input(group.get(),ctx.get(),n); bool found=false;
            for (std::size_t i=0;i<count;++i) {
                require(EC_POINT_add(group.get(),rest.get(),target.get(),negatives[i].get(),ctx.get())==1,"subtraction");
                auto hit=index.find(key(group.get(),rest.get(),ctx.get()));
                if (hit!=index.end()) { std::cout<<t<<' '<<i<<' '<<hit->second<<'\n'; found=true; break; }
            }
            if (!found) std::cout<<t<<" none\n";
        }
        std::string extra; require(!(std::cin>>extra),"trailing input");
        return 0;
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
