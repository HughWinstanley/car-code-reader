import Foundation

struct LivePID {
    let pid: UInt8
    let name: String
    let decode: ([UInt8]) -> Double
    let format: (Double) -> String
}

enum PIDs {
    static func f(_ v: Double, _ unit: String) -> String {
        switch unit {
        case "degC":  return String(format: "%.0f °F  (%.0f °C)", v * 9 / 5 + 32, v)
        case "kmh":   return String(format: "%.0f mph  (%.0f km/h)", v * 0.621371, v)
        case "kpa":   return String(format: "%.0f kPa  (%.1f psi)", v, v * 0.145038)
        case "rpm":   return String(format: "%.0f rpm", v)
        case "pct":   return String(format: "%.1f %%", v)
        case "volt":  return String(format: "%.2f V", v)
        case "gs":    return String(format: "%.1f g/s", v)
        case "deg":   return String(format: "%.1f°", v)
        default:      return String(format: "%.1f", v)
        }
    }

    static let list: [LivePID] = [
        LivePID(pid: 0x0C, name: "Engine RPM",               decode: { (Double($0[0]) * 256 + Double($0[1])) / 4 }, format: { f($0, "rpm") }),
        LivePID(pid: 0x0D, name: "Vehicle speed",            decode: { Double($0[0]) },                             format: { f($0, "kmh") }),
        LivePID(pid: 0x05, name: "Coolant temperature",      decode: { Double($0[0]) - 40 },                        format: { f($0, "degC") }),
        LivePID(pid: 0x0F, name: "Intake air temperature",   decode: { Double($0[0]) - 40 },                        format: { f($0, "degC") }),
        LivePID(pid: 0x04, name: "Engine load",              decode: { Double($0[0]) * 100 / 255 },                 format: { f($0, "pct") }),
        LivePID(pid: 0x11, name: "Throttle position",        decode: { Double($0[0]) * 100 / 255 },                 format: { f($0, "pct") }),
        LivePID(pid: 0x0B, name: "Intake manifold pressure", decode: { Double($0[0]) },                             format: { f($0, "kpa") }),
        LivePID(pid: 0x10, name: "Mass air flow",            decode: { (Double($0[0]) * 256 + Double($0[1])) / 100 }, format: { f($0, "gs") }),
        LivePID(pid: 0x06, name: "Short-term fuel trim b1",  decode: { (Double($0[0]) - 128) * 100 / 128 },         format: { f($0, "pct") }),
        LivePID(pid: 0x07, name: "Long-term fuel trim b1",   decode: { (Double($0[0]) - 128) * 100 / 128 },         format: { f($0, "pct") }),
        LivePID(pid: 0x0E, name: "Ignition timing advance",  decode: { Double($0[0]) / 2 - 64 },                    format: { f($0, "deg") }),
        LivePID(pid: 0x2F, name: "Fuel level",               decode: { Double($0[0]) * 100 / 255 },                 format: { f($0, "pct") }),
        LivePID(pid: 0x42, name: "Battery (module) voltage", decode: { (Double($0[0]) * 256 + Double($0[1])) / 1000 }, format: { f($0, "volt") }),
    ]
}
