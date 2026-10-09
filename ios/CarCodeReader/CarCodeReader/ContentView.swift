import SwiftUI

struct ContentView: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        TabView {
            ProblemsTab().tabItem { Label("Problems", systemImage: "exclamationmark.triangle") }
            LiveTab().tabItem { Label("Live data", systemImage: "gauge") }
            SmogTab().tabItem { Label("Smog", systemImage: "checkmark.seal") }
            VehicleTab().tabItem { Label("Vehicle", systemImage: "car") }
        }
    }
}

// Shared connect / status header
struct ConnectBar: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        VStack(spacing: 10) {
            if !reader.connected {
                Toggle("Use Bluetooth adapter", isOn: $reader.useBluetooth)
                if !reader.useBluetooth {
                    HStack {
                        TextField("Adapter IP", text: $reader.host).textFieldStyle(.roundedBorder).autocorrectionDisabled()
                        TextField("Port", text: $reader.port).textFieldStyle(.roundedBorder).frame(width: 80).keyboardType(.numberPad)
                    }
                }
            }
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
                Section("Tell the app the make (for factory code meanings)") {
                    Picker("Make", selection: $reader.make) {
                        Text("Other").tag(Make.other); Text("Ford / Lincoln / Mercury").tag(Make.ford); Text("GM (Chevy / GMC …)").tag(Make.gm)
                    }
                }
            }
            .navigationTitle("Vehicle")
        }
    }
    func row(_ k: String, _ v: String) -> some View {
        HStack { Text(k).foregroundStyle(.secondary); Spacer(); Text(v.isEmpty ? "—" : v).fontWeight(.semibold) }
    }
}
