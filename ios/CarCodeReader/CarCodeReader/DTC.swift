import Foundation

enum Make { case ford, gm, other }

enum DTC {
    /// Plain-English meaning. With the make, manufacturer-specific codes get their factory meaning.
    /// Codes not in the built-in list are still described by their system area, and a "-XX"
    /// failure-type byte (on module / ABS / airbag codes) is decoded — matching the Mac app.
    static func describe(_ code: String, make: Make = .other) -> (text: String, factory: String?) {
        let up = code.uppercased()
        let parts = up.split(separator: "-", maxSplits: 1, omittingEmptySubsequences: false)
        let base = String(parts.first ?? Substring(up))
        let ftbSuffix = parts.count > 1 ? String(parts[1]) : ""

        var desc: String
        var factory: String? = nil

        if isManufacturerSpecific(base), make == .ford, let d = CodeData.ford[base] {
            desc = d; factory = "Ford"
        } else if isManufacturerSpecific(base), make == .gm, let d = CodeData.gm[base] {
            desc = d; factory = "GM"
        } else if let d = CodeData.generic[base] {
            desc = d
        } else {
            desc = fallbackDescription(base)
        }

        if let ft = describeFTB(ftbSuffix) { desc += " · \(ft)" }
        return (desc, factory)
    }

    /// Build a useful description for a code that isn't in the list, from its system + area.
    private static func fallbackDescription(_ base: String) -> String {
        let systems = ["P": "powertrain", "C": "chassis", "B": "body", "U": "network"]
        guard base.count == 5, let letter = base.first,
              let system = systems[String(letter)] else {
            return "Code not recognized — use Search for repair info"
        }
        let chars = Array(base)
        var area = system
        if letter == "P", let sub = subsystems[String(chars[2])] { area = sub }
        if isManufacturerSpecific(base) {
            return "Manufacturer-specific \(area) code — use Search for repair info to look it up for your make"
        }
        return "\(area.prefix(1).uppercased())\(area.dropFirst()) code — not in the built-in list, use Search for repair info"
    }

    /// Decode the "-XX" UDS failure-type byte into words (module / ABS / airbag codes).
    private static func describeFTB(_ hex: String) -> String? {
        guard !hex.isEmpty, let value = Int(hex, radix: 16) else { return nil }
        let meaning = ftb[value] ?? "Manufacturer-specific failure type"
        return String(format: "-%02X: %@", value, meaning)
    }

    static func isManufacturerSpecific(_ code: String) -> Bool {
        guard code.count == 5 else { return false }
        let chars = Array(code)
        let digit = chars[1]
        if chars[0] == "P" { return digit == "1" || (digit == "3" && "0123".contains(chars[2])) }
        return digit == "1" || digit == "2"
    }

    static func urgency(_ code: String, status: String, module: String) -> String {
        let c = String(code.prefix(5)).uppercased()
        let s = status.lowercased(), m = module.lowercased()
        if s.contains("history") || s.contains("past") { return "past" }
        if m.contains("airbag") || m.contains("abs") || m.contains("brake") { return "high" }
        if ("P0300"..."P0312").contains(c) { return "high" }
        if ("P0440"..."P0457").contains(c) { return "low" }
        if s.contains("pending") || s.contains("permanent") { return "low" }
        return "medium"
    }

    // MARK: - Structural tables (ported from the Mac app's dtc_database.py)

    /// The area named by the 3rd character of a P-code.
    static let subsystems: [String: String] = [
        "0": "fuel/air metering and auxiliary emission controls",
        "1": "fuel and air metering",
        "2": "fuel and air metering (injector circuits)",
        "3": "ignition system or misfire",
        "4": "auxiliary emission controls (EGR, EVAP, catalyst)",
        "5": "vehicle speed, idle control and auxiliary inputs",
        "6": "computer and output circuits",
        "7": "transmission",
        "8": "transmission",
        "9": "transmission",
        "A": "hybrid propulsion system",
        "B": "hybrid propulsion system",
        "C": "hybrid propulsion system",
    ]

    /// UDS failure-type byte meanings (the "-XX" after a module code).
    static let ftb: [Int: String] = [
        0x00: "No sub-type information",
        0x01: "General electrical failure",
        0x02: "General signal failure",
        0x03: "Frequency/PWM signal failure",
        0x04: "System internal failure",
        0x05: "System programming failure",
        0x06: "Algorithm-based failure",
        0x07: "Mechanical failure",
        0x08: "Bus signal/message failure",
        0x09: "Component failure",
        0x11: "Circuit short to ground",
        0x12: "Circuit short to battery",
        0x13: "Circuit open",
        0x14: "Circuit short to ground or open",
        0x15: "Circuit short to battery or open",
        0x16: "Circuit voltage below threshold",
        0x17: "Circuit voltage above threshold",
        0x19: "Circuit current above threshold",
        0x1C: "Circuit voltage out of range",
        0x1D: "Circuit current out of range",
        0x1F: "Circuit intermittent",
        0x21: "Signal amplitude below minimum",
        0x22: "Signal amplitude above maximum",
        0x23: "Signal stuck low",
        0x24: "Signal stuck high",
        0x26: "Signal rate of change too low",
        0x27: "Signal rate of change too high",
        0x28: "Signal bias level out of range",
        0x29: "Signal invalid",
        0x2F: "Signal erratic",
        0x31: "No signal",
        0x36: "Signal frequency too low",
        0x37: "Signal frequency too high",
        0x38: "Signal frequency incorrect",
        0x41: "General checksum failure",
        0x42: "General memory failure",
        0x44: "Data memory failure",
        0x45: "Program memory failure",
        0x46: "Calibration/parameter memory failure",
        0x47: "Watchdog/safety processor failure",
        0x48: "Supervision software failure",
        0x49: "Internal electronic failure",
        0x4B: "Over temperature",
        0x51: "Not programmed",
        0x52: "Not activated",
        0x54: "Missing calibration",
        0x55: "Not configured",
        0x61: "Signal calculation failure",
        0x62: "Signal compare failure",
        0x64: "Signal plausibility failure",
        0x67: "Signal incorrect after event",
        0x71: "Actuator stuck",
        0x72: "Actuator stuck open",
        0x73: "Actuator stuck closed",
        0x74: "Actuator slipping",
        0x77: "Commanded position not reachable",
        0x78: "Alignment or adjustment incorrect",
        0x7B: "Low fluid level",
        0x81: "Invalid serial data received",
        0x82: "Alive/sequence counter incorrect",
        0x83: "Message signature/checksum incorrect",
        0x84: "Signal below allowable range",
        0x85: "Signal above allowable range",
        0x86: "Signal invalid",
        0x87: "Missing message",
        0x88: "Bus off",
        0x8F: "Erratic",
        0x92: "Performance or incorrect operation",
        0x93: "No operation",
        0x94: "Unexpected operation",
        0x95: "Incorrect assembly",
        0x96: "Component internal failure",
        0x97: "Operation obstructed or blocked",
        0x98: "Component or system over temperature",
    ]
}
