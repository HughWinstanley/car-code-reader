import SwiftUI

// MARK: - Maker logo badges (monograms from the Mac app)

enum VehicleBadges {
    /// make -> monogram, taken from the Mac app's vehicles.MAKES.
    static let info: [String: String] = [
        "Ford": "FD", "Chevrolet": "CHV", "GMC": "GMC", "Buick": "BU", "Cadillac": "CA", "Pontiac": "PO",
        "Oldsmobile": "OL", "Saturn": "ST", "Hummer": "HM", "Lincoln": "LN", "Mercury": "MC", "Dodge": "DG",
        "Ram": "RAM", "Jeep": "JP", "Chrysler": "CHR", "Plymouth": "PL", "Toyota": "TY", "Lexus": "LX",
        "Scion": "SC", "Honda": "HO", "Acura": "AC", "Nissan": "NI", "Infiniti": "IN", "Hyundai": "HY",
        "Genesis": "GN", "Kia": "KIA", "Mazda": "MZ", "Subaru": "SU", "Mitsubishi": "MI", "Suzuki": "SZ",
        "Isuzu": "IS", "Volkswagen": "VW", "Audi": "AU", "BMW": "BMW", "Mini": "MN", "Mercedes-Benz": "MB",
        "Volvo": "VO", "Saab": "SA", "Porsche": "PR", "Jaguar": "JA", "Land Rover": "LR", "Fiat": "FI",
        "GM": "GM",
    ]
    static func mono(_ make: String) -> String {
        if let m = info[make] { return m }
        let words = make.split(separator: " ")
        if words.count >= 2 { return String(words[0].prefix(1) + words[1].prefix(1)).uppercased() }
        return String(make.prefix(2)).uppercased()
    }
}

/// The Mac app's shield outline (icons.make_badge), smoothed the same way Tk smooths a polygon.
private struct ShieldShape: Shape {
    var inset: CGFloat = 0         // as a fraction of the size
    var squash: CGFloat = 1        // < 1 pulls the shape up into its top part (the gloss)

    func path(in rect: CGRect) -> Path {
        let size = min(rect.width, rect.height)
        let (cx, cy, h, i) = (rect.midX, rect.midY, size / 2, inset * size)
        let (l, r) = (cx - h * 0.86 + i, cx + h * 0.86 - i)
        let (t, b) = (cy - h * 0.9 + i, cy + h - i * 1.3)
        var pts = [CGPoint(x: l, y: t + size * 0.06), CGPoint(x: (l + r) / 2, y: t - size * 0.03),
                   CGPoint(x: r, y: t + size * 0.06), CGPoint(x: r, y: cy + h * 0.2),
                   CGPoint(x: cx, y: b), CGPoint(x: l, y: cy + h * 0.2)]
        let top = pts.map(\.y).min() ?? t
        pts = pts.map { CGPoint(x: $0.x, y: top + ($0.y - top) * squash) }

        func mid(_ a: CGPoint, _ b: CGPoint) -> CGPoint { CGPoint(x: (a.x + b.x) / 2, y: (a.y + b.y) / 2) }
        var path = Path()
        path.move(to: mid(pts[pts.count - 1], pts[0]))
        for (n, p) in pts.enumerated() {
            path.addQuadCurve(to: mid(p, pts[(n + 1) % pts.count]), control: p)
        }
        path.closeSubpath()
        return path
    }
}

/// A shield-style maker emblem: steel rim, dark field, glossy top and the monogram.
struct MakeBadge: View {
    let make: String
    var size: CGFloat = 56
    var body: some View {
        let letters = VehicleBadges.mono(make)
        ZStack {
            ShieldShape().fill(Color.black.opacity(0.12)).offset(y: size * 0.03)
            ShieldShape().fill(Color(hex: "#8F8F8F"))
            ShieldShape(inset: 0.07).fill(Color(hex: "#1E1E1E"))
            ShieldShape(inset: 0.07, squash: 0.45).fill(Color.white.opacity(0.14))
            Text(letters)
                .font(.system(size: size * (letters.count < 3 ? 0.27 : 0.22), weight: .bold))
                .foregroundStyle(.white)
                .lineLimit(1).minimumScaleFactor(0.6)
                .offset(y: size * 0.03)
        }
        .frame(width: size, height: size)
        .accessibilityHidden(true)   // the make's name is always next to it
    }
}

// MARK: - Choose vehicle (make → model → year)

struct VehiclePickerSheet: View {
    @EnvironmentObject var reader: Reader
    @Environment(\.dismiss) private var dismiss
    @State private var make: String? = nil
    @State private var model: VModel? = nil
    @State private var otherModel = false
    @State private var search = ""

    private var title: String {
        if make == nil { return "Choose the make" }
        if model == nil && !otherModel { return "Choose the \(make!) model" }
        return "Choose the year"
    }
    private var trail: String {
        if make == nil { return "Ford and GM brands get engine, ABS and airbag. Every other make gets engine codes, and ABS and airbag on many newer models." }
        return "\(make!) \(model?.name ?? "")".trimmingCharacters(in: .whitespaces)
    }
    private func matches(_ text: String) -> Bool {
        let q = search.trimmingCharacters(in: .whitespaces).lowercased()
        return q.isEmpty || text.lowercased().contains(q)
    }
    private var years: [Int] {
        if let model { return Array((model.minYear...model.maxYear).reversed()) }
        let all = VehicleData.models[make ?? ""] ?? []
        guard let low = all.map(\.minYear).min(), let high = all.map(\.maxYear).max() else { return [] }
        return Array((low...high).reversed())
    }

    /// Truck, SUV or van picture for a model, falling back to the car on iOS versions without that symbol.
    private func modelSymbol(_ model: String) -> String {
        let wanted: String
        switch VehicleKinds.byModel[make ?? ""]?[model] {
        case "t": wanted = "truck.pickup.side.fill"
        case "s": wanted = "suv.side.fill"
        case "v": wanted = "bus.fill"
        default:  wanted = "car.side.fill"
        }
        return UIImage(systemName: wanted) == nil ? "car.side.fill" : wanted
    }

    private func goBack() {
        search = ""
        if model != nil || otherModel { model = nil; otherModel = false } else { make = nil }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                if make != nil { LinkLabel("Back") { goBack() } }
                Spacer()
                LinkLabel("Cancel") { dismiss() }
            }
            Text(title).scaledFont(22, weight: .bold).foregroundStyle(MacColor.ink).padding(.top, 10)
            Text(trail).scaledFont(13).foregroundStyle(MacColor.muted)
                .fixedSize(horizontal: false, vertical: true).padding(.top, 2)
            HStack(spacing: 8) {
                Text("Search").scaledFont(13).foregroundStyle(MacColor.ink)
                TextField("", text: $search)
                    .scaledFont(13).autocorrectionDisabled().textInputAutocapitalization(.never)
                    .padding(.horizontal, 10).padding(.vertical, 7)
                    .overlay(RoundedRectangle(cornerRadius: 9, style: .continuous).stroke(MacColor.line, lineWidth: 1))
            }
            .padding(.top, 10).padding(.bottom, 12)

            ScrollView {
                if make == nil {
                    TileGrid(items: VehicleData.makes.filter(matches), columns: 3) { m in
                        Button { make = m; search = "" } label: {
                            TileCard(title: m) { MakeBadge(make: m, size: 62) }
                        }
                        .buttonStyle(.plain)
                    }
                } else if model == nil && !otherModel {
                    let list = (VehicleData.models[make!] ?? []).filter { matches($0.name) }
                    TileGrid(items: list.map(\.name) + ["Other model"]) { name in
                        Button {
                            search = ""
                            if let m = list.first(where: { $0.name == name }) { model = m } else { otherModel = true }
                        } label: {
                            TileCard(title: name, subtitle: name == "Other model" ? "Not in the list" : "") {
                                Image(systemName: modelSymbol(name)).font(.system(size: 34))
                                    .foregroundStyle(name == "Other model" ? MacColor.off : MacColor.ink)
                                    .accessibilityHidden(true)
                            }
                        }
                        .buttonStyle(.plain)
                    }
                } else {
                    VStack(alignment: .leading, spacing: 10) {
                        FlowLayout {
                            ForEach(years.filter { matches(String($0)) }, id: \.self) { y in
                                Button {
                                    reader.setVehicle(makeName: make!, model: model?.name ?? "", year: y)
                                    dismiss()
                                } label: {
                                    Text(String(y)).frame(minWidth: 40)
                                }
                                .buttonStyle(PillStyle(big: true))
                            }
                        }
                        .padding(1)   // keeps the pill edges clear of the scroll view's clipping
                        Text(years.contains { $0 < 1996 }
                             ? "1995 and older: use OBD-I on the Home page to read the blink codes, no adapter needed."
                             : "Only the years this model was sold, and that this app can read, are shown.")
                            .scaledFont(12).foregroundStyle(MacColor.muted)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            .scrollDismissesKeyboard(.interactively)
        }
        .padding(16)
        .background(MacColor.page)
        .tint(MacColor.ink)
    }
}

extension VehicleData {
    /// What the app can read on a chosen vehicle (the Mac app's support_text).
    static func supportText(make: String, year: Int?) -> String {
        if let year, year < 1996 { return "Engine codes by blink-code guide" }
        let fam = family[make] ?? ""
        return fam == "Ford" || fam == "GM" ? "Engine, ABS and airbag" : "Engine codes, some ABS and airbag"
    }
}
