import SwiftUI

enum AppInfo { static let version = "0.3 — Oct 9" }

struct ContentView: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        TabView {
            ProblemsTab().tabItem { Label("Problems", systemImage: "exclamationmark.triangle") }
            LiveTab().tabItem { Label("Live data", systemImage: "gauge") }
            SmogTab().tabItem { Label("Smog", systemImage: "checkmark.seal") }
            VehicleTab().tabItem { Label("Vehicle", systemImage: "car") }
            SettingsTab().tabItem { Label("Settings", systemImage: "gearshape") }
        }
    }
}

// Shared connect / status header
struct ConnectBar: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        VStack(spacing: 10) {
            Text(reader.status).font(.footnote).foregroundStyle(.secondary).multilineTextAlignment(.center)
            HStack {
                Button(reader.connected ? "Scan again" : "Connect") {
                    reader.connected ? reader.scan() : reader.connect()
                }
                .buttonStyle(.borderedProminent).disabled(reader.busy)
                if reader.connected {
                    Button("Disconnect") { reader.disconnect() }.buttonStyle(.bordered)
                }
            }
            if !reader.connected {
                Text(reader.useBluetooth ? "Using Bluetooth · change in Settings"
                                         : "Using Wi-Fi \(reader.host):\(reader.port) · change in Settings")
                    .font(.caption2).foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal)
    }
}

struct ProblemsTab: View {
    @EnvironmentObject var reader: Reader
    func color(_ u: String) -> Color {
        switch u { case "high": return .red; case "medium": return .orange; case "low": return .blue; default: return .gray }
    }
    var body: some View {
        NavigationStack {
            VStack {
                ConnectBar()
                if reader.scanned && reader.problems.isEmpty {
                    Spacer(); Label("No codes found", systemImage: "checkmark.circle").foregroundStyle(.green).font(.title3); Spacer()
                }
                List(reader.problems) { p in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(p.code).font(.headline)
                            Spacer()
                            Text(p.status).font(.caption).foregroundStyle(color(p.urgency))
                        }
                        Text(p.meaning).font(.subheadline).foregroundStyle(.secondary)
                        if let f = p.factory { Text("\(f) factory meaning").font(.caption2).foregroundStyle(.secondary) }
                    }
                }.listStyle(.plain)
                if reader.connected && !reader.problems.isEmpty {
                    Button("Clear codes & turn off light") { reader.clearCodes() }
                        .buttonStyle(.bordered).tint(.red).padding(.bottom, 6).disabled(reader.busy)
                }
            }
            .navigationTitle("Problems")
        }
    }
}

struct LiveTab: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        NavigationStack {
            VStack {
                if reader.connected {
                    Button(reader.liveRunning ? "Stop" : "Start live data") { reader.toggleLive() }
                        .buttonStyle(.borderedProminent).padding(.top)
                } else {
                    Text("Connect on the Problems tab first.").foregroundStyle(.secondary).padding()
                }
                List(reader.live) { r in
                    HStack { Text(r.name); Spacer(); Text(r.value).fontWeight(.semibold) }
                }.listStyle(.plain)
            }
            .navigationTitle("Live data")
        }
    }
}

struct SmogTab: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        NavigationStack {
            VStack(alignment: .leading) {
                if reader.monitors.isEmpty {
                    Text("Connect and scan to see whether the vehicle is ready for inspection.")
                        .foregroundStyle(.secondary).padding()
                } else {
                    Text(reader.smogText).font(.title3).fontWeight(.bold)
                        .foregroundStyle(reader.smogOK ? .green : .orange).padding(.horizontal).padding(.top)
                    Text(reader.smogDetail).font(.footnote).foregroundStyle(.secondary).padding(.horizontal)
                    List(reader.monitors, id: \.name) { m in
                        HStack {
                            Text(m.name).foregroundStyle(m.supported ? .primary : .secondary)
                            Spacer()
                            if !m.supported { Text("Not on this vehicle").font(.caption).foregroundStyle(.secondary) }
                            else if m.incomplete { Text("Still running").font(.caption).foregroundStyle(.orange) }
                            else { Text("Done").font(.caption).foregroundStyle(.green) }
                        }
                    }.listStyle(.plain)
                }
                if reader.connected {
                    Button("Check again") { reader.checkSmog() }.buttonStyle(.bordered).padding().disabled(reader.busy)
                }
            }
            .navigationTitle("Smog check")
        }
    }
}

struct VehicleTab: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        NavigationStack {
            Form {
                Section("Vehicle") {
                    row("VIN", reader.vin)
                    row("Battery", reader.battery)
                    row("Protocol", reader.protocolName)
                }
            }
            .navigationTitle("Vehicle")
        }
    }
    func row(_ k: String, _ v: String) -> some View {
        HStack { Text(k).foregroundStyle(.secondary); Spacer(); Text(v.isEmpty ? "—" : v).fontWeight(.semibold) }
    }
}

struct SettingsTab: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Toggle("Use Bluetooth adapter", isOn: $reader.useBluetooth)
                    if !reader.useBluetooth {
                        HStack {
                            Text("Wi-Fi address")
                            Spacer()
                            TextField("192.168.0.10", text: $reader.host)
                                .multilineTextAlignment(.trailing).autocorrectionDisabled()
                        }
                        HStack {
                            Text("Port")
                            Spacer()
                            TextField("35000", text: $reader.port)
                                .multilineTextAlignment(.trailing).keyboardType(.numberPad).frame(width: 110)
                        }
                    }
                } header: {
                    Text("Adapter")
                } footer: {
                    Text("Wi-Fi adapters make their own Wi-Fi network — join it in the iPhone's Settings first. The OBDLink MX+ (classic Bluetooth) isn't supported here; use a Wi-Fi or BLE adapter.")
                }

                Section("Vehicle make (for factory code meanings)") {
                    Picker("Make", selection: $reader.make) {
                        Text("Other").tag(Make.other)
                        Text("Ford / Lincoln / Mercury").tag(Make.ford)
                        Text("GM (Chevy / GMC …)").tag(Make.gm)
                    }
                }

                Section("About") {
                    HStack { Text("App version").foregroundStyle(.secondary); Spacer(); Text(AppInfo.version).fontWeight(.semibold) }
                }
            }
            .navigationTitle("Settings")
        }
    }
}
