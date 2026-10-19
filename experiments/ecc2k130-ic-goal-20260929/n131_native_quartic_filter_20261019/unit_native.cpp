// Exact arithmetic and planted-subspace-root controls for the native filter.
#define main native_program_main
#include "native_batch.cpp"
#undef main

static uint64_t state=0x9e3779b97f4a7c15ULL;
static uint64_t next_word(){
    state^=state<<13;state^=state>>7;state^=state<<17;
    return state;
}
static Fe random_fe(){return {next_word(),next_word(),next_word()&7};}

int main(){
    unsigned multiplication_checks=0,square_checks=0,inverse_checks=0;
    for(int i=0;i<200;++i){
        Fe a=random_fe(),b=random_fe();
        if(!eq(fm(a,b),field.mul(a,b)))throw std::runtime_error("fast multiply mismatch");
        ++multiplication_checks;
        if(!eq(fs(a),field.sq(a)))throw std::runtime_error("byte square mismatch");
        ++square_checks;
        if(!zero(a)){
            if(!eq(fm(a,inv(a)),one))throw std::runtime_error("inverse mismatch");
            ++inverse_checks;
        }
    }
    Fe seed{898618ULL<<1,0,0};
    std::vector<int> bits;
    for(int i=0;i<29;++i)if(i!=19)bits.push_back(i);
    std::vector<Fe> qbasis;
    for(int j=0;j<28;++j)qbasis.push_back(source_product(1u<<j,bits,seed,18));
    auto av=annihilator(qbasis);
    unsigned planted=0,perturbed_rejected=0,exceptional=0;
    for(int i=0;i<100;++i){
        unsigned code=static_cast<unsigned>(next_word())&((1u<<28)-1);
        Fe q=source_product(code,bits,seed,18);
        if(!zero(linearized(av,q)))throw std::runtime_error("planted code outside right space");
        std::array<Fe,5> h{};
        for(int j=1;j<5;++j)h[j]=random_fe();
        if(zero(h[4]))h[4]=one;
        h[0]=eval_quartic(h,q);
        if(!zero(eval_quartic(h,q)))throw std::runtime_error("planted quartic construction");
        if(reject(h,av,exceptional))throw std::runtime_error("planted root rejected");
        ++planted;
        h[0]=xo(h[0],one);
        if(reject(h,av,exceptional))++perturbed_rejected;
    }
    if(exceptional)throw std::runtime_error("unexpected lower degree");
    std::cout<<"{\"status\":\"PASS_NATIVE_FIELD_AND_PLANTED_ROOTS\","
             <<"\"multiplication_checks\":"<<multiplication_checks
             <<",\"square_checks\":"<<square_checks
             <<",\"inverse_checks\":"<<inverse_checks
             <<",\"planted_roots_preserved\":"<<planted
             <<",\"perturbed_rejected\":"<<perturbed_rejected<<"}"<<std::endl;
}
