import Foundation

struct Monitor { let name: String; let supported: Bool; let incomplete: Bool; let continuous: Bool }

enum Readiness {
    static let spark = ["Catalyst", "Heated catalyst", "Evaporative system (EVAP)", "Secondary air system",
                        "A/C refrigerant", "Oxygen sensor", "Oxygen sensor heater", "EGR system"]
    static let diesel = ["NMHC catalyst", "NOx / SCR aftertreatment", "", "Boost pressure", "",
                         "Exhaust gas sensor", "Particulate filter (DPF)", "EGR / VVT system"]

    static func decode(_ d: [UInt8]) -> (milOn: Bool, diesel: Bool, monitors: [Monitor]) {
        let a = d[0], b = d[1], c = d[2], dd = d[3]
        let milOn = a & 0x80 != 0
        let isDiesel = b & 0x08 != 0
        var mons: [Monitor] = []
        for (i, name) in ["Misfire", "Fuel system", "Comprehensive components"].enumerated() {
            mons.append(Monitor(name: name, supported: b & (1 << i) != 0,
                                incomplete: b & (1 << (i + 4)) != 0, continuous: true))
        }
        for (i, name) in (isDiesel ? diesel : spark).enumerated() where !name.isEmpty {
            mons.append(Monitor(name: name, supported: c & (1 << i) != 0,
                                incomplete: dd & (1 << i) != 0, continuous: false))
        }
        return (milOn, isDiesel, mons)
    }

    /// Inspection verdict. Only the non-continuous monitors count toward the allowed-unfinished limit.
    static func verdict(_ d: [UInt8], year: Int?) -> (text: String, ok: Bool, detail: String) {
        let (milOn, _, mons) = decode(d)
        let allowed = (year ?? 2001) <= 2000 ? 2 : 1
        let notReady = mons.filter { !$0.continuous && $0.supported && $0.incomplete }
        if milOn {
            return ("Not ready: the check-engine light is on", false,
                    "Vehicles with the check-engine light on fail inspection. Fix the problem first.")
        }
        if notReady.count > allowed {
            return ("Not ready yet: \(notReady.count) self-tests still running", false,
                    "Most inspections allow \(allowed) unfinished test\(allowed > 1 ? "s" : ""). Drive normally for a few days, then check again.")
        }
        return ("Ready for inspection", true,
                "The check-engine light is off and enough self-tests have finished.")
    }
}
