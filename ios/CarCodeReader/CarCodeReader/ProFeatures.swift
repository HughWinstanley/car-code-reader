import SwiftUI
import Charts
import UniformTypeIdentifiers

// MARK: - Data

struct SelfTest: Identifiable {
    let id = UUID()
    let mid: Int, tid: Int
    let name: String
    let value: Double, low: Double, high: Double
    let unit: String
    let passed: Bool
    var isMisfire: Bool { (0xA2...0xAD).contains(mid) && (tid == 0x0B || tid == 0x0C) }
}

struct ModuleInfo: Identifiable {
    var id: String { ecu }
    let ecu: String
    var name = ""
    var calids: [String] = []
    var cvns: [String] = []
    var usage: [(String, String)] = []
}

struct BatteryRow: Identifiable {
    let id = UUID()
    let label: String, value: String, verdict: String
    let good: Bool
}

struct Recall: Identifiable {
    var id: String { campaign }
    let campaign: String, date: String, component: String, summary: String, consequence: String, remedy: String
    let parkIt: Bool
}

struct ScanRecord: Codable, Identifiable {
    struct Code: Codable { let code: String, text: String, module: String, status: String, level: String }
    var id: String { when.description + vehicle }
    let when: Date
    let vehicle: String, name: String, vin: String, kind: String
    let milOn: Bool?
    let codes: [Code]
}

/// Every scan, saved per vehicle in the app's own folder and never sent anywhere (the Mac app's history.py).
enum ScanHistory {
    private static let maxPerVehicle = 50
    private static var url: URL? {
        guard let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first else { return nil }
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent("history.json")
    }
    static func load() -> [ScanRecord] {
        guard let url, let data = try? Data(contentsOf: url) else { return [] }
        return (try? JSONDecoder().decode([ScanRecord].self, from: data)) ?? []
    }
    static func add(_ record: ScanRecord) {
        var all = load()
        all.append(record)
        let mine = all.filter { $0.vehicle == record.vehicle }.sorted { $0.when < $1.when }
        if mine.count > maxPerVehicle, let oldest = mine.first, let at = all.firstIndex(where: { $0.id == oldest.id }) { all.remove(at: at) }
        if let url, let data = try? JSONEncoder().encode(all) { try? data.write(to: url, options: .atomic) }
    }
    static func clear() { if let url { try? FileManager.default.removeItem(at: url) } }
    /// Newest vehicle first, each with its scans newest first.
    static func byVehicle() -> [(name: String, scans: [ScanRecord])] {
        Dictionary(grouping: load(), by: \.vehicle).values
            .map { group in
                let scans = group.sorted { $0.when > $1.when }
                return (scans[0].name, scans)
            }
            .sorted { $0.1[0].when > $1.1[0].when }
    }
}

/// Safety recalls from the U.S. government's free NHTSA database (the Mac app's recalls.py).
enum Recalls {
    private static func json(_ url: String) async throws -> [String: Any] {
        guard let u = URL(string: url) else { throw URLError(.badURL) }
        let (data, _) = try await URLSession.shared.data(from: u)
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }
    private static func enc(_ s: String) -> String { s.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed.subtracting(CharacterSet(charactersIn: "&+="))) ?? s }
    private static func norm(_ t: String) -> String {
        t.uppercased().replacingOccurrences(of: "SUPER DUTY", with: "SD").replacingOccurrences(of: "HEAVY DUTY", with: "HD")
            .filter { $0.isASCII && ($0.isLetter || $0.isNumber) }
    }
    private static func variants(_ model: String) -> [String] {
        let clean = model.replacingOccurrences(of: "\\(.*?\\)", with: "", options: .regularExpression)
        let parts = clean.split(separator: "/").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
        guard let firstWord = parts.first?.split(separator: " ").first else { return [] }
        return parts.map { norm($0.first?.isNumber == true ? "\(firstWord) \($0)" : $0) }.filter { !$0.isEmpty }
    }
    /// Names to ask the recall search for directly: "F-250 Super Duty" -> "F-250 SD". NHTSA's model list can leave
    /// out vehicles that do have recalls, so the list alone can't say a vehicle isn't there.
    private static func directNames(_ model: String) -> [String] {
        let clean = model.replacingOccurrences(of: "\\(.*?\\)", with: "", options: .regularExpression)
        let parts = clean.split(separator: "/").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
        guard let firstWord = parts.first?.split(separator: " ").first else { return [] }
        var out: [String] = []
        for part in parts {
            let name = (part.first?.isNumber == true ? "\(firstWord) \(part)" : part).uppercased()
                .replacingOccurrences(of: "SUPER DUTY", with: "SD").replacingOccurrences(of: "HEAVY DUTY", with: "HD")
            if !out.contains(name) { out.append(name) }
        }
        return out
    }
    /// Leftovers only count as the same vehicle if they're a size or duty rating, not another model.
    private static func sameLine(_ extra: String) -> Bool {
        extra.range(of: "^(\\d+|HD|SD|PICKUP|TRUCK)*$", options: .regularExpression) != nil
    }
    private static func sentence(_ text: String) -> String {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard t == t.uppercased(), !t.isEmpty else { return t }
        var out = "", startOfSentence = true
        for ch in t.lowercased() {
            out.append(startOfSentence && ch.isLetter ? Character(ch.uppercased()) : ch)
            if ch.isLetter { startOfSentence = false } else if ".!?".contains(ch) { startOfSentence = true }
        }
        return out
    }
    /// `matched` is false when the vehicle couldn't be found in the database, which is not the same as "no recalls".
    static func find(make: String, model: String, year: Int?, vin: String) async throws -> (recalls: [Recall], matched: Bool) {
        var (make, model, year) = (make, model, year)
        if vin.count == 17 {
            let d = try? await json("https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/\(enc(vin))?format=json")
            if let r = (d?["Results"] as? [[String: Any]])?.first, let m = r["Make"] as? String, !m.isEmpty,
               let y = r["ModelYear"] as? String, let yy = Int(y) {
                make = m
                year = yy
                if let vm = r["Model"] as? String, !vm.isEmpty { model = vm }
            }
        }
        guard !make.isEmpty, !model.isEmpty, let year else { return ([], false) }
        let list = try await json("https://api.nhtsa.gov/products/vehicle/models?modelYear=\(year)&make=\(enc(make.uppercased()))&issueType=r")
        let names = ((list["results"] as? [[String: Any]]) ?? []).compactMap { $0["model"] as? String }
        let wanted = variants(model)
        let matches = names.filter { name in
            let n = norm(name)
            guard n.count >= 3 else { return false }
            return wanted.contains { v in
                n == v || (v.hasPrefix(n) && sameLine(String(v.dropFirst(n.count)))) || (n.hasPrefix(v) && sameLine(String(n.dropFirst(v.count))))
            }
        }
        let listed = Set(matches.map(norm))
        var seen = Set<String>(), out: [Recall] = [], matched = !matches.isEmpty
        for name in matches + directNames(model).filter({ !listed.contains(norm($0)) }) {
            let d = try await json("https://api.nhtsa.gov/recalls/recallsByVehicle?make=\(enc(make.uppercased()))&model=\(enc(name))&modelYear=\(year)")
            let results = (d["results"] as? [[String: Any]]) ?? []
            if !results.isEmpty { matched = true }   // not in NHTSA's list, but the search knows it
            for r in results {
                let camp = r["NHTSACampaignNumber"] as? String ?? ""
                // 'V' = vehicle recall ('E' = aftermarket part)
                guard camp.count > 3, Array(camp)[2] == "V", seen.insert(camp).inserted else { continue }
                out.append(Recall(campaign: camp, date: r["ReportReceivedDate"] as? String ?? "",
                                  component: (r["Component"] as? String ?? "").replacingOccurrences(of: ":", with: " - ").capitalized,
                                  summary: sentence(r["Summary"] as? String ?? ""), consequence: sentence(r["Consequence"] as? String ?? ""),
                                  remedy: sentence(r["Remedy"] as? String ?? ""), parkIt: r["parkIt"] as? Bool ?? false))
            }
        }
        return (out.sorted { $0.campaign > $1.campaign }, matched)
    }
}

/// A file made only when the user actually shares it (reports and recordings).
struct ExportFile: Transferable {
    let data: Data
    let name: String
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(exportedContentType: .data) { file in
            let url = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
            try file.data.write(to: url, options: .atomic)
            return SentTransferredFile(url)
        }
    }
}

/// The adapter log for the Help page: passes everything through and keeps the last lines.
final class LoggingLink: OBDLink {
    private let inner: OBDLink
    private let onLine: (String) -> Void
    init(_ inner: OBDLink, onLine: @escaping (String) -> Void) { self.inner = inner; self.onLine = onLine }
    func connect() async throws { try await inner.connect() }
    func close() { inner.close() }
    func command(_ text: String, timeout: TimeInterval) async throws -> String {
        onLine("> " + text)
        let reply = try await inner.command(text, timeout: timeout)
        onLine("< " + reply.replacingOccurrences(of: "\r", with: " ").trimmingCharacters(in: .whitespaces))
        return reply
    }
}

// MARK: - Reader actions

extension Reader {
    /// Stop live data and run one read-only job with the busy flag held.
    private func runTest(_ step: String, _ work: @escaping (ELM327) async throws -> Void) {
        guard let e = elm, !busy else { return }
        busy = true
        status = step
        let live = pauseLive()
        Task {
            await live?.value
            do { try await work(e) } catch { testMessage = error.localizedDescription }
            status = "Connected."
            busy = false
        }
    }

    func readSelfTests() {
        testMessage = ""
        if isDemo {
            selfTests = [
                SelfTest(mid: 0x21, tid: 0x91, name: "Catalytic converter, bank 1", value: 0.42, low: 0, high: 1, unit: "ratio", passed: true),
                SelfTest(mid: 0x01, tid: 0x05, name: "Oxygen sensor, bank 1 sensor 1", value: 0.71, low: 0.2, high: 1.1, unit: "V", passed: true),
                SelfTest(mid: 0x3A, tid: 0xA1, name: "EVAP leak test (0.090 inch)", value: 3.6, low: 0, high: 2.5, unit: "kPa", passed: false),
                SelfTest(mid: 0xA2, tid: 0x0C, name: "Misfire, cylinder 1", value: 14, low: 0, high: 65535, unit: "counts", passed: true),
                SelfTest(mid: 0xA2, tid: 0x0B, name: "Misfire, cylinder 1", value: 9, low: 0, high: 65535, unit: "counts", passed: true),
                SelfTest(mid: 0xA3, tid: 0x0C, name: "Misfire, cylinder 2", value: 0, low: 0, high: 65535, unit: "counts", passed: true),
                SelfTest(mid: 0xA3, tid: 0x0B, name: "Misfire, cylinder 2", value: 0, low: 0, high: 65535, unit: "counts", passed: true),
            ]
            return
        }
        runTest("Reading self-test results…") { [weak self] e in self?.selfTests = try await e.selfTests() }
    }

    func readModuleInfo() {
        testMessage = ""
        if isDemo {
            moduleInfo = [ModuleInfo(ecu: "7E8", name: "ECM - Engine Control", calids: ["DEMO-CAL-0001"], cvns: ["A1B2C3D4"],
                                     usage: [("Ignition cycles counted", "812"), ("Catalyst, bank 1", "ran 96 times in 340 chances")])]
            return
        }
        runTest("Reading module info…") { [weak self] e in self?.moduleInfo = try await e.moduleInfo() }
    }

    func readFreezeFrame() {
        if isDemo {
            freezeFrame = [("Code that saved this snapshot", "P0301"), ("Engine RPM", "2140 rpm"), ("Vehicle speed", "41 mph  (66 km/h)"),
                           ("Coolant temperature", "194 °F  (90 °C)"), ("Engine load", "62.0 %")]
            freezeFrameRead = true
            return
        }
        runTest("Reading the freeze frame…") { [weak self] e in
            self?.freezeFrame = try await e.freezeFrame()
            self?.freezeFrameRead = true
        }
    }

    // Battery and charging test, one step at a time (the Mac app's battery_test).
    private func volts(_ e: ELM327) async -> Double? {
        guard let text = try? await e.voltage() else { return nil }
        return Double(text.uppercased().replacingOccurrences(of: "V", with: "").trimmingCharacters(in: .whitespacesAndNewlines))
    }
    private func engineRPM(_ e: ELM327) async -> Double? {
        guard let d = try? await e.pid(0x0C), d.count >= 2 else { return nil }
        return (Double(d[0]) * 256 + Double(d[1])) / 4
    }
    private func chargeRow(_ label: String, _ v: Double) -> BatteryRow {
        let (verdict, good) = (13.4...14.9).contains(v) ? ("Charging normally", true)
            : v > 14.9 ? ("Overcharging - check the alternator", false)
            : ("Not charging enough - check alternator, belt and cables", false)
        return BatteryRow(label: label, value: String(format: "%.2f V", v), verdict: verdict, good: good)
    }

    func batteryStart() {
        batteryRows = []; batteryPrompt = nil; batteryNote = ""
        if isDemo {
            batteryRows = [BatteryRow(label: "Battery at rest", value: "12.61 V", verdict: "Fully charged", good: true),
                           BatteryRow(label: "Lowest while starting", value: "10.20 V", verdict: "Strong", good: true),
                           chargeRow("Charging at idle", 14.1), chargeRow("Charging at 2,000 rpm", 14.3)]
            batteryNote = "Sample results. Parts stores can do a load test if anything here looks weak."
            return
        }
        runTest("Checking the battery…") { [weak self] e in
            guard let self else { return }
            if let r = await self.engineRPM(e), r > 300 {
                self.batteryNote = "Turn the engine OFF (key ON is fine) and tap Start test again. The battery is checked at rest first."
                return
            }
            var readings: [Double] = []
            for _ in 0..<5 { if let v = await self.volts(e) { readings.append(v) } }
            guard let v = readings.max() else {
                self.batteryNote = "Couldn't read the voltage from the adapter."
                return
            }
            self.batteryRest = v
            let (words, good) = v >= 12.55 ? ("Fully charged", true) : v >= 12.35 ? ("Good", true)
                : v >= 12.0 ? ("Half charged - charge it", false) : ("Low - charge or replace", false)
            self.batteryRows.append(BatteryRow(label: "Battery at rest", value: String(format: "%.2f V", v), verdict: words, good: good))
            self.batteryPrompt = "Now start the engine. Tap Ready, then start it within 10 seconds."
            self.batteryStep = 1
        }
    }

    func batteryReady() {
        batteryPrompt = nil
        if batteryStep == 1 {
            runTest("Start the engine now…") { [weak self] e in
                guard let self else { return }
                var low = 99.0, started = false
                let end = Date().addingTimeInterval(15)
                while Date() < end {
                    if let v = await self.volts(e) {
                        low = min(low, v)
                        if low < self.batteryRest - 0.4 && v > 13 { started = true; break }
                    }
                }
                if !started { self.batteryNote = "Didn't see the engine start. If it did start, the adapter may have missed the dip; otherwise try again." }
                if low < 50 {
                    let (words, good) = low >= 10 ? ("Strong", true) : low >= 9.6 ? ("OK", true) : ("Weak - battery or starter", false)
                    self.batteryRows.append(BatteryRow(label: "Lowest while starting", value: String(format: "%.2f V", low), verdict: words, good: good))
                }
                self.status = "Checking charging at idle…"
                try await Task.sleep(nanoseconds: 4_000_000_000)
                var idle: [Double] = []
                for _ in 0..<6 { if let v = await self.volts(e) { idle.append(v) } }
                guard !idle.isEmpty else { return }
                self.batteryRows.append(self.chargeRow("Charging at idle", idle.reduce(0, +) / Double(idle.count)))
                self.batteryPrompt = "Last step: hold the engine at about 2,000 rpm (in Park or Neutral), then tap Ready."
                self.batteryStep = 2
            }
        } else {
            runTest("Hold about 2,000 rpm…") { [weak self] e in
                guard let self else { return }
                var readings: [Double] = []
                let end = Date().addingTimeInterval(12)
                while Date() < end && readings.count < 5 {
                    if let r = await self.engineRPM(e), r > 1500, let v = await self.volts(e) { readings.append(v) }
                }
                if readings.isEmpty {
                    self.batteryNote = "Didn't see the engine above 1,500 rpm, so this step was skipped."
                } else {
                    self.batteryRows.append(self.chargeRow("Charging at 2,000 rpm", readings.reduce(0, +) / Double(readings.count)))
                    self.batteryNote = "Done. You can let the engine idle again. Parts stores can do a load test if anything here looks weak."
                }
            }
        }
    }

    func checkRecalls() {
        recallStatus = "Looking up recalls…"
        Task {
            do {
                let found = try await Recalls.find(make: chosenMake, model: chosenModel, year: year, vin: vin)
                recalls = found.matched ? found.recalls : nil
                recallStatus = !found.matched ? "Couldn't find this vehicle in the recall database, so this isn't an all-clear. Check at nhtsa.gov/recalls with the VIN."
                    : found.recalls.isEmpty ? "No recalls found in the NHTSA database."
                    : "\(found.recalls.count) recall\(found.recalls.count == 1 ? "" : "s") found."
            } catch {
                recallStatus = "Couldn't reach the recall database. Check the internet connection and try again."
            }
        }
    }

    // MARK: Report

    func reportHTML() -> String {
        func e(_ t: String) -> String {
            t.replacingOccurrences(of: "&", with: "&amp;").replacingOccurrences(of: "<", with: "&lt;")
                .replacingOccurrences(of: ">", with: "&gt;").replacingOccurrences(of: "\"", with: "&quot;")
        }
        var o = "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Vehicle report</title><style>body{font-family:-apple-system,Helvetica,Arial,sans-serif;color:#111;background:#fff;padding:24px;max-width:860px;margin:auto;line-height:1.45}h1{font-size:28px;margin:0 0 4px}h2{font-size:19px;margin:28px 0 10px;padding-bottom:6px;border-bottom:2px solid #111}.muted{color:#666}.card{border:1px solid #E2E2E2;border-radius:14px;padding:14px 18px;margin:10px 0}.good{color:#1E8A4A;font-weight:600}.bad{color:#D9362B;font-weight:600}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:5px 8px;border-bottom:1px solid #eee;font-size:14px}</style></head><body>"
        o += "<h1>Vehicle health report</h1><div class='muted'>\(Date().formatted(date: .long, time: .shortened)) · Car Code Reader</div><h2>Vehicle</h2>"
        for (label, value) in [("Vehicle", chosenName), ("VIN", vin), ("Battery", battery), ("Protocol", protocolName)] where !value.isEmpty {
            o += "<div><span class='muted'>\(label):</span> <b>\(e(value))</b></div>"
        }
        if let milOn { o += "<div><span class='muted'>Check-engine light:</span> <b class='\(milOn ? "bad" : "good")'>\(milOn ? "ON" : "Off")</b></div>" }
        let active = problems.filter { $0.urgency != "past" }.count
        o += "<h2>Problems found (\(active) active)</h2>"
        if !scanned { o += "<p class='muted'>No scan was run.</p>" } else if problems.isEmpty { o += "<p class='good'>No trouble codes found.</p>" }
        for p in problems {
            o += "<div class='card'><b>\(e(p.code))</b> \(e(p.meaning))<div class='muted'>\(e(p.module)) · \(e(p.status))</div>"
            o += "<p><b>Why it matters:</b> \(e(CodeDetail.whyItMatters(p.code, status: p.status, module: p.module)))</p>"
            let causes = CodeDetail.commonCauses(p.code)
            if !causes.isEmpty { o += "<p><b>Common causes:</b> \(e(causes))</p>" }
            o += "</div>"
        }
        if !monitors.isEmpty {
            o += "<h2>Smog check self-tests</h2><table>"
            for m in monitors { o += "<tr><td>\(e(m.name))</td><td>\(!m.supported ? "<span class='muted'>Not on this vehicle</span>" : m.incomplete ? "<span class='bad'>Still running</span>" : "<span class='good'>Done</span>")</td></tr>" }
            o += "</table>"
        }
        if !selfTests.isEmpty {
            o += "<h2>Self-test results</h2><table><tr><th>Test</th><th>Result</th><th>Allowed</th><th></th></tr>"
            for t in selfTests { o += "<tr><td>\(e(t.name))</td><td>\(String(format: "%.4g", t.value)) \(e(t.unit))</td><td>\(String(format: "%.4g to %.4g", t.low, t.high)) \(e(t.unit))</td><td class='\(t.passed ? "good" : "bad")'>\(t.passed ? "Pass" : "Fail")</td></tr>" }
            o += "</table>"
        }
        if !batteryRows.isEmpty {
            o += "<h2>Battery and charging test</h2><table>"
            for r in batteryRows { o += "<tr><td>\(e(r.label))</td><td><b>\(e(r.value))</b></td><td class='\(r.good ? "good" : "bad")'>\(e(r.verdict))</td></tr>" }
            o += "</table>"
        }
        if !moduleInfo.isEmpty {
            o += "<h2>Module info</h2>"
            for m in moduleInfo {
                o += "<div class='card'><b>\(e(m.name.isEmpty ? m.ecu : m.name))</b>"
                for c in m.calids { o += "<div>Calibration ID: \(e(c))</div>" }
                for c in m.cvns { o += "<div>Calibration check number: \(e(c))</div>" }
                for (label, value) in m.usage { o += "<div class='muted'>\(e(label)): \(e(value))</div>" }
                o += "</div>"
            }
        }
        if let recalls {
            o += "<h2>Safety recalls (\(recalls.count))</h2>"
            if recalls.isEmpty { o += "<p class='muted'>None found in the NHTSA database.</p>" }
            for r in recalls { o += "<div class='card'><b>\(e(r.component))</b><div class='muted'>Recall \(e(r.campaign)), \(e(r.date))</div><p>\(e(r.summary))</p><p><b>Fix:</b> \(e(r.remedy))</p></div>" }
        }
        o += "<p class='muted' style='margin-top:30px'>This report lists what the vehicle's computers reported. Code meanings and steps are general guidance; confirm with a test before replacing parts.</p></body></html>"
        return o
    }

    func recordingCSV() -> String {
        let names = reader_recordingNames
        var out = "Seconds," + names.map { n in "\"\(n)\(recordingUnits[n].map { $0.isEmpty ? "" : " (\($0))" } ?? "")\"" }.joined(separator: ",") + "\n"
        guard let start = recordingRows.first?.0 else { return out }
        for (t, values) in recordingRows {
            out += String(format: "%.1f", t.timeIntervalSince(start)) + "," + names.map { values[$0].map { String(format: "%g", $0) } ?? "" }.joined(separator: ",") + "\n"
        }
        return out
    }
    private var reader_recordingNames: [String] {
        var seen: [String] = []
        for (_, values) in recordingRows { for k in values.keys.sorted() where !seen.contains(k) { seen.append(k) } }
        return seen
    }
}

// MARK: - Shared pieces

/// A simple page under Home: title, then content on the page colour.
struct ProPage<Content: View>: View {
    let title: String
    let subtitle: String
    @ViewBuilder let content: Content
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                PageTitle(title: title, subtitle: subtitle)
                content
            }
            .padding(16)
        }
        .scrollDismissesKeyboard(.interactively)
        .background(MacColor.page)
        .navigationBarTitleDisplayMode(.inline)
    }
}

private func proText(_ text: String, muted: Bool = false, size: CGFloat = 13, bold: Bool = false) -> some View {
    Text(text).font(.system(size: size, weight: bold ? .bold : .regular))
        .foregroundStyle(muted ? MacColor.muted : MacColor.ink)
        .fixedSize(horizontal: false, vertical: true)
}

// MARK: - Tests

struct TestsView: View {
    @EnvironmentObject var reader: Reader
    @State private var codeEntry = ""
    @State private var lookedUp = ""
    private var ready: Bool { reader.connected && !reader.busy }

    private var misfires: [(cyl: Int, current: Double?, average: Double?)] {
        var map: [Int: (Double?, Double?)] = [:]
        for t in reader.selfTests where t.isMisfire {
            var entry = map[t.mid - 0xA1] ?? (nil, nil)
            if t.tid == 0x0C { entry.0 = t.value } else { entry.1 = t.value }
            map[t.mid - 0xA1] = entry
        }
        return map.keys.sorted().map { ($0, map[$0]!.0, map[$0]!.1) }
    }

    private func section<Body: View>(_ title: String, _ text: String, @ViewBuilder body: () -> Body) -> some View {
        RoundCard(radius: 20) {
            VStack(alignment: .leading, spacing: 8) {
                proText(title, size: 16, bold: true)
                proText(text, muted: true)
                body()
            }
        }
    }

    private func lookup() {
        var code = codeEntry.uppercased().filter { $0.isLetter || $0.isNumber }
        if code.count == 5, let first = code.first {   // people often type the letter O for zero
            code = String(first) + code.dropFirst().replacingOccurrences(of: "O", with: "0").replacingOccurrences(of: "I", with: "1")
        }
        codeEntry = code
        lookedUp = code
    }

    var body: some View {
        ProPage(title: "Tests", subtitle: "Deeper checks that professional scan tools do. They only read from the vehicle and never change anything.") {
            if !reader.connected { proText("Connect to a vehicle to run the first three tests. Look up a code works without one.", muted: true) }
            if reader.busy { BusyLine() }
            if !reader.testMessage.isEmpty { proText(reader.testMessage, muted: true) }

            section("Battery and charging test", "Checks the battery at rest, how far it drops while starting, and whether the alternator charges at idle and at 2,000 rpm. Takes about a minute.") {
                Button("Start test") { reader.batteryStart() }.buttonStyle(PillStyle(kind: .primary)).disabled(!ready)
                ForEach(reader.batteryRows) { r in
                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: 1) {
                            proText(r.label)
                            proText(r.value, size: 16, bold: true)
                        }
                        Spacer(minLength: 8)
                        Text(r.verdict).font(.system(size: 12, weight: .bold))
                            .foregroundStyle(r.good ? MacColor.green : MacColor.red)
                            .multilineTextAlignment(.trailing)
                    }
                }
                if let prompt = reader.batteryPrompt {
                    proText(prompt, bold: true)
                    Button("Ready") { reader.batteryReady() }.buttonStyle(PillStyle(kind: .primary)).disabled(reader.busy)
                }
                if !reader.batteryNote.isEmpty { proText(reader.batteryNote, muted: true, size: 12) }
            }

            section("Self-test results and misfire counts", "The numbers behind each emissions self-test with its pass/fail limits, and misfire counts for each cylinder. Most 2008 and newer vehicles.") {
                Button("Read results") { reader.readSelfTests() }.buttonStyle(PillStyle(kind: .primary)).disabled(!ready)
                if !misfires.isEmpty {
                    proText("Misfires per cylinder", bold: true)
                    ForEach(misfires, id: \.cyl) { m in
                        proText("Cylinder \(m.cyl): this or last drive \(m.current.map { String(format: "%.0f", $0) } ?? "-"), 10-drive average \(m.average.map { String(format: "%.0f", $0) } ?? "-")")
                    }
                }
                ForEach(reader.selfTests.filter { !$0.isMisfire }) { t in
                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: 1) {
                            proText(t.name)
                            proText(String(format: "%.4g %@, allowed %.4g to %.4g", t.value, t.unit, t.low, t.high), muted: true, size: 12)
                        }
                        Spacer(minLength: 8)
                        StatusPill(words: t.passed ? "Pass" : "Fail", fill: t.passed ? MacColor.greenSoft : MacColor.redSoft,
                                   text: t.passed ? MacColor.green : MacColor.red)
                    }
                }
            }

            section("Module info", "Software calibration numbers for each computer, and how often each self-test has had a chance to run.") {
                Button("Read info") { reader.readModuleInfo() }.buttonStyle(PillStyle(kind: .primary)).disabled(!ready)
                ForEach(reader.moduleInfo) { m in
                    VStack(alignment: .leading, spacing: 2) {
                        proText(m.name.isEmpty ? m.ecu : m.name, bold: true)
                        ForEach(m.calids, id: \.self) { proText("Calibration ID: " + $0, size: 12) }
                        ForEach(m.cvns, id: \.self) { proText("Calibration check number: " + $0, size: 12) }
                        ForEach(m.usage, id: \.0) { proText("\($0.0): \($0.1)", muted: true, size: 12) }
                    }
                }
            }

            section("Look up a code", "Find out what any code means, without the vehicle. Factory meanings use the vehicle you picked.") {
                HStack(spacing: 10) {
                    TextField("P0301", text: $codeEntry)
                        .font(.system(size: 15)).textInputAutocapitalization(.characters).autocorrectionDisabled()
                        .submitLabel(.search).onSubmit { lookup() }
                        .padding(.horizontal, 12).padding(.vertical, 8)
                        .overlay(RoundedRectangle(cornerRadius: 10, style: .continuous).stroke(MacColor.line, lineWidth: 1))
                    Button("Look up") { lookup() }.buttonStyle(PillStyle(kind: .primary))
                }
                if !lookedUp.isEmpty {
                    if lookedUp.range(of: "^[PCBU][0-9A-F]{4}$", options: .regularExpression) == nil {
                        proText("Type a code like P0301, C0035, B1932 or U0100 (a letter, then 4 numbers or letters).", muted: true)
                    } else {
                        let (text, factory) = DTC.describe(lookedUp, make: reader.make)
                        proText("\(lookedUp): \(text)", bold: true)
                        if let factory { proText("\(factory) factory meaning. It can differ by model and year.", muted: true, size: 12) }
                        let causes = CodeDetail.commonCauses(lookedUp)
                        if !causes.isEmpty { proText("Common causes: " + causes) }
                    }
                }
            }
        }
    }
}

// MARK: - Service guides

struct ServiceView: View {
    @EnvironmentObject var reader: Reader
    @State private var open: String? = nil

    private var guides: [ServiceGuide] {
        let family: String? = reader.make == .ford ? "ford" : reader.make == .gm ? "gm" : nil
        guard let family else { return ProData.guides }
        return ProData.guides.filter { $0.family == family } + ProData.guides.filter { $0.family == nil }
    }

    var body: some View {
        ProPage(title: "Service", subtitle: "Relearns, resets and brake bleeding you can do by hand. Tap one to see the steps.") {
            ForEach(guides, id: \.title) { g in
                RoundCard(radius: 16) {
                    VStack(alignment: .leading, spacing: 6) {
                        proText(g.title, size: 15, bold: true)
                        proText(g.applies, muted: true, size: 12)
                        if open == g.title {
                            if !g.needs.isEmpty { proText("You'll need: " + g.needs) }
                            ForEach(Array(g.steps.enumerated()), id: \.offset) { i, step in
                                HStack(alignment: .top, spacing: 10) {
                                    StepDot(number: i + 1, fill: MacTint.vehicle.opacity(0.15), text: Color(light: "#1F6FD1", dark: "#7DB3F2"))
                                    proText(step)
                                }
                            }
                            if !g.note.isEmpty { proText(g.note, muted: true, size: 12) }
                        }
                    }
                    .contentShape(Rectangle())
                    .onTapGesture { withAnimation(.easeInOut(duration: 0.2)) { open = open == g.title ? nil : g.title } }
                }
            }
        }
    }
}

// MARK: - Vehicle and recalls

struct VehiclePageView: View {
    @EnvironmentObject var reader: Reader
    @Environment(\.openURL) private var openURL

    var body: some View {
        ProPage(title: "Vehicle", subtitle: "What the vehicle and adapter report about themselves, plus safety recalls.") {
            RoundCard(padY: 8) {
                let rows = [("Vehicle", reader.chosenName), ("VIN", reader.vin), ("Battery", reader.battery), ("Protocol", reader.protocolName)]
                ForEach(rows, id: \.0) { row in
                    HStack(alignment: .top) {
                        proText(row.0, muted: true)
                        Spacer(minLength: 12)
                        Text(row.1.isEmpty ? "—" : row.1).font(.system(size: 13, weight: .bold)).foregroundStyle(MacColor.ink).multilineTextAlignment(.trailing)
                    }
                    .padding(.vertical, 7)
                }
            }
            RoundCard(radius: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    proText("Safety recalls", size: 16, bold: true)
                    proText("From the U.S. government's free NHTSA database. Dealers repair recalls free.", muted: true)
                    if reader.vin.count != 17 && (reader.chosenMake.isEmpty || reader.chosenModel.isEmpty) {
                        proText("Choose a vehicle on Home, or connect to one, so the app knows which recalls to look up.", muted: true)
                    } else {
                        Button("Check for recalls") { reader.checkRecalls() }.buttonStyle(PillStyle(kind: .primary))
                    }
                    if !reader.recallStatus.isEmpty { proText(reader.recallStatus, muted: true) }
                }
            }
            ForEach(reader.recalls ?? []) { r in
                RoundCard(radius: 16) {
                    VStack(alignment: .leading, spacing: 5) {
                        if r.parkIt { StatusPill(words: "Don't drive: park it", fill: MacColor.redSoft, text: MacColor.red) }
                        proText(r.component, size: 15, bold: true)
                        proText("Recall \(r.campaign), \(r.date)", muted: true, size: 12)
                        proText(r.summary)
                        if !r.consequence.isEmpty { proText("Risk: " + r.consequence) }
                        if !r.remedy.isEmpty { proText("Fix: " + r.remedy) }
                    }
                }
            }
            if !reader.recallStatus.isEmpty, reader.recallStatus != "Looking up recalls…" {
                FlowLayout(spacing: 16) {
                    if let url = URL(string: reader.vin.count == 17 ? "https://www.nhtsa.gov/recalls?vin=\(reader.vin)" : "https://www.nhtsa.gov/recalls") {
                        LinkLabel("Check my VIN on nhtsa.gov") { openURL(url) }
                    }
                    if var bulletins = URLComponents(string: "https://www.google.com/search") {
                        LinkLabel("Service bulletins") {
                            bulletins.queryItems = [URLQueryItem(name: "q", value: "\(reader.chosenName.isEmpty ? reader.vin : reader.chosenName) technical service bulletins")]
                            if let url = bulletins.url { openURL(url) }
                        }
                    }
                }
            }
        }
    }
}

// MARK: - History

struct HistoryView: View {
    @State private var groups: [(name: String, scans: [ScanRecord])] = []
    @State private var confirmClear = false

    var body: some View {
        ProPage(title: "History", subtitle: "Every scan is saved here by vehicle, so you can see what came back after a repair.") {
            if groups.isEmpty {
                proText("No scans saved yet. Scans are saved here automatically after each scan.", muted: true)
            }
            ForEach(groups, id: \.scans[0].vehicle) { group in
                proText(group.name, size: 18, bold: true)
                ForEach(Array(group.scans.prefix(15).enumerated()), id: \.element.id) { i, scan in
                    RoundCard(radius: 16, padY: 12) {
                        VStack(alignment: .leading, spacing: 3) {
                            HStack(alignment: .top) {
                                proText("\(scan.when.formatted(date: .abbreviated, time: .shortened)) · \(["engine": "Engine codes", "safety": "ABS and airbag"][scan.kind] ?? "Full scan")", bold: true)
                                Spacer(minLength: 6)
                                StatusPill(words: scan.codes.isEmpty ? "No codes" : "\(scan.codes.count) code\(scan.codes.count == 1 ? "" : "s")",
                                           fill: scan.codes.isEmpty ? MacColor.greenSoft : MacColor.redSoft,
                                           text: scan.codes.isEmpty ? MacColor.green : MacColor.red)
                            }
                            if i + 1 < group.scans.count {
                                let now = Set(scan.codes.map(\.code)), before = Set(group.scans[i + 1].codes.map(\.code))
                                let new = now.subtracting(before).sorted(), gone = before.subtracting(now).sorted()
                                if !new.isEmpty { Text("New since the scan before: " + new.joined(separator: ", ")).font(.system(size: 12)).foregroundStyle(MacColor.amberInk) }
                                if !gone.isEmpty { Text("Gone since the scan before: " + gone.joined(separator: ", ")).font(.system(size: 12)).foregroundStyle(MacColor.green) }
                            }
                            ForEach(Array(scan.codes.prefix(12).enumerated()), id: \.offset) { _, c in
                                proText("\(c.code)  \(c.text)  (\(c.module))", size: 12)
                            }
                            if scan.codes.count > 12 { proText("…and \(scan.codes.count - 12) more", muted: true, size: 12) }
                        }
                    }
                }
            }
            if !groups.isEmpty { LinkLabel("Clear history") { confirmClear = true } }
        }
        .onAppear { groups = ScanHistory.byVehicle() }
        .alert("Delete all saved scans?", isPresented: $confirmClear) {
            Button("Delete", role: .destructive) { ScanHistory.clear(); groups = [] }
            Button("Cancel", role: .cancel) { }
        } message: { Text("This can't be undone.") }
    }
}

// MARK: - Help

struct HelpView: View {
    @EnvironmentObject var reader: Reader
    @State private var showLog = false
    private let steps = [
        "Plug the adapter into the OBD port under the dashboard, near the steering column.",
        "Turn the key to ON. The engine can be off or running.",
        "On Home, tap Engine codes, ABS and airbag, or Full scan. The app connects by itself.",
        "Tap any problem to see what it means, how urgent it is, and what usually fixes it.",
        "To clear codes, turn the engine off and leave the key on first.",
    ]
    private let colors = [MacTint.vehicle, MacTint.engine, MacTint.scan, MacTint.safety, MacTint.smog]
    private let numberColors = [Color(light: "#1F6FD1", dark: "#7DB3F2"), Color(light: "#E08A00", dark: "#F5B942"),
                                Color(light: "#6C4BD1", dark: "#B5A1F0"), Color(light: "#D9362B", dark: "#FF8A82"),
                                Color(light: "#1E8A4A", dark: "#6FDB95")]

    var body: some View {
        ProPage(title: "Help", subtitle: "Getting codes off your vehicle in five steps.") {
            RoundCard(radius: 22) {
                VStack(alignment: .leading, spacing: 10) {
                    ForEach(Array(steps.enumerated()), id: \.offset) { i, s in
                        HStack(alignment: .top, spacing: 12) {
                            StepDot(number: i + 1, fill: colors[i].opacity(0.15), text: numberColors[i], size: 30)
                            proText(s, size: 14)
                        }
                    }
                }
            }
            proText("Something not working right? Open the adapter log below, copy it, and send it to whoever maintains this app.", muted: true)
            proText("Version \(AppInfo.version)", bold: true)
            FlowLayout {
                Button(showLog ? "Hide adapter log" : "Show adapter log") { showLog.toggle() }.buttonStyle(PillStyle())
                Button("Copy log") { UIPasteboard.general.string = reader.adapterLog.joined(separator: "\n") }.buttonStyle(PillStyle())
            }
            if showLog {
                Text(reader.adapterLog.isEmpty ? "Nothing yet. Connect to an adapter first." : reader.adapterLog.suffix(300).joined(separator: "\n"))
                    .font(.system(size: 11, design: .monospaced)).foregroundStyle(MacColor.ink)
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(10)
                    .overlay(RoundedRectangle(cornerRadius: 10, style: .continuous).stroke(MacColor.line, lineWidth: 1))
            }
        }
    }
}

// MARK: - Live graph

/// Up to 4 readings over the last 90 seconds. Each line has its own scale, like the Mac app's LiveGraph.
struct LiveGraphCard: View {
    @EnvironmentObject var reader: Reader
    private let colors: [Color] = [MacTint.engine, MacTint.vehicle, MacTint.smog, MacTint.scan]

    var body: some View {
        RoundCard(padY: 12) {
            VStack(alignment: .leading, spacing: 6) {
                Chart {
                    ForEach(Array(reader.graphKeys.enumerated()), id: \.element) { i, name in
                        let points = reader.liveSeries[name] ?? []
                        let low = points.map(\.1).min() ?? 0, high = points.map(\.1).max() ?? 1
                        let range = max(high - low, 0.0001)
                        ForEach(Array(points.enumerated()), id: \.offset) { _, p in
                            LineMark(x: .value("Time", p.0), y: .value("Scaled", (p.1 - low) / range), series: .value("Reading", name))
                                .foregroundStyle(colors[i % colors.count])
                        }
                    }
                }
                .chartYAxis(.hidden)
                .chartXAxis(.hidden)
                .frame(height: 150)
                ForEach(Array(reader.graphKeys.enumerated()), id: \.element) { i, name in
                    HStack(spacing: 6) {
                        Circle().fill(colors[i % colors.count]).frame(width: 8, height: 8)
                        Text(name).font(.system(size: 12)).foregroundStyle(MacColor.ink).lineLimit(1)
                        Spacer(minLength: 4)
                        Text(reader.live.first { $0.name == name }?.mainValue ?? "").font(.system(size: 12, weight: .bold)).foregroundStyle(MacColor.ink)
                    }
                }
            }
        }
    }
}
