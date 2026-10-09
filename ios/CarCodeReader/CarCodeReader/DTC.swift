import Foundation

enum Make { case ford, gm, other }

enum DTC {
    /// Plain-English meaning. With the make, manufacturer-specific codes get their factory meaning.
    static func describe(_ code: String, make: Make = .other) -> (text: String, factory: String?) {
        let base = String(code.split(separator: "-").first ?? Substring(code)).uppercased()
        if isManufacturerSpecific(base) {
            if make == .ford, let d = CodeData.ford[base] { return (d, "Ford") }
            if make == .gm, let d = CodeData.gm[base] { return (d, "GM") }
        }
        if let d = CodeData.generic[base] { return (d, nil) }
        let system = ["P": "Powertrain", "C": "Chassis", "B": "Body", "U": "Network"]
        let name = system[String(base.prefix(1))] ?? "Unknown"
        if isManufacturerSpecific(base) {
            return ("\(name) manufacturer-specific code — look it up for your make", nil)
        }
        return ("\(name) code — not in the built-in list", nil)
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
}
