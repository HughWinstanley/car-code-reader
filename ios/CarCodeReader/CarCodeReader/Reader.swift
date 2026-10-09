import Foundation
import SwiftUI

struct Problem: Identifiable {
    let id = UUID()
    let code: String
    let meaning: String
    let status: String
    let urgency: String        // high / medium / low / past
    let factory: String?
}

struct LiveReading: Identifiable { let id = UUID(); let name: String; let value: String }

/// Which home tile started the scan — drives the Problems page's icon & wording.
enum ScanKind {
    case engine, safety, all

    var icon: String {
        switch self {
        case .engine: return "icon-engine"
        case .safety: return "icon-absbag"
        case .all:    return "icon-scan"
        }
    }
    var subtitle: String {
        switch self {
        case .engine: return "Check-engine and transmission codes, in plain language."
        case .safety: return "Brake (ABS) and airbag warning lights, in plain language."
        case .all:    return "Every module at once — engine, transmission, ABS, airbag and more."
        }
    }
    var message: String {
        switch self {
        case .engine: return "Plug the adapter in, turn the key to ON, then connect to scan the engine."
        case .safety: return "Plug the adapter in, turn the key to ON, then connect to scan ABS and airbag."
        case .all:    return "Plug the adapter in, turn the key to ON, then connect to run a full scan."
        }
    }
}

@MainActor
final class Reader: ObservableObject {
    @Published var isDemo = false          // sample data; never saved — gone when the app restarts
    @Published var scanKind: ScanKind = .all
    @Published var status = "Not connected"
    @Published var connected = false
    @Published var busy = false
    @Published var problems: [Problem] = []
    @Published var scanned = false
    @Published var live: [LiveReading] = []
    @Published var liveRunning = false
    @Published var smogText = ""
    @Published var smogOK = false
    @Published var smogDetail = ""
    @Published var monitors: [Monitor] = []
    @Published var vin = ""
    @Published var battery = ""
    @Published var protocolName = ""
    @Published var semiFaults: [J1939Fault] = []
    @Published var semiStatus = ""

    // Connection choice
    @Published var useBluetooth = false
    @Published var host = "192.168.0.10"
    @Published var port = "35000"
    @Published var make: Make = .other
    @Published var year: Int? = nil
    @Published var chosenName = ""

    private var link: OBDLink?
    private var elm: ELM327?
    private var liveTask: Task<Void, Never>?

    func connect() {
        guard !busy else { return }
        busy = true
        status = useBluetooth ? "Looking for a Bluetooth adapter…" : "Connecting to \(host):\(port)…"
        let newLink: OBDLink = useBluetooth ? BLELink()
            : WifiLink(host: host, port: UInt16(port) ?? 35000)
        Task {
            do {
                try await newLink.connect()
                status = "Waking up the vehicle…"
                let e = ELM327(newLink)
                try await e.initialize()
                link = newLink; elm = e
                connected = true
                protocolName = e.protocolName
                status = "Connected (\(e.protocolName)). Scanning…"
                await readVehicleInternal(e)
                await scanInternal(e)
            } catch {
                status = "Couldn't connect: \(error.localizedDescription)"
                newLink.close()
            }
            busy = false
        }
    }

    func disconnect() {
        stopLive()
        link?.close(); link = nil; elm = nil
        connected = false; scanned = false; problems = []; live = []
        monitors = []; vin = ""; battery = ""; status = "Not connected"
    }

    func scan() {
        if isDemo { status = "Demo scan complete — \(problems.count) sample codes."; return }
        guard let e = elm, !busy else { return }
        busy = true; status = "Scanning…"
        Task { await scanInternal(e); busy = false }
    }

    private func scanInternal(_ e: ELM327) async {
        do {
            let dtcs = try await e.readDTCs()
            problems = dtcs.map {
                let (text, factory) = DTC.describe($0.code, make: make)
                return Problem(code: $0.code, meaning: text, status: $0.status,
                               urgency: CodeDetail.severity($0.code, status: $0.status, module: "Engine"),
                               factory: factory)
            }
            scanned = true
            status = problems.isEmpty ? "No codes found." : "\(problems.count) code\(problems.count == 1 ? "" : "s") found."
            if let d = try await e.readiness() { applySmog(d) }
        } catch { status = "Scan error: \(error.localizedDescription)" }
    }

    func clearCodes() {
        if isDemo { problems = []; scanned = true; status = "Codes cleared (demo)."; return }
        guard let e = elm, !busy else { return }
        busy = true; status = "Clearing codes…"
        Task {
            do { try await e.clearCodes(); await scanInternal(e); status = "Codes cleared." }
            catch { status = "Couldn't clear: \(error.localizedDescription)" }
            busy = false
        }
    }

    /// Remove one code from the list (swipe-to-delete). See note in the UI about what this means on a real car.
    func removeProblem(at offsets: IndexSet) {
        problems.remove(atOffsets: offsets)
        status = problems.isEmpty ? "No codes shown." : "\(problems.count) code\(problems.count == 1 ? "" : "s") shown."
    }

    func checkSmog() {
        if isDemo { return }
        guard let e = elm, !busy else { return }
        busy = true
        Task {
            if let d = try? await e.readiness() { applySmog(d) }
            busy = false
        }
    }

    private func applySmog(_ d: [UInt8]) {
        let (text, ok, detail) = Readiness.verdict(d, year: year)
        smogText = text; smogOK = ok; smogDetail = detail
        monitors = Readiness.decode(d).monitors
    }

    private func readVehicleInternal(_ e: ELM327) async {
        vin = (try? await e.readVIN()) ?? ""
        battery = (try? await e.voltage()) ?? ""
    }

    func setVehicle(makeName: String, model: String, year: Int) {
        let fam = VehicleData.family[makeName] ?? "Other"
        make = (fam == "Ford") ? .ford : (fam == "GM" ? .gm : .other)
        self.year = year
        chosenName = "\(year) \(makeName) \(model)"
    }

    // MARK: - Demo mode (sample data only — nothing is saved, cleared on restart)

    func loadDemo() {
        isDemo = true
        connected = true
        busy = false
        scanned = true
        make = .other
        protocolName = "ISO 15765-4 (CAN 11/500)"
        vin = "1HGCR2F5XFA027358"
        battery = "14.1 V"
        chosenName = "2015 Honda Accord EX"
        year = 2015

        let samples: [(String, String)] = [
            ("P0301", "pending"), ("P0171", "stored"), ("P0420", "stored"), ("P0455", "history"),
        ]
        problems = samples.map { code, status in
            let (text, factory) = DTC.describe(code, make: make)
            return Problem(code: code, meaning: text, status: status,
                           urgency: CodeDetail.severity(code, status: status, module: "Engine"),
                           factory: factory)
        }

        live = [
            LiveReading(name: "Engine RPM", value: "842 rpm"),
            LiveReading(name: "Vehicle speed", value: "0 mph"),
            LiveReading(name: "Coolant temperature", value: "197 °F"),
            LiveReading(name: "Intake air temperature", value: "88 °F"),
            LiveReading(name: "Calculated engine load", value: "18 %"),
            LiveReading(name: "Throttle position", value: "14 %"),
            LiveReading(name: "Short-term fuel trim", value: "+6 %"),
            LiveReading(name: "Mass airflow (MAF)", value: "3.1 g/s"),
        ]
        liveRunning = false

        monitors = [
            Monitor(name: "Misfire", supported: true, incomplete: false, continuous: true),
            Monitor(name: "Fuel system", supported: true, incomplete: false, continuous: true),
            Monitor(name: "Comprehensive components", supported: true, incomplete: false, continuous: true),
            Monitor(name: "Catalyst", supported: true, incomplete: false, continuous: false),
            Monitor(name: "Evaporative system (EVAP)", supported: true, incomplete: true, continuous: false),
            Monitor(name: "Oxygen sensor", supported: true, incomplete: false, continuous: false),
            Monitor(name: "Oxygen sensor heater", supported: true, incomplete: false, continuous: false),
            Monitor(name: "EGR system", supported: true, incomplete: false, continuous: false),
            Monitor(name: "Secondary air system", supported: false, incomplete: false, continuous: false),
        ]
        smogText = "Not ready yet: 1 self-test still running"
        smogOK = false
        smogDetail = "Most inspections allow 1 unfinished test. Drive normally for a few days, then check again."

        semiFaults = J1939.example
        semiStatus = "Demo: 1 active fault shown."

        status = "Demo data — this isn't a real car."
    }

    func exitDemo() {
        isDemo = false
        stopLive()
        connected = false; busy = false; scanned = false
        problems = []; live = []; liveRunning = false
        monitors = []; smogText = ""; smogOK = false; smogDetail = ""
        semiFaults = []; semiStatus = ""
        vin = ""; battery = ""; protocolName = ""; chosenName = ""; year = nil
        status = "Not connected"
    }

    func readSemi() {
        if isDemo { semiFaults = J1939.example; semiStatus = "Demo: 1 active fault shown."; return }
        guard let link = link else { semiStatus = "Connect on the Problems tab first."; return }
        guard !busy else { return }
        busy = true; semiStatus = "Listening to the truck's J1939 network…"; semiFaults = []
        Task {
            do {
                _ = try await link.command("ATSP A")                 // SAE J1939
                _ = try await link.command("ATH1")                   // show message IDs
                _ = try await link.command("ATCAF0")                 // no auto formatting
                let dump = try await link.command("ATMA", timeout: 3) // ~3s of broadcasts
                _ = try? await link.command("ATH0")                  // any command stops the monitor
                semiFaults = J1939.parseMonitor(dump)
                semiStatus = semiFaults.isEmpty
                    ? "No fault broadcasts seen. The truck may have none, or needs a J1939-capable adapter."
                    : "\(semiFaults.count) fault\(semiFaults.count == 1 ? "" : "s") found."
            } catch {
                semiStatus = "Couldn't read: \(error.localizedDescription)"
            }
            busy = false
        }
    }

    func toggleLive() {
        if isDemo { liveRunning.toggle(); return }
        if liveRunning { stopLive(); return }
        guard let e = elm else { return }
        liveRunning = true
        liveTask = Task {
            while !Task.isCancelled {
                var out: [LiveReading] = []
                for p in PIDs.list {
                    if let data = try? await e.pid(p.pid), data.count >= p.len {
                        out.append(LiveReading(name: p.name, value: p.format(p.decode(data))))
                    }
                }
                if !out.isEmpty { live = out }
            }
        }
    }

    func stopLive() { liveTask?.cancel(); liveTask = nil; liveRunning = false }
}
