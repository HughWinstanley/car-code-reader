import Foundation

enum OBDError: Error, LocalizedError {
    case notConnected, cancelled, noAnswer, bluetoothOff, noAdapterFound, noAdapterOnWifi
    case noAdapterChosen, bluetoothDenied, bluetoothUnsupported, notAnAdapter
    var errorDescription: String? {
        switch self {
        case .notConnected:   return "Not connected to the adapter."
        case .cancelled:      return "The connection was cancelled."
        case .noAnswer:       return "The adapter is working, but the vehicle didn't answer. Turn the key to ON and make sure the adapter is pushed in fully."
        case .bluetoothOff:   return "Bluetooth is off. Turn it on in Settings."
        case .noAdapterOnWifi: return "Couldn't reach the adapter. Join the adapter's Wi-Fi network in the iPhone's Settings, then try again."
        case .noAdapterFound: return "Couldn't reach your Bluetooth adapter. Make sure it's plugged in with the key ON, or choose it again in Settings."
        case .noAdapterChosen: return "Choose your Bluetooth adapter first: Settings, then Find adapters."
        case .bluetoothDenied: return "Car Code Reader isn't allowed to use Bluetooth. Turn it on in the iPhone's Settings, under Car Code Reader."
        case .bluetoothUnsupported: return "This device doesn't have Bluetooth Low Energy."
        case .notAnAdapter: return "That device doesn't work like an OBD adapter. Choose a different one in Settings."
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
