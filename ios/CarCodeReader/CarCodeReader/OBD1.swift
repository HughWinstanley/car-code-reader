import SwiftUI

/// The Mac app's obd1.py helpers that aren't in the generated data.
enum OBD1Help {
    static let safety = "Park on level ground with the parking brake set and the transmission in Park (or Neutral for a manual). Only connect the terminals named below. A wrong jumper can damage the computer."
    static let groups: [(key: String, makes: String)] = [
        ("GM", "Chevy, GMC, Buick, Cadillac, Olds, Pontiac"), ("Ford", "Ford, Lincoln, Mercury"),
        ("Chrysler", "Chrysler, Dodge, Jeep, Plymouth"), ("Toyota", "Toyota and Lexus"), ("Honda", "Honda and Acura"),
    ]
    /// Codes that aren't faults.
    static let notFaults: [String: [String: String]] = [
        "GM": ["12": "Self-test is working (this isn't a fault)."],
        "Ford": ["10": "Separator: the codes after this are from memory (recent driving).",
                 "11": "System passed (no problem found).", "111": "System passed (no problem found)."],
        "Chrysler": ["55": "End of the list.", "12": "Battery was disconnected recently (not a fault)."],
        "Toyota": ["0": "Steady, even blinking: no codes stored."],
    ]

    /// "12, 33  44 111" -> ["12", "33", "44", "111"] (keeps order, drops repeats).
    static func parse(_ text: String) -> [String] {
        var out: [String] = []
        for part in text.split(whereSeparator: { !$0.isNumber }) {
            let trimmed = part.drop { $0 == "0" }
            let code = trimmed.isEmpty ? "0" : String(trimmed)
            if !out.contains(code) { out.append(code) }
        }
        return out
    }

    enum Kind { case ok, fault, unknown }

    static func explain(_ group: String, _ code: String) -> (String, Kind) {
        if let text = notFaults[group]?[code] { return (text, .ok) }
        let table = group == "Ford" ? (code.count == 3 ? "Ford3" : "Ford2") : group
        if let text = OBD1Data.codes[table]?[code] { return (text, .fault) }
        return ("Not in the built-in list for this make. Check that the flashes were counted correctly.", .unknown)
    }
}

struct OBD1View: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                PageTitle(title: "Read codes on 1995 and older vehicles",
                          subtitle: "These vehicles blink their codes on the check-engine light instead of sending them to an adapter. Pick the make and the app shows you how.")
                TileGrid(items: OBD1Help.groups.map(\.key)) { key in
                    NavigationLink { OBD1GuideView(group: key) } label: {
                        TileCard(title: key, subtitle: OBD1Help.groups.first { $0.key == key }?.makes ?? "") {
                            MakeBadge(make: key, size: 62)
                        }
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(16)
        }
        .background(Color.white)
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct OBD1GuideView: View {
    let group: String
    @State private var entry = ""
    @State private var results: [String]? = nil

    private var guide: OBD1Guide? { OBD1Data.guides[group] }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                PageTitle(title: guide?.title ?? group,
                          subtitle: "Follow the steps, count the flashes, then type the codes below.")
                RoundCard(fill: MacColor.amberSoft, outline: MacColor.amberSoft, padY: 12) {
                    Text(OBD1Help.safety).font(.system(size: 13)).foregroundStyle(MacColor.ink)
                        .fixedSize(horizontal: false, vertical: true)
                }
                if let guide {
                    VStack(alignment: .leading, spacing: 12) {
                        ForEach(Array(guide.steps.enumerated()), id: \.offset) { i, step in
                            HStack(alignment: .top, spacing: 12) {
                                StepDot(number: i + 1, size: 30)
                                Text(step).font(.system(size: 14)).foregroundStyle(MacColor.ink)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }
                    if !guide.note.isEmpty {
                        Text(guide.note).font(.system(size: 12)).foregroundStyle(MacColor.muted)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text("Codes you counted").font(.system(size: 14, weight: .bold)).foregroundStyle(MacColor.ink)
                    HStack(spacing: 10) {
                        TextField("", text: $entry)
                            .font(.system(size: 14)).keyboardType(.numbersAndPunctuation).submitLabel(.done)
                            .onSubmit { results = OBD1Help.parse(entry) }
                            .padding(.horizontal, 12).padding(.vertical, 9)
                            .overlay(RoundedRectangle(cornerRadius: 10, style: .continuous).stroke(MacColor.line, lineWidth: 1))
                        Button("Explain codes") { results = OBD1Help.parse(entry) }
                            .buttonStyle(PillStyle(kind: .primary))
                    }
                    Text("Separate codes with spaces or commas, for example: 12 33 44")
                        .font(.system(size: 12)).foregroundStyle(MacColor.muted)
                }

                if let results {
                    if results.isEmpty {
                        Text("Type the numbers you counted first.").font(.system(size: 13)).foregroundStyle(MacColor.muted)
                    }
                    ForEach(results, id: \.self) { code in resultCard(code) }
                }
            }
            .padding(16)
        }
        .scrollDismissesKeyboard(.interactively)
        .background(Color.white)
        .navigationBarTitleDisplayMode(.inline)
    }

    private func resultCard(_ code: String) -> some View {
        let (meaning, kind) = OBD1Help.explain(group, code)
        return RoundCard(radius: 16, padY: 12) {
            HStack(alignment: .center, spacing: 10) {
                Text(code).font(.system(size: 22, weight: .bold)).foregroundStyle(MacColor.ink)
                    .frame(minWidth: 44, alignment: .leading)
                Text(meaning).font(.system(size: 14)).foregroundStyle(MacColor.ink)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 4)
                switch kind {
                case .ok:      StatusPill(words: "Not a fault", fill: MacColor.greenSoft, text: MacColor.green)
                case .fault:   StatusPill(words: "Problem", fill: MacColor.amberSoft, text: MacColor.amberInk)
                case .unknown: StatusPill(words: "Not in list", fill: MacColor.offSoft, text: MacColor.muted)
                }
            }
        }
    }
}
