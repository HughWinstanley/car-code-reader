import Foundation
import CoreBluetooth

/// Talks to a Bluetooth Low Energy OBD-II adapter (a generic BLE ELM327, e.g. Vgate iCar Pro BLE)
/// through Core Bluetooth. NOTE: the OBDLink MX+ uses classic Bluetooth and needs OBDLink's own
/// SDK instead — it won't connect here. A Wi-Fi or BLE adapter is the simplest for this app.
final class BLELink: NSObject, OBDLink, CBCentralManagerDelegate, CBPeripheralDelegate {
    private var central: CBCentralManager!
    private var peripheral: CBPeripheral?
    private var writeChar: CBCharacteristic?
    private var buffer = ""

    private var powerCont: CheckedContinuation<Void, Error>?
    private var connectCont: CheckedContinuation<Void, Error>?
    private var readCont: CheckedContinuation<String, Error>?

    // Common serial-service UUIDs used by BLE ELM327 clones.
    private let serialServices = [CBUUID(string: "FFF0"), CBUUID(string: "FFE0"),
                                  CBUUID(string: "18F0"), CBUUID(string: "FFF1")]

    func connect() async throws {
        central = CBCentralManager(delegate: self, queue: nil)
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Void, Error>) in
            self.powerCont = c                       // resumed in centralManagerDidUpdateState
        }
        central.scanForPeripherals(withServices: nil, options: nil)
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Void, Error>) in
            self.connectCont = c                     // resumed once a characteristic is ready
        }
    }

    func close() {
        if let p = peripheral { central?.cancelPeripheralConnection(p) }
        central?.stopScan(); peripheral = nil; writeChar = nil
    }

    func command(_ text: String, timeout: TimeInterval) async throws -> String {
        guard let p = peripheral, let ch = writeChar else { throw OBDError.notConnected }
        buffer = ""
        p.writeValue((text + "\r").data(using: .ascii)!, for: ch,
                     type: ch.properties.contains(.writeWithoutResponse) ? .withoutResponse : .withResponse)
        return try await withTimeout(timeout) {
            try await withCheckedThrowingContinuation { (c: CheckedContinuation<String, Error>) in
                self.readCont = c                    // resumed in didUpdateValueFor when '>' arrives
            }
        }
    }

    private func withTimeout<T>(_ seconds: TimeInterval, _ op: @escaping () async throws -> T) async throws -> T {
        try await withThrowingTaskGroup(of: T.self) { group in
            group.addTask { try await op() }
            group.addTask { try await Task.sleep(nanoseconds: UInt64(seconds * 1e9)); throw OBDError.noAnswer }
            let result = try await group.next()!
            group.cancelAll()
            return result
        }
    }

    // MARK: Core Bluetooth delegate
    func centralManagerDidUpdateState(_ c: CBCentralManager) {
        switch c.state {
        case .poweredOn: powerCont?.resume(); powerCont = nil
        case .poweredOff: powerCont?.resume(throwing: OBDError.bluetoothOff); powerCont = nil
        default: break
        }
    }

    func centralManager(_ c: CBCentralManager, didDiscover p: CBPeripheral,
                        advertisementData: [String: Any], rssi RSSI: NSNumber) {
        let name = (p.name ?? "").uppercased()
        let looksLikeOBD = ["OBD", "ELM", "VLINK", "VGATE", "ICAR", "VIECAR"].contains { name.contains($0) }
        if looksLikeOBD || name.isEmpty == false {
            central.stopScan()
            peripheral = p; p.delegate = self
            central.connect(p, options: nil)
        }
    }

    func centralManager(_ c: CBCentralManager, didConnect p: CBPeripheral) {
        p.discoverServices(nil)
    }

    func centralManager(_ c: CBCentralManager, didFailToConnect p: CBPeripheral, error: Error?) {
        connectCont?.resume(throwing: error ?? OBDError.noAdapterFound); connectCont = nil
    }

    func peripheral(_ p: CBPeripheral, didDiscoverServices error: Error?) {
        for s in p.services ?? [] { p.discoverCharacteristics(nil, for: s) }
    }

    func peripheral(_ p: CBPeripheral, didDiscoverCharacteristicsFor s: CBService, error: Error?) {
        for ch in s.characteristics ?? [] {
            if ch.properties.contains(.notify) || ch.properties.contains(.indicate) {
                p.setNotifyValue(true, for: ch)
            }
            if ch.properties.contains(.write) || ch.properties.contains(.writeWithoutResponse) {
                if writeChar == nil { writeChar = ch }
            }
        }
        if writeChar != nil { connectCont?.resume(); connectCont = nil }
    }

    func peripheral(_ p: CBPeripheral, didUpdateValueFor ch: CBCharacteristic, error: Error?) {
        if let data = ch.value, let s = String(data: data, encoding: .ascii) {
            buffer += s
            if buffer.contains(">") {
                let out = buffer.replacingOccurrences(of: ">", with: "")
                readCont?.resume(returning: out); readCont = nil
            }
        }
    }
}
