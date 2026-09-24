import AppKit
import SwiftUI

enum Theme {
    static let surface = Color(red: 0.141, green: 0.153, blue: 0.227)
    static let text = Color(red: 0.792, green: 0.827, blue: 0.961)
    static let secondary = Color(red: 0.576, green: 0.604, blue: 0.718)
    static let accent = Color(red: 0.541, green: 0.678, blue: 0.957)
    static let selection = Color(red: 0.286, green: 0.302, blue: 0.392)
    static let panelHeight: CGFloat = 420
    static let cornerRadius: CGFloat = 9
    static let monoFont = Font.custom("JetBrainsMono Nerd Font", size: 13)
        .weight(.medium)
    static let monoFontBold = Font.custom("JetBrainsMono Nerd Font", size: 13)
        .weight(.semibold)
}

final class PanelController: NSWindowController {
    static let shared = PanelController()

    private var clickMonitor: Any?
    private var keyMonitor: Any?
    private var isVisible = false

    private init() {
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 800, height: Theme.panelHeight),
            styleMask: [.fullSizeContentView, .borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.isFloatingPanel = true
        panel.level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.mainMenuWindow)) + 2)
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.backgroundColor = .clear
        panel.isOpaque = false
        panel.hasShadow = true
        panel.titleVisibility = .hidden
        panel.titlebarAppearsTransparent = true
        panel.hidesOnDeactivate = false
        panel.isMovable = false
        panel.isMovableByWindowBackground = false

        super.init(window: panel)

        let rootView = ContentView(onClose: { [weak self] in
            self?.hide()
        })
        panel.contentView = NSHostingView(rootView: rootView)
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    func toggle() {
        if isVisible {
            hide()
        } else {
            show()
        }
    }

    func show() {
        AppState.shared.reloadBindings()
        positionPanel()
        window?.alphaValue = 0
        window?.orderFrontRegardless()
        NSApp.activate(ignoringOtherApps: true)
        window?.makeKey()

        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.12
            window?.animator().alphaValue = 1
        }

        isVisible = true
        installMonitors()
        DispatchQueue.main.async {
            AppState.shared.focusSearch()
        }
    }

    func hide() {
        removeMonitors()
        window?.orderOut(nil)
        isVisible = false
    }

    private func positionPanel() {
        guard let window else { return }

        let mouse = NSEvent.mouseLocation
        let screen = NSScreen.screens.first { $0.frame.contains(mouse) }
            ?? NSScreen.main
            ?? NSScreen.screens.first
        guard let screen else { return }

        let visible = screen.visibleFrame
        let height = min(Theme.panelHeight, visible.height * 0.55)
        let rect = NSRect(
            x: visible.origin.x,
            y: visible.maxY - height,
            width: visible.width,
            height: height
        )
        window.setFrame(rect, display: true)
    }

    private func installMonitors() {
        removeMonitors()

        clickMonitor = NSEvent.addGlobalMonitorForEvents(matching: [.leftMouseDown, .rightMouseDown]) { [weak self] event in
            guard let self, let window = self.window else { return }
            let screenPoint = NSEvent.mouseLocation
            if !window.frame.contains(screenPoint) {
                self.hide()
            }
            _ = event
        }

        keyMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if event.keyCode == 53 { // Escape
                self?.hide()
                return nil
            }

            let state = AppState.shared
            let rows = state.filteredRows
            guard !rows.isEmpty else { return event }

            if event.keyCode == 125 { // Down
                state.selectNext(from: rows)
                return nil
            }
            if event.keyCode == 126 { // Up
                state.selectPrevious(from: rows)
                return nil
            }

            return event
        }
    }

    private func removeMonitors() {
        if let clickMonitor {
            NSEvent.removeMonitor(clickMonitor)
            self.clickMonitor = nil
        }
        if let keyMonitor {
            NSEvent.removeMonitor(keyMonitor)
            self.keyMonitor = nil
        }
    }
}

final class AppState: ObservableObject {
    static let shared = AppState()

    @Published var rows: [BindingRow] = []
    @Published var searchText = ""
    @Published var selectedMode = "All"
    @Published var selectedRowID: BindingRow.ID?
    @Published var loadError: String?
    @Published var requestSearchFocus = false

    let modes = ["All", "main", "service", "apps"]

    var filteredRows: [BindingRow] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return rows.filter { row in
            let modeMatches = selectedMode == "All" || row.mode == selectedMode
            guard modeMatches else { return false }
            guard !query.isEmpty else { return true }
            return row.key.lowercased().contains(query) || row.command.lowercased().contains(query)
        }
    }

    func reloadBindings() {
        do {
            rows = try BindingParser.load()
            loadError = nil
            if selectedRowID == nil {
                selectedRowID = filteredRows.first?.id
            }
        } catch {
            rows = []
            loadError = error.localizedDescription
        }
        searchText = ""
        selectedMode = "All"
        selectedRowID = filteredRows.first?.id
    }

    func focusSearch() {
        requestSearchFocus.toggle()
    }

    func selectNext(from rows: [BindingRow]) {
        guard let current = selectedRowID,
              let index = rows.firstIndex(where: { $0.id == current }),
              index + 1 < rows.count else {
            selectedRowID = rows.first?.id
            return
        }
        selectedRowID = rows[index + 1].id
    }

    func selectPrevious(from rows: [BindingRow]) {
        guard let current = selectedRowID,
              let index = rows.firstIndex(where: { $0.id == current }),
              index > 0 else {
            selectedRowID = rows.first?.id
            return
        }
        selectedRowID = rows[index - 1].id
    }
}

struct ContentView: View {
    let onClose: () -> Void
    @ObservedObject private var state = AppState.shared
    @FocusState private var searchFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            header
            if let error = state.loadError {
                Text(error)
                    .font(Theme.monoFont)
                    .foregroundStyle(.red)
                    .padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            table
        }
        .background(
            RoundedRectangle(cornerRadius: Theme.cornerRadius, style: .continuous)
                .fill(Theme.surface)
                .padding(.horizontal, 10)
                .padding(.bottom, 10)
        )
        .padding(.top, 0)
        .onChange(of: state.requestSearchFocus) { _, _ in
            searchFocused = true
        }
        .onAppear {
            searchFocused = true
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                TextField("Search bindings…", text: $state.searchText)
                    .textFieldStyle(.plain)
                    .font(Theme.monoFont)
                    .foregroundStyle(Theme.text)
                    .focused($searchFocused)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(
                        RoundedRectangle(cornerRadius: 8, style: .continuous)
                            .fill(Theme.selection.opacity(0.65))
                    )

                Button("Esc") {
                    onClose()
                }
                .buttonStyle(.plain)
                .font(Theme.monoFont)
                .foregroundStyle(Theme.secondary)
            }

            Picker("Mode", selection: $state.selectedMode) {
                ForEach(state.modes, id: \.self) { mode in
                    Text(mode).tag(mode)
                }
            }
            .pickerStyle(.segmented)
        }
        .padding(.horizontal, 22)
        .padding(.top, 14)
        .padding(.bottom, 10)
    }

    private var table: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 0, pinnedViews: [.sectionHeaders]) {
                    if state.filteredRows.isEmpty {
                        Text(state.searchText.isEmpty ? "No bindings found." : "No bindings match \"\(state.searchText)\".")
                            .font(Theme.monoFont)
                            .foregroundStyle(Theme.secondary)
                            .padding(.horizontal, 22)
                            .padding(.vertical, 16)
                    } else {
                        ForEach(groupedRows, id: \.mode) { group in
                            Section {
                                ForEach(group.rows) { row in
                                    rowView(row)
                                        .id(row.id)
                                }
                            } header: {
                                if state.selectedMode == "All" {
                                    Text(group.mode.uppercased())
                                        .font(Theme.monoFontBold)
                                        .foregroundStyle(Theme.accent)
                                        .padding(.horizontal, 22)
                                        .padding(.top, 10)
                                        .padding(.bottom, 4)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .background(Theme.surface.opacity(0.95))
                                }
                            }
                        }
                    }
                }
            }
            .onChange(of: state.selectedRowID) { _, newValue in
                if let newValue {
                    withAnimation(.easeInOut(duration: 0.12)) {
                        proxy.scrollTo(newValue, anchor: .center)
                    }
                }
            }
        }
    }

    private var groupedRows: [(mode: String, rows: [BindingRow])] {
        let rows = state.filteredRows
        if state.selectedMode != "All" {
            return [(mode: state.selectedMode, rows: rows)]
        }
        let order = ["main", "service", "apps"]
        return order.compactMap { mode in
            let modeRows = rows.filter { $0.mode == mode }
            return modeRows.isEmpty ? nil : (mode: mode, rows: modeRows)
        }
    }

    private func rowView(_ row: BindingRow) -> some View {
        let selected = state.selectedRowID == row.id
        return HStack(alignment: .top, spacing: 12) {
            Text(row.key)
                .font(Theme.monoFontBold)
                .foregroundStyle(Theme.accent)
                .frame(width: 220, alignment: .trailing)
            Text(row.command)
                .font(Theme.monoFont)
                .foregroundStyle(Theme.text)
                .frame(maxWidth: .infinity, alignment: .leading)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.horizontal, 22)
        .padding(.vertical, 6)
        .background(selected ? Theme.selection : Color.clear)
        .contentShape(Rectangle())
        .onTapGesture {
            state.selectedRowID = row.id
        }
    }
}
