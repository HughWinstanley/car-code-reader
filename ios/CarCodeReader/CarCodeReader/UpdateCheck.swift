import Foundation

/// Looks for a newer iPhone version, published on GitHub like the Mac app's release.json.
/// An iPhone app can't replace its own code the way the Mac app does, so this only tells you one exists.
///     <repo>/ios/version.json    {"version": "2.11", "notes": "...", "url": "https://... (optional)"}
enum UpdateCheck {
    struct Release: Decodable {
        let version: String
        var notes: String? = nil
        var url: String? = nil
    }

    private static let repoBase = "https://raw.githubusercontent.com/HughWinstanley/car-code-reader/main"

    private static var versionURL: URL? {
        let base = ProcessInfo.processInfo.environment["CCR_UPDATE_URL"] ?? repoBase   // override used for testing
        return URL(string: base + "/ios/version.json")
    }

    /// "2.10 — Nov 4" -> [2, 10]
    static func parts(_ version: String) -> [Int] {
        let number = version.prefix { $0.isNumber || $0 == "." }
        return number.split(separator: ".").compactMap { Int($0) }
    }

    /// Compares number by number, so 2.10 is newer than 2.9.
    static func isNewer(_ version: String, than current: String) -> Bool {
        parts(current).lexicographicallyPrecedes(parts(version))
    }

    static func latest() async throws -> Release {
        guard let url = versionURL else { throw URLError(.badURL) }
        let request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 15)
        let (data, response) = try await URLSession.shared.data(for: request)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
        return try JSONDecoder().decode(Release.self, from: data)
    }
}
