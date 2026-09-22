import Foundation

enum SupportPaths {
    static var appSupportDirectory: URL {
        let base = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/aerospace-cheatsheet", isDirectory: true)
        try? FileManager.default.createDirectory(at: base, withIntermediateDirectories: true)
        return base
    }

    static var socketURL: URL {
        appSupportDirectory.appendingPathComponent("server.sock")
    }

    static var socketPath: String {
        socketURL.path
    }
}
