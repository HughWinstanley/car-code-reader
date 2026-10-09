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

@MainActor
final class Reader: ObservableObject {
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
                               urgency: DTC.urgency($0.code, status: $0.status, module: "Engine"),
                               factory: factory)
            }
            scanned = true
            status = problems.isEmpty ? "No codes found." : "\(problems.count) code\(problems.count == 1 ? "" : "s") found."
            if let d = try await e.readiness() { applySmog(d) }
        } catch { status = "Scan error: \(error.localizedDescription)" }
    }

    func clearCodes() {
        guard let e = elm, !busy else { return }
        busy = true; status = "Clearing codes…"
        Task {
            do { try await e.clearCodes(); await scanInternal(e); status = "Codes cleared." }
            catch { status = "Couldn't clear: \(error.localizedDescription)" }
            busy = false
        }
    }

    func checkSmog() {
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

    func readSemi() {
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
        if liveRunning { stopLive(); return }
        guard let e = elm else { return }
        liveRunning = true
        liveTask = Task {
            while !Task.isCancelled {
                var out: [LiveReading] = []
                for p in PIDs.list {
                    if let data = try? await e.pid(p.pid), data.count >= 2 {
                        out.append(LiveReading(name: p.name, value: p.format(p.decode(data))))
                    }
                }
                if !out.isEmpty { live = out }
            }
        }
    }

    func stopLive() { liveTask?.cancel(); liveTask = nil; liveRunning = false }
}
