import Foundation
import Combine
import CoreBluetooth

/// Which nearby Bluetooth devices look like OBD adapters, and which characteristics to talk through.
enum BLEMatch {
    /// Serial services used by BLE ELM327 adapters (the last is the one Vgate-style adapters use).
    static let serialServices = ["FFF0", "FFE0", "18F0", "E7810A71-73AE-499D-8C15-FAA9AEF0C3F2"]
    /// Generic Access, Generic Attribute, Current Time, Device Information, Battery: never the serial link.
    private static let standardServices = ["1800", "1801", "1805", "180A", "180F"]
    private static let nameHints = ["OBD", "ELM3", "VLINK", "VGATE", "ICAR", "VIECAR", "VEEPEAK", "LELINK", "KONNWEI"]

    static func isLikelyAdapter(name: String, services: [String]) -> Bool {
        let upper = name.uppercased()
        return nameHints.contains { upper.contains($0) } || upper.hasPrefix("ELM")
            || services.contains { serialServices.contains($0.uppercased()) }
    }

    struct Characteristic {
        let service: String, id: String
        let canWrite: Bool, canNotify: Bool
    }

    /// -> the characteristic to write to and the ones to listen on, all from one service, or nil if nothing fits.
    static func choose(_ all: [Characteristic]) -> (write: Int, notify: [Int])? {
        let services = NSOrderedSet(array: all.map { $0.service.uppercased() }).array.compactMap { $0 as? String }
        let known = serialServices.filter { services.contains($0) }
        let others = services.filter { !serialServices.contains($0) && !standardServices.contains($0) }
        for service in known + others {
            let here = all.indices.filter { all[$0].service.uppercased() == service }
            let notify = here.filter { all[$0].canNotify }
            if let write = here.first(where: { all[$0].canWrite }), !notify.isEmpty { return (write, notify) }
        }
        return nil
    }
}

/// Collects one command's reply as it arrives in pieces. A late timer from an older command can't end a newer one.
struct ReplyCollector {
    private var buffer = ""
    private var token = 0
    private var waiting = false

    private var cleaned: String { String(buffer.prefix { $0 != ">" }) }

    mutating func begin() -> Int {
        token += 1
        buffer = ""
        waiting = true
        return token
    }

    /// -> the whole reply once the '>' prompt arrives.
    mutating func add(_ data: Data) -> String? {
        guard waiting else { return nil }
        buffer += String(decoding: data.filter { $0 != 0 }, as: UTF8.self)
        guard buffer.contains(">") else { return nil }
        waiting = false
        return cleaned
    }

    /// -> whatever arrived before the time ran out, like the Wi-Fi link gives back.
    mutating func expire(_ expired: Int) -> String? {
        guard waiting, expired == token else { return nil }
        waiting = false
        return cleaned
    }
}

/// Talks to the chosen Bluetooth Low Energy OBD-II adapter (a generic BLE ELM327, e.g. Vgate iCar Pro BLE)
/// through Core Bluetooth. NOTE: the OBDLink MX+ uses classic Bluetooth and needs OBDLink's own
/// SDK instead — it won't connect here. A Wi-Fi or BLE adapter is the simplest for this app.
final class BLELink: NSObject, OBDLink, CBCentralManagerDelegate, CBPeripheralDelegate {
    private static let connectSeconds = 20.0
    private let adapterID: UUID?
    private let queue = DispatchQueue(label: "obd.ble")   // every Core Bluetooth callback and all state below
    private var central: CBCentralManager?
    private var peripheral: CBPeripheral?
    private var writeChar: CBCharacteristic?
    private var collector = ReplyCollector()
    private var connectCont: CheckedContinuation<Void, Error>?
    private var replyCont: CheckedContinuation<String, Error>?
    private var started = false
    private var servicesLeft = 0

    init(adapterID: UUID?) { self.adapterID = adapterID }

    func connect() async throws {
        guard adapterID != nil else { throw OBDError.noAdapterChosen }
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Void, Error>) in
            queue.async {
                self.connectCont = c
                self.central = CBCentralManager(delegate: self, queue: self.queue)
                self.queue.asyncAfter(deadline: .now() + Self.connectSeconds) {
                    self.finishConnect(OBDError.noAdapterFound)
                }
            }
        }
    }

    func close() {
        queue.async {
            if let p = self.peripheral { self.central?.cancelPeripheralConnection(p) }
            self.peripheral = nil
            self.writeChar = nil
            self.finishConnect(OBDError.cancelled)
            self.finishReply("")
        }
    }

    func command(_ text: String, timeout: TimeInterval) async throws -> String {
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<String, Error>) in
            queue.async {
                guard let p = self.peripheral, let ch = self.writeChar else {
                    c.resume(throwing: OBDError.notConnected)
                    return
                }
                self.finishReply("")   // nothing should be waiting, but never strand a caller
                self.replyCont = c
                let token = self.collector.begin()
                p.writeValue(Data((text + "\r").utf8), for: ch,
                             type: ch.properties.contains(.writeWithoutResponse) ? .withoutResponse : .withResponse)
                self.queue.asyncAfter(deadline: .now() + timeout) {
                    if let partial = self.collector.expire(token) { self.finishReply(partial) }
                }
            }
        }
    }

    private func finishConnect(_ error: Error?) {
        guard let c = connectCont else { return }
        connectCont = nil
        if let error {
            if let p = peripheral { central?.cancelPeripheralConnection(p) }
            peripheral = nil
            writeChar = nil
            c.resume(throwing: error)
        } else {
            c.resume()
        }
    }

    private func finishReply(_ text: String) {
        replyCont?.resume(returning: text)
        replyCont = nil
    }

    // MARK: Core Bluetooth delegate
    func centralManagerDidUpdateState(_ c: CBCentralManager) {
        switch c.state {
        case .poweredOn:
            guard !started, let id = adapterID else { return }
            started = true
            guard let p = c.retrievePeripherals(withIdentifiers: [id]).first else {
                finishConnect(OBDError.noAdapterFound)
                return
            }
            peripheral = p
            p.delegate = self
            c.connect(p, options: nil)
        case .poweredOff:   finishConnect(OBDError.bluetoothOff)
        case .unauthorized: finishConnect(OBDError.bluetoothDenied)
        case .unsupported:  finishConnect(OBDError.bluetoothUnsupported)
        default: break
        }
    }

    func centralManager(_ c: CBCentralManager, didConnect p: CBPeripheral) {
        p.discoverServices(nil)
    }

    func centralManager(_ c: CBCentralManager, didFailToConnect p: CBPeripheral, error: Error?) {
        finishConnect(error ?? OBDError.noAdapterFound)
    }

    func centralManager(_ c: CBCentralManager, didDisconnectPeripheral p: CBPeripheral, error: Error?) {
        peripheral = nil
        writeChar = nil
        finishConnect(error ?? OBDError.noAdapterFound)
        finishReply("")
    }

    func peripheral(_ p: CBPeripheral, didDiscoverServices error: Error?) {
        let services = p.services ?? []
        guard !services.isEmpty else {
            finishConnect(OBDError.notAnAdapter)
            return
        }
        servicesLeft = services.count
        for s in services { p.discoverCharacteristics(nil, for: s) }
    }

    func peripheral(_ p: CBPeripheral, didDiscoverCharacteristicsFor s: CBService, error: Error?) {
        servicesLeft -= 1
        guard servicesLeft == 0 else { return }
        let chars = (p.services ?? []).flatMap { $0.characteristics ?? [] }
        let described = chars.map { ch in
            BLEMatch.Characteristic(service: ch.service?.uuid.uuidString ?? "", id: ch.uuid.uuidString,
                                    canWrite: ch.properties.contains(.write) || ch.properties.contains(.writeWithoutResponse),
                                    canNotify: ch.properties.contains(.notify) || ch.properties.contains(.indicate))
        }
        guard let chosen = BLEMatch.choose(described) else {
            finishConnect(OBDError.notAnAdapter)
            return
        }
        writeChar = chars[chosen.write]
        for i in chosen.notify { p.setNotifyValue(true, for: chars[i]) }
    }

    /// Replies only arrive once the adapter has accepted the subscription, so only now is it ready.
    func peripheral(_ p: CBPeripheral, didUpdateNotificationStateFor ch: CBCharacteristic, error: Error?) {
        if let error { finishConnect(error) } else if ch.isNotifying { finishConnect(nil) }
    }

    func peripheral(_ p: CBPeripheral, didUpdateValueFor ch: CBCharacteristic, error: Error?) {
        if let data = ch.value, let whole = collector.add(data) { finishReply(whole) }
    }
}

/// A nearby Bluetooth device the user could pick as their adapter.
struct BLEDevice: Identifiable, Equatable {
    let id: UUID
    let name: String
    let likely: Bool
}

/// Lists nearby Bluetooth devices for Settings. It never connects to anything; that takes the user choosing one.
final class BLEScanner: NSObject, ObservableObject, CBCentralManagerDelegate {
    private static let scanSeconds = 15.0
    @Published private(set) var devices: [BLEDevice] = []
    @Published private(set) var scanning = false
    @Published private(set) var message = ""
    private var central: CBCentralManager?
    private var wantScan = false
    private var stopTimer: DispatchWorkItem?

    func start() {
        devices = []
        message = ""
        scanning = true
        wantScan = true
        #if targetEnvironment(simulator)
        // The Simulator has no Bluetooth, so this sample list is the only way to try the screen there.
        if ProcessInfo.processInfo.environment["CCR_BLE_SAMPLE"] != nil {
            devices = [BLEDevice(id: UUID(uuidString: "11111111-1111-1111-1111-111111111111")!, name: "VGate iCar Pro", likely: true),
                       BLEDevice(id: UUID(uuidString: "22222222-2222-2222-2222-222222222222")!, name: "Someone's Headphones", likely: false)]
            finishScan()
            return
        }
        #endif
        if let central { begin(central) } else { central = CBCentralManager(delegate: self, queue: nil) }
    }

    func stop() {
        guard scanning else { return }
        central?.stopScan()
        finishScan()
    }

    private func finishScan() {
        stopTimer?.cancel()
        wantScan = false
        scanning = false
        if message.isEmpty && devices.isEmpty {
            message = "Nothing found. Plug the adapter in, turn the key to ON, and try again."
        }
    }

    private func begin(_ c: CBCentralManager) {
        guard wantScan else { return }
        switch c.state {
        case .poweredOn:
            c.scanForPeripherals(withServices: nil, options: nil)
            let timer = DispatchWorkItem { [weak self] in self?.stop() }
            stopTimer?.cancel()
            stopTimer = timer
            DispatchQueue.main.asyncAfter(deadline: .now() + Self.scanSeconds, execute: timer)
        case .poweredOff:   fail(OBDError.bluetoothOff)
        case .unauthorized: fail(OBDError.bluetoothDenied)
        case .unsupported:  fail(OBDError.bluetoothUnsupported)
        default: break     // still starting up; centralManagerDidUpdateState calls back
        }
    }

    private func fail(_ error: OBDError) {
        message = error.localizedDescription
        finishScan()
    }

    func centralManagerDidUpdateState(_ c: CBCentralManager) { begin(c) }

    func centralManager(_ c: CBCentralManager, didDiscover p: CBPeripheral,
                        advertisementData: [String: Any], rssi RSSI: NSNumber) {
        let services = (advertisementData[CBAdvertisementDataServiceUUIDsKey] as? [CBUUID] ?? []).map(\.uuidString)
        let name = advertisementData[CBAdvertisementDataLocalNameKey] as? String ?? p.name ?? ""
        let likely = BLEMatch.isLikelyAdapter(name: name, services: services)
        guard !name.isEmpty || likely, !devices.contains(where: { $0.id == p.identifier }) else { return }
        devices.append(BLEDevice(id: p.identifier, name: name.isEmpty ? "Unnamed adapter" : name, likely: likely))
    }
}
