import Foundation
import SwiftUI

struct Problem: Identifiable {
    let id = UUID()
    let code: String
    let meaning: String
    let status: String
    let urgency: String        // high / medium / low / past
    let factory: String?
    var module = "Engine"      // friendly name of the module that reported it
}

struct LiveReading: Identifiable {
    let id = UUID()
    let name: String
    let value: String
    /// "197 °F  (91 °C)" -> "197 °F"
    var mainValue: String { value.split(separator: "(", maxSplits: 1).first.map { $0.trimmingCharacters(in: .whitespaces) } ?? value }
    var number: Double? { mainValue.split(separator: " ").first.flatMap { Double($0) } }
    var unit: String { mainValue.split(separator: " ", maxSplits: 1).dropFirst().first.map(String.init) ?? "" }
}

/// Which home tile started the scan — drives the Problems page's wording.
enum ScanKind { case engine, safety, all }

@MainActor
final class Reader: ObservableObject {
    @Published var isDemo = false          // sample data; never saved — gone when the app restarts
    @Published var scanKind: ScanKind = .all
    @Published var status = "Not connected"
    @Published var errorMessage: String? = nil   // what went wrong, in plain words, until the next try
    @Published var connected = false
    @Published var busy = false
    @Published var problems: [Problem] = []
    @Published var scanned = false
    @Published var lastScanAt: Date? = nil
    @Published var milOn: Bool? = nil      // check-engine light, once read
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
    @Published var useBluetooth = UserDefaults.standard.bool(forKey: "useBluetooth") {
        didSet { UserDefaults.standard.set(useBluetooth, forKey: "useBluetooth") }
    }
    @Published var bleAdapterName = UserDefaults.standard.string(forKey: "bleAdapterName") ?? "" {
        didSet { UserDefaults.standard.set(bleAdapterName, forKey: "bleAdapterName") }
    }
    @Published var bleAdapterID = UserDefaults.standard.string(forKey: "bleAdapterID").flatMap(UUID.init) {
        didSet { UserDefaults.standard.set(bleAdapterID?.uuidString, forKey: "bleAdapterID") }
    }
    @Published var host = UserDefaults.standard.string(forKey: "adapterHost") ?? "192.168.0.10" {
        didSet { UserDefaults.standard.set(host, forKey: "adapterHost") }
    }
    @Published var port = UserDefaults.standard.string(forKey: "adapterPort") ?? "35000" {
        didSet { UserDefaults.standard.set(port, forKey: "adapterPort") }
    }
    @Published var make: Make = .other
    @Published var year: Int? = nil
    @Published var chosenName = ""
    @Published var chosenMake = ""
    @Published var chosenModel = ""
    @Published var usedCarRows: [UsedCarRow] = []
    @Published var usedCarHeadline = ""
    @Published var usedCarWhy = ""
    @Published var vinDetails: [(String, String)] = []
    @Published var vinDetailsStatus = ""
    @Published var tripRunning = false
    @Published var trip = TripMeter()
    var tripTask: Task<Void, Never>?
    @Published var selfTests: [SelfTest] = []
    @Published var moduleInfo: [ModuleInfo] = []
    @Published var freezeFrame: [(String, String)] = []
    @Published var freezeFrameRead = false
    @Published var testMessage = ""
    @Published var batteryRows: [BatteryRow] = []
    @Published var batteryPrompt: String? = nil
    @Published var batteryNote = ""
    var batteryRest = 0.0
    var batteryStep = 0
    @Published var recalls: [Recall]? = nil
    @Published var recallStatus = ""
    @Published var adapterLog: [String] = []
    @Published var liveStats: [String: (Double, Double)] = [:]
    @Published var liveSeries: [String: [(Date, Double)]] = [:]
    @Published var graphKeys: [String] = []
    @Published var recording = false
    @Published var recordingRows: [(Date, [String: Double])] = []
    var recordingUnits: [String: String] = [:]
    @Published var moduleNames: [String] = []   // modules that answered the last scan
    @Published var canScanModules = false
    private var scannedModules: [ScannedModule] = []
    private var stopRequested = false
    private var demoSamples: [(String, String, String)] = []

    private var link: OBDLink?
    var elm: ELM327?
    private var liveTask: Task<Void, Never>?

    func connect() {
        guard !busy else { return }
        busy = true
        errorMessage = nil
        status = useBluetooth ? "Connecting to \(bleAdapterName)…" : "Connecting to \(host):\(port)…"
        let raw: OBDLink = useBluetooth ? BLELink(adapterID: bleAdapterID) : WifiLink(host: host, port: UInt16(port) ?? 35000)
        let newLink = LoggingLink(raw) { [weak self] line in
            Task { @MainActor in
                self?.adapterLog.append(line)
                if (self?.adapterLog.count ?? 0) > 2000 { self?.adapterLog.removeFirst(500) }
            }
        }
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
                canScanModules = e.canScanModules
                await readVehicleInternal(e)
                await scanInternal(e)
            } catch {
                status = "Not connected"
                errorMessage = Reader.plainWords(error, or: useBluetooth
                    ? "Couldn't reach your Bluetooth adapter. Make sure it's plugged in with the key ON."
                    : "Couldn't reach the adapter at \(host). Join its Wi-Fi network in the iPhone's Settings and check the key is ON.")
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
        lastScanAt = nil; milOn = nil; moduleNames = []; scannedModules = []; canScanModules = false
        clearPerVehicleResults()
    }

    func scan(deep: Bool = false) {
        if isDemo { applyDemoScan(); return }
        guard let e = elm, !busy else { return }
        busy = true; status = "Scanning…"; errorMessage = nil
        let live = pauseLive()
        Task {
            await live?.value   // a scan changes adapter settings, so live data must be fully stopped first
            await scanInternal(e, deep: deep)
            busy = false
        }
    }

    private func clearPerVehicleResults() {
        selfTests = []; moduleInfo = []; freezeFrame = []; freezeFrameRead = false; testMessage = ""
        usedCarRows = []; usedCarHeadline = ""; usedCarWhy = ""; vinDetails = []; vinDetailsStatus = ""
        stopTrip(); trip = TripMeter()
        batteryRows = []; batteryPrompt = nil; batteryNote = ""
        recalls = nil; recallStatus = ""
        liveStats = [:]; liveSeries = [:]; graphKeys = []; recording = false; recordingRows = []
    }

    /// Our own errors already say what to do. Anything from the system gets the given message instead.
    static func plainWords(_ error: Error, or fallback: String) -> String {
        (error as? OBDError)?.errorDescription ?? fallback
    }

    /// Stop a module scan after the module it's on.
    func stopScan() { stopRequested = true }

    /// 'Engine (ECM/PCM)' -> 'Engine'; keeps '(second network)' (the Mac app's friendly_module).
    private static func friendlyModule(_ name: String) -> String {
        var out = name
        while let open = out.range(of: " ("), let close = out.range(of: ")", range: open.upperBound..<out.endIndex),
              out[open.upperBound..<close.lowerBound] != "second network" {
            out.removeSubrange(open.lowerBound..<close.upperBound)
        }
        return out.replacingOccurrences(of: " / ", with: " and ")
    }

    private func scanInternal(_ e: ELM327, deep: Bool = false) async {
        let kind = scanKind
        stopRequested = false
        do {
            var obd: [Dtc] = []
            var ready: [UInt8]? = nil
            if kind != .safety {
                status = "Reading engine and transmission codes…"
                obd = try await e.readDTCs()
                status = "Checking the check-engine light and smog tests…"
                ready = try await e.readiness()
            }
            var modules: [ScannedModule] = []
            if kind != .engine && e.canScanModules {
                var targets = e.moduleTargets(deep: deep, make: make)
                if kind == .safety {
                    let safety = targets.filter { ModuleTable.isSafety($0.name) }
                    if !safety.isEmpty { targets = safety }
                }
                modules = try await e.moduleScan(targets) { [weak self] i, n, name in
                    await MainActor.run {
                        self?.status = "Checking \(name)… (\(i + 1) of \(n))"
                        return !(self?.stopRequested ?? true)
                    }
                }
                if kind == .safety { modules = modules.filter { ModuleTable.isSafety($0.target.name) } }
            }
            applyScan(obd: obd, modules: modules)
            if let ready { applySmog(ready) }
            saveToHistory()
        } catch {
            status = ""
            errorMessage = Reader.plainWords(error, or: "The scan stopped because the adapter stopped answering. Check it's plugged in, then scan again.")
        }
    }

    private func saveToHistory() {
        let name = chosenName.isEmpty ? (vin.isEmpty ? "Unknown vehicle" : "Vehicle \(vin)") : chosenName
        let kind = scanKind == .engine ? "engine" : scanKind == .safety ? "safety" : "all"
        ScanHistory.add(ScanRecord(when: Date(), vehicle: vin.count == 17 ? vin : name, name: name, vin: vin, kind: kind, milOn: milOn,
                                   codes: problems.map { .init(code: $0.code, text: $0.meaning, module: $0.module, status: $0.status, level: $0.urgency) }))
    }

    /// Merge everything into one list: a code from the same module shows once (the Mac app's _apply_scan).
    private func applyScan(obd: [Dtc], modules: [ScannedModule]) {
        var merged: [Problem] = []
        func add(_ d: Dtc) {
            let module = Reader.friendlyModule(d.module)
            let base = d.code.split(separator: "-").first.map(String.init) ?? d.code
            if let at = merged.firstIndex(where: { $0.module == module && $0.code.split(separator: "-").first.map(String.init) == base }) {
                let it = merged[at]
                if it.status.contains(d.status) { return }
                let new = CodeDetail.severity(d.code, status: d.status, module: module)
                let keepOld = UrgencyLevel(it.urgency).order <= UrgencyLevel(new).order
                merged[at] = Problem(code: it.code, meaning: it.meaning, status: it.status + ", " + d.status.lowercased(),
                                     urgency: keepOld ? it.urgency : new, factory: it.factory, module: module)
            } else {
                let (text, factory) = DTC.describe(d.code, make: make)
                merged.append(Problem(code: d.code, meaning: text, status: d.status,
                                      urgency: CodeDetail.severity(d.code, status: d.status, module: module),
                                      factory: factory, module: module))
            }
        }
        obd.forEach(add)
        let seen = Set(obd.map(\.code))
        for m in modules {
            for d in m.codes where !(d.code.hasPrefix("P") && seen.contains(d.code.split(separator: "-").first.map(String.init) ?? d.code)) {
                add(Dtc(code: d.code, status: d.status, module: d.module + (m.target.bus == .ms ? " (second network)" : "")))
            }
        }
        problems = merged
        scannedModules = modules
        var names: [String] = []
        for m in modules {
            let n = Reader.friendlyModule(m.target.name + (m.target.bus == .ms ? " (second network)" : ""))
            if !names.contains(n) { names.append(n) }
        }
        moduleNames = names
        scanned = true
        lastScanAt = Date()
        status = problems.isEmpty ? "No codes found." : "\(problems.count) code\(problems.count == 1 ? "" : "s") found."
    }

    func clearCodes() {
        if isDemo { demoSamples = []; problems = []; moduleNames = []; scanned = true; status = "Codes cleared (demo)."; return }
        guard let e = elm, !busy else { return }
        busy = true; status = "Clearing engine codes…"; errorMessage = nil
        let before = Set(problems.filter { $0.urgency != "past" }.map(\.code))
        let targets = scannedModules.filter { !$0.codes.isEmpty }.map(\.target)
        let live = pauseLive()
        Task {
            await live?.value
            do {
                try await e.clearCodes()
                if !targets.isEmpty {
                    status = "Clearing module codes…"
                    try await e.moduleClear(targets)
                }
                await scanInternal(e)
                let still = before.intersection(problems.filter { $0.urgency != "past" }.map(\.code))
                status = still.isEmpty ? "Codes cleared. If a problem returns after some driving, it still needs fixing."
                                       : "Codes cleared, but \(still.count) came straight back. That problem is still there and needs fixing."
            }
            catch {
                status = ""
                errorMessage = Reader.plainWords(error, or: "Codes may not have cleared because the adapter stopped answering. Scan again to check.")
            }
            busy = false
        }
    }

    /// Remove one code from the list (swipe "Clear code"). See the UI note about what this means on a real car.
    func removeProblem(_ p: Problem) {
        problems.removeAll { $0.id == p.id }
        status = problems.isEmpty ? "No codes shown." : "\(problems.count) code\(problems.count == 1 ? "" : "s") shown."
    }

    func checkSmog() {
        if isDemo { return }
        guard let e = elm, !busy else { return }
        busy = true
        let live = pauseLive()
        Task {
            await live?.value
            if let d = try? await e.readiness() { applySmog(d) }
            busy = false
        }
    }

    private func applySmog(_ d: [UInt8]) {
        let (text, ok, detail) = Readiness.verdict(d, year: year)
        smogText = text; smogOK = ok; smogDetail = detail
        let decoded = Readiness.decode(d)
        monitors = decoded.monitors; milOn = decoded.milOn
    }

    private func readVehicleInternal(_ e: ELM327) async {
        vin = (try? await e.readVIN()) ?? ""
        battery = (try? await e.voltage()) ?? ""
        // The VIN beats the picked vehicle for which module addresses and factory meanings to use.
        let family = VehicleData.family[chosenMake] ?? ""
        make = family == "Ford" ? .ford : (family == "GM" ? .gm : .other)
        switch String(vin.prefix(2)).uppercased() {
        case _ where vin.count != 17: break
        case "1F", "2F", "3F", "1L", "5L", "1M", "2M": make = .ford
        case "1G", "2G", "3G", "KL": make = .gm
        default: break
        }
    }

    func setVehicle(makeName: String, model: String, year: Int) {
        chosenModel = model
        recalls = nil; recallStatus = ""
        let fam = VehicleData.family[makeName] ?? "Other"
        make = (fam == "Ford") ? .ford : (fam == "GM" ? .gm : .other)
        self.year = year
        chosenMake = makeName
        chosenName = "\(year) \(makeName) \(model)".trimmingCharacters(in: .whitespaces)
    }

    // MARK: - Demo mode (sample data only — nothing is saved, cleared on restart)

    func loadDemo() {
        isDemo = true
        connected = true
        busy = false
        scanned = true
        lastScanAt = Date()
        make = .other
        protocolName = "ISO 15765-4 (CAN 11/500)"
        vin = "1HGCR2F5XFA027358"
        battery = "14.1 V"
        chosenName = "2015 Honda Accord EX"
        chosenMake = "Honda"
        chosenModel = "Accord"
        year = 2015

        canScanModules = true
        demoSamples = [
            ("P0301", "Pending", "Engine"), ("P0171", "Stored", "Engine"), ("P0420", "Stored", "Engine"),
            ("P0455", "History", "Engine"),
            ("C0035-1C", "Active now, Stored", "ABS and brakes"), ("B0001-13", "Stored", "Airbag"),
        ]
        applyDemoScan()

        live = [
            LiveReading(name: "Engine RPM", value: "842 rpm"),
            LiveReading(name: "Vehicle speed", value: "0 mph"),
            LiveReading(name: "Coolant temperature", value: "197 °F"),
            LiveReading(name: "Intake air temperature", value: "88 °F"),
            LiveReading(name: "Calculated engine load", value: "18 %"),
            LiveReading(name: "Throttle position", value: "14 %"),
            LiveReading(name: "Short-term fuel trim", value: "+6 %"),
            LiveReading(name: "Mass airflow (MAF)", value: "3.1 g/s"),
            LiveReading(name: "Transmission fluid temp", value: "174 °F  (79 °C)"),
        ]
        liveRunning = false

        monitors = [
            Monitor(name: "Misfire", supported: true, incomplete: false, continuous: true),
            Monitor(name: "Fuel system", supported: true, incomplete: false, continuous: true),
            Monitor(name: "Comprehensive components", supported: true, incomplete: false, continuous: true),
            Monitor(name: "Catalyst", supported: true, incomplete: true, continuous: false),
            Monitor(name: "Evaporative system (EVAP)", supported: true, incomplete: true, continuous: false),
            Monitor(name: "Oxygen sensor", supported: true, incomplete: false, continuous: false),
            Monitor(name: "Oxygen sensor heater", supported: true, incomplete: false, continuous: false),
            Monitor(name: "EGR system", supported: true, incomplete: false, continuous: false),
            Monitor(name: "Secondary air system", supported: false, incomplete: false, continuous: false),
        ]
        smogText = "Not ready yet: 2 self-tests still running"
        smogOK = false
        smogDetail = "Most inspections allow 1 unfinished test. Drive normally for a few days, with some city and highway, then check again."

        semiFaults = J1939.example
        semiStatus = "Demo: 1 active fault shown."

        status = "Demo data — this isn't a real car."
    }

    /// Show the sample codes this scan kind would find, like a real scan would.
    private func applyDemoScan() {
        let safety = ["ABS and brakes", "Airbag"]
        let picked = demoSamples.filter { sample in
            switch scanKind {
            case .engine: return !safety.contains(sample.2)
            case .safety: return safety.contains(sample.2)
            case .all:    return true
            }
        }
        problems = picked.map { code, status, module in
            let (text, factory) = DTC.describe(code, make: make)
            return Problem(code: code, meaning: text, status: status,
                           urgency: CodeDetail.severity(code, status: status, module: module),
                           factory: factory, module: module)
        }
        moduleNames = scanKind == .engine ? [] : (scanKind == .safety ? safety : ["Engine", "Body control"] + safety)
        scanned = true
        lastScanAt = Date()
        status = "Demo data — this isn't a real car."
    }

    func exitDemo() {
        isDemo = false
        stopLive()
        connected = false; busy = false; scanned = false
        problems = []; live = []; liveRunning = false
        monitors = []; smogText = ""; smogOK = false; smogDetail = ""
        semiFaults = []; semiStatus = ""
        vin = ""; battery = ""; protocolName = ""; chosenName = ""; chosenMake = ""; chosenModel = ""; year = nil
        clearPerVehicleResults()
        lastScanAt = nil; milOn = nil; moduleNames = []; canScanModules = false; demoSamples = []
        status = "Not connected"
    }

    func readSemi() {
        if isDemo { semiFaults = J1939.example; semiStatus = "Demo: 1 active fault shown."; return }
        guard let link = link else { semiStatus = "Connect on the Problems tab first."; return }
        guard !busy else { return }
        busy = true; semiStatus = "Listening to the truck's J1939 network…"; semiFaults = []
        let live = pauseLive()
        Task {
            await live?.value
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

    /// Publish one round of readings and keep the low/high, graph and recording up to date.
    private func applyLive(_ readings: [LiveReading]) {
        live = readings
        let now = Date()
        var row: [String: Double] = [:]
        for reading in readings {
            guard let v = reading.number else { continue }
            let old = liveStats[reading.name]
            liveStats[reading.name] = (min(old?.0 ?? v, v), max(old?.1 ?? v, v))
            var points = liveSeries[reading.name] ?? []
            points.append((now, v))
            points.removeAll { now.timeIntervalSince($0.0) > 90 }
            liveSeries[reading.name] = points
            row[reading.name] = v
            recordingUnits[reading.name] = reading.unit
        }
        if recording { recordingRows.append((now, row)) }
    }

    func toggleGraph(_ name: String) {
        if let at = graphKeys.firstIndex(of: name) {
            graphKeys.remove(at: at)
        } else {
            if graphKeys.count >= 4 { graphKeys.removeFirst() }
            graphKeys.append(name)
        }
    }

    func toggleRecording() {
        if !recording { recordingRows = [] }
        recording.toggle()
    }

    func toggleLive() {
        if liveRunning { stopLive(); return }
        if isDemo {
            liveRunning = true
            let base = live
            liveTask = Task { [weak self] in
                while !Task.isCancelled {   // sample data that moves a little, so the graphs have something to show
                    self?.applyLive(base.map { reading in
                        guard let v = reading.number, v != 0 else { return reading }
                        let moved = v * Double.random(in: 0.96...1.04)
                        return LiveReading(name: reading.name, value: String(format: abs(v) < 20 ? "%.1f %@" : "%.0f %@", moved, reading.unit))
                    })
                    try? await Task.sleep(nanoseconds: 1_000_000_000)
                }
            }
            return
        }
        guard let e = elm, !busy else { return }
        let trip = tripTask
        stopTrip()
        liveRunning = true
        liveTask = Task {
            await trip?.value
            let supported = (try? await e.supportedPIDs()) ?? []
            let pids = supported.isEmpty ? PIDs.list : PIDs.list.filter { supported.contains($0.pid) }
            while !Task.isCancelled {
                var out: [LiveReading] = []
                for p in pids {
                    if Task.isCancelled { return }
                    if let data = try? await e.pid(p.pid), data.count >= p.len {
                        out.append(LiveReading(name: p.name, value: p.format(p.decode(data))))
                    }
                }
                // Factory transmission fluid temperature (Ford/GM), read via mode $22 like the Mac app.
                if make == .ford, let d = try? await e.readMode22(0x1E1C), d.count >= 2 {
                    let c = Double(Int16(bitPattern: UInt16(d[0]) << 8 | UInt16(d[1]))) / 16
                    if (-40...180).contains(c) {
                        out.append(LiveReading(name: "Transmission fluid temp", value: PIDs.f(c, "degC")))
                    }
                } else if make == .gm, let d = try? await e.readMode22(0x1940), d.count >= 1 {
                    let c = Double(d[0]) - 40
                    if (-40...180).contains(c) {
                        out.append(LiveReading(name: "Transmission fluid temp", value: PIDs.f(c, "degC")))
                    }
                }
                if !out.isEmpty { applyLive(out) }
            }
        }
    }

    /// Stop live data and hand back its task, so the caller can wait until it has really finished.
    func pauseLive() -> Task<Void, Never>? {
        let task = liveTask ?? tripTask   // only one job can talk to the adapter at a time
        stopLive()
        stopTrip()
        return task
    }

    func stopLive() { liveTask?.cancel(); liveTask = nil; liveRunning = false; recording = false }
}
