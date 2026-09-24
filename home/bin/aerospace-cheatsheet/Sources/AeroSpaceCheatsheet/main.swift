import AppKit

let executablePath = ExecutablePath.resolved()

if CommandLine.arguments.count > 1 && CommandLine.arguments[1] != "--gui" {
    let commandName = CommandLine.arguments[1]
    guard let command = IPCCommand(rawValue: commandName) else {
        fputs("Usage: aerospace-cheatsheet [toggle|show|hide|quit]\n", stderr)
        exit(1)
    }
    exit(IPCClient.send(command, executablePath: executablePath))
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
