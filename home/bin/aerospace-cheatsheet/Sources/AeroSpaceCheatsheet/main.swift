import AppKit

let executablePath = ExecutablePath.resolved()

if CommandLine.arguments.count > 1 && CommandLine.arguments[1] != "--gui" {
    let commandName = CommandLine.arguments[1]
    guard let command = IPCCommand(rawValue: commandName) else {
        fputs("Usage: aerospace-cheatsheet [toggle|show|hide|quit]\n", stderr)
        exit(1)
    }

    if IPCClient.trySend(command) {
        exit(0)
    }

    if command == .quit {
        exit(0)
    }

    // No reachable daemon: run the GUI in this process (reliable under exec-and-forget).
    PendingCommand.value = command
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
