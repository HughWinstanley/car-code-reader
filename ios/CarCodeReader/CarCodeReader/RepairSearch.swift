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
    @State private var fixText = ""
    @State private var codeText = ""
    @State private var fixQuery = ""
    @State private var codeQuery = ""
    @State private var showFix = false
    @State private var showCode = false
    @State private var codeHint = false

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
        VStack(alignment: .leading, spacing: 8) {
            bar("Search how to fix something", $fixText, action: searchFix)
            bar("Type a code, like P0301", $codeText, action: searchCode)
                .textInputAutocapitalization(.characters)
            if codeHint {
                proText("That isn't a code. A code is a letter and 4 numbers or letters, like P0301. To search by words, use the top bar.", muted: true, size: 12)
            }
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
