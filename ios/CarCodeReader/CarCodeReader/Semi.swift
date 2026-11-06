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

/// Semi trucks for Choose vehicle (the Mac app's vehicles.TRUCKS). They all read over J1939, so the brand only labels
/// the truck. Years start at 2000 because older trucks mostly have the round 6-pin J1708 port instead.
enum TruckData {
    static let firstYear = 2000
    static let brands = ["Freightliner", "Peterbilt", "Kenworth", "Mack", "International", "Volvo Trucks", "Western Star", "Sterling"]
    static let models: [String: [VModel]] = [
        "Freightliner": [t("Cascadia", 2007, nil), t("Columbia", 2000, 2013), t("Century Class", 2000, 2011), t("Classic", 2000, 2011), t("Coronado", 2001, 2017), t("M2 106", 2002, nil), t("M2 112", 2004, 2016), t("108SD", 2011, nil), t("114SD", 2011, nil), t("122SD", 2011, nil)],
        "Peterbilt": [t("579", 2012, nil), t("589", 2024, nil), t("567", 2013, nil), t("389", 2007, nil), t("379", 2000, 2007), t("387", 2000, 2010), t("386", 2005, 2015), t("384", 2008, 2015), t("367", 2007, nil), t("365", 2007, nil), t("357", 2000, 2007), t("348", 2006, 2017), t("337", 2005, 2017)],
        "Kenworth": [t("T680", 2013, nil), t("T880", 2014, nil), t("W900", 2000, nil), t("W990", 2018, nil), t("T800", 2000, nil), t("T660", 2008, 2017), t("T600", 2000, 2007), t("T700", 2010, 2015), t("T2000", 2000, 2010), t("T370", 2010, 2021), t("T300", 2000, 2010)],
        "Mack": [t("Anthem", 2018, nil), t("Pinnacle", 2006, nil), t("Granite", 2002, nil), t("Vision", 2000, 2007), t("CH", 2000, 2006), t("CL", 2000, 2006), t("RD", 2000, 2013), t("LR", 2015, nil), t("MD", 2020, nil), t("TerraPro", 2007, nil)],
        "International": [t("LT", 2017, nil), t("RH", 2018, nil), t("HX", 2016, nil), t("MV", 2018, nil), t("ProStar", 2008, 2018), t("LoneStar", 2009, 2019), t("TranStar", 2009, 2019), t("WorkStar", 2008, 2017), t("DuraStar", 2002, 2018), t("PayStar", 2004, 2017), t("9900i", 2000, 2016), t("9400i", 2000, 2007), t("9200i", 2000, 2007), t("8600", 2002, 2014)],
        "Volvo Trucks": [t("VNL", 2000, nil), t("VNR", 2018, nil), t("VNX", 2003, nil), t("VHD", 2000, nil), t("VAH", 2008, 2019), t("VT", 2003, 2009)],
        "Western Star": [t("49X", 2021, nil), t("57X", 2023, nil), t("47X", 2021, nil), t("4900", 2000, 2024), t("5700XE", 2015, 2023), t("4700", 2012, 2021), t("6900", 2000, nil)],
        "Sterling": [t("A-Line", 2000, 2009), t("L-Line", 2000, 2009), t("Acterra", 2001, 2009), t("Bullet", 2008, 2009)],
    ]
    /// Padded by a year at each end, the same as the car list. nil = still made.
    private static func t(_ name: String, _ from: Int, _ to: Int?) -> VModel {
        let next = Calendar.current.component(.year, from: Date()) + 1
        return VModel(name: name, minYear: max(firstYear, from - 1), maxYear: min(next, (to ?? next - 1) + 1))
    }
}

struct SemiView: View {
    @EnvironmentObject var reader: Reader
    @State private var showExample = false

    var faults: [J1939Fault] { showExample ? J1939.example : reader.semiFaults }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                PageTitle(title: "Semi trucks",
                          subtitle: reader.semiStatus.isEmpty
                              ? "Reads heavy-duty truck codes over the J1939 network (9-pin port)."
                              : reader.semiStatus,
                          icon: "icon-semi")
                if !reader.connected && !showExample {
                    EmptyStateCard(icon: "icon-semi", title: "Not connected yet",
                                   message: "Plug a J1939-capable adapter into the truck's 9-pin port, then connect.",
                                   buttonTitle: "Connect and read", action: { reader.readTruck() })
                }
                FlowLayout {
                    if reader.connected {
                        Button("Read from truck") { showExample = false; reader.readTruck() }
                            .buttonStyle(PillStyle(kind: .primary)).disabled(reader.busy)
                    }
                    Button(showExample ? "Hide example" : "See an example") { showExample.toggle() }
                        .buttonStyle(PillStyle())
                }
                ForEach(faults) { f in
                    RoundCard(radius: 16, padY: 14) {
                        HStack(alignment: .top, spacing: 10) {
                            ZStack {
                                Circle().fill((f.active ? MacColor.red : MacColor.off).opacity(0.22)).frame(width: 16, height: 16)
                                Circle().fill(f.active ? MacColor.red : MacColor.off).frame(width: 8, height: 8)
                            }
                            .padding(.top, 2)
                            Text(f.title).scaledFont(15, weight: .bold).foregroundStyle(MacColor.ink)
                                .fixedSize(horizontal: false, vertical: true)
                            Spacer(minLength: 4)
                            StatusPill(words: f.active ? "Active" : "Previous",
                                       fill: f.active ? MacColor.redSoft : MacColor.offSoft,
                                       text: f.active ? MacColor.red : MacColor.muted)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text("SPN \(f.spn), FMI \(f.fmi)").scaledFont(12).foregroundStyle(MacColor.muted)
                            Text(f.detail).scaledFont(13).foregroundStyle(MacColor.ink)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        .padding(.leading, 26).padding(.top, 3)
                    }
                }
            }
            .padding(16)
        }
        .background(MacColor.page)
        .navigationBarTitleDisplayMode(.inline)
    }
}
