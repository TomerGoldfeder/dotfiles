import Foundation

enum IPCCommand: String {
    case toggle
    case show
    case hide
    case quit
}

private func makeUnixSocketAddress(path: String) -> sockaddr_un? {
    var addr = sockaddr_un()
    addr.sun_family = sa_family_t(AF_UNIX)
    let maxLen = MemoryLayout.size(ofValue: addr.sun_path)
    guard path.utf8.count < maxLen else { return nil }

    return path.withCString { cString in
        withUnsafeMutableBytes(of: &addr.sun_path) { rawBuffer in
            _ = strncpy(rawBuffer.baseAddress!.assumingMemoryBound(to: CChar.self), cString, maxLen - 1)
        }
        return addr
    }
}

enum IPCClient {
    @discardableResult
    static func send(_ command: IPCCommand, executablePath: String) -> Int32 {
        launchServerIfNeeded(executablePath: executablePath)

        guard let socket = openSocket() else {
            fputs("aerospace-cheatsheet: could not connect to server\n", stderr)
            return 1
        }

        defer { close(socket) }

        let message = command.rawValue + "\n"
        message.withCString { pointer in
            _ = write(socket, pointer, strlen(pointer))
        }

        var buffer = [UInt8](repeating: 0, count: 16)
        _ = read(socket, &buffer, buffer.count)
        return 0
    }

    private static func launchServerIfNeeded(executablePath: String) {
        let path = SupportPaths.socketPath
        if isServerAlive(at: path) {
            return
        }

        if FileManager.default.fileExists(atPath: path) {
            try? FileManager.default.removeItem(atPath: path)
        }

        // Detach from the short-lived CLI parent (AeroSpace exec-and-forget).
        // Direct Process.run() lets the GUI receive SIGHUP and exit immediately.
        let shell = Process()
        shell.executableURL = URL(fileURLWithPath: "/bin/sh")
        shell.arguments = [
            "-c",
            "nohup '\(executablePath)' --gui >/dev/null 2>&1 &",
        ]
        shell.standardOutput = FileHandle.nullDevice
        shell.standardError = FileHandle.nullDevice

        do {
            try shell.run()
            shell.waitUntilExit()
        } catch {
            fputs("aerospace-cheatsheet: failed to start server: \(error)\n", stderr)
            return
        }

        for _ in 0..<80 {
            if isServerAlive(at: path) {
                return
            }
            usleep(100_000)
        }
    }

    private static func isServerAlive(at path: String) -> Bool {
        guard FileManager.default.fileExists(atPath: path) else {
            return false
        }
        guard let socket = openSocket(path: path) else {
            try? FileManager.default.removeItem(atPath: path)
            return false
        }
        close(socket)
        return true
    }

    private static func openSocket(path: String = SupportPaths.socketPath) -> Int32? {
        let socketFD = socket(AF_UNIX, SOCK_STREAM, 0)
        guard socketFD >= 0 else { return nil }
        guard var addr = makeUnixSocketAddress(path: path) else {
            close(socketFD)
            return nil
        }

        let size = socklen_t(MemoryLayout<sockaddr_un>.size)
        let result = withUnsafePointer(to: &addr) { pointer in
            pointer.withMemoryRebound(to: sockaddr.self, capacity: 1) { sockaddrPointer in
                Darwin.connect(socketFD, sockaddrPointer, size)
            }
        }

        guard result == 0 else {
            close(socketFD)
            return nil
        }

        return socketFD
    }
}

final class IPCServer {
    private var source: DispatchSourceRead?
    private let socketFD: Int32
    private let onCommand: (IPCCommand) -> Void

    init(onCommand: @escaping (IPCCommand) -> Void) throws {
        self.onCommand = onCommand
        let path = SupportPaths.socketPath
        if FileManager.default.fileExists(atPath: path) {
            try FileManager.default.removeItem(atPath: path)
        }

        socketFD = socket(AF_UNIX, SOCK_STREAM, 0)
        guard socketFD >= 0 else {
            throw NSError(domain: "IPCServer", code: 1, userInfo: [NSLocalizedDescriptionKey: "socket() failed"])
        }

        guard var addr = makeUnixSocketAddress(path: path) else {
            close(socketFD)
            throw NSError(domain: "IPCServer", code: 2, userInfo: [NSLocalizedDescriptionKey: "socket path too long"])
        }

        let bindResult = withUnsafePointer(to: &addr) { pointer in
            pointer.withMemoryRebound(to: sockaddr.self, capacity: 1) { sockaddrPointer in
                bind(socketFD, sockaddrPointer, socklen_t(MemoryLayout<sockaddr_un>.size))
            }
        }
        guard bindResult == 0 else {
            close(socketFD)
            throw NSError(domain: "IPCServer", code: 3, userInfo: [NSLocalizedDescriptionKey: "bind() failed"])
        }

        guard listen(socketFD, 5) == 0 else {
            close(socketFD)
            throw NSError(domain: "IPCServer", code: 3, userInfo: [NSLocalizedDescriptionKey: "listen() failed"])
        }

        source = DispatchSource.makeReadSource(fileDescriptor: socketFD, queue: .global(qos: .userInitiated))
        source?.setEventHandler { [weak self] in
            self?.acceptConnections()
        }
        source?.resume()
    }

    deinit {
        source?.cancel()
        close(socketFD)
        try? FileManager.default.removeItem(atPath: SupportPaths.socketPath)
    }

    private func acceptConnections() {
        let clientFD = accept(socketFD, nil, nil)
        guard clientFD >= 0 else { return }

        var buffer = [UInt8](repeating: 0, count: 64)
        let count = read(clientFD, &buffer, buffer.count - 1)
        if count > 0 {
            let message = String(bytes: buffer.prefix(count), encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            if let command = IPCCommand(rawValue: message) {
                DispatchQueue.main.async {
                    self.onCommand(command)
                }
            }
        }

        "ok\n".withCString { pointer in
            _ = write(clientFD, pointer, strlen(pointer))
        }
        close(clientFD)
    }
}
