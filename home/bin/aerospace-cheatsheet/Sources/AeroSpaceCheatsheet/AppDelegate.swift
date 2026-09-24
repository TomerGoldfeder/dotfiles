import AppKit

enum PendingCommand {
    static var value: IPCCommand?
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var server: IPCServer?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)

        do {
            server = try IPCServer { command in
                Self.handle(command)
            }
        } catch {
            fputs("aerospace-cheatsheet: IPC server failed: \(error)\n", stderr)
            NSApp.terminate(nil)
            return
        }

        if let pending = PendingCommand.value {
            PendingCommand.value = nil
            DispatchQueue.main.async {
                Self.handle(pending)
            }
        }
    }

    private static func handle(_ command: IPCCommand) {
        switch command {
        case .toggle:
            PanelController.shared.toggle()
        case .show:
            PanelController.shared.show()
        case .hide:
            PanelController.shared.hide()
        case .quit:
            NSApp.terminate(nil)
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        false
    }
}
