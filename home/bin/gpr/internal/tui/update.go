package tui

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"

	"gpr/internal/fill"
)

// Update implements tea.Model.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.body.SetWidth(max(20, msg.Width-8))
		return m, nil

	case runResultMsg:
		if msg.err != nil {
			m.phase = phaseErr
			m.status = msg.err.Error()
			if msg.out != "" {
				m.preview = msg.out
			}
			return m, nil
		}
		if msg.dryRun {
			m.phase = phasePreview
			m.preview = msg.out
			m.status = "dry-run preview · Esc back · s submit for real"
			return m, nil
		}
		m.phase = phaseDone
		m.result = strings.TrimSpace(msg.out)
		m.status = "PR created"
		m.quitting = true
		return m, tea.Quit

	case diffMsg:
		m.phase = phaseDiff
		if msg.err != nil && strings.TrimSpace(msg.out) == "" {
			m.preview = msg.err.Error()
		} else {
			m.preview = msg.out
		}
		m.status = "diff preview · Esc back"
		return m, nil

	case fillMsg:
		if msg.err != nil {
			m.status = msg.err.Error()
			return m, nil
		}
		m.inputs[fieldTitle].SetValue(msg.title)
		m.body.SetValue(msg.body)
		m.status = fmt.Sprintf("filled (%s) — edit freely before submit", modeName(msg.mode))
		return m, nil

	case tea.KeyMsg:
		return m.handleKey(msg)
	}

	if m.phase != phaseForm {
		return m, nil
	}
	return m.updateInputs(msg)
}

func modeName(mode fill.Mode) string {
	switch mode {
	case fill.FillFirst:
		return "fill-first"
	case fill.FillVerbose:
		return "fill-verbose"
	default:
		return "fill"
	}
}

func (m Model) handleKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	if m.phase == phaseDone {
		return m, tea.Quit
	}

	if m.phase == phasePreview || m.phase == phaseDiff || m.phase == phaseErr {
		switch msg.String() {
		case "esc", "q":
			m.phase = phaseForm
			m.status = "back to form"
			return m, nil
		case "s":
			if m.phase == phasePreview {
				m.status = "creating PR…"
				return m, m.cmdCreate(false)
			}
		}
		return m, nil
	}

	if m.editing {
		switch msg.String() {
		case "esc":
			m.editing = false
			m.status = "navigation mode"
			return m, nil
		case "ctrl+s":
			m.editing = false
			m.status = "creating PR…"
			return m, m.cmdCreate(false)
		}
		return m.updateInputs(msg)
	}

	switch msg.String() {
	case "q", "ctrl+c":
		m.quitting = true
		m.status = "cancelled"
		return m, tea.Quit
	case "tab", "j", "down":
		m.focusField((m.focus + 1) % fieldCount)
		return m, nil
	case "shift+tab", "k", "up":
		m.focusField((m.focus + fieldCount - 1) % fieldCount)
		return m, nil
	case "enter", "i", "e":
		m.editing = true
		m.status = "editing · Esc done"
		return m, nil
	case " ":
		if m.focus == fieldTitle {
			// space on title starts edit
			m.editing = true
			return m.updateInputs(msg)
		}
	case "D":
		m.draft = !m.draft
		m.status = fmt.Sprintf("draft=%v", m.draft)
		return m, nil
	case "M":
		m.noMaint = !m.noMaint
		m.status = fmt.Sprintf("no-maintainer-edit=%v", m.noMaint)
		return m, nil
	case "f":
		m.status = "filling from commits…"
		return m, m.cmdFill(fill.Fill)
	case "F":
		m.status = "fill-first…"
		return m, m.cmdFill(fill.FillFirst)
	case "v":
		m.status = "fill-verbose…"
		return m, m.cmdFill(fill.FillVerbose)
	case "t":
		m.applyTemplate()
		return m, nil
	case "d":
		m.status = "loading diff…"
		return m, m.cmdDiff()
	case "b":
		md := "# " + m.inputs[fieldTitle].Value() + "\n\n" + m.body.Value()
		m.phase = phasePreview
		m.preview = renderMarkdown(md, m.width)
		m.status = "body preview (glamour) · Esc back"
		return m, nil
	case "p":
		if strings.TrimSpace(m.inputs[fieldTitle].Value()) == "" {
			m.status = "title required for dry-run"
			return m, nil
		}
		m.status = "dry-run…"
		return m, m.cmdCreate(true)
	case "s":
		if strings.TrimSpace(m.inputs[fieldTitle].Value()) == "" {
			m.status = "title required"
			return m, nil
		}
		m.status = "creating PR…"
		return m, m.cmdCreate(false)
	}
	return m, nil
}

func (m Model) updateInputs(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	if m.focus == fieldBody {
		m.body, cmd = m.body.Update(msg)
		return m, cmd
	}
	m.inputs[m.focus], cmd = m.inputs[m.focus].Update(msg)
	return m, cmd
}
