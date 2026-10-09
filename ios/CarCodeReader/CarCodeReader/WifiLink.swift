import Foundation
import Network

/// Talks to a Wi-Fi OBD-II adapter over a plain TCP connection (e.g. 192.168.0.10:35000).
final class WifiLink: OBDLink {
    private var conn: NWConnection?
    private let queue = DispatchQueue(label: "obd.wifi")
    let host: String
    let port: UInt16

    init(host: String, port: UInt16) { self.host = host; self.port = port }

    func connect() async throws {
        let c = NWConnection(host: NWEndpoint.Host(host),
                             port: NWEndpoint.Port(rawValue: port) ?? 35000, using: .tcp)
        conn = c
        var resumed = false
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            c.stateUpdateHandler = { state in
                switch state {
                case .ready:           if !resumed { resumed = true; cont.resume() }
                case .failed(let e):   if !resumed { resumed = true; cont.resume(throwing: e) }
                case .cancelled:       if !resumed { resumed = true; cont.resume(throwing: OBDError.cancelled) }
                default: break
                }
            }
            c.start(queue: queue)
        }
    }

    func close() { conn?.cancel(); conn = nil }

    func command(_ text: String, timeout: TimeInterval) async throws -> String {
        guard let c = conn else { throw OBDError.notConnected }
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            c.send(content: (text + "\r").data(using: .ascii)!,
                   completion: .contentProcessed { if let e = $0 { cont.resume(throwing: e) } else { cont.resume() } })
        }
        var reply = ""
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            let chunk: Data = try await withCheckedThrowingContinuation { cont in
                c.receive(minimumIncompleteLength: 1, maximumLength: 1024) { data, _, _, error in
                    if let error = error { cont.resume(throwing: error) } else { cont.resume(returning: data ?? Data()) }
                }
            }
            if let s = String(data: chunk, encoding: .ascii) { reply += s; if reply.contains(">") { break } }
        }
        return reply.replacingOccurrences(of: ">", with: "")
    }
}
