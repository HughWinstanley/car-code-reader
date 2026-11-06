import SwiftUI

/// Searches the app's own code list and repair guides, and builds web searches for what they don't cover.
enum RepairSearch {
    private static let ignored: Set<String> = ["how", "to", "fix", "repair", "my", "a", "an", "the", "i", "do", "does", "is", "of", "for", "on", "in", "and", "it", "what", "can"]
    /// Everyday words -> the ones the code list uses.
    private static let sameAs = [("catalytic converter", "catalyst"), ("oxygen", "o2"), ("gas cap", "evap"),
                                 ("spark plugs", "misfire"), ("spark plug", "misfire")]
    static let maxCodes = 25

    /// "How do I fix my brakes" -> ["brake"]
    static func words(_ query: String) -> [String] {
        sameAs.reduce(query.lowercased()) { $0.replacingOccurrences(of: $1.0, with: $1.1) }
            .split { !$0.isLetter && !$0.isNumber }.map(String.init)
            .filter { !ignored.contains($0) }
            .map { $0.count > 3 && $0.hasSuffix("s") ? String($0.dropLast()) : $0 }
    }

    private static func matches(_ text: String, _ words: [String]) -> Bool {
        // From the start of a word, so "oil" doesn't find "coil".
        let inText = text.lowercased().split { !$0.isLetter && !$0.isNumber }
        return !words.isEmpty && words.allSatisfy { w in inText.contains { $0.hasPrefix(w) } }
    }

    static func guides(_ query: String) -> [ServiceGuide] {
        let w = words(query)
        return ProData.guides.filter { g in
            matches(g.title + " " + g.applies, w)   // not the steps: they mention too much in passing
        }
    }

    /// Codes whose meaning mentions every word, standard codes plus the factory ones for this vehicle's make.
    static func codes(_ query: String, make: Make) -> [(code: String, meaning: String)] {
        let w = words(query)
        var table = CodeData.generic
        if make == .ford { table.merge(CodeData.ford) { _, factory in factory } }
        if make == .gm { table.merge(CodeData.gm) { _, factory in factory } }
        return table.filter { matches($0.value, w) }.map { (code: $0.key, meaning: $0.value) }.sorted { $0.code < $1.code }
    }

    /// What to ask the web: "brakes" -> "how to fix brakes", and a full question stays as it was typed.
    static func howTo(_ query: String) -> String {
        let lower = query.lowercased()
        return lower.contains("how") || lower.contains("fix") ? query : "how to fix \(query)"
    }

    /// Tidies what someone typed: "po300" -> "P0300". Nil if it isn't shaped like a code.
    static func cleanCode(_ text: String) -> String? {
        var code = (text.split(separator: "-").first.map(String.init) ?? "").uppercased().filter { $0.isLetter || $0.isNumber }
        if code.count == 5, let first = code.first {   // people often type the letter O for zero
            code = String(first) + code.dropFirst().replacingOccurrences(of: "O", with: "0").replacingOccurrences(of: "I", with: "1")
        }
        return code.range(of: "^[PCBU][0-9A-F]{4}$", options: .regularExpression) == nil ? nil : code
    }

    enum Web { case google, youtube, diagrams }

    static func url(_ kind: Web, _ query: String) -> URL? {
        var parts: URLComponents?
        switch kind {
        case .google:
            parts = URLComponents(string: "https://www.google.com/search")
            parts?.queryItems = [URLQueryItem(name: "q", value: query)]
        case .youtube:
            parts = URLComponents(string: "https://www.youtube.com/results")
            parts?.queryItems = [URLQueryItem(name: "search_query", value: query)]
        case .diagrams:
            parts = URLComponents(string: "https://www.google.com/search")
            parts?.queryItems = [URLQueryItem(name: "tbm", value: "isch"), URLQueryItem(name: "q", value: query)]
        }
        return parts?.url
    }
}

/// Three buttons that open the web. `base` is what to search for; the chosen vehicle is added to it.
private struct WebLinks: View {
    @EnvironmentObject var reader: Reader
    @Environment(\.openURL) private var openURL
    let base: String
    let topic: String

    private func open(_ kind: RepairSearch.Web, _ extra: String) {
        let text = ([base, reader.chosenName, extra]).filter { !$0.isEmpty }.joined(separator: " ")
        if let url = RepairSearch.url(kind, text) { openURL(url) }
    }

    var body: some View {
        RoundCard(radius: 16) {
            VStack(alignment: .leading, spacing: 10) {
                proText("On the web", size: 15, bold: true)
                proText("Opens your browser to search for \(topic)\(reader.chosenName.isEmpty ? "" : " on a \(reader.chosenName)").", muted: true)
                FlowLayout {
                    Button("Search for repair info") { open(.google, "") }.buttonStyle(PillStyle(kind: .primary))
                    Button("Repair videos") { open(.youtube, "") }.buttonStyle(PillStyle())
                    Button("Diagrams") { open(.diagrams, "diagram") }.buttonStyle(PillStyle())
                }
            }
        }
    }
}

// MARK: - The two search bars

struct SearchBars: View {
    @EnvironmentObject var reader: Reader
    /// One tap away. Each of these finds a guide in the app as well as the web links (same list as the Mac app).
    private let repairs: [(title: String, query: String, symbol: String, tint: Color)] = [
        ("Brake pads", "how to replace brake pads", "exclamationmark.brakesignal", MacTint.safety),
        ("Battery", "how to replace a car battery", "minus.plus.batteryblock.fill", MacTint.smog),
        ("Spark plugs", "how to replace spark plugs", "bolt.fill", MacTint.engine),
        ("Air filter", "how to replace the engine air filter", "wind", MacTint.vehicle),
        ("Overheating", "how to fix an overheating engine", "thermometer.high", MacTint.semi),
        ("Jump start", "how to jump-start a dead battery", "bolt.car.fill", MacTint.scan),
    ]
    private let commonCodes = ["P0300", "P0420", "P0171", "P0442", "P0128", "P0455"]
    @State private var fixText = ""
    @State private var codeText = ""
    @State private var fixQuery = ""
    @State private var codeQuery = ""
    @State private var showFix = false
    @State private var showCode = false
    @State private var codeHint = false
    @State private var guided: String? = nil

    private func searchFix() {
        let text = fixText.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }
        if let code = RepairSearch.cleanCode(text) {   // a code in the top bar still goes to the code page
            codeQuery = code
            showCode = true
        } else {
            fixQuery = text
            showFix = true
        }
    }

    private func searchCode() {
        guard !codeText.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        if let code = RepairSearch.cleanCode(codeText) {
            codeText = code
            codeHint = false
            codeQuery = code
            showCode = true
        } else {
            codeHint = true
        }
    }

    private func bar(_ prompt: String, _ text: Binding<String>, action: @escaping () -> Void) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass").foregroundStyle(MacColor.muted).accessibilityHidden(true)
            TextField(prompt, text: text)
                .scaledFont(15).autocorrectionDisabled().submitLabel(.search).onSubmit(action)
            if !text.wrappedValue.isEmpty {
                Button(action: { text.wrappedValue = "" }) {
                    Image(systemName: "xmark.circle.fill").foregroundStyle(MacColor.muted)
                }
                .buttonStyle(.plain).accessibilityLabel("Clear")
            }
        }
        .padding(.horizontal, 14).padding(.vertical, 11)
        .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(MacColor.panel))
        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(MacColor.line, lineWidth: 1))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
        VStack(alignment: .leading, spacing: 8) {
            bar("Search how to fix something", $fixText, action: searchFix)
            bar("Type a code, like P0301", $codeText, action: searchCode)
                .textInputAutocapitalization(.characters)
            if codeHint {
                proText("That isn't a code. A code is a letter and 4 numbers or letters, like P0301. To search by words, use the top bar.", muted: true, size: 12)
            }
        }
        Text("Popular repairs").scaledFont(16, weight: .bold).foregroundStyle(MacColor.ink).padding(.top, 8)
        TileGrid(items: repairs.map(\.title)) { title in
            let r = repairs.first { $0.title == title }!
            Button { fixQuery = r.query; showFix = true } label: {
                SymbolTile(title: r.title, subtitle: "", symbol: r.symbol, tint: r.tint)
            }
            .buttonStyle(.plain)
        }
        Text("Common codes").scaledFont(16, weight: .bold).foregroundStyle(MacColor.ink).padding(.top, 8)
        ForEach(commonCodes, id: \.self) { code in
            Button { codeQuery = code; showCode = true } label: {
                RoundCard(radius: 14, padY: 11) {
                    HStack(spacing: 12) {
                        proText(code, size: 14, bold: true).frame(minWidth: 52, alignment: .leading)
                        proText(DTC.describe(code, make: reader.make).0, muted: true)
                            .multilineTextAlignment(.leading)
                        Spacer(minLength: 4)
                        Image(systemName: "chevron.right").foregroundStyle(MacColor.muted).accessibilityHidden(true)
                    }
                }
            }
            .buttonStyle(.plain)
        }
        Text("Step-by-step help").scaledFont(16, weight: .bold).foregroundStyle(MacColor.ink).padding(.top, 8)
        ForEach(GuidedHelp.topics, id: \.key) { t in
            Button { guided = t.key } label: {
                RoundCard(radius: 14, padY: 12) {
                    HStack {
                        proText(t.title, size: 14, bold: true)
                        Spacer(minLength: 8)
                        Image(systemName: "chevron.right").foregroundStyle(MacColor.muted).accessibilityHidden(true)
                    }
                }
            }
            .buttonStyle(.plain)
        }
        }
        .sheet(isPresented: Binding(get: { guided != nil }, set: { if !$0 { guided = nil } })) {
            if let t = GuidedHelp.topics.first(where: { $0.key == guided }) { GuidedView(topic: t) }
        }
        .navigationDestination(isPresented: $showFix) { FixResultsView(query: fixQuery) }
        .navigationDestination(isPresented: $showCode) { CodeResultView(code: codeQuery) }
    }
}

// MARK: - Results

struct CodeResultView: View {
    @EnvironmentObject var reader: Reader
    let code: String

    var body: some View {
        let (meaning, factory) = DTC.describe(code, make: reader.make)
        let causes = CodeDetail.commonCauses(code)
        let steps = CodeDetail.checkSteps(code, make: reader.make)
        return ProPage(title: code, subtitle: meaning) {
            if let factory { proText("\(factory) factory meaning. It can differ a little by model and year.", muted: true, size: 12) }
            GuidedButton(code: code)
            if code.hasPrefix("P") {
                RoundCard(radius: 16) {
                    VStack(alignment: .leading, spacing: 4) {
                        proText("Why it matters", size: 15, bold: true)
                        proText(CodeDetail.whyItMatters(code, status: "Stored", module: "Engine"))
                    }
                }
            }
            if !causes.isEmpty {
                RoundCard(radius: 16) {
                    VStack(alignment: .leading, spacing: 4) {
                        proText("Common causes", size: 15, bold: true)
                        proText(causes)
                    }
                }
            }
            if !steps.isEmpty {
                RoundCard(radius: 16) {
                    VStack(alignment: .leading, spacing: 8) {
                        proText("How to check it", size: 15, bold: true)
                        ForEach(Array(steps.enumerated()), id: \.offset) { i, step in
                            HStack(alignment: .top, spacing: 10) {
                                StepDot(number: i + 1, fill: MacTint.vehicle.opacity(0.15), text: Color(light: "#1F6FD1", dark: "#7DB3F2"))
                                proText(step)
                            }
                        }
                    }
                }
            }
            WebLinks(base: code, topic: code)
            proText("This is general guidance. Confirm with a test before buying parts.", muted: true, size: 12)
        }
    }
}

struct FixResultsView: View {
    @EnvironmentObject var reader: Reader
    let query: String
    @State private var openGuide: String? = nil

    var body: some View {
        let guides = RepairSearch.guides(query)
        let codes = RepairSearch.codes(query, make: reader.make)
        return ProPage(title: "Results for \"\(query)\"", subtitle: "From the app's own guides and code list, plus the web.") {
            WebLinks(base: RepairSearch.howTo(query), topic: query)
            if !guides.isEmpty {
                proText("Repair guides", size: 16, bold: true)
                ForEach(guides, id: \.title) { g in
                    RoundCard(radius: 16) {
                        VStack(alignment: .leading, spacing: 6) {
                            proText(g.title, size: 15, bold: true)
                            proText(g.applies, muted: true, size: 12)
                            if openGuide == g.title {
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
                        .onTapGesture { withAnimation(.easeInOut(duration: 0.2)) { openGuide = openGuide == g.title ? nil : g.title } }
                        .accessibilityElement(children: .combine)
                        .accessibilityAddTraits(.isButton)
                    }
                }
            }
            if !codes.isEmpty {
                proText("Codes that mention this", size: 16, bold: true)
                ForEach(codes.prefix(RepairSearch.maxCodes), id: \.code) { item in
                    NavigationLink { CodeResultView(code: item.code) } label: {
                        RoundCard(radius: 14, padY: 11) {
                            HStack(alignment: .top, spacing: 10) {
                                proText(item.code, size: 14, bold: true)
                                proText(item.meaning)
                                Spacer(minLength: 4)
                                Image(systemName: "chevron.right").foregroundStyle(MacColor.muted).accessibilityHidden(true)
                            }
                        }
                        .accessibilityElement(children: .combine)
                    }
                    .buttonStyle(.plain)
                }
                if codes.count > RepairSearch.maxCodes {
                    proText("Showing the first \(RepairSearch.maxCodes) of \(codes.count). Add a word to narrow it down.", muted: true, size: 12)
                }
            }
            if guides.isEmpty && codes.isEmpty {
                proText("Nothing in the app's own guides or code list matches this. Try the web buttons above, or a simpler word.", muted: true)
            }
        }
    }
}

// MARK: - Normal ranges and step-by-step help (data generated from the Mac app's service_guides.py)

enum NormalRanges {
    static let note = "Normal ranges are typical values and vary by vehicle. Check the service manual to be sure."
    private static let table: [(String, String?, Double?, Double?)] = [
        ("absolute", nil, nil, nil),
        ("relative", nil, nil, nil),
        ("commanded", nil, nil, nil),
        ("fuel trim", "Normal: -10 to +10 %", -10, 10),
        ("coolant", "Warmed up: 180 to 220 °F", nil, 235),
        ("oil temp", "Warmed up: 190 to 250 °F", nil, 270),
        ("transmission", "Warmed up: 150 to 200 °F", nil, 240),
        ("intake air", "Usually near the outside temperature", nil, nil),
        ("rpm", "Idle: about 600 to 1,000 rpm", nil, nil),
        ("engine speed", "Idle: about 600 to 1,000 rpm", nil, nil),
        ("engine load", "Idle: about 15 to 35 %", nil, nil),
        ("throttle position", "Idle: usually under 20 %", nil, nil),
        ("mass air", "Idle: about 2 to 7 g/s, more on big engines", nil, nil),
        ("intake manifold", "Idle: about 20 to 40 kPa", nil, nil),
        ("barometric", "About 100 kPa near sea level", nil, nil),
        ("o2 sensor", "Front sensor swings about 0.1 to 0.9 V", nil, nil),
        ("voltage", "Engine running: 13.5 to 14.8 V", nil, 15.5),
        ("ignition timing", "Idle: usually 5 to 20°", nil, nil)
    ]
    static func range(_ name: String) -> (text: String, below: Double?, above: Double?)? {
        let low = name.lowercased()
        guard let hit = table.first(where: { low.contains($0.0) }), let text = hit.1 else { return nil }
        return (text, hit.2, hit.3)
    }
    static func outside(_ name: String, _ value: Double) -> Bool {
        guard let r = range(name) else { return false }
        return (r.below.map { value < $0 } ?? false) || (r.above.map { value > $0 } ?? false)
    }
}

struct GuidedNode { let text: String; let options: [(String, String)] }
struct GuidedTopic { let key: String; let title: String; let codes: [String]; let start: String; let nodes: [String: GuidedNode] }

enum GuidedHelp {
    static func topic(forCode code: String) -> GuidedTopic? {
        let base = code.split(separator: "-").first.map { String($0).uppercased() } ?? ""
        return topics.first { $0.codes.contains(base) }
    }
    static let topics: [GuidedTopic] = [
        GuidedTopic(key: "misfire", title: "Find a misfire", codes: ["P0300", "P0301", "P0302", "P0303", "P0304", "P0305", "P0306", "P0307", "P0308", "P0309", "P0310", "P0311", "P0312"], start: "flash", nodes: [
            "flash": GuidedNode(text: "Is the check-engine light flashing, or is the engine shaking badly?", options: [("Yes", "severe"), ("No", "which")]),
            "severe": GuidedNode(text: "A flashing light means unburned fuel can overheat and ruin the catalytic converter. Drive gently and as little as possible until this is fixed.", options: [("Okay, keep going", "which")]),
            "which": GuidedNode(text: "What does the code say? P0301 to P0312 name one cylinder. P0300 means random or several.", options: [("One cylinder", "coil"), ("P0300, random or several", "multi")]),
            "coil": GuidedNode(text: "With the engine off and cool, swap that cylinder's ignition coil with a neighbor's. Clear the codes and drive. Did the misfire move to the other cylinder?", options: [("Yes, it moved", "badcoil"), ("No, it stayed", "plug"), ("This engine has no separate coils", "plug")]),
            "badcoil": GuidedNode(text: "The coil you moved is bad. Replace it, then clear the codes and drive to confirm.", options: []),
            "plug": GuidedNode(text: "Pull that cylinder's spark plug. Is it worn, cracked, oily or wet?", options: [("Worn or cracked", "newplug"), ("Oily or wet", "wetplug"), ("It looks fine", "swapplug")]),
            "newplug": GuidedNode(text: "Replace the spark plugs. If one is worn, the others usually are too.", options: []),
            "wetplug": GuidedNode(text: "Something is getting into that cylinder. Oil can mean a leaking valve cover or tube seal. Coolant can mean a head gasket problem, so have that checked before driving much.", options: []),
            "swapplug": GuidedNode(text: "Swap that spark plug with a neighbor's, clear the codes and drive. Did the misfire move?", options: [("Yes, it moved", "newplug"), ("No, it stayed", "deeper")]),
            "deeper": GuidedNode(text: "The coil and plug are fine, so the fuel injector and compression are next. A shop can test both quickly. Compare before buying parts.", options: []),
            "multi": GuidedNode(text: "With the engine warmed up and idling, look at long-term fuel trim in Live data. Is it above +10 %?", options: [("Yes, above +10 %", "multilean"), ("No", "multiage"), ("I can't read it", "multiage")]),
            "multilean": GuidedNode(text: "The engine is running lean, which can cause random misfires. Look for vacuum leaks first. The lean guide has the next steps.", options: []),
            "multiage": GuidedNode(text: "When were the spark plugs last changed?", options: [("Over 60,000 miles ago, or not sure", "newplug"), ("Recently", "multideep")]),
            "multideep": GuidedNode(text: "With fresh plugs and normal fuel trims, the next checks are fuel pressure, a shared coil pack if it has one, and compression. A shop can test these.", options: []),
        ]),
        GuidedTopic(key: "lean", title: "Find why it's running lean", codes: ["P0171", "P0174"], start: "trim", nodes: [
            "trim": GuidedNode(text: "Warm up the engine, park with the brake on, and watch long-term fuel trim in Live data at idle and then holding 2,500 rpm. What do you see?", options: [("High at idle, better at 2,500 rpm", "vac"), ("High at both", "fuel"), ("Normal at both", "intermittent")]),
            "vac": GuidedNode(text: "That points to a vacuum leak. With the engine off, check the hoses and the rubber intake boot after the air flow sensor for cracks or loose clamps. Find anything?", options: [("Yes", "fixvac"), ("No", "smoke")]),
            "fixvac": GuidedNode(text: "Fix the leak, clear the codes and drive. Fuel trim should come back within about 10 %.", options: []),
            "smoke": GuidedNode(text: "Small leaks are hard to see. A shop can find them quickly with a smoke test.", options: []),
            "fuel": GuidedNode(text: "Clean the mass air flow sensor with MAF cleaner only, let it dry, clear the codes and drive. Did fuel trim improve?", options: [("Yes", "fixedmaf"), ("No", "pressure")]),
            "fixedmaf": GuidedNode(text: "A dirty sensor was likely the cause. Check that the air filter is clean too.", options: []),
            "pressure": GuidedNode(text: "Next, check fuel pressure against the spec for your vehicle. A weak pump or clogged filter can do this. An exhaust leak ahead of the oxygen sensor can too.", options: []),
            "intermittent": GuidedNode(text: "It may only happen sometimes. Check the air filter and intake ducts, clear the codes, and see if it comes back.", options: []),
        ]),
        GuidedTopic(key: "evap", title: "Find an EVAP leak", codes: ["P0440", "P0442", "P0455", "P0456", "P0457"], start: "cap", nodes: [
            "cap": GuidedNode(text: "Check the gas cap first. Is it loose, or is its rubber seal cracked or worn?", options: [("Yes", "fixcap"), ("It looks fine", "again")]),
            "fixcap": GuidedNode(text: "Tighten it until it clicks, or replace it if the seal is bad. Clear the codes. It can take several drives for the car to re-check. Did the code come back?", options: [("Yes", "hoses"), ("No", "done")]),
            "done": GuidedNode(text: "That was it. No more steps needed.", options: []),
            "again": GuidedNode(text: "Tighten it anyway until it clicks, clear the codes and drive for a few days. Did the code come back?", options: [("Yes", "hoses"), ("No", "done")]),
            "hoses": GuidedNode(text: "Look at the rubber EVAP hoses you can reach, especially near the engine and the charcoal canister. Find a crack or a loose one?", options: [("Yes", "fixhose"), ("No", "smoke")]),
            "fixhose": GuidedNode(text: "Replace that hose, clear the codes and drive for a few days to confirm.", options: []),
            "smoke": GuidedNode(text: "A shop can find the leak with a smoke test. The purge and vent valves are also common causes.", options: []),
        ]),
        GuidedTopic(key: "catalyst", title: "Check the catalytic converter", codes: ["P0420", "P0430"], start: "others", nodes: [
            "others": GuidedNode(text: "Are there other codes too, like misfires, lean or rich codes, or oxygen sensor codes?", options: [("Yes", "fixfirst"), ("No", "leak")]),
            "fixfirst": GuidedNode(text: "Fix those first. They can set this code, and they can ruin a new converter. Then clear the codes and see if this one returns.", options: []),
            "leak": GuidedNode(text: "Check for an exhaust leak ahead of the rear oxygen sensor: ticking when cold, or black soot at a joint. Find one?", options: [("Yes", "fixleak"), ("No", "sensor")]),
            "fixleak": GuidedNode(text: "Fix the leak, clear the codes and drive. A leak can make the rear sensor read wrong.", options: []),
            "sensor": GuidedNode(text: "With the engine warmed up, hold 2,500 rpm in park and watch the rear oxygen sensor voltage in Live data, if your vehicle shows it. What is it doing?", options: [("Fairly steady", "ok"), ("Swinging up and down quickly", "worn"), ("I can't see it", "shop")]),
            "ok": GuidedNode(text: "The converter may be okay. Clear the code and see if it returns. If it does, have the sensor and converter tested.", options: []),
            "worn": GuidedNode(text: "The converter is likely worn out. Have a shop confirm before buying one, because they're expensive. Check your warranty: US federal emissions coverage is often 8 years or 80,000 miles.", options: []),
            "shop": GuidedNode(text: "A shop can test the converter before you buy one. Converters are expensive, so it's worth confirming.", options: []),
        ]),
        GuidedTopic(key: "cold", title: "Engine not warming up", codes: ["P0128"], start: "level", nodes: [
            "level": GuidedNode(text: "With the engine fully cold, check the coolant level in the overflow tank. Is it between the marks?", options: [("Yes", "drive"), ("It's low", "low")]),
            "low": GuidedNode(text: "Top it up with the coolant type your manual lists, and look for leaks. Then clear the code and see if it returns.", options: []),
            "drive": GuidedNode(text: "Drive for about 15 minutes and watch coolant temperature in Live data. Where does it end up?", options: [("Stays under about 180 °F", "stat"), ("Reaches 190 °F or more", "sensor")]),
            "stat": GuidedNode(text: "The thermostat is probably stuck open. Replacing it is the usual fix.", options: []),
            "sensor": GuidedNode(text: "The engine is warming up fine. Check the coolant temperature sensor and its connector, then clear the code and see if it returns.", options: []),
        ]),
        GuidedTopic(key: "overheat", title: "Engine overheating", codes: ["P0217"], start: "safe", nodes: [
            "safe": GuidedNode(text: "Pull over and turn the engine off if the gauge is in the red. Never open the radiator cap while it's hot, because the coolant can spray out and burn you. Is the engine fully cool?", options: [("Yes, it's cool", "level"), ("Not yet", "wait")]),
            "wait": GuidedNode(text: "Wait at least 30 minutes, then come back to this step.", options: [("It's cool now", "level")]),
            "level": GuidedNode(text: "Check the coolant level in the overflow tank. Is it low?", options: [("Yes, it's low", "leak"), ("No, it's fine", "fan")]),
            "leak": GuidedNode(text: "Top it up with the right coolant and look for leaks under the car and around the hoses. Coolant that keeps dropping with no visible leak needs a shop to check the head gasket.", options: []),
            "fan": GuidedNode(text: "Start the engine and turn the A/C on. Keep your hands clear of the fan. Do the radiator fans run?", options: [("Yes", "stat"), ("No", "badfan")]),
            "badfan": GuidedNode(text: "Check the fan's fuse and relay, then the fan itself. A shop can test the fan circuit.", options: []),
            "stat": GuidedNode(text: "The next suspects are a stuck thermostat, a clogged radiator, or a weak water pump. Have them checked before driving far, because overheating can badly damage an engine.", options: []),
        ]),
        GuidedTopic(key: "charging", title: "Check the charging system", codes: ["P0562", "P0563"], start: "volts", nodes: [
            "volts": GuidedNode(text: "With the engine running, read the battery voltage in Live data or with a meter. What is it?", options: [("13.5 to 14.8 V", "okay"), ("Under 13 V", "low"), ("Over 15 V", "high")]),
            "okay": GuidedNode(text: "Charging looks normal right now. Clean and tighten the battery terminals, then test the battery itself. Clear the code and see if it returns.", options: []),
            "low": GuidedNode(text: "With the engine off, check the belt and the battery terminals. Is the belt loose or cracked, or are the terminals corroded?", options: [("Yes", "fixbelt"), ("No, they look fine", "alt")]),
            "fixbelt": GuidedNode(text: "Fix that first, then read the voltage again with the engine running.", options: []),
            "alt": GuidedNode(text: "The alternator is likely weak. Most parts stores can test it for free before you buy one.", options: []),
            "high": GuidedNode(text: "The alternator is probably overcharging, which can damage the battery and electronics. Have it checked soon.", options: []),
        ]),
    ]
}

/// One question at a time: each answer leads to the next check, until there's a result.
struct GuidedView: View {
    @Environment(\.dismiss) private var dismiss
    let topic: GuidedTopic
    @State private var path: [String] = []

    private var current: String { path.last ?? topic.start }

    var body: some View {
        let node = topic.nodes[current]!
        return ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    if !path.isEmpty { LinkLabel("Back") { path.removeLast() } }
                    Spacer()
                    LinkLabel("Done") { dismiss() }
                }
                proText(topic.title, size: 22, bold: true)
                proText(node.options.isEmpty ? "Result" : "Step \(path.count + 1)", muted: true)
                RoundCard(radius: 16) { proText(node.text, size: 15) }
                ForEach(node.options, id: \.1) { option in
                    Button { path.append(option.1) } label: {
                        RoundCard(radius: 14, padY: 12) {
                            HStack {
                                proText(option.0, size: 14, bold: true).multilineTextAlignment(.leading)
                                Spacer(minLength: 8)
                                Image(systemName: "chevron.right").foregroundStyle(MacColor.muted).accessibilityHidden(true)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                }
                if node.options.isEmpty {
                    WebLinks(base: topic.title, topic: topic.title.lowercased())
                    Button("Start over") { path = [] }.buttonStyle(PillStyle())
                    proText("This is general guidance. Confirm with a test before buying parts.", muted: true, size: 12)
                }
            }
            .padding(16)
        }
        .background(MacColor.page)
        .tint(MacColor.ink)
    }
}

/// The way into step-by-step help from a code's page. Shows nothing for codes with no guide.
struct GuidedButton: View {
    let code: String
    @State private var show = false
    var body: some View {
        if let topic = GuidedHelp.topic(forCode: code) {
            Button("Walk me through it") { show = true }
                .buttonStyle(PillStyle(kind: .primary))
                .sheet(isPresented: $show) { GuidedView(topic: topic) }
        }
    }
}

/// Choose which live readings are on your dashboard, and their order.
struct DashboardEditor: View {
    @Environment(\.dismiss) private var dismiss
    let names: [String]
    @Binding var pins: [String]
    @Binding var only: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                HStack { Spacer(); LinkLabel("Done") { dismiss() } }
                proText("Customize dashboard", size: 22, bold: true)
                proText("Add the readings you care about. They show first on Live data, in this order.", muted: true)
                Toggle(isOn: $only) { proText("Only show my dashboard", size: 14) }
                    .tint(MacTint.vehicle).disabled(pins.isEmpty)
                if !pins.isEmpty { proText("My dashboard", size: 16, bold: true) }
                ForEach(Array(pins.enumerated()), id: \.element) { i, name in
                    RoundCard(radius: 14, padY: 8) {
                        HStack(spacing: 14) {
                            proText(name, size: 14)
                            Spacer(minLength: 4)
                            Button { pins.swapAt(i, i - 1) } label: { Image(systemName: "arrow.up") }
                                .disabled(i == 0).accessibilityLabel("Move \(name) up")
                            Button { pins.swapAt(i, i + 1) } label: { Image(systemName: "arrow.down") }
                                .disabled(i == pins.count - 1).accessibilityLabel("Move \(name) down")
                            Button { pins.remove(at: i); if pins.isEmpty { only = false } } label: {
                                Image(systemName: "minus.circle.fill").foregroundStyle(MacColor.red)
                            }
                            .accessibilityLabel("Remove \(name)")
                        }
                        .buttonStyle(.plain)
                    }
                }
                let rest = names.filter { !pins.contains($0) }
                if !rest.isEmpty { proText("Add a reading", size: 16, bold: true).padding(.top, 4) }
                ForEach(rest, id: \.self) { name in
                    Button { pins.append(name) } label: {
                        RoundCard(radius: 14, padY: 10) {
                            HStack {
                                proText(name, size: 14).multilineTextAlignment(.leading)
                                Spacer(minLength: 8)
                                Image(systemName: "plus.circle.fill").foregroundStyle(MacTint.vehicle).accessibilityHidden(true)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(16)
        }
        .background(MacColor.page)
        .tint(MacColor.ink)
    }
}
