import SwiftUI

// MARK: - Maker logo badges (monograms & colours from the Mac app)

enum VehicleBadges {
    /// make -> (monogram, hex colour), taken from the Mac app's vehicles.MAKES / badge_color.
    static let info: [String: (String, String)] = [
        "Ford": ("FD", "#2C5C9A"), "Chevrolet": ("CHV", "#2C5C9A"), "GMC": ("GMC", "#2E9C94"),
        "Buick": ("BU", "#2E9C94"), "Cadillac": ("CA", "#2F7BC0"), "Pontiac": ("PO", "#2E9C94"),
        "Oldsmobile": ("OL", "#2C5C9A"), "Saturn": ("ST", "#7A5CC8"), "Hummer": ("HM", "#5E7488"),
        "Lincoln": ("LN", "#C8901E"), "Mercury": ("MC", "#7A5CC8"), "Dodge": ("DG", "#B03E6E"),
        "Ram": ("RAM", "#7A5CC8"), "Jeep": ("JP", "#B03E6E"), "Chrysler": ("CHR", "#7A5CC8"),
        "Plymouth": ("PL", "#2E9C94"), "Toyota": ("TY", "#C8901E"), "Lexus": ("LX", "#3A9A56"),
        "Scion": ("SC", "#2F7BC0"), "Honda": ("HO", "#D0502A"), "Acura": ("AC", "#C8901E"),
        "Nissan": ("NI", "#5E7488"), "Infiniti": ("IN", "#3A9A56"), "Hyundai": ("HY", "#C0622F"),
        "Genesis": ("GN", "#B03E6E"), "Kia": ("KIA", "#2E9C94"), "Mazda": ("MZ", "#C0622F"),
        "Subaru": ("SU", "#3A9A56"), "Mitsubishi": ("MI", "#D0502A"), "Suzuki": ("SZ", "#2E9C94"),
        "Isuzu": ("IS", "#B03E6E"), "Volkswagen": ("VW", "#3A9A56"), "Audi": ("AU", "#D0502A"),
        "BMW": ("BMW", "#3A9A56"), "Mini": ("MN", "#B03E6E"), "Mercedes-Benz": ("MB", "#3A9A56"),
        "Volvo": ("VO", "#D0502A"), "Saab": ("SA", "#2F7BC0"), "Porsche": ("PR", "#2F7BC0"),
        "Jaguar": ("JA", "#2C5C9A"), "Land Rover": ("LR", "#C0622F"), "Fiat": ("FI", "#C8901E"),
        "GM": ("GM", "#2C5C9A"),
    ]
    static func mono(_ make: String) -> String {
        if let m = info[make]?.0 { return m }
        let words = make.split(separator: " ")
        if words.count >= 2 { return String(words[0].prefix(1) + words[1].prefix(1)).uppercased() }
        return String(make.prefix(2)).uppercased()
    }
    static func color(_ make: String) -> Color { Color(hex: info[make]?.1 ?? "#5E7488") }
}

/// A shield-style maker emblem with the make's monogram, matching the Mac app's badges.
struct MakeBadge: View {
    let make: String
    var size: CGFloat = 56
    var body: some View {
        let c = VehicleBadges.color(make)
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.28, style: .continuous)
                .fill(LinearGradient(colors: [c.opacity(0.92), c], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: size * 0.28, style: .continuous)
                    .stroke(Color.white.opacity(0.55), lineWidth: max(1, size * 0.03)))
                .shadow(color: c.opacity(0.35), radius: size * 0.06, y: size * 0.03)
            Text(VehicleBadges.mono(make))
                .font(.system(size: size * 0.36, weight: .heavy, design: .rounded))
                .foregroundStyle(.white)
                .minimumScaleFactor(0.5).lineLimit(1).padding(.horizontal, size * 0.08)
        }
        .frame(width: size, height: size)
    }
}

/// A tappable maker tile (badge + name) for the logo grids.
struct MakeTile: View {
    let make: String
    var body: some View {
        VStack(spacing: 8) {
            MakeBadge(make: make)
            Text(make).font(.caption).foregroundStyle(.primary)
                .lineLimit(1).minimumScaleFactor(0.7)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12).padding(.horizontal, 6)
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemGroupedBackground)))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color(.separator), lineWidth: 0.5))
    }
}

// MARK: - Choose vehicle (make → model → year)

struct VehiclePickerSheet: View {
    @EnvironmentObject var reader: Reader
    @Environment(\.dismiss) private var dismiss
    @State private var make: String? = nil
    @State private var model: VModel? = nil

    private let cols = [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12),
                        GridItem(.flexible(), spacing: 12)]

    var body: some View {
        NavigationStack {
            Group {
                if make == nil {
                    ScrollView {
                        LazyVGrid(columns: cols, spacing: 12) {
                            ForEach(VehicleData.makes, id: \.self) { m in
                                Button { make = m } label: { MakeTile(make: m) }.buttonStyle(.plain)
                            }
                        }
                        .padding(.horizontal, 14).padding(.top, 10)
                    }
                } else if model == nil {
                    List(VehicleData.models[make!] ?? [], id: \.name) { mm in
                        Button(mm.name) { model = mm }.foregroundStyle(.primary)
                    }
                } else {
                    List(Array((model!.minYear...model!.maxYear).reversed()), id: \.self) { y in
                        Button(String(y)) {
                            reader.setVehicle(makeName: make!, model: model!.name, year: y)
                            dismiss()
                        }.foregroundStyle(.primary)
                    }
                }
            }
            .navigationTitle(make == nil ? "Make" : (model == nil ? make! : model!.name))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                if make != nil {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button("Back") { if model != nil { model = nil } else { make = nil } }
                    }
                }
            }
        }
    }
}

// MARK: - Problem detail (why it matters, causes, how to check)

struct ProblemDetailView: View {
    @EnvironmentObject var reader: Reader
    @Environment(\.openURL) private var openURL
    let problem: Problem

    var body: some View {
        List {
            Section {
                Text(problem.meaning).font(.headline)
                if let f = problem.factory {
                    Text("\(f) factory meaning — can differ by model and year").font(.caption).foregroundStyle(.secondary)
                }
                Text(problem.status).font(.caption).foregroundStyle(.secondary)
            }

            Section("Why it matters") {
                Text(CodeDetail.whyItMatters(problem.code, status: problem.status, module: "Engine"))
            }

            let causes = CodeDetail.commonCauses(problem.code)
            if !causes.isEmpty {
                Section("Common causes") { Text(causes) }
            }

            let steps = CodeDetail.checkSteps(problem.code, make: reader.make)
            if !steps.isEmpty {
                Section("How to check it") {
                    ForEach(Array(steps.enumerated()), id: \.offset) { i, s in
                        HStack(alignment: .top, spacing: 8) {
                            Text("\(i + 1).").foregroundStyle(.blue).frame(width: 20, alignment: .trailing)
                            Text(s)
                        }
                    }
                }
            }

            Section {
                Button("Search this code online") { search() }
                Button("Repair videos") { search(videos: true) }
            }
        }
        .navigationTitle(problem.code)
        .navigationBarTitleDisplayMode(.inline)
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
