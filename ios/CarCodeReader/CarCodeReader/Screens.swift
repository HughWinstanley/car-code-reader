import SwiftUI

// MARK: - Choose vehicle (make → model → year)

struct VehiclePickerSheet: View {
    @EnvironmentObject var reader: Reader
    @Environment(\.dismiss) private var dismiss
    @State private var make: String? = nil
    @State private var model: VModel? = nil

    var body: some View {
        NavigationStack {
            Group {
                if make == nil {
                    List(VehicleData.makes, id: \.self) { m in
                        Button(m) { make = m }.foregroundStyle(.primary)
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
