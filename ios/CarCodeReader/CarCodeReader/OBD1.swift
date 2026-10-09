import SwiftUI

struct OBD1View: View {
    @State private var group = "GM"
    @State private var query = ""
    private let groups = ["GM", "Ford", "Chrysler", "Toyota", "Honda"]

    private var guide: OBD1Guide? { OBD1Data.guides[group] }
    private var codeGroups: [String] { group == "Ford" ? ["Ford2", "Ford3"] : [group] }
    private var matches: [(String, String)] {
        let q = query.trimmingCharacters(in: .whitespaces)
        if q.isEmpty { return [] }
        var out: [(String, String)] = []
        for cg in codeGroups {
            for (k, v) in (OBD1Data.codes[cg] ?? [:]) where k.contains(q) { out.append((k, v)) }
        }
        return out.sorted { $0.0 < $1.0 }
    }

    var body: some View {
        Form {
            Section {
                Picker("Make", selection: $group) {
                    ForEach(groups, id: \.self) { Text($0).tag($0) }
                }
                .pickerStyle(.segmented)
            } footer: {
                Text("1995 and older vehicles have no data port standard — you read the codes by watching the dash light flash. No adapter needed.")
            }

            if let g = guide {
                Section("How to read the codes") {
                    Text(g.title).font(.subheadline).foregroundStyle(.secondary)
                    ForEach(Array(g.steps.enumerated()), id: \.offset) { i, s in
                        HStack(alignment: .top, spacing: 8) {
                            Text("\(i + 1).").foregroundStyle(.blue).frame(width: 20, alignment: .trailing)
                            Text(s)
                        }
                        .font(.subheadline)
                    }
                }
                if !g.note.isEmpty {
                    Section { Text(g.note).font(.footnote).foregroundStyle(.secondary) }
                }
            }

            Section("Look up a blink code") {
                TextField("e.g. 13", text: $query).keyboardType(.numbersAndPunctuation)
                if query.isEmpty {
                    Text("Type the code you saw flash to see what it means.")
                        .font(.footnote).foregroundStyle(.secondary)
                } else if matches.isEmpty {
                    Text("No \(group) code matches “\(query)”.").font(.footnote).foregroundStyle(.secondary)
                } else {
                    ForEach(matches.prefix(40), id: \.0) { code, meaning in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(code).font(.headline)
                            Text(meaning).font(.subheadline).foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .navigationTitle("OBD-I (1995 & older)")
        .navigationBarTitleDisplayMode(.inline)
    }
}
