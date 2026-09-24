// hs — Herdr session picker built from glyph command-palette + spinner templates.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"sort"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	commandpalette "hs/internal/ui/commandpalette"
	"hs/internal/ui/spinner"
	"hs/internal/ui/theme"
)

type herdrSession struct {
	Name       string `json:"name"`
	Running    bool   `json:"running"`
	Default    bool   `json:"default"`
	SessionDir string `json:"session_dir"`
}

type phase int

const (
	phaseLoading phase = 0
	phasePicker  phase = 1
	phaseError   phase = 2
)

type sessionsLoadedMsg struct {
	sessions []herdrSession
}

type sessionsErrMsg struct {
	err error
}

type model struct {
	theme    theme.Theme
	phase    phase
	spinner  spinner.Spinner
	palette  commandpalette.Palette
	width    int
	height   int
	err      string
	selected string
}

func newModel() model {
	t := theme.Default
	loadSpinner := spinner.New(t).
		WithStyle(spinner.StyleDots).
		WithLabel("Loading sessions").
		WithID("load")

	palette := commandpalette.New(t).
		WithTitle("Herdr sessions").
		WithPlaceholder("Filter by name, path, or status…").
		WithMatcher(sessionMatcher).
		WithSize(72, 12)

	return model{
		theme:   t,
		phase:   phaseLoading,
		spinner: loadSpinner,
		palette: palette,
	}
}

func (m model) Init() tea.Cmd {
	return tea.Batch(m.spinner.Init(), loadSessions())
}

func loadSessions() tea.Cmd {
	return func() tea.Msg {
		out, err := exec.Command("herdr", "session", "list", "--json").Output()
		if err != nil {
			return sessionsErrMsg{err: fmt.Errorf("herdr session list: %w", err)}
		}

		var payload struct {
			Sessions []herdrSession `json:"sessions"`
		}
		if err := json.Unmarshal(out, &payload); err != nil {
			return sessionsErrMsg{err: fmt.Errorf("parse session list: %w", err)}
		}
		if len(payload.Sessions) == 0 {
			return sessionsErrMsg{err: fmt.Errorf("no Herdr sessions")}
		}
		return sessionsLoadedMsg{sessions: payload.Sessions}
	}
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		body := msg.Height - 8
		if body < 6 {
			body = 6
		}
		width := msg.Width - 4
		if width < 72 {
			width = 72
		}
		m.palette = m.palette.WithSize(width, body)
		return m, nil

	case sessionsLoadedMsg:
		m.phase = phasePicker
		cmds, table := sessionsToCommands(msg.sessions)
		m.palette = m.palette.WithCommands(cmds).WithTableLayout(table)
		return m, nil

	case sessionsErrMsg:
		m.phase = phaseError
		m.err = msg.err.Error()
		return m, nil

	case commandpalette.SelectMsg:
		m.selected = msg.Command.ID
		return m, tea.Quit

	case commandpalette.CancelMsg:
		return m, tea.Quit

	case tea.KeyMsg:
		if m.phase == phaseError && msg.String() == "esc" {
			return m, tea.Quit
		}
	}

	switch m.phase {
	case phaseLoading:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd
	case phasePicker:
		var cmd tea.Cmd
		m.palette, cmd = m.palette.Update(msg)
		return m, cmd
	}

	return m, nil
}

func (m model) View() string {
	switch m.phase {
	case phaseLoading:
		return lipgloss.Place(
			m.width, m.height,
			lipgloss.Center, lipgloss.Center,
			m.spinner.View(),
			lipgloss.WithWhitespaceChars(" "),
		)
	case phasePicker:
		return lipgloss.Place(
			m.width, m.height,
			lipgloss.Center, lipgloss.Center,
			m.palette.View(),
			lipgloss.WithWhitespaceChars(" "),
		)
	case phaseError:
		errStyle := lipgloss.NewStyle().
			Foreground(m.theme.Error).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(m.theme.BorderStrong).
			Padding(1, 2).
			Width(56)
		body := errStyle.Render("hs: " + m.err + "\n\nesc to close")
		return lipgloss.Place(
			m.width, m.height,
			lipgloss.Center, lipgloss.Center,
			body,
			lipgloss.WithWhitespaceChars(" "),
		)
	default:
		return ""
	}
}

func sessionsToCommands(sessions []herdrSession) ([]commandpalette.Command, commandpalette.TableLayout) {
	sort.SliceStable(sessions, func(i, j int) bool {
		a, b := sessions[i], sessions[j]
		rank := func(s herdrSession) int {
			switch {
			case s.Default:
				return 0
			case s.Running:
				return 1
			default:
				return 2
			}
		}
		ra, rb := rank(a), rank(b)
		if ra != rb {
			return ra < rb
		}
		return a.Name < b.Name
	})

	nameWidth := len("name")
	statusWidth := len("stopped")
	for _, s := range sessions {
		if len(s.Name) > nameWidth {
			nameWidth = len(s.Name)
		}
	}

	table := commandpalette.TableLayout{
		Enabled:      true,
		NameHeader:   "name",
		StatusHeader: "status",
		DirHeader:    "directory",
		NameWidth:    nameWidth,
		StatusWidth:  statusWidth,
		ColGap:       2,
	}

	cmds := make([]commandpalette.Command, 0, len(sessions))
	for _, s := range sessions {
		cmds = append(cmds, commandpalette.Command{
			ID:          s.Name,
			Title:       s.Name,
			Keybinding:  sessionStatusText(s),
			Description: s.SessionDir,
		})
	}
	return cmds, table
}

func sessionStatusText(s herdrSession) string {
	if s.Running {
		return "running"
	}
	return "stopped"
}

func sessionMatcher(cmd commandpalette.Command, query string) int {
	if query == "" {
		return 100
	}
	q := strings.ToLower(query)
	for _, field := range []string{cmd.Title, cmd.Description, cmd.Keybinding} {
		if i := strings.Index(strings.ToLower(field), q); i >= 0 {
			return 1000 - i
		}
	}
	return 0
}

func main() {
	m, err := tea.NewProgram(newModel(), tea.WithAltScreen()).Run()
	if err != nil {
		fmt.Fprintf(os.Stderr, "hs: %v\n", err)
		os.Exit(1)
	}

	final, ok := m.(model)
	if !ok || final.selected == "" {
		return
	}

	attach := exec.Command("herdr", "session", "attach", final.selected)
	attach.Stdin = os.Stdin
	attach.Stdout = os.Stdout
	attach.Stderr = os.Stderr
	if err := attach.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "hs: attach %s: %v\n", final.selected, err)
		os.Exit(1)
	}
}
