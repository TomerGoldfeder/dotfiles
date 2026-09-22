import AppKit

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var server: IPCServer?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)

        do {
            server = try IPCServer { command in
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
        } catch {
            fputs("aerospace-cheatsheet: IPC server failed: \(error)\n", stderr)
            NSApp.terminate(nil)
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        false
    }
}
