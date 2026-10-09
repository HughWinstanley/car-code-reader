import SwiftUI

@main
struct CarCodeReaderApp: App {
    @StateObject private var reader = Reader()
    var body: some Scene {
        WindowGroup { ContentView().environmentObject(reader) }
    }
}
