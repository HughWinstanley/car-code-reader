import Foundation

struct Dtc { let code: String; let status: String }

/// The ELM327 "language": wake the vehicle (trying each protocol if auto-detect misses it,
/// which is what lets it read 1996-2005 GM trucks), read and clear codes, VIN, voltage, readiness, live data.
final class ELM327 {
    private let link: OBDLink
    private(set) var ecus: [String] = []
    private(set) var protocolName = ""
    init(_ link: OBDLink) { self.link = link }

    func initialize() async throws {
        _ = try? await link.command("ATZ", timeout: 4)
        for c in ["ATE0", "ATL0", "ATS0", "ATH0", "ATAT1"] { _ = try await link.command(c) }
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
            protocolName = (try? await link.command("ATDP"))?
                .replacingOccurrences(of: "AUTO, ", with: "")
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            return true
        }
        return false
    }

    func readDTCs() async throws -> [Dtc] {
        var out: [Dtc] = []
        for (cmd, marker, status) in [("03", UInt8(0x43), "Stored"),
                                      ("07", UInt8(0x47), "Pending"),
                                      ("0A", UInt8(0x4A), "Permanent")] {
            let bytes = ELM327.hexBytes(try await link.command(cmd, timeout: 8))
            for code in ELM327.parseDTCs(bytes, marker: marker) { out.append(Dtc(code: code, status: status)) }
        }
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
            let t = token.trimmingCharacters(in: .whitespaces)
            if t.count == 2, let b = UInt8(t, radix: 16) { bytes.append(b) }
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

    /// Collect codes after every occurrence of the mode marker (handles several modules answering).
    static func parseDTCs(_ bytes: [UInt8], marker: UInt8) -> [String] {
        var codes: [String] = []
        var i = 0
        while i < bytes.count {
            if bytes[i] == marker {
                var j = i + 1
                while j + 1 < bytes.count && bytes[j] != marker {
                    let a = bytes[j], b = bytes[j + 1]
                    if a == 0 && b == 0 { j += 2; continue }
                    let code = decode(a, b)
                    if !codes.contains(code) { codes.append(code) }
                    j += 2
                }
                i = j
            } else { i += 1 }
        }
        return codes
    }

    static func decode(_ a: UInt8, _ b: UInt8) -> String {
        let letter = ["P", "C", "B", "U"][Int(a >> 6)]
        let second = String((a >> 4) & 0x3)
        let third  = String((a & 0xF), radix: 16, uppercase: true)
        return letter + second + third + String(format: "%02X", b)
    }
}
