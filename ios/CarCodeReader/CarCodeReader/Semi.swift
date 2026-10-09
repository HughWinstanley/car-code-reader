import SwiftUI

struct J1939Fault: Identifiable {
    let id = UUID()
    let spn: Int
    let fmi: Int
    let oc: Int
    let source: Int
    let active: Bool
    var title: String { J1939Data.spn[spn] ?? "SPN \(spn) (maker-specific — look it up)" }
    var detail: String {
        let f = J1939Data.fmi[fmi] ?? "fault type \(fmi)"
        let src = J1939Data.source[source] ?? "source \(source)"
        return "\(f) · from \(src) · seen \(oc)×"
    }
}

enum J1939 {
    /// Decode a DM1/DM2 payload (the bytes after the 2 lamp-status bytes) into faults.
    static func decodeDTCs(_ bytes: [UInt8], source: Int, active: Bool) -> [J1939Fault] {
        var out: [J1939Fault] = []
        var i = 2
        while i + 3 < bytes.count {
            let b0 = Int(bytes[i]), b1 = Int(bytes[i + 1]), b2 = Int(bytes[i + 2]), b3 = Int(bytes[i + 3])
            let spn = b0 | (b1 << 8) | ((b2 >> 5) << 16)
            let fmi = b2 & 0x1F
            let oc = b3 & 0x7F
            if spn == 0 && fmi == 0 { i += 4; continue }
            if spn >= 0x7FFFF { break }
            out.append(J1939Fault(spn: spn, fmi: fmi, oc: oc, source: source, active: active))
            i += 4
        }
        return out
    }

    /// Parse a block of monitored J1939 frames (from ATMA) for single-frame DM1/DM2 messages.
    static func parseMonitor(_ text: String) -> [J1939Fault] {
        var out: [J1939Fault] = []
        for raw in text.split(whereSeparator: { $0 == "\r" || $0 == "\n" }) {
            let line = raw.replacingOccurrences(of: " ", with: "").uppercased()
            guard line.count >= 10, line.allSatisfy({ $0.isHexDigit }) else { continue }
            let id = Array(line.prefix(8))
            func byte(_ o: Int) -> UInt8? { UInt8(String(id[o..<o + 2]), radix: 16) }
            guard let pf = byte(2), let ps = byte(4), let sa = byte(6) else { continue }
            guard pf == 0xFE, ps == 0xCA || ps == 0xCB else { continue }   // DM1 active / DM2 previous
            var data: [UInt8] = []
            var h = Substring(line.dropFirst(8))
            while h.count >= 2 { data.append(UInt8(h.prefix(2), radix: 16) ?? 0); h = h.dropFirst(2) }
            out += decodeDTCs(data, source: Int(sa), active: ps == 0xCA)
        }
        return out
    }

    /// A worked example (one active fault) so the screen is useful without a truck connected.
    static var example: [J1939Fault] {
        parseMonitor("18FECA00 00 00 6E 00 03 05")   // SPN 110 engine coolant temp, FMI 3, seen 5x
    }
}

struct SemiView: View {
    @EnvironmentObject var reader: Reader
    @State private var showExample = false

    var faults: [J1939Fault] { showExample ? J1939.example : reader.semiFaults }

    var body: some View {
        Group {
            if !reader.connected && !showExample {
                ScrollView {
                    VStack(alignment: .leading, spacing: 14) {
                        Text("Reads heavy-duty truck codes over the J1939 network (9-pin port).")
                            .font(.subheadline).foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true).padding(.horizontal)
                        EmptyStateCard(icon: "icon-semi", tint: MacTint.semi, title: "Not connected yet",
                                       message: "Plug a J1939-capable adapter into the truck's 9-pin port, then connect.")
                        Button("See an example") { showExample = true }
                            .buttonStyle(.bordered).padding(.horizontal)
                    }
                    .padding(.top, 8)
                }
            } else {
                VStack(alignment: .leading, spacing: 0) {
                    VStack(spacing: 10) {
                        Text(reader.semiStatus.isEmpty
                             ? "Reads heavy-duty truck codes over the J1939 network (9-pin port)."
                             : reader.semiStatus)
                            .font(.footnote).foregroundStyle(.secondary).multilineTextAlignment(.center)
                        HStack {
                            if reader.connected {
                                Button("Read from truck") { showExample = false; reader.readSemi() }
                                    .buttonStyle(.borderedProminent).disabled(reader.busy)
                            }
                            Button(showExample ? "Hide example" : "See an example") { showExample.toggle() }
                                .buttonStyle(.bordered)
                        }
                    }
                    .frame(maxWidth: .infinity).padding()

                    List(faults) { f in
                        VStack(alignment: .leading, spacing: 3) {
                            HStack {
                                Text("SPN \(f.spn) · FMI \(f.fmi)").font(.headline)
                                Spacer()
                                Text(f.active ? "Active" : "Previous").font(.caption)
                                    .foregroundStyle(f.active ? .red : .gray)
                            }
                            Text(f.title).font(.subheadline)
                            Text(f.detail).font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .listStyle(.plain)
                }
            }
        }
        .navigationTitle("Semi trucks")
        .navigationBarTitleDisplayMode(.inline)
    }
}
