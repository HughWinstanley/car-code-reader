import Foundation

enum OBDError: Error, LocalizedError {
    case notConnected, cancelled, noAnswer, bluetoothOff, noAdapterFound
    var errorDescription: String? {
        switch self {
        case .notConnected:   return "Not connected to the adapter."
        case .cancelled:      return "The connection was cancelled."
        case .noAnswer:       return "The adapter is working, but the vehicle didn't answer. Turn the key to ON and make sure the adapter is pushed in fully."
        case .bluetoothOff:   return "Bluetooth is off. Turn it on in Settings."
        case .noAdapterFound: return "No Bluetooth OBD adapter found. Make sure it's plugged in and powered."
        }
    }
}

/// Anything that can send an ELM327 command line and return the reply up to the '>' prompt.
/// Both the Wi-Fi (TCP) and Bluetooth (BLE) connections implement this, so the ELM327 layer
/// doesn't care which one is in use.
protocol OBDLink: AnyObject {
    func connect() async throws
    func command(_ text: String, timeout: TimeInterval) async throws -> String
    func close()
}

extension OBDLink {
    func command(_ text: String) async throws -> String { try await command(text, timeout: 5) }
}
