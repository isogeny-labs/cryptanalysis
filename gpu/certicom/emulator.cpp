// Explicit host emulation of the device source. Never identified as a GPU.
#include "wire.hpp"
class CcEmulator {
public:
    CcEmulator(int ordinal,const char *) {
        if (ordinal!=0) throw std::runtime_error("emulator has only device ordinal 0");
    }
    const char *kind() const {return "gpu-emulator";}
    const char *name() const {return "host emulation; no GPU";}
    void execute(CcRequest &r) {
        for (unsigned i=0;i<r.n;++i) {
            if (r.op==1) r.points[i]=cc_point_add(r.curve,r.left[i],r.right[i]);
            else if (r.op==2) r.points[i]=cc_point_mul(r.curve,r.left[i],r.scalars[i]);
            else r.rho[i]=cc_rho_advance(r.curve,r.states[i],r.steps);
        }
    }
};
int main(int argc,char **argv) {return cc_worker_main<CcEmulator>(argc,argv);}
