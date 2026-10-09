import SwiftUI

enum AppInfo { static let version = "2.6 — Oct 9" }
enum Tab { case home, problems, live, smog, settings }

extension Color {
    /// Build a colour from a "#RRGGBB" hex string (matches the Mac app's exact tints).
    init(hex: String) {
        let s = hex.hasPrefix("#") ? String(hex.dropFirst()) : hex
        var v: UInt64 = 0
        Scanner(string: s).scanHexInt64(&v)
        self = Color(red: Double((v >> 16) & 0xFF) / 255,
                     green: Double((v >> 8) & 0xFF) / 255,
                     blue: Double(v & 0xFF) / 255)
    }
}

/// The exact logo colours from the Mac app (car_code_reader.py TINT).
enum MacTint {
    static let engine  = Color(hex: "#E08A00")
    static let safety  = Color(hex: "#D9362B")
    static let scan    = Color(hex: "#6C4BD1")
    static let gauge   = Color(hex: "#0F8B8D")
    static let smog    = Color(hex: "#1E8A4A")
    static let vehicle = Color(hex: "#1F6FD1")
    static let semi    = Color(hex: "#B4532A")
    static let old     = Color(hex: "#7A5A2E")
}

struct ContentView: View {
    @EnvironmentObject var reader: Reader
    @State private var selection: Tab = .home
    var body: some View {
        TabView(selection: $selection) {
            HomeTab(selection: $selection).tabItem { Label("Home", systemImage: "house") }.tag(Tab.home)
            ProblemsTab().tabItem { Label("Problems", systemImage: "exclamationmark.triangle") }.tag(Tab.problems)
            LiveTab().tabItem { Label("Live", systemImage: "gauge") }.tag(Tab.live)
            SmogTab().tabItem { Label("Smog", image: "tab-smog") }.tag(Tab.smog)
            SettingsTab().tabItem { Label("Settings", systemImage: "gearshape") }.tag(Tab.settings)
        }
    }
}

// MARK: - Home

/// Either a hand-drawn asset icon (ported from the Mac app) or an SF Symbol.
enum TileIcon {
    case asset(String)
    case system(String)
}

/// The coloured icon-and-text card used on the Home grid.
struct TileLabel: View {
    let title: String
    let subtitle: String
    let icon: TileIcon
    let tint: Color
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Group {
                switch icon {
                case .asset(let name):
                    // full-colour logo from the Mac app (pale halo baked in)
                    Image(name).resizable().scaledToFit().frame(width: 58, height: 58)
                case .system(let name):
                    ZStack {
                        Circle().fill(tint.opacity(0.15)).frame(width: 52, height: 52)
                        Image(systemName: name).font(.system(size: 23, weight: .semibold)).foregroundStyle(tint)
                    }
                }
            }
            .frame(height: 58, alignment: .leading)
            Text(title).font(.headline).foregroundStyle(.primary)
            Text(subtitle).font(.caption).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 128, alignment: .leading)
        .padding(16)
        .background(RoundedRectangle(cornerRadius: 18).fill(Color(.secondarySystemGroupedBackground)))
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color(.separator), lineWidth: 0.5))
    }
}

struct HomeTab: View {
    @EnvironmentObject var reader: Reader
    @Binding var selection: Tab
    @State private var showPicker = false
    private let cols = [GridItem(.flexible(), spacing: 14), GridItem(.flexible(), spacing: 14)]

    var body: some View {
        NavigationStack {
            ScrollView {
                if reader.isDemo {
                    VStack(spacing: 6) {
                        Text("Demo mode — sample data (not a real car)")
                            .font(.footnote).fontWeight(.semibold).foregroundStyle(.orange)
                        Text("Close and reopen the app to clear it.")
                            .font(.caption2).foregroundStyle(.secondary)
                        Button("Exit demo") { reader.exitDemo() }
                            .font(.caption).buttonStyle(.bordered).tint(.orange)
                    }
                    .multilineTextAlignment(.center).frame(maxWidth: .infinity)
                    .padding(.horizontal).padding(.top, 4)
                } else {
                    VStack(spacing: 6) {
                        Text(reader.connected ? reader.status : "Not connected · open Problems or tap Scan to connect")
                            .font(.footnote).foregroundStyle(.secondary)
                        if !reader.connected {
                            Button("See a demo (sample data)") { reader.loadDemo(); selection = .problems }
                                .font(.footnote).buttonStyle(.bordered)
                        }
                    }
                    .multilineTextAlignment(.center).frame(maxWidth: .infinity)
                    .padding(.horizontal).padding(.top, 4)
                }

                LazyVGrid(columns: cols, spacing: 14) {
                    // Order matches the Mac app's home screen.
                    Button {
                        reader.scanKind = .engine
                        if reader.connected { reader.scan() } else { reader.connect() }
                        selection = .problems
                    } label: {
                        TileLabel(title: "Engine codes", subtitle: "Check-engine and transmission codes",
                                  icon: .asset("icon-engine"), tint: MacTint.engine)
                    }.buttonStyle(.plain)

                    Button {
                        reader.scanKind = .safety
                        if reader.connected { reader.scan() } else { reader.connect() }
                        selection = .problems
                    } label: {
                        TileLabel(title: "ABS and airbag", subtitle: "Brake and airbag warning lights",
                                  icon: .asset("icon-absbag"), tint: MacTint.safety)
                    }.buttonStyle(.plain)

                    Button {
                        reader.scanKind = .all
                        if reader.connected { reader.scan() } else { reader.connect() }
                        selection = .problems
                    } label: {
                        TileLabel(title: "Full scan", subtitle: "Everything at once",
                                  icon: .asset("icon-scan"), tint: MacTint.scan)
                    }.buttonStyle(.plain)

                    NavigationLink {
                        SemiView()
                    } label: {
                        TileLabel(title: "Semi trucks", subtitle: "Heavy-duty trucks, 9-pin port",
                                  icon: .asset("icon-semi"), tint: MacTint.semi)
                    }.buttonStyle(.plain)

                    Button { selection = .live } label: {
                        TileLabel(title: "Live data", subtitle: "Engine readings in real time",
                                  icon: .asset("icon-gauge"), tint: MacTint.gauge)
                    }.buttonStyle(.plain)

                    Button { selection = .smog } label: {
                        TileLabel(title: "Smog check", subtitle: "Ready for an emissions test?",
                                  icon: .asset("icon-smog"), tint: MacTint.smog)
                    }.buttonStyle(.plain)

                    NavigationLink {
                        OBD1View()
                    } label: {
                        TileLabel(title: "OBD-I", subtitle: "Blink codes (1995 & older), no adapter",
                                  icon: .asset("icon-blink"), tint: MacTint.old)
                    }.buttonStyle(.plain)

                    Button { showPicker = true } label: {
                        TileLabel(title: "Choose vehicle", subtitle: "Make, model and year",
                                  icon: .asset("icon-vehicle"), tint: MacTint.vehicle)
                    }.buttonStyle(.plain)
                }
                .padding(.horizontal, 14).padding(.top, 8)
            }
            .navigationTitle("Car Code Reader")
            .sheet(isPresented: $showPicker) { VehiclePickerSheet() }
        }
    }
}

// MARK: - Shared connect bar

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

// MARK: - Mac-style empty state (shown when nothing is connected)

struct EmptyStateCard: View {
    @EnvironmentObject var reader: Reader
    let icon: String
    let tint: Color
    let title: String
    let message: String

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .center, spacing: 16) {
                Image(icon).resizable().scaledToFit().frame(width: 64, height: 64)
                VStack(alignment: .leading, spacing: 4) {
                    Text(title).font(.headline)
                    Text(message).font(.subheadline).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            if reader.busy {
                HStack(spacing: 8) {
                    ProgressView()
                    Text(reader.status).font(.footnote).foregroundStyle(.secondary)
                }
            } else {
                Button { reader.connect() } label: {
                    Text("Connect").font(.headline).foregroundStyle(.white)
                        .padding(.horizontal, 28).padding(.vertical, 12)
                        .background(Capsule().fill(Color.primary))
                }
                if reader.status != "Not connected" {
                    Text(reader.status).font(.footnote).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(20)
        .background(RoundedRectangle(cornerRadius: 18).fill(Color(.secondarySystemGroupedBackground)))
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color(.separator), lineWidth: 0.5))
        .padding(.horizontal)
    }
}

/// The subtitle + empty-state card laid out like the Mac app's pages.
struct NotConnectedView: View {
    let subtitle: String
    let icon: String
    let tint: Color
    let message: String
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text(subtitle).font(.subheadline).foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true).padding(.horizontal)
                EmptyStateCard(icon: icon, tint: tint, title: "Not connected yet", message: message)
            }
            .padding(.top, 8)
        }
    }
}

// MARK: - Problems

struct ProblemsTab: View {
    @EnvironmentObject var reader: Reader
    func color(_ u: String) -> Color {
        switch u { case "high": return .red; case "medium": return .orange; case "low": return .blue; default: return .gray }
    }
    var body: some View {
        NavigationStack {
            Group {
            if !reader.connected {
                NotConnectedView(
                    subtitle: reader.scanKind.subtitle,
                    icon: reader.scanKind.icon, tint: MacTint.engine,
                    message: reader.scanKind.message)
            } else {
            VStack {
                ConnectBar()
                if reader.scanned && reader.problems.isEmpty {
                    Spacer(); Label("No codes found", systemImage: "checkmark.circle").foregroundStyle(.green).font(.title3); Spacer()
                }
                List {
                    ForEach(reader.problems) { p in
                        NavigationLink {
                            ProblemDetailView(problem: p)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text(p.code).font(.headline)
                                    Spacer()
                                    Text(p.status).font(.caption).foregroundStyle(color(p.urgency))
                                }
                                Text(p.meaning).font(.subheadline).foregroundStyle(.secondary)
                                if let f = p.factory { Text("\(f) factory meaning").font(.caption2).foregroundStyle(.secondary) }
                            }
                        }
                        .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                            Button(role: .destructive) { reader.removeProblem(p) } label: {
                                Label("Clear code", systemImage: "bolt.slash")
                            }
                        }
                    }

                    if !reader.problems.isEmpty {
                        Text("Swipe a code left to clear it from this list. Note: a car can only erase all codes at once (the button below) — one-at-a-time erasing isn't something the OBD port supports.")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                }.listStyle(.plain)
                if reader.connected && !reader.problems.isEmpty {
                    Button("Clear codes & turn off light") { reader.clearCodes() }
                        .buttonStyle(.bordered).tint(.red).padding(.bottom, 6).disabled(reader.busy)
                }
            }
            }
            }
            .navigationTitle("Problems")
        }
    }
}

// MARK: - Live data

struct LiveTab: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        NavigationStack {
            Group {
                if reader.connected {
                    VStack(spacing: 0) {
                        Button(reader.liveRunning ? "Stop" : "Start live data") { reader.toggleLive() }
                            .buttonStyle(.borderedProminent).padding(.vertical, 8)
                        List {
                            Section("Vehicle") {
                                if !reader.chosenName.isEmpty { vrow("Make / model / year", reader.chosenName) }
                                vrow("VIN", reader.vin)
                                vrow("Battery", reader.battery)
                                vrow("Protocol", reader.protocolName)
                            }
                            Section("Live readings") {
                                if reader.live.isEmpty {
                                    Text("Tap “Start live data” to stream engine readings.")
                                        .font(.footnote).foregroundStyle(.secondary)
                                } else {
                                    ForEach(reader.live) { r in
                                        HStack { Text(r.name); Spacer(); Text(r.value).fontWeight(.semibold) }
                                    }
                                }
                            }
                        }
                        .listStyle(.insetGrouped)
                    }
                } else {
                    NotConnectedView(
                        subtitle: "The vehicle's VIN and details, plus live engine readings that update about once a second.",
                        icon: "icon-gauge", tint: MacTint.gauge,
                        message: "Plug the adapter in, turn the key to ON, then connect to see the vehicle info and live data.")
                }
            }
            .navigationTitle("Live data")
        }
    }

    /// A label/value row that shows “—” when the value hasn't been read.
    private func vrow(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label).foregroundStyle(.secondary)
            Spacer()
            Text(value.isEmpty ? "—" : value).fontWeight(.semibold)
                .multilineTextAlignment(.trailing)
        }
    }
}

// MARK: - Smog

struct SmogTab: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        NavigationStack {
            VStack(alignment: .leading) {
                if !reader.connected {
                    NotConnectedView(
                        subtitle: "Whether the vehicle's self-tests are done, so it can pass an emissions inspection.",
                        icon: "icon-smog", tint: MacTint.smog,
                        message: "Connect and scan to see whether the vehicle is ready for inspection.")
                } else if reader.monitors.isEmpty {
                    Text("Tap Check again to read the self-tests.")
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

// MARK: - Vehicle (opened from Home)

struct VehicleView: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        Form {
            Section("Vehicle") {
                if !reader.chosenName.isEmpty { row("Chosen", reader.chosenName) }
                row("VIN", reader.vin)
                row("Battery", reader.battery)
                row("Protocol", reader.protocolName)
            }
        }
        .navigationTitle("Vehicle")
    }
    func row(_ k: String, _ v: String) -> some View {
        HStack { Text(k).foregroundStyle(.secondary); Spacer(); Text(v.isEmpty ? "—" : v).fontWeight(.semibold) }
    }
}

// MARK: - Settings

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


                Section {
                    if reader.isDemo {
                        Button("Exit demo", role: .destructive) { reader.exitDemo() }
                    } else {
                        Button("Load demo data") { reader.loadDemo() }
                    }
                } header: {
                    Text("Demo")
                } footer: {
                    Text("Fills the app with sample data so you can look around without a car. It's never saved — closing and reopening the app clears it.")
                }

                Section("About") {
                    HStack { Text("App version").foregroundStyle(.secondary); Spacer(); Text(AppInfo.version).fontWeight(.semibold) }
                }
            }
            .navigationTitle("Settings")
        }
    }
}
