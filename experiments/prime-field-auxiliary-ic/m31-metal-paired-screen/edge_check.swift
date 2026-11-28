import Foundation

struct ProbePoint {
    var x: UInt64
    var y: UInt64
    var finite: UInt64
}

let modulus: UInt64 = 2_147_483_647
let zero = ProbePoint(x: 0, y: 0, finite: 0)
let p = ProbePoint(x: 1, y: 814_455_902, finite: 1)
let minusP = ProbePoint(x: 1, y: modulus - p.y, finite: 1)
let twiceP = ProbePoint(x: 1_042_161_180, y: 156_591_454, finite: 1)
let entries = [zero, p, minusP, twiceP]
let targets = entries
let bitmap = [UInt64](repeating: UInt64.max, count: 1 << 16)
let shaderPath = CommandLine.arguments[1]

func screen(_ mode: Int32) -> [UInt8] {
    var flags = [UInt8](repeating: 0, count: targets.count * entries.count * 2)
    let initialized = entries.withUnsafeBytes { points in
        bitmap.withUnsafeBytes { bits in
            shaderPath.withCString { path in
                m31MetalInit(points.baseAddress, Int32(entries.count), bits.baseAddress,
                             Int32(bitmap.count), 22, mode, path)
            }
        }
    }
    precondition(initialized == 0, "Metal initialization failed")
    let screened = targets.withUnsafeBytes { points in
        flags.withUnsafeMutableBytes { output in
            m31MetalScreen(points.baseAddress, Int32(targets.count), output.baseAddress)
        }
    }
    precondition(screened == 0, "Metal dispatch failed")
    return flags
}

@main struct EdgeCheck {
    static func main() {
        let scalar = screen(2)
        let paired = screen(3)
        precondition(scalar == paired, "paired screen disagreed on edge inputs")
        func flag(_ target: Int, _ entry: Int, _ sign: Int) -> UInt8 {
            paired[2 * (target * entries.count + entry) + sign]
        }
        precondition(flag(1, 1, 0) == 2 && flag(1, 1, 1) == 1,
                     "P minus/plus P identity and tangent")
        precondition(flag(1, 2, 0) == 1 && flag(1, 2, 1) == 2,
                     "P minus/plus negative P tangent and identity")
        precondition(flag(0, 1, 0) == 1 && flag(0, 1, 1) == 1,
                     "left identity")
        precondition(flag(1, 0, 0) == 1 && flag(1, 0, 1) == 1,
                     "right identity")
        print("edge flags matched for 4 targets x 4 entries x 2 signs")
    }
}
