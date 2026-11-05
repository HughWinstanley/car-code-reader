import Foundation

struct Dtc { let code: String; let status: String; var module = "Engine (ECM/PCM)" }

/// Which wires a module is on. "ms" is Ford's medium-speed network, which only OBDLink-type adapters reach.
enum ModuleBus { case hs, ms, j1850 }
struct ModuleTarget { let id: Int; let name: String; let bus: ModuleBus }
struct ScannedModule { let target: ModuleTarget; let codes: [Dtc] }

/// Where each vehicle's modules live, taken from the Mac app (obd_core.py).
enum ModuleTable {
    static let ecuNames = [
        "7E8": "Engine (ECM/PCM)", "7E9": "Transmission (TCM)", "7EA": "OBD module #3",
        "7EB": "OBD module #4", "7EC": "OBD module #5", "7ED": "OBD module #6",
        "7EE": "OBD module #7", "7EF": "OBD module #8",
        "18DAF110": "Engine (ECM/PCM)", "18DAF111": "Engine #2", "18DAF118": "Transmission (TCM)",
        "10": "Engine (ECM/PCM)", "18": "Transmission (TCM)",
    ]
    static let modules11Bit: [(Int, String)] = [
        (0x7E0, "Engine (ECM/PCM)"), (0x7E1, "Transmission (TCM)"), (0x7E2, "OBD module #3"),
        (0x7E3, "OBD module #4"), (0x7E4, "OBD module #5"), (0x7E5, "OBD module #6"),
        (0x7E6, "OBD module #7"), (0x7E7, "OBD module #8"),
        (0x760, "ABS / brakes (typical Ford)"), (0x737, "Airbag (typical Ford)"),
        (0x726, "Body control (typical Ford)"), (0x720, "Instrument cluster (typical Ford)"),
        (0x730, "Power steering (typical Ford)"),
        (0x7B0, "ABS / brakes (typical Toyota/Lexus)"), (0x780, "Airbag (typical Toyota/Lexus)"),
        (0x7C0, "Instrument cluster (typical Toyota/Lexus)"),
        (0x241, "Body control (typical GM)"), (0x243, "ABS / brakes (typical GM)"), (0x247, "Airbag (typical GM)"),
        (0x7D1, "ABS / brakes (typical Hyundai/Kia)"), (0x7D2, "Airbag (typical Hyundai/Kia)"),
        (0x7A0, "Body control (typical Hyundai/Kia)"), (0x7C6, "Instrument cluster (typical Hyundai/Kia)"),
        (0x713, "ABS / brakes (typical VW/Audi)"), (0x715, "Airbag (typical VW/Audi)"),
        (0x710, "Gateway (typical VW/Audi)"),
    ]
    static let modules29Bit = [0x10: "Engine (ECM/PCM)", 0x11: "Engine #2", 0x18: "Transmission (TCM)"]
    static let ford: [(Int, String)] = [
        (0x7E0, "Engine (PCM)"), (0x7E1, "Transmission (TCM)"), (0x760, "ABS / brakes"),
        (0x737, "Airbag (RCM)"), (0x726, "Body control (BCM)"), (0x720, "Instrument cluster (IPC)"),
        (0x730, "Power steering (PSCM)"), (0x7D0, "SYNC / infotainment (APIM)"), (0x727, "Audio (ACM)"),
        (0x733, "Climate control (HVAC)"), (0x736, "Parking aid (PAM)"),
    ]
    static let fordExtra = [0x724, 0x740, 0x741, 0x761, 0x765, 0x706, 0x7A7, 0x775, 0x70C, 0x732, 0x734, 0x7C5]
    static let gm = [0x241: "Body control (BCM)", 0x243: "ABS / brakes (EBCM)", 0x247: "Airbag (SDM)"]
    static let legacyRanges: [(ClosedRange<Int>, String)] = [
        (0x10...0x17, "Engine (PCM)"), (0x18...0x1F, "Transmission / transfer case"),
        (0x28...0x2F, "ABS / brakes"), (0x30...0x37, "Steering"), (0x38...0x3F, "Suspension"),
        (0x40...0x57, "Body control (BCM/GEM)"), (0x58...0x5F, "Airbag (SDM/RCM)"),
        (0x60...0x6F, "Instrument cluster"), (0x70...0x7F, "Lighting"), (0x80...0x8F, "Radio / audio"),
        (0x90...0x97, "Phone / communication"), (0x98...0x9F, "Climate control (HVAC)"),
        (0xA0...0xBF, "Doors / seats / convenience"), (0xC0...0xC7, "Security / anti-theft"),
    ]
    static let legacyQuick = [0x10, 0x11, 0x18, 0x1A, 0x28, 0x29, 0x30, 0x38, 0x40, 0x41, 0x45,
                              0x58, 0x60, 0x61, 0x80, 0x98, 0x99, 0xA0, 0xA1, 0xC0]

    static func isSafety(_ name: String) -> Bool {
        let n = name.lowercased()
        return ["abs", "brake", "airbag", "restraint", "sdm", "rcm"].contains { n.contains($0) }
    }

    private static func name(_ id: Int, ford: Bool, prefix: String = "Module") -> String {
        let table = ford ? Dictionary(uniqueKeysWithValues: Self.ford) : gm
        return table[id] ?? Dictionary(uniqueKeysWithValues: modules11Bit)[id] ?? String(format: "\(prefix) 0x%03X", id)
    }

    static func targets(is29Bit: Bool, deep: Bool, make: Make, msCan: Bool) -> [ModuleTarget] {
        if is29Bit {   // try every address (skip the tester's own 0xF1 and broadcast 0x33)
            return (0..<0x100).filter { $0 != 0x33 && $0 != 0xF1 }.map {
                ModuleTarget(id: $0, name: modules29Bit[$0] ?? String(format: "Module 0x%02X", $0), bus: .hs)
            }
        }
        let isFord = make == .ford, isGM = make == .gm
        if deep {
            let ids = Array(0x700..<0x7F0) + Array(0x240..<0x260)
            var out = ids.filter { $0 != 0x7DF }.map { ModuleTarget(id: $0, name: name($0, ford: isFord), bus: .hs) }
            if msCan && !isGM {
                out += (0x700..<0x7F0).filter { $0 != 0x7DF }.map { ModuleTarget(id: $0, name: name($0, ford: true), bus: .ms) }
            }
            return out
        }
        let table11 = Dictionary(uniqueKeysWithValues: modules11Bit)
        let obd = (0x7E0..<0x7E8).map { ModuleTarget(id: $0, name: table11[$0]!, bus: .hs) }
        let gmList = (0x241..<0x260).map { ModuleTarget(id: $0, name: name($0, ford: false, prefix: "GM module"), bus: .hs) }
        let fordIds = ford.map(\.0).filter { $0 != 0x7E0 && $0 != 0x7E1 } + fordExtra
        let fordHS = fordIds.map { ModuleTarget(id: $0, name: name($0, ford: true, prefix: "Ford module"), bus: .hs) }
        let fordMS = msCan ? fordIds.map { ModuleTarget(id: $0, name: name($0, ford: true, prefix: "Ford module"), bus: .ms) } : []
        if isGM { return obd + gmList }
        if isFord { return obd + fordHS + fordMS }
        let others = modules11Bit.filter { !(0x7E0..<0x7E8).contains($0.0) }.map { ModuleTarget(id: $0.0, name: $0.1, bus: .hs) }
        var seen = Set<String>()
        return (obd + others + gmList + fordHS + fordMS).filter { seen.insert("\($0.id)\($0.bus)").inserted }
    }

    static func legacyTargets(deep: Bool) -> [ModuleTarget] {
        (deep ? Array(0x10..<0xF0) : legacyQuick).filter { $0 != 0xF1 }.map { addr in
            let name = legacyRanges.first { $0.0.contains(addr) }?.1 ?? String(format: "Module 0x%02X", addr)
            return ModuleTarget(id: addr, name: name, bus: .j1850)
        }
    }

    /// UDS status byte -> words (the Mac app's uds_status_text).
    static func statusText(_ status: UInt8) -> String {
        var parts: [String] = []
        if status & 0x01 != 0 { parts.append("Active now") }
        if status & 0x08 != 0 { parts.append("Stored") } else if status & 0x04 != 0 { parts.append("Pending") }
        if status & 0x80 != 0 { parts.append("Warning light on") }
        return parts.isEmpty ? "History" : parts.joined(separator: ", ")
    }
}

/// The ELM327 "language": wake the vehicle (trying each protocol if auto-detect misses it,
/// which is what lets it read 1996-2005 GM trucks), read and clear codes, VIN, voltage, readiness, live data.
final class ELM327 {
    private let link: OBDLink
    private(set) var ecus: [String] = []
    private(set) var protocolName = ""
    private(set) var protocolNumber = ""   // from ATDPN: 1-2 = J1850, 6-9 = CAN (7 and 9 are 29-bit)
    private(set) var isSTN = false         // OBDLink-type adapter (can reach Ford MS-CAN)
    private var bus: ModuleBus? = nil
    var isCAN: Bool { ["6", "7", "8", "9"].contains(protocolNumber) }
    var is29Bit: Bool { protocolNumber == "7" || protocolNumber == "9" }
    var isJ1850: Bool { protocolNumber == "1" || protocolNumber == "2" }
    var canScanModules: Bool { isCAN || isJ1850 }
    init(_ link: OBDLink) { self.link = link }

    func initialize() async throws {
        _ = try? await link.command("ATZ", timeout: 4)
        for c in ["ATE0", "ATL0", "ATS0", "ATH0", "ATAT1"] { _ = try await link.command(c) }
        let sti = (try? await link.command("STI", timeout: 1.5)) ?? ""   // OBDLink (STN chip) adapters answer this
        isSTN = sti.uppercased().contains("STN")
        ecus = []
        _ = try await link.command("ATSP0")                 // automatic protocol search first
        if try await handshake(timeout: 25) { return }
        for proto in ["2", "1", "3", "4", "5", "6", "7", "8", "9"] {   // 2 = J1850 VPW (GM), then the rest
            _ = try await link.command("ATSP\(proto)")
            if try await handshake(timeout: 12) { return }
        }
        _ = try await link.command("ATSP0")
        throw OBDError.noAnswer
    }

    private func handshake(timeout: TimeInterval) async throws -> Bool {
        let reply = try await link.command("0100", timeout: timeout)
        let bytes = ELM327.hexBytes(reply)
        for i in 0..<max(0, bytes.count - 1) where bytes[i] == 0x41 && bytes[i + 1] == 0x00 {
            let dpn = (try? await link.command("ATDPN"))?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            protocolNumber = String(dpn.suffix(1)).uppercased()
            protocolName = (try? await link.command("ATDP"))?
                .replacingOccurrences(of: "AUTO, ", with: "")
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            return true
        }
        return false
    }

    /// Stored, pending and permanent codes, with the module that reported each one.
    func readDTCs() async throws -> [Dtc] {
        _ = try await link.command("ATH1")
        var out: [Dtc] = []
        do {
            for (cmd, sid, status) in [("03", UInt8(0x43), "Stored"), ("07", UInt8(0x47), "Pending"), ("0A", UInt8(0x4A), "Permanent")] {
                for (ecu, messages) in try await request(cmd, timeout: 10) {
                    for m in messages where m.first == sid {
                        let body = Array(m.dropFirst(isCAN ? 2 : 1))   // CAN replies carry a count byte
                        for i in stride(from: 0, to: body.count - 1, by: 2) where body[i] != 0 || body[i + 1] != 0 {
                            let code = ELM327.decode(body[i], body[i + 1])
                            if !out.contains(where: { $0.code == code && $0.status == status }) {
                                out.append(Dtc(code: code, status: status, module: ModuleTable.ecuNames[ecu] ?? "Module \(ecu)"))
                            }
                        }
                    }
                }
            }
        } catch {
            _ = try? await link.command("ATH0")
            throw error
        }
        _ = try await link.command("ATH0")
        return out
    }

    func clearCodes() async throws { _ = try await link.command("04", timeout: 6) }

    func readVIN() async throws -> String {
        let bytes = ELM327.hexBytes(try await link.command("0902", timeout: 8))
        guard let i = firstIndex(bytes, 0x49, 0x02) else { return "" }
        let ascii = bytes[(i + 3)...].filter { (48...90).contains($0) || (97...122).contains($0) }
        let s = String(ascii.map { Character(UnicodeScalar($0)) })
        return s.count >= 17 ? String(s.suffix(17)) : s
    }

    func voltage() async throws -> String {
        (try await link.command("ATRV")).trimmingCharacters(in: .whitespacesAndNewlines)
    }

    func readiness() async throws -> [UInt8]? {
        let bytes = ELM327.hexBytes(try await link.command("0101", timeout: 6))
        guard let i = firstIndex(bytes, 0x41, 0x01), bytes.count >= i + 6 else { return nil }
        return Array(bytes[(i + 2)...(i + 5)])
    }

    func pid(_ pid: UInt8) async throws -> [UInt8]? {
        let cmd = String(format: "01%02X", pid)
        let bytes = ELM327.hexBytes(try await link.command(cmd, timeout: 4))
        guard let i = firstIndex(bytes, 0x41, pid) else { return nil }
        return Array(bytes[(i + 2)...])
    }

    /// Read a manufacturer-specific value via mode $22 (e.g. Ford/GM transmission fluid temp).
    /// Returns the data bytes after the 2-byte identifier echo.
    func readMode22(_ did: UInt16) async throws -> [UInt8]? {
        let hi = UInt8(did >> 8), lo = UInt8(did & 0xFF)
        let cmd = String(format: "22%02X%02X", hi, lo)
        let bytes = ELM327.hexBytes(try await link.command(cmd, timeout: 4))
        guard let i = ELM327.find3(bytes, 0x62, hi, lo) else { return nil }
        return Array(bytes[(i + 3)...])
    }

    static func find3(_ bytes: [UInt8], _ a: UInt8, _ b: UInt8, _ c: UInt8) -> Int? {
        guard bytes.count >= 3 else { return nil }
        for i in 0...(bytes.count - 3) where bytes[i] == a && bytes[i + 1] == b && bytes[i + 2] == c { return i }
        return nil
    }

    // MARK: parsing helpers
    static func hexBytes(_ reply: String) -> [UInt8] {
        var bytes: [UInt8] = []
        let flat = reply.replacingOccurrences(of: "\r", with: " ").replacingOccurrences(of: "\n", with: " ")
        for token in flat.split(separator: " ") {
            // ATS0 runs the bytes together, and long replies come as "0:4902...", "1:...".
            var t = token.trimmingCharacters(in: .whitespaces)
            if let colon = t.firstIndex(of: ":") { t = String(t[t.index(after: colon)...]) }
            guard t.count >= 2, t.count % 2 == 0, t.allSatisfy(\.isHexDigit) else { continue }
            var i = t.startIndex
            while i < t.endIndex {
                let next = t.index(i, offsetBy: 2)
                if let b = UInt8(t[i..<next], radix: 16) { bytes.append(b) }
                i = next
            }
        }
        return bytes
    }

    private func firstIndex(_ bytes: [UInt8], _ a: UInt8, _ b: UInt8) -> Int? {
        ELM327.find(bytes, a, b)
    }
    static func find(_ bytes: [UInt8], _ a: UInt8, _ b: UInt8) -> Int? {
        guard bytes.count >= 2 else { return nil }
        for i in 0...(bytes.count - 2) where bytes[i] == a && bytes[i + 1] == b { return i }
        return nil
    }

    static func decode(_ a: UInt8, _ b: UInt8) -> String {
        let letter = ["P", "C", "B", "U"][Int(a >> 6)]
        let second = String((a >> 4) & 0x3)
        let third  = String((a & 0xF), radix: 16, uppercase: true)
        return letter + second + third + String(format: "%02X", b)
    }

    // MARK: - Modules beyond the engine computer (ABS, airbag, body...), ported from the Mac app's obd_core.py

    private func lines(_ cmd: String, timeout: TimeInterval = 5) async throws -> [String] {
        let reply = try await link.command(cmd, timeout: timeout)
        var out = reply.replacingOccurrences(of: "\0", with: "").split(whereSeparator: { $0 == "\r" || $0 == "\n" })
            .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
        if let first = out.first, first.replacingOccurrences(of: " ", with: "").uppercased() == cmd.replacingOccurrences(of: " ", with: "").uppercased() {
            out.removeFirst()   // echo
        }
        return out
    }

    private static func hexData(_ hex: String) -> [UInt8] {
        var out: [UInt8] = [], i = hex.startIndex
        while let next = hex.index(i, offsetBy: 2, limitedBy: hex.endIndex), i != hex.endIndex {
            out.append(UInt8(hex[i..<next], radix: 16) ?? 0)
            i = next
        }
        return out
    }

    /// Join ISO-TP CAN frames (each starting with its PCI byte) into whole messages.
    static func reassemble(_ frames: [[UInt8]]) -> [[UInt8]] {
        var messages: [[UInt8]] = [], current: [UInt8]? = nil, need = 0
        for f in frames where !f.isEmpty {
            switch f[0] >> 4 {
            case 0:
                messages.append(Array(f.dropFirst().prefix(Int(f[0] & 0x0F))))
                current = nil
            case 1 where f.count >= 2:
                need = Int(f[0] & 0x0F) << 8 | Int(f[1])
                current = Array(f.dropFirst(2))
            case 2:
                guard current != nil else { continue }
                current! += f.dropFirst()
                if current!.count >= need {
                    messages.append(Array(current!.prefix(need)))
                    current = nil
                }
            default: break
            }
        }
        if let current { messages.append(current) }
        return messages
    }

    /// Reply lines (with headers on) -> [module header: messages].
    func parse(_ lines: [String]) -> [String: [[UInt8]]] {
        let frames = lines.map { $0.replacingOccurrences(of: " ", with: "").uppercased() }
            .filter { $0.count >= 4 && $0.allSatisfy(\.isHexDigit) }
        var out: [String: [[UInt8]]] = [:]
        if isCAN {
            let headerLength = is29Bit ? 8 : 3
            var groups: [String: [[UInt8]]] = [:]
            for f in frames where f.count > headerLength && (f.count - headerLength) % 2 == 0 {
                groups[String(f.prefix(headerLength)), default: []].append(ELM327.hexData(String(f.dropFirst(headerLength))))
            }
            for (header, list) in groups {
                let messages = ELM327.reassemble(list)
                if !messages.isEmpty { out[header] = messages }
            }
        } else {   // older protocols: 3 header bytes + data + checksum
            for f in frames where f.count >= 10 && f.count % 2 == 0 {
                let b = ELM327.hexData(f)
                out[String(format: "%02X", b[2]), default: []].append(Array(b[3..<(b.count - 1)]))
            }
        }
        return out
    }

    private func request(_ cmd: String, timeout: TimeInterval = 5) async throws -> [String: [[UInt8]]] {
        parse(try await lines(cmd, timeout: timeout))
    }

    func moduleTargets(deep: Bool, make: Make) -> [ModuleTarget] {
        isJ1850 ? ModuleTable.legacyTargets(deep: deep)
                : ModuleTable.targets(is29Bit: is29Bit, deep: deep, make: make, msCan: isSTN)
    }

    /// Ask each module for its codes. `progress` gets (index, total, module name) and returns false to stop early.
    func moduleScan(_ targets: [ModuleTarget], progress: (Int, Int, String) async -> Bool) async throws -> [ScannedModule] {
        var found: [ScannedModule] = []
        var failure: Error? = nil
        do {
            if isJ1850 {
                _ = try await link.command("ATH1")
                _ = try await link.command("ATAT0")
                _ = try await link.command("ATST32")
                _ = try await link.command("ATAL")
            } else {
                bus = nil
                _ = try await link.command("ATH1")
            }
            for (i, t) in targets.enumerated() {
                guard await progress(i, targets.count, t.name + (t.bus == .ms ? " (second network)" : "")) else { break }
                if let codes = try await readModule(t) { found.append(ScannedModule(target: t, codes: codes)) }
            }
        } catch { failure = error }
        try await restore()
        if let failure { throw failure }
        return found
    }

    private func readModule(_ t: ModuleTarget) async throws -> [Dtc]? {
        if t.bus == .j1850 {
            _ = try await link.command("ATSH" + legacyHeader(t.id))
            return try await legacyRead(t)
        }
        try await selectBus(t.bus)
        if !is29Bit && (0x240...0x25F).contains(t.id) { return try await gmlanRead(t) }   // GM GMLAN address range
        try await udsTarget(t.id)
        for (_, messages) in try await request("19028D", timeout: 2) {
            for m in messages {
                if m.count >= 3 && m[0] == 0x59 && m[1] == 0x02 {
                    let records = Array(m.dropFirst(3))
                    var codes: [Dtc] = []
                    for j in stride(from: 0, to: records.count - 3, by: 4) where records[j + 3] & 0x8D != 0 {
                        let code = ELM327.decode(records[j], records[j + 1]) + String(format: "-%02X", records[j + 2])
                        codes.append(Dtc(code: code, status: ModuleTable.statusText(records[j + 3]), module: t.name))
                    }
                    return codes
                }
                if m.count >= 2 && m[0] == 0x7F && m[1] == 0x19 {   // module is there but speaks KWP2000
                    return try await kwpRead(t)
                }
            }
        }
        return nil
    }

    /// Older CAN modules (e.g. some 2005-2010 Fords) use KWP2000 service $18 instead of $19.
    private func kwpRead(_ t: ModuleTarget) async throws -> [Dtc] {
        for req in ["1800FF00", "1802FF00"] {
            for (_, messages) in try await request(req, timeout: 2) {
                for m in messages where m.first == 0x58 {
                    let body = Array(m.dropFirst(2))
                    var codes: [Dtc] = []
                    for i in stride(from: 0, to: body.count - 2, by: 3) where body[i] != 0 || body[i + 1] != 0 {
                        codes.append(Dtc(code: ELM327.decode(body[i], body[i + 1]), status: "Stored", module: t.name))
                    }
                    return codes
                }
            }
        }
        return []
    }

    private func rawFrames(_ lines: [String]) -> [(id: String, data: [UInt8])] {
        lines.map { $0.replacingOccurrences(of: " ", with: "").uppercased() }
            .filter { $0.count >= 5 && $0.allSatisfy(\.isHexDigit) && ($0.count - 3) % 2 == 0 }
            .map { (String($0.prefix(3)), ELM327.hexData(String($0.dropFirst(3)))) }
    }

    /// GM 2007-2016 (GMLAN) service $A9/$81. Codes come back as single frames on ID+0x300.
    /// Returns nil if the module stayed silent.
    private func gmlanRead(_ t: ModuleTarget) async throws -> [Dtc]? {
        _ = try await link.command("ATCAF0")
        _ = try await link.command(String(format: "ATSH%03X", t.id))
        let reply = try await lines("03A9811200000000", timeout: 2)   // status mask $12 = current + history
        _ = try await link.command("ATCAF1")
        let uudt = String(format: "%03X", t.id + 0x300), usdt = String(format: "%03X", t.id + 0x400)
        var answered = false, codes: [Dtc] = []
        for (id, data) in rawFrames(reply) {
            if id == usdt { answered = true }
            if id == uudt && data.first == 0x81 {
                answered = true
                if data.count >= 5 && (data[1] != 0 || data[2] != 0) {
                    let st = data[4]
                    var label = st & 0x02 != 0 ? "Current" : st & 0x10 != 0 ? "History (not active now)" : "Stored"
                    if st & 0x80 != 0 { label += ", warning light on" }
                    if data[3] != 0 { label += String(format: ", symptom %02X", data[3]) }
                    let code = ELM327.decode(data[1], data[2])
                    if !codes.contains(where: { $0.code == code && $0.status == label }) {
                        codes.append(Dtc(code: code, status: label, module: t.name))
                    }
                }
            }
        }
        return answered ? codes : nil
    }

    // Older trucks: GM Class 2 (J1850 VPW) and Ford SCP (J1850 PWM).
    private func legacyHeader(_ addr: Int) -> String {   // GM uses priority byte 6C, Ford SCP uses C4; the scan tool is F1
        String(format: protocolNumber == "2" ? "6C%02XF1" : "C4%02XF1", addr)
    }

    private func legacyReplies(_ cmd: String, addr: Int, sid: UInt8) async throws -> (answered: Bool, messages: [[UInt8]]) {
        let all = try await request(cmd, timeout: 2)[String(format: "%02X", addr)] ?? []
        return (!all.isEmpty, all.filter { $0.first == sid })
    }

    private func legacyRead(_ t: ModuleTarget) async throws -> [Dtc]? {
        func add(_ code: String, _ status: String, _ to: inout [Dtc]) {
            if !to.contains(where: { $0.code == code }) { to.append(Dtc(code: code, status: status, module: t.name)) }
        }
        var out: [Dtc] = []
        if protocolNumber == "2" {   // GM Class 2: service $19, one code per reply, list ends with 00 00
            let current = try await legacyReplies("19D2FF00", addr: t.id, sid: 0x59)
            guard current.answered else { return nil }
            let all = try await legacyReplies("19FFFF00", addr: t.id, sid: 0x59)
            for m in current.messages where m.count >= 3 && (m[1] != 0 || m[2] != 0) { add(ELM327.decode(m[1], m[2]), "Current", &out) }
            for m in all.messages where m.count >= 3 && (m[1] != 0 || m[2] != 0) { add(ELM327.decode(m[1], m[2]), "History (not active now)", &out) }
            return out
        }
        // Ford SCP: try service $13 (all codes), then $18 (codes by status)
        let first = try await legacyReplies("13", addr: t.id, sid: 0x53)
        for m in first.messages {
            let body = Array(m.dropFirst())
            for i in stride(from: 0, to: body.count - 1, by: 2) where body[i] != 0 || body[i + 1] != 0 { add(ELM327.decode(body[i], body[i + 1]), "Stored", &out) }
        }
        if !first.messages.isEmpty { return out }
        let second = try await legacyReplies("1800FF00", addr: t.id, sid: 0x58)
        for m in second.messages {
            var body = Array(m.dropFirst())
            if body.count % 3 == 1 { body.removeFirst() }   // leading count byte
            for i in stride(from: 0, to: body.count - 2, by: 3) where body[i] != 0 || body[i + 1] != 0 { add(ELM327.decode(body[i], body[i + 1]), "Stored", &out) }
        }
        return (first.answered || second.answered) ? out : nil
    }

    private func udsSetup() async throws {
        _ = try await link.command("ATAT0")
        _ = try await link.command("ATST32")   // wait up to 200 ms for each module
        if is29Bit {
            for c in ["ATCP18", "ATCF18DAF100", "ATCM1FFFFF00"] { _ = try await link.command(c) }
        } else {
            for c in ["ATCF400", "ATCM400"] { _ = try await link.command(c) }   // accept replies from IDs 0x400-0x7FF
        }
        _ = try await link.command("ATFCSD300000")
        _ = try await link.command("ATFCSM1")
    }

    /// Switch between the normal high-speed CAN and Ford's MS-CAN (OBDLink only).
    private func selectBus(_ wanted: ModuleBus) async throws {
        if wanted == bus { return }
        if wanted == .ms {
            _ = try await link.command("STP53")   // ISO 15765, 11-bit, 125 kbps on pins 3/11
        } else if bus == .ms {
            _ = try await link.command("STP33")   // back to 500 kbps on pins 6/14
        }
        bus = wanted
        try await udsSetup()                      // filters must be set again after STP
    }

    private func udsTarget(_ id: Int) async throws {
        if is29Bit {
            _ = try await link.command(String(format: "ATSHDA%02XF1", id))
            _ = try await link.command(String(format: "ATFCSH18DA%02XF1", id))
        } else {
            _ = try await link.command(String(format: "ATSH%03X", id))
            _ = try await link.command(String(format: "ATFCSH%03X", id))
        }
    }

    /// Put the adapter back the way the engine-computer commands expect it.
    private func restore() async throws {
        if bus == .ms { _ = try await link.command("STP33") }
        bus = nil
        _ = try await link.command("ATWS", timeout: 4)
        for c in ["ATE0", "ATL0", "ATS0", "ATH0", "ATAT1", "ATSPA" + (protocolNumber.isEmpty ? "0" : protocolNumber)] {
            _ = try await link.command(c)
        }
    }

    /// Erase codes from the given modules (the Clear codes button).
    func moduleClear(_ targets: [ModuleTarget]) async throws {
        var failure: Error? = nil
        do {
            bus = nil
            _ = try await link.command("ATH1")
            if isJ1850 {
                _ = try await link.command("ATAT0")
                _ = try await link.command("ATST32")
            }
            for t in targets {
                if t.bus == .j1850 {
                    _ = try await link.command("ATSH" + legacyHeader(t.id))
                    _ = try await legacyReplies("14", addr: t.id, sid: 0x54)
                    continue
                }
                try await selectBus(t.bus)
                if !is29Bit && (0x240...0x25F).contains(t.id) {
                    _ = try await link.command("ATCAF0")
                    _ = try await link.command(String(format: "ATSH%03X", t.id))
                    _ = try await lines("0104000000000000", timeout: 3)
                    _ = try await link.command("ATCAF1")
                    continue
                }
                try await udsTarget(t.id)
                for req in ["14FFFFFF", "14FF00"] {   // UDS, then KWP2000 style
                    let reply = try await request(req, timeout: 4)
                    if reply.values.contains(where: { $0.contains { $0.first == 0x54 } }) { break }
                }
            }
        } catch { failure = error }
        try await restore()
        if let failure { throw failure }
    }
}
