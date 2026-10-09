import Foundation

struct LivePID {
    let pid: UInt8
    let name: String
    let len: Int                       // data bytes needed (1 or 2)
    let decode: ([UInt8]) -> Double
    let format: (Double) -> String
}

enum PIDs {
    static func f(_ v: Double, _ unit: String) -> String {
        switch unit {
        case "degC":   return String(format: "%.0f °F  (%.0f °C)", v * 9 / 5 + 32, v)
        case "kmh":    return String(format: "%.0f mph  (%.0f km/h)", v * 0.621371, v)
        case "kpa":    return String(format: "%.0f kPa  (%.1f psi)", v, v * 0.145038)
        case "rpm":    return String(format: "%.0f rpm", v)
        case "pct":    return String(format: "%.1f %%", v)
        case "volt":   return String(format: "%.3f V", v)
        case "gs":     return String(format: "%.1f g/s", v)
        case "deg":    return String(format: "%.1f°", v)
        case "sec":    return String(format: "%.0f s", v)
        case "min":    return String(format: "%.0f min", v)
        case "km":     return String(format: "%.0f km  (%.0f mi)", v, v * 0.621371)
        case "count":  return String(format: "%.0f", v)
        case "lambda": return String(format: "%.2f λ", v)
        case "lph":    return String(format: "%.1f L/h  (%.1f gal/h)", v, v * 0.264172)
        default:       return String(format: "%.1f", v)
        }
    }

    static func p(_ pid: UInt8, _ name: String, _ len: Int,
                  _ decode: @escaping ([UInt8]) -> Double, _ unit: String) -> LivePID {
        LivePID(pid: pid, name: name, len: len, decode: decode, format: { f($0, unit) })
    }

    // Mirrors the Mac app's PIDS table. The live view only shows the ones the car supports.
    static let list: [LivePID] = [
        p(0x0C, "Engine RPM", 2, { (Double($0[0]) * 256 + Double($0[1])) / 4 }, "rpm"),
        p(0x0D, "Vehicle speed", 1, { Double($0[0]) }, "kmh"),
        p(0x05, "Coolant temperature", 1, { Double($0[0]) - 40 }, "degC"),
        p(0x0F, "Intake air temperature", 1, { Double($0[0]) - 40 }, "degC"),
        p(0x5C, "Engine oil temperature", 1, { Double($0[0]) - 40 }, "degC"),
        p(0x04, "Engine load", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x43, "Absolute engine load", 2, { (Double($0[0]) * 256 + Double($0[1])) * 100 / 255 }, "pct"),
        p(0x11, "Throttle position", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x45, "Relative throttle position", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x4C, "Commanded throttle", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x49, "Accelerator pedal position", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x0B, "Intake manifold pressure", 1, { Double($0[0]) }, "kpa"),
        p(0x33, "Barometric pressure", 1, { Double($0[0]) }, "kpa"),
        p(0x10, "Mass air flow", 2, { (Double($0[0]) * 256 + Double($0[1])) / 100 }, "gs"),
        p(0x06, "Short-term fuel trim (bank 1)", 1, { (Double($0[0]) - 128) * 100 / 128 }, "pct"),
        p(0x07, "Long-term fuel trim (bank 1)", 1, { (Double($0[0]) - 128) * 100 / 128 }, "pct"),
        p(0x08, "Short-term fuel trim (bank 2)", 1, { (Double($0[0]) - 128) * 100 / 128 }, "pct"),
        p(0x09, "Long-term fuel trim (bank 2)", 1, { (Double($0[0]) - 128) * 100 / 128 }, "pct"),
        p(0x44, "Commanded air/fuel ratio (lambda)", 2, { (Double($0[0]) * 256 + Double($0[1])) * 2 / 65536 }, "lambda"),
        p(0x0E, "Ignition timing advance", 1, { Double($0[0]) / 2 - 64 }, "deg"),
        p(0x0A, "Fuel pressure", 1, { Double($0[0]) * 3 }, "kpa"),
        p(0x23, "Fuel rail pressure", 2, { (Double($0[0]) * 256 + Double($0[1])) * 10 }, "kpa"),
        p(0x2F, "Fuel level", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x52, "Ethanol in fuel", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x5E, "Fuel use rate", 2, { (Double($0[0]) * 256 + Double($0[1])) / 20 }, "lph"),
        p(0x2C, "Commanded EGR", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x2E, "Commanded EVAP purge", 1, { Double($0[0]) * 100 / 255 }, "pct"),
        p(0x14, "O2 sensor voltage, B1S1", 1, { Double($0[0]) / 200 }, "volt"),
        p(0x15, "O2 sensor voltage, B1S2", 1, { Double($0[0]) / 200 }, "volt"),
        p(0x16, "O2 sensor voltage, B1S3", 1, { Double($0[0]) / 200 }, "volt"),
        p(0x18, "O2 sensor voltage, B2S1", 1, { Double($0[0]) / 200 }, "volt"),
        p(0x19, "O2 sensor voltage, B2S2", 1, { Double($0[0]) / 200 }, "volt"),
        p(0x3C, "Catalyst temperature, bank 1", 2, { (Double($0[0]) * 256 + Double($0[1])) / 10 - 40 }, "degC"),
        p(0x3D, "Catalyst temperature, bank 2", 2, { (Double($0[0]) * 256 + Double($0[1])) / 10 - 40 }, "degC"),
        p(0x46, "Outside air temperature", 1, { Double($0[0]) - 40 }, "degC"),
        p(0x42, "Control module voltage", 2, { (Double($0[0]) * 256 + Double($0[1])) / 1000 }, "volt"),
        p(0x1F, "Time since engine start", 2, { Double($0[0]) * 256 + Double($0[1]) }, "sec"),
        p(0x4D, "Time run with light on", 2, { Double($0[0]) * 256 + Double($0[1]) }, "min"),
        p(0x4E, "Time since codes cleared", 2, { Double($0[0]) * 256 + Double($0[1]) }, "min"),
        p(0x21, "Distance driven with light on", 2, { Double($0[0]) * 256 + Double($0[1]) }, "km"),
        p(0x31, "Distance since codes cleared", 2, { Double($0[0]) * 256 + Double($0[1]) }, "km"),
        p(0x30, "Warm-ups since codes cleared", 1, { Double($0[0]) }, "count"),
    ]
}
