import Foundation

enum ExecutablePath {
    /// Resolve the real binary path. argv[0] is often bare "aerospace-cheatsheet"
    /// when launched by AeroSpace exec-and-forget (PWD may not contain the binary).
    static func resolved() -> String {
        var buffer = [CChar](repeating: 0, count: Int(PATH_MAX))
        var size = UInt32(buffer.count)
        guard _NSGetExecutablePath(&buffer, &size) == 0 else {
            return fallback()
        }

        var resolved = [CChar](repeating: 0, count: Int(PATH_MAX))
        if realpath(buffer, &resolved) != nil {
            return String(cString: resolved)
        }

        return String(cString: buffer)
    }

    private static func fallback() -> String {
        let arg0 = CommandLine.arguments[0]
        if arg0.hasPrefix("/") {
            return arg0
        }

        let which = Process()
        which.executableURL = URL(fileURLWithPath: "/usr/bin/which")
        which.arguments = [arg0]

        let pipe = Pipe()
        which.standardOutput = pipe
        which.standardError = FileHandle.nullDevice

        do {
            try which.run()
            which.waitUntilExit()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            if let path = String(data: data, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines),
                !path.isEmpty {
                return path
            }
        } catch {
            // fall through
        }

        return arg0
    }
}
