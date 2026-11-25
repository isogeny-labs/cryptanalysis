// Uses the pinned public fixture's curve arithmetic, initialized once for y²=x³+x.
#include "common.hpp"

namespace {
const bool initialized = [] { A=1; B=0; return true; }();
}

// Return the ordered abscissas of the full fixed-size public coset. Check the
// actual successor of the last point, including on the level-wise path.
extern "C" bool public_walk(U tx, U ty, U gx, U gy, bool levels, uint32_t* xs, uint32_t* successor) {
    constexpr size_t n = 1024;
    Point t{tx,ty,false}, g{gx,gy,false};
    if (!initialized || !oncurve(t) || !oncurve(g)) return false;
    std::vector<Point> points{t};
    points.reserve(n);
    if (levels) {
        Point stride = g;
        while (points.size() < n) {
            auto translated = add_batch(stride, points, 0);
            points.insert(points.end(), translated.begin(), translated.end());
            if (points.size() < n) stride = add(stride, stride);
        }
    } else {
        while (points.size() < n) points.push_back(add(points.back(), g));
    }
    Point next = add(points.back(),g);
    if (next.inf) return false;
    successor[0] = static_cast<uint32_t>(next.x);
    successor[1] = static_cast<uint32_t>(next.y);
    for (size_t i=0; i<n; ++i) {
        if (points[i].inf || !oncurve(points[i])) return false;
        xs[i] = static_cast<uint32_t>(points[i].x);
    }
    return true;
}
