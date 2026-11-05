import SwiftUI

enum AppInfo { static let version = "2.12 — Nov 5" }
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

extension Color {
    /// A colour that follows the app's light or dark appearance.
    init(light: String, dark: String) {
        let (l, d) = (UIColor(Color(hex: light)), UIColor(Color(hex: dark)))
        self = Color(UIColor { $0.userInterfaceStyle == .dark ? d : l })
    }
}

/// The Mac app's palette (car_code_reader.py C): paper and ink, colour only for status.
enum MacColor {
    static let page      = Color(light: "#FFFFFF", dark: "#000000")
    static let panel     = Color(light: "#FFFFFF", dark: "#1C1C1E")
    static let ink       = Color(light: "#000000", dark: "#FFFFFF")
    static let muted     = Color(light: "#6B6B6B", dark: "#A1A1A6")
    static let line      = Color(light: "#E2E2E2", dark: "#38383A")
    static let raised    = Color(light: "#F3F3F3", dark: "#2C2C2E")
    static let pressed   = Color(light: "#2A2A2A", dark: "#D1D1D6")
    static let amber     = Color(hex: "#E39A12")
    static let amberInk  = Color(light: "#8A5A00", dark: "#F5B942")
    static let amberSoft = Color(light: "#FFF3DC", dark: "#3A2A0B")
    static let red       = Color(light: "#D9362B", dark: "#FF6259")
    static let redSoft   = Color(light: "#FDE6E4", dark: "#401815")
    static let green     = Color(light: "#1E8A4A", dark: "#3DCB6C")
    static let greenSoft = Color(light: "#E2F3E8", dark: "#12331F")
    static let blueSoft  = Color(light: "#EFEFEF", dark: "#2C2C2E")
    static let off       = Color(light: "#A3A3A3", dark: "#8E8E93")
    static let offSoft   = Color(light: "#F1F1F1", dark: "#2C2C2E")
}

/// The Settings choice: follow the iPhone, or always light or dark.
enum Appearance: String, CaseIterable, Identifiable {
    case automatic, light, dark
    var id: String { rawValue }
    var title: String { rawValue.capitalized }
    var scheme: ColorScheme? {
        switch self {
        case .automatic: return nil
        case .light:     return .light
        case .dark:      return .dark
        }
    }
}

/// Urgency -> dot colour, pill colours and words (the Mac app's LEVELS).
struct UrgencyLevel {
    let dot: Color
    let pillFill: Color
    let pillText: Color
    let words: String
    let order: Int

    init(_ level: String) {
        switch level {
        case "high":   (dot, pillFill, pillText, words, order) = (MacColor.red, MacColor.redSoft, MacColor.red, "Fix soon", 0)
        case "medium": (dot, pillFill, pillText, words, order) = (MacColor.amber, MacColor.amberSoft, MacColor.amberInk, "Get it checked", 1)
        case "low":    (dot, pillFill, pillText, words, order) = (MacColor.ink, MacColor.blueSoft, MacColor.ink, "Low priority", 2)
        default:       (dot, pillFill, pillText, words, order) = (MacColor.off, MacColor.offSoft, MacColor.muted, "Past problem", 3)
        }
    }
}

// MARK: - Mac-style building blocks

/// The Mac app's PillButton.
struct PillStyle: ButtonStyle {
    enum Kind { case primary, secondary, danger }
    var kind: Kind = .secondary
    var big = false
    @Environment(\.isEnabled) private var isEnabled

    func makeBody(configuration: Configuration) -> some View {
        let down = configuration.isPressed
        let fill: Color, text: Color, outline: Color
        if !isEnabled {
            (fill, text, outline) = (MacColor.offSoft, MacColor.off, MacColor.line)
        } else {
            switch kind {
            case .primary:   (fill, text, outline) = (down ? MacColor.pressed : MacColor.ink, MacColor.page, MacColor.ink)
            case .secondary: (fill, text, outline) = (down ? MacColor.raised : MacColor.panel, MacColor.ink, MacColor.ink)
            case .danger:    (fill, text, outline) = (down ? MacColor.redSoft : MacColor.panel, MacColor.red, MacColor.red)
            }
        }
        return configuration.label
            .font(.system(size: big ? 15 : 13, weight: .bold))
            .foregroundStyle(text)
            .padding(.horizontal, big ? 20 : 15).padding(.vertical, big ? 12 : 7)
            .background(Capsule().fill(fill))
            .overlay(Capsule().stroke(outline, lineWidth: 1))
            .contentShape(Capsule())
    }
}

/// A small coloured status pill ("Fix soon", "Done", ...).
struct StatusPill: View {
    let words: String
    let fill: Color
    let text: Color
    var body: some View {
        Text(words).font(.system(size: 12, weight: .bold)).foregroundStyle(text)
            .lineLimit(1).fixedSize()
            .padding(.horizontal, 12).padding(.vertical, 5)
            .background(Capsule().fill(fill))
    }
}

/// The Mac app's underlined text link.
struct LinkLabel: View {
    let title: String
    let action: () -> Void
    init(_ title: String, action: @escaping () -> Void) { self.title = title; self.action = action }
    var body: some View {
        Button(action: action) {
            Text(title).font(.system(size: 13, weight: .bold)).underline().foregroundStyle(MacColor.ink)
        }
        .buttonStyle(.plain)
    }
}

/// The Mac app's RoundPanel: a white rounded card with a thin grey edge.
struct RoundCard<Content: View>: View {
    var radius: CGFloat = 18
    var fill: Color = MacColor.panel
    var outline: Color = MacColor.line
    var padX: CGFloat = 18
    var padY: CGFloat = 14
    @ViewBuilder let content: Content
    var body: some View {
        VStack(alignment: .leading, spacing: 0) { content }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, padX).padding(.vertical, padY)
            .background(RoundedRectangle(cornerRadius: radius, style: .continuous).fill(fill))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous).stroke(outline, lineWidth: 1))
    }
}

/// Lays out pills left to right, wrapping when they don't fit a phone's width.
struct FlowLayout: Layout {
    var spacing: CGFloat = 10

    private func rows(_ width: CGFloat, _ subviews: Subviews) -> [(items: [(Int, CGSize)], height: CGFloat)] {
        var out: [(items: [(Int, CGSize)], height: CGFloat)] = [([], 0)]
        var x: CGFloat = 0
        for (i, view) in subviews.enumerated() {
            let size = view.sizeThatFits(.unspecified)
            if x > 0 && x + size.width > width {
                out.append(([], 0))
                x = 0
            }
            out[out.count - 1].items.append((i, size))
            out[out.count - 1].height = max(out[out.count - 1].height, size.height)
            x += size.width + spacing
        }
        return out
    }

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? .infinity
        let all = rows(width, subviews)
        let used = all.map { row in row.items.reduce(CGFloat(0)) { $0 + $1.1.width } + spacing * CGFloat(max(0, row.items.count - 1)) }.max() ?? 0
        let height = all.reduce(CGFloat(0)) { $0 + $1.height } + spacing * CGFloat(max(0, all.count - 1))
        return CGSize(width: proposal.width ?? used, height: height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var y = bounds.minY
        for row in rows(bounds.width, subviews) {
            var x = bounds.minX
            for (i, size) in row.items {
                subviews[i].place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(size))
                x += size.width + spacing
            }
            y += row.height + spacing
        }
    }
}

/// Page heading: the same round picture as the Home tiles, a bold title and a muted line under it.
struct PageTitle: View {
    let title: String
    var subtitle = ""
    var icon: String? = nil
    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            if let icon { Image(icon).resizable().scaledToFit().frame(width: 66, height: 66) }
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 24, weight: .bold)).foregroundStyle(MacColor.ink)
                    .fixedSize(horizontal: false, vertical: true)
                if !subtitle.isEmpty {
                    Text(subtitle).font(.system(size: 13)).foregroundStyle(MacColor.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// A number in a circle, used for how-to steps.
struct StepDot: View {
    let number: Int
    var fill: Color = MacColor.ink
    var text: Color = MacColor.page
    var size: CGFloat = 26
    var body: some View {
        ZStack {
            Circle().fill(fill)
            Text("\(number)").font(.system(size: size * 0.46, weight: .bold)).foregroundStyle(text)
        }
        .frame(width: size, height: size)
    }
}

/// The strip across the top: the chosen vehicle and Disconnect. Only there when it has something to show.
struct AppHeader: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        HStack(spacing: 10) {
            if !reader.chosenName.isEmpty {
                Text(reader.chosenName).font(.system(size: 13, weight: .bold)).foregroundStyle(MacColor.ink)
                    .lineLimit(1).minimumScaleFactor(0.8)
            }
            Spacer(minLength: 8)
            if reader.isDemo {
                Button("Exit demo") { reader.exitDemo() }.buttonStyle(PillStyle())
            } else if reader.connected {
                Button("Disconnect") { reader.disconnect() }.buttonStyle(PillStyle())
            }
        }
        .padding(.horizontal, 16).padding(.vertical, 10)
        .background(MacColor.page)
    }
}

/// One tab's page: the header strip and hairline, then the content on white paper.
struct MacPage<Content: View>: View {
    @EnvironmentObject var reader: Reader
    @ViewBuilder let content: Content
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if reader.connected || reader.isDemo || !reader.chosenName.isEmpty {
                    AppHeader()
                    Rectangle().fill(MacColor.line).frame(height: 1)
                }
                content.frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            .background(MacColor.page)
            .toolbar(.hidden, for: .navigationBar)
        }
        .tint(MacColor.ink)
    }
}

/// The Mac app's Tile: a centred picture, bold title and muted line on a white card.
struct TileCard<Art: View>: View {
    let title: String
    var subtitle = ""
    @ViewBuilder let art: Art
    var body: some View {
        VStack(spacing: 6) {
            art.frame(height: 72)
            Text(title).font(.system(size: 15, weight: .bold)).foregroundStyle(MacColor.ink)
                .multilineTextAlignment(.center).fixedSize(horizontal: false, vertical: true)
            if !subtitle.isEmpty {
                Text(subtitle).font(.system(size: 12)).foregroundStyle(MacColor.muted)
                    .multilineTextAlignment(.center).fixedSize(horizontal: false, vertical: true)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .padding(.horizontal, 10).padding(.vertical, 14)
        .background(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(MacColor.panel))
        .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).stroke(MacColor.line, lineWidth: 1))
        .contentShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
    }
}

/// A grid where every card in a row gets the same height, like the Mac app's tile_grid.
struct TileGrid<Item: Hashable, Cell: View>: View {
    let items: [Item]
    var columns = 2
    @ViewBuilder let cell: (Item) -> Cell

    var body: some View {
        Grid(horizontalSpacing: 12, verticalSpacing: 12) {
            ForEach(Array(stride(from: 0, to: items.count, by: columns)), id: \.self) { start in
                GridRow {
                    ForEach(0..<columns, id: \.self) { i in
                        if start + i < items.count {
                            cell(items[start + i])
                        } else {
                            Color.clear.gridCellUnsizedAxes([.horizontal, .vertical])
                        }
                    }
                }
            }
        }
    }
}

/// The Mac app's _empty_card: a picture, a line and a button for a page with nothing to show yet.
struct EmptyStateCard: View {
    @EnvironmentObject var reader: Reader
    let icon: String
    let title: String
    let message: String
    var buttonTitle: String? = "Connect"
    var action: (() -> Void)? = nil

    var body: some View {
        RoundCard(radius: 22) {
            HStack(alignment: .center, spacing: 14) {
                Image(icon).resizable().scaledToFit().frame(width: 66, height: 66)
                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(.system(size: 16, weight: .bold)).foregroundStyle(MacColor.ink)
                    Text(message).font(.system(size: 13)).foregroundStyle(MacColor.muted)
                        .fixedSize(horizontal: false, vertical: true)
                    if reader.busy {
                        BusyLine().padding(.top, 8)
                    } else if let buttonTitle {
                        Button(buttonTitle) { (action ?? { reader.connect() })() }
                            .buttonStyle(PillStyle(kind: .primary)).padding(.top, 10)
                    }
                }
            }
            if !reader.busy && !reader.connected && reader.status != "Not connected" {
                Text(reader.status).font(.system(size: 12)).foregroundStyle(MacColor.muted)
                    .fixedSize(horizontal: false, vertical: true).padding(.top, 10)
            }
        }
    }
}

/// A spinner and the current step.
struct BusyLine: View {
    @EnvironmentObject var reader: Reader
    var body: some View {
        HStack(spacing: 8) {
            ProgressView()
            Text(reader.status).font(.system(size: 12)).foregroundStyle(MacColor.muted)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

// MARK: - Tabs

struct ContentView: View {
    @EnvironmentObject var reader: Reader
    @State private var selection: Tab = .home
    @AppStorage("appearance") private var appearance: Appearance = .automatic
    var body: some View {
        TabView(selection: $selection) {
            HomeTab(selection: $selection).tabItem { Label("Home", systemImage: "house") }.tag(Tab.home)
            ProblemsTab(selection: $selection).tabItem { Label("Problems", systemImage: "exclamationmark.triangle") }.tag(Tab.problems)
            LiveTab().tabItem { Label("Live", systemImage: "gauge") }.tag(Tab.live)
            SmogTab().tabItem { Label("Smog", image: "tab-smog") }.tag(Tab.smog)
            SettingsTab().tabItem { Label("Settings", systemImage: "gearshape") }.tag(Tab.settings)
        }
        .preferredColorScheme(appearance.scheme)
    }
}

// MARK: - Home

struct HomeTab: View {
    @EnvironmentObject var reader: Reader
    @Binding var selection: Tab
    @State private var showPicker = false

    private func startScan(_ kind: ScanKind) {
        reader.scanKind = kind
        if reader.connected { reader.scan() } else { reader.connect() }
        selection = .problems
    }

    private func tile(_ title: String, _ subtitle: String, _ icon: String) -> some View {
        TileCard(title: title, subtitle: subtitle) {
            Image(icon).resizable().scaledToFit().frame(height: 72)
        }
    }

    var body: some View {
        MacPage {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    if reader.isDemo || !reader.chosenName.isEmpty { vehicleBlock.padding(.bottom, 18) }

                    // Order matches the Mac app's home screen.
                    Grid(horizontalSpacing: 12, verticalSpacing: 12) {
                        GridRow {
                            Button { startScan(.engine) } label: {
                                tile("Engine codes", "Check-engine and transmission codes", "icon-engine")
                            }.buttonStyle(.plain)
                            Button { startScan(.safety) } label: {
                                tile("ABS and airbag", "Brake and airbag warning lights", "icon-absbag")
                            }.buttonStyle(.plain)
                        }
                        GridRow {
                            Button { startScan(.all) } label: {
                                tile("Full scan", "Everything at once", "icon-scan")
                            }.buttonStyle(.plain)
                            NavigationLink { SemiView() } label: {
                                tile("Semi trucks", "Heavy-duty trucks, 9-pin port", "icon-semi")
                            }.buttonStyle(.plain)
                        }
                        GridRow {
                            Button { selection = .live } label: {
                                tile("Live data", "Engine readings in real time", "icon-gauge")
                            }.buttonStyle(.plain)
                            Button { selection = .smog } label: {
                                tile("Smog check", "Ready for an emissions test?", "icon-smog")
                            }.buttonStyle(.plain)
                        }
                        GridRow {
                            NavigationLink { OBD1View() } label: {
                                tile("OBD-I", "Blink codes (1995 & older), no adapter", "icon-blink")
                            }.buttonStyle(.plain)
                            Button { showPicker = true } label: {
                                tile("Choose vehicle", "Make, model and year", "icon-vehicle")
                            }.buttonStyle(.plain)
                        }
                    }
                }
                .padding(16)
            }
            .sheet(isPresented: $showPicker) { VehiclePickerSheet() }
        }
    }

    @ViewBuilder private var vehicleBlock: some View {
        VStack(alignment: .leading, spacing: 10) {
            if reader.isDemo {
                RoundCard(fill: MacColor.amberSoft, outline: MacColor.amberSoft, padY: 12) {
                    Text("Demo mode: sample data, not a real car").font(.system(size: 14, weight: .bold))
                        .foregroundStyle(MacColor.ink)
                    Text("Close and reopen the app to clear it.").font(.system(size: 13))
                        .foregroundStyle(MacColor.ink)
                }
            }
            if !reader.chosenName.isEmpty {
                HStack(spacing: 14) {
                    if !reader.chosenMake.isEmpty { MakeBadge(make: reader.chosenMake, size: 56) }
                    VStack(alignment: .leading, spacing: 2) {
                        Text(reader.chosenName).font(.system(size: 17, weight: .bold)).foregroundStyle(MacColor.ink)
                        HStack(spacing: 10) {
                            Text(VehicleData.supportText(make: reader.chosenMake, year: reader.year)).font(.system(size: 13))
                                .foregroundStyle(MacColor.muted)
                            LinkLabel("Change") { showPicker = true }
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Problems

/// The dashboard warning light from the Mac app: picture (not connected), amber/red (problems), green (all clear).
struct Lamp: View {
    enum Mode { case off, busy, ok, warn, bad }
    let mode: Mode
    var size: CGFloat = 92

    private var core: Color {
        switch mode {
        case .off, .busy: return MacColor.ink
        case .ok: return MacColor.green
        case .warn: return MacColor.amber
        case .bad: return MacColor.red
        }
    }
    private var glyph: String {
        switch mode {
        case .off: return "?"
        case .busy: return "…"
        case .ok: return "✓"
        case .warn, .bad: return "!"
        }
    }

    var body: some View {
        Group {
            if mode == .off {
                Image("icon-engine").resizable().scaledToFit()
            } else if mode == .busy {
                TimelineView(.periodic(from: .now, by: 0.55)) { ctx in
                    light(glow: Int(ctx.date.timeIntervalSinceReferenceDate / 0.55) % 2 == 0)
                }
            } else {
                light(glow: true)
            }
        }
        .frame(width: size, height: size)
    }

    private func light(glow: Bool) -> some View {
        ZStack {
            if glow {
                Circle().fill(RadialGradient(colors: [core.opacity(0.45), core.opacity(0)], center: .center,
                                             startRadius: size * 0.28, endRadius: size * 0.5))
            }
            Circle().fill(core).frame(width: size * 0.6, height: size * 0.6)
            Ellipse().fill(Color.white.opacity(0.25))
                .frame(width: size * 0.44, height: size * 0.28)
                .offset(y: -size * 0.13)
            Text(glyph).font(.system(size: size * 0.28, weight: .bold))
                .foregroundStyle(mode == .busy ? MacColor.page : .white)
        }
    }
}

/// One problem as a rounded card (the Mac app's ProblemRow). Tap to open the details in place.
struct ProblemCard: View {
    @EnvironmentObject var reader: Reader
    @Environment(\.openURL) private var openURL
    let problem: Problem
    @State private var open = false

    private var statusWords: String { problem.status.prefix(1).uppercased() + problem.status.dropFirst() }

    var body: some View {
        let level = UrgencyLevel(problem.urgency)
        RoundCard(radius: 16, padY: 14) {
            VStack(alignment: .leading, spacing: 3) {
                HStack(alignment: .top, spacing: 10) {
                    ZStack {
                        Circle().fill(level.dot.opacity(0.22)).frame(width: 16, height: 16)
                        Circle().fill(level.dot).frame(width: 8, height: 8)
                    }
                    .padding(.top, 2)
                    Text(problem.meaning).font(.system(size: 15, weight: .bold)).foregroundStyle(MacColor.ink)
                        .fixedSize(horizontal: false, vertical: true)
                    Spacer(minLength: 4)
                    StatusPill(words: level.words, fill: level.pillFill, text: level.pillText)
                }
                Text("\(problem.module), code \(problem.code). \(statusWords).")
                    .font(.system(size: 12)).foregroundStyle(MacColor.muted)
                    .padding(.leading, 26)
            }
            .contentShape(Rectangle())
            .onTapGesture { withAnimation(.easeInOut(duration: 0.2)) { open.toggle() } }

            if open { details.padding(.leading, 26).padding(.top, 10) }
        }
    }

    private var details: some View {
        VStack(alignment: .leading, spacing: 10) {
            section("Why it matters", CodeDetail.whyItMatters(problem.code, status: problem.status, module: problem.module))
            section("Common causes", CodeDetail.commonCauses(problem.code))

            let steps = CodeDetail.checkSteps(problem.code, make: reader.make)
            if !steps.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("How to check it").font(.system(size: 13, weight: .bold)).foregroundStyle(MacColor.ink)
                    ForEach(Array(steps.enumerated()), id: \.offset) { i, s in
                        HStack(alignment: .top, spacing: 10) {
                            StepDot(number: i + 1, fill: MacTint.vehicle.opacity(0.15), text: Color(light: "#1F6FD1", dark: "#7DB3F2"))
                            Text(s).font(.system(size: 13)).foregroundStyle(MacColor.ink)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
            }

            if let f = problem.factory {
                section("About this code", "This is the \(f) factory meaning of this code. It can differ a little by model and year, so double-check before buying parts.")
            }

            FlowLayout {
                Button("Search for repair info") { search() }.buttonStyle(PillStyle())
                Button("Repair videos") { search(videos: true) }.buttonStyle(PillStyle())
            }
        }
    }

    @ViewBuilder private func section(_ heading: String, _ text: String) -> some View {
        if !text.isEmpty {
            VStack(alignment: .leading, spacing: 2) {
                Text(heading).font(.system(size: 13, weight: .bold)).foregroundStyle(MacColor.ink)
                Text(text).font(.system(size: 13)).foregroundStyle(MacColor.ink)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private func search(videos: Bool = false) {
        let base = String(problem.code.split(separator: "-").first ?? Substring(problem.code))
        let car = reader.chosenName.isEmpty ? "" : " " + reader.chosenName
        var comps = URLComponents(string: videos ? "https://www.youtube.com/results" : "https://www.google.com/search")!
        comps.queryItems = [URLQueryItem(name: videos ? "search_query" : "q",
                                         value: "\(base)\(car) \(videos ? "fix" : "code")")]
        if let u = comps.url { openURL(u) }
    }
}

extension View {
    /// A List row with no separator or background, so the page looks like the Mac app's white paper.
    func macRow(top: CGFloat = 5, bottom: CGFloat = 5) -> some View {
        listRowInsets(EdgeInsets(top: top, leading: 16, bottom: bottom, trailing: 16))
            .listRowSeparator(.hidden)
            .listRowBackground(Color.clear)
    }
}

struct ProblemsTab: View {
    @EnvironmentObject var reader: Reader
    @Binding var selection: Tab
    @State private var confirmClear = false

    /// Worst first, like the Mac app.
    private var sorted: [Problem] {
        reader.problems.enumerated().sorted {
            let a = UrgencyLevel($0.element.urgency).order, b = UrgencyLevel($1.element.urgency).order
            return a != b ? a < b : $0.offset < $1.offset
        }.map(\.element)
    }
    private var active: [Problem] { reader.problems.filter { $0.urgency != "past" } }

    /// An ABS and airbag scan where neither module answered: nothing was actually checked.
    private var safetyUnreached: Bool { reader.scanned && reader.scanKind == .safety && reader.moduleNames.isEmpty }

    private var lamp: Lamp.Mode {
        if reader.busy { return .busy }
        if !reader.connected || !reader.scanned || safetyUnreached { return .off }
        if reader.problems.isEmpty { return .ok }
        if active.contains(where: { $0.urgency == "high" }) { return .bad }
        return active.isEmpty ? .ok : .warn
    }

    private var headline: String {
        if !reader.connected { return "Let's check your vehicle" }
        if !reader.scanned { return "Ready to scan" }
        if safetyUnreached { return "ABS and airbag modules didn't answer" }
        let prefix = reader.scanKind == .engine ? "Engine codes: " : reader.scanKind == .safety ? "ABS and airbag: " : ""
        if reader.problems.isEmpty { return prefix.isEmpty ? "No problems found" : prefix + "no problems found" }
        let n = active.count
        let head = n > 0 ? "\(n) problem\(n == 1 ? "" : "s") found" : "No active problems"
        return prefix + (prefix.isEmpty ? head : head.lowercased())
    }

    private var subline: String {
        if !reader.connected {
            return "Plug the adapter into the port under the dashboard, near the steering column. Turn the key to ON. The engine can be off or running."
        }
        if !reader.scanned {
            return "Scanning checks the engine and transmission, plus ABS, airbag and other modules the vehicle lets us reach."
        }
        var out = ""
        if safetyUnreached {
            out += reader.canScanModules
                ? "This vehicle didn't let us reach its ABS or airbag module. Try a deep scan below, or pick the vehicle on the Home page so the app knows where to look. "
                : "This vehicle's protocol only lets us read engine and transmission codes. "
        } else if reader.scanKind != .safety, let on = reader.milOn { out += on ? "The check-engine light is on. " : "The check-engine light is off. " }
        let past = reader.problems.count - active.count
        if past > 0 { out += "\(past) past problem\(past == 1 ? "" : "s") also listed. " }
        if !reader.problems.isEmpty { out += "Tap a problem for what it means and what usually fixes it. " }
        return out.trimmingCharacters(in: .whitespaces)
    }

    private var scanTitle: String {
        switch reader.scanKind {
        case .engine: return "Scan engine again"
        case .safety: return "Scan ABS and airbag again"
        case .all:    return "Scan for problems"
        }
    }

    var body: some View {
        MacPage {
            List {
                hero.macRow(top: 16, bottom: 8)

                if !reader.connected {
                    connectPanel.macRow()
                } else {
                    ForEach(sorted) { p in
                        ProblemCard(problem: p)
                            .macRow()
                            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                Button(role: .destructive) { reader.removeProblem(p) } label: {
                                    Label("Clear code", systemImage: "bolt.slash")
                                }
                                .tint(MacColor.red)
                            }
                    }
                    if !reader.problems.isEmpty {
                        Text("Swipe a code left to clear it from this list. Note: a car can only erase all codes at once (the Clear codes button) — one-at-a-time erasing isn't something the OBD port supports.")
                            .font(.system(size: 12)).foregroundStyle(MacColor.muted)
                            .macRow()
                    }
                    if reader.scanned && reader.scanKind != .engine { modulesNote.macRow() }
                }
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .alert("Clear all codes and turn off the warning lights?", isPresented: $confirmClear) {
                Button("Clear codes", role: .destructive) { reader.clearCodes() }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("Turn the engine OFF and leave the key ON first.\n\nThis also resets the smog-check self-tests. The vehicle will fail an emissions test until it's driven for a few days.\n\nIf a problem isn't fixed, its code and light will come back.")
            }
        }
    }

    private var hero: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 14) {
                Lamp(mode: lamp)
                VStack(alignment: .leading, spacing: 3) {
                    Text(headline).font(.system(size: 24, weight: .bold)).foregroundStyle(MacColor.ink)
                        .fixedSize(horizontal: false, vertical: true)
                    Text(subline).font(.system(size: 14)).foregroundStyle(MacColor.muted)
                        .fixedSize(horizontal: false, vertical: true)
                    if reader.scanned, let when = reader.lastScanAt {
                        Text("Last scanned \(when.formatted(date: .omitted, time: .standard))")
                            .font(.system(size: 12)).foregroundStyle(MacColor.muted).padding(.top, 1)
                    }
                }
            }

            FlowLayout {
                if !reader.connected {
                    Button("Connect") { reader.connect() }
                        .buttonStyle(PillStyle(kind: .primary, big: true)).disabled(reader.busy)
                } else {
                    Button(scanTitle) { reader.scan() }
                        .buttonStyle(PillStyle(kind: .primary, big: true)).disabled(reader.busy)
                    if reader.scanned && !reader.problems.isEmpty {
                        Button("Clear codes") { confirmClear = true }
                            .buttonStyle(PillStyle(kind: .danger, big: true)).disabled(reader.busy)
                    }
                    if reader.busy {
                        Button("Stop") { reader.stopScan() }.buttonStyle(PillStyle(big: true))
                    }
                }
            }

            if reader.busy {
                BusyLine()
            } else if reader.status != "Not connected" {
                Text(reader.status).font(.system(size: 12)).foregroundStyle(MacColor.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    /// Which modules answered, and the deep scan for when one is missing (the Mac app's _modules_note).
    private var modulesNote: some View {
        VStack(alignment: .leading, spacing: 4) {
            Group {
                if !reader.moduleNames.isEmpty {
                    Text("Modules that answered: " + reader.moduleNames.joined(separator: ", ") + ".")
                } else if reader.canScanModules {
                    Text("Only the engine computer answered. Some vehicles hide other modules.")
                } else {
                    Text("This vehicle's protocol only lets us read engine and transmission codes (\(reader.protocolName)).")
                }
            }
            .font(.system(size: 12)).foregroundStyle(MacColor.muted)
            .fixedSize(horizontal: false, vertical: true)
            if reader.canScanModules {
                Text("Missing a module, like ABS or airbag? A deep scan checks every address and takes 1 to 3 minutes.")
                    .font(.system(size: 12)).foregroundStyle(MacColor.muted)
                    .fixedSize(horizontal: false, vertical: true)
                LinkLabel("Run a deep scan") { reader.scan(deep: true) }.disabled(reader.busy)
            }
        }
    }

    private var connectPanel: some View {
        VStack(alignment: .leading, spacing: 14) {
            RoundCard(padX: 20, padY: 16) {
                Text("No adapter yet?").font(.system(size: 15, weight: .bold)).foregroundStyle(MacColor.ink)
                Text("Try everything with a pretend vehicle:").font(.system(size: 13)).foregroundStyle(MacColor.muted)
                    .padding(.top, 4).padding(.bottom, 6)
                LinkLabel("See a demo (sample data)") { reader.loadDemo() }
            }
            Text(reader.useBluetooth ? "Using Bluetooth." : "Using Wi-Fi \(reader.host):\(reader.port).")
                .font(.system(size: 12)).foregroundStyle(MacColor.muted)
            LinkLabel("Connection options") { selection = .settings }
        }
    }
}

// MARK: - Live data

struct LiveTab: View {
    @EnvironmentObject var reader: Reader

    var body: some View {
        MacPage {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    PageTitle(title: "Live data",
                              subtitle: "What the engine computer sees right now. Values update about once a second.",
                              icon: "icon-gauge")
                    if reader.connected {
                        if !reader.live.isEmpty {
                            Button(reader.liveRunning ? "Stop" : "Start live data") { reader.toggleLive() }
                                .buttonStyle(PillStyle(kind: .primary))
                        }
                        vehicleCard
                        if reader.live.isEmpty {
                            EmptyStateCard(icon: "icon-gauge", title: "Ready when you are",
                                           message: "Tap Start live data to watch speed, RPM, temperatures and more, updated every second.",
                                           buttonTitle: "Start live data") { reader.toggleLive() }
                        } else {
                            TileGrid(items: reader.live.map(\.name)) { name in
                                if let r = reader.live.first(where: { $0.name == name }) { readingTile(r) }
                            }
                        }
                    } else {
                        EmptyStateCard(icon: "icon-gauge", title: "Not connected yet",
                                       message: "Plug the adapter in, turn the key to ON, then connect to see live readings.")
                    }
                }
                .padding(16)
            }
        }
    }

    private var vehicleCard: some View {
        RoundCard(padY: 8) {
            let rows: [(String, String)] = (reader.chosenName.isEmpty ? [] : [("Make / model / year", reader.chosenName)])
                + [("VIN", reader.vin), ("Battery", reader.battery), ("Protocol", reader.protocolName)]
            ForEach(Array(rows.enumerated()), id: \.offset) { i, row in
                if i > 0 { Rectangle().fill(MacColor.line).frame(height: 1) }
                HStack(alignment: .top) {
                    Text(row.0).font(.system(size: 13)).foregroundStyle(MacColor.muted)
                    Spacer(minLength: 12)
                    Text(row.1.isEmpty ? "—" : row.1).font(.system(size: 13, weight: .bold))
                        .foregroundStyle(MacColor.ink).multilineTextAlignment(.trailing)
                }
                .padding(.vertical, 8)
            }
        }
    }

    /// Big value, the other units under it in grey, then the name (the Mac app's live tile).
    private func readingTile(_ r: LiveReading) -> some View {
        let parts = r.value.split(separator: "(", maxSplits: 1).map { $0.trimmingCharacters(in: .whitespaces) }
        let alt = parts.count > 1 ? parts[1].replacingOccurrences(of: ")", with: "") : ""
        return VStack(alignment: .leading, spacing: 1) {
            Text(parts.first ?? r.value).font(.system(size: 24, weight: .bold)).foregroundStyle(MacColor.ink)
                .lineLimit(1).minimumScaleFactor(0.6)
            if !alt.isEmpty { Text(alt).font(.system(size: 12)).foregroundStyle(MacColor.muted) }
            Text(r.name).font(.system(size: 13)).foregroundStyle(MacColor.ink)
                .fixedSize(horizontal: false, vertical: true).padding(.top, 1)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .padding(.horizontal, 16).padding(.vertical, 14)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(MacColor.panel))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(MacColor.line, lineWidth: 1))
    }
}

// MARK: - Smog

struct SmogTab: View {
    @EnvironmentObject var reader: Reader

    /// How to get each self-test to run (the Mac app's DRIVE_CYCLES).
    private static let driveCycles: [String: String] = [
        "Catalyst": "once fully warmed up, drive at a steady 40-55 mph for about 5 minutes.",
        "Heated catalyst": "once fully warmed up, drive at a steady 40-55 mph for about 5 minutes.",
        "Oxygen sensor": "after warming up, drive at a steady 30-45 mph for 2-3 minutes, then idle for 30 seconds.",
        "Oxygen sensor heater": "let the vehicle sit off for at least 8 hours, then start it and idle for 2 minutes.",
        "Evaporative system (EVAP)": "keep the tank between 1/4 and 3/4 full, park overnight, then start it cold and drive normally. This one can take several days.",
        "EGR system": "after warming up, make a few gentle slow-downs from 50 mph to 20 mph without braking hard.",
        "Secondary air system": "start the engine cold (after sitting overnight) and let it idle for 2 minutes.",
        "Misfire": "runs all the time while driving.",
        "Fuel system": "runs all the time while driving.",
        "Comprehensive components": "runs all the time while driving.",
    ]

    private var verdictColor: Color {
        if reader.smogOK { return MacColor.green }
        return reader.smogText.contains("check-engine") ? MacColor.red : MacColor.amberInk
    }

    var body: some View {
        MacPage {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    PageTitle(title: "Smog check",
                              subtitle: "Before an emissions inspection, the vehicle has to finish its own self-tests. Here's where they stand.",
                              icon: "icon-smog")
                    if reader.connected {
                        Button("Check again") { reader.checkSmog() }
                            .buttonStyle(PillStyle()).disabled(reader.busy)
                    }
                    if !reader.connected {
                        EmptyStateCard(icon: "icon-smog", title: "Not connected yet",
                                       message: "Connect and scan to see whether the vehicle is ready for inspection.")
                    } else if reader.monitors.isEmpty {
                        EmptyStateCard(icon: "icon-smog", title: "Not checked yet",
                                       message: "Tap Check again to read the vehicle's self-tests.", buttonTitle: nil)
                    } else {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(reader.smogText).font(.system(size: 20, weight: .bold)).foregroundStyle(verdictColor)
                                .fixedSize(horizontal: false, vertical: true)
                            Text(reader.smogDetail).font(.system(size: 13)).foregroundStyle(MacColor.ink)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        monitorCard
                    }
                }
                .padding(16)
            }
        }
    }

    private var monitorCard: some View {
        RoundCard(padX: 16, padY: 6) {
            ForEach(Array(reader.monitors.enumerated()), id: \.offset) { i, m in
                if i > 0 { Rectangle().fill(MacColor.line).frame(height: 1) }
                monitorRow(m).padding(.vertical, 9)
            }
        }
    }

    private func monitorRow(_ m: Monitor) -> some View {
        let name = ["Comprehensive components": "General sensors and parts", "Misfire": "Misfire detection"][m.name] ?? m.name
        return VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(name).font(.system(size: 14)).foregroundStyle(m.supported ? MacColor.ink : MacColor.muted)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 8)
                if !m.supported {
                    StatusPill(words: "Not on this vehicle", fill: MacColor.offSoft, text: MacColor.muted)
                } else if m.incomplete {
                    StatusPill(words: "Still running", fill: MacColor.amberSoft, text: MacColor.amberInk)
                } else {
                    StatusPill(words: "Done", fill: MacColor.greenSoft, text: MacColor.green)
                }
            }
            if m.supported && m.incomplete, let tip = Self.driveCycles[m.name] {
                Text("How to finish it: " + tip).font(.system(size: 12)).foregroundStyle(MacColor.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
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
    @Environment(\.openURL) private var openURL
    @State private var checking = false
    @State private var updateMessage = ""
    @State private var available: UpdateCheck.Release? = nil
    @AppStorage("appearance") private var appearance: Appearance = .automatic

    private func checkForUpdates() {
        checking = true
        updateMessage = ""
        available = nil
        Task {
            do {
                let latest = try await UpdateCheck.latest()
                if UpdateCheck.isNewer(latest.version, than: AppInfo.version) {
                    available = latest
                } else {
                    updateMessage = "You have the latest version."
                }
            } catch {
                updateMessage = "Couldn't check for updates. An adapter's Wi-Fi network has no internet, so try again on a network that does."
            }
            checking = false
        }
    }

    private var updatesCard: some View {
        RoundCard(padX: 20, padY: 16) {
            VStack(alignment: .leading, spacing: 10) {
                Text("Version \(AppInfo.version)").font(.system(size: 15, weight: .bold)).foregroundStyle(MacColor.ink)
                if checking {
                    HStack(spacing: 8) {
                        ProgressView()
                        note("Checking…")
                    }
                } else {
                    Button("Check for updates") { checkForUpdates() }.buttonStyle(PillStyle())
                }
                if !updateMessage.isEmpty { note(updateMessage) }
                if let available {
                    Text("Version \(available.version) is available.").font(.system(size: 14, weight: .bold))
                        .foregroundStyle(MacColor.ink)
                    if let notes = available.notes, !notes.isEmpty { note(notes) }
                    if let link = available.url, let url = URL(string: link) {
                        Button("Get update") { openURL(url) }.buttonStyle(PillStyle(kind: .primary))
                    } else {
                        note("To install it, get the newest code and run the app on your iPhone from Xcode again.")
                    }
                }
            }
        }
    }

    private func heading(_ text: String) -> some View {
        Text(text).font(.system(size: 15, weight: .bold)).foregroundStyle(MacColor.ink)
    }
    private func note(_ text: String) -> some View {
        Text(text).font(.system(size: 12)).foregroundStyle(MacColor.muted)
            .fixedSize(horizontal: false, vertical: true)
    }
    private func field(_ label: String, _ placeholder: String, _ text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label).font(.system(size: 13, weight: .bold)).foregroundStyle(MacColor.ink)
            TextField(placeholder, text: text)
                .font(.system(size: 14)).autocorrectionDisabled().textInputAutocapitalization(.never)
                .padding(.horizontal, 12).padding(.vertical, 9)
                .overlay(RoundedRectangle(cornerRadius: 10, style: .continuous).stroke(MacColor.line, lineWidth: 1))
        }
    }

    var body: some View {
        MacPage {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    PageTitle(title: "Settings", subtitle: "How the app looks and reaches your adapter.")

                    RoundCard(padX: 20, padY: 16) {
                        VStack(alignment: .leading, spacing: 10) {
                            heading("Appearance")
                            Picker("Appearance", selection: $appearance) {
                                ForEach(Appearance.allCases) { Text($0.title).tag($0) }
                            }
                            .pickerStyle(.segmented)
                            note("Automatic follows your iPhone's light or dark setting.")
                        }
                    }

                    RoundCard(padX: 20, padY: 16) {
                        VStack(alignment: .leading, spacing: 10) {
                            heading("How the adapter connects")
                            Toggle("Use Bluetooth adapter", isOn: $reader.useBluetooth)
                                .font(.system(size: 14)).tint(MacColor.green)
                            if !reader.useBluetooth {
                                field("Wi-Fi address", "192.168.0.10", $reader.host)
                                field("Port", "35000", $reader.port).keyboardType(.numberPad)
                            }
                            note("Wi-Fi adapters make their own Wi-Fi network — join it in the iPhone's Settings first. The OBDLink MX+ (classic Bluetooth) isn't supported here; use a Wi-Fi or BLE adapter.")
                        }
                    }

                    RoundCard(padX: 20, padY: 16) {
                        VStack(alignment: .leading, spacing: 10) {
                            heading("Demo")
                            if reader.isDemo {
                                Button("Exit demo") { reader.exitDemo() }.buttonStyle(PillStyle(kind: .danger))
                            } else {
                                Button("Load demo data") { reader.loadDemo() }.buttonStyle(PillStyle(kind: .primary))
                            }
                            note("Fills the app with sample data so you can look around without a car. It's never saved — closing and reopening the app clears it.")
                        }
                    }

                    updatesCard
                }
                .padding(16)
            }
            .scrollDismissesKeyboard(.interactively)
        }
    }
}
