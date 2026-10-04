package tui

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// View implements tea.Model.
func (m Model) View() string {
	if m.quitting && m.phase == phaseDone {
		return ""
	}
	t := m.theme
	title := lipgloss.NewStyle().
		Foreground(t.PrimaryStrong).
		Bold(true).
		Render("gpr")
	subtitle := lipgloss.NewStyle().
		Foreground(t.TextMuted).
		Render(fmt.Sprintf("  %s  %s → %s", m.ctx.Root, m.inputs[fieldHead].Value(), m.inputs[fieldBase].Value()))

	header := lipgloss.NewStyle().
		Background(t.SurfaceStrong).
		Foreground(t.Text).
		Padding(0, 1).
		Render(title + subtitle)

	if m.phase == phasePreview || m.phase == phaseDiff || m.phase == phaseErr {
		box := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.BorderStrong).
			Background(t.Surface).
			Foreground(t.Text).
			Padding(1, 2).
			Width(max(40, m.width-4)).
			Render(m.preview)
		status := lipgloss.NewStyle().Foreground(t.Info).Render(m.status)
		return lipgloss.JoinVertical(lipgloss.Left, header, "", box, "", status)
	}

	rows := []string{
		m.row("Title", fieldTitle, m.inputs[fieldTitle].View()),
		m.row("Body", fieldBody, m.body.View()),
		m.row("Base", fieldBase, m.inputs[fieldBase].View()),
		m.row("Head", fieldHead, m.inputs[fieldHead].View()),
		m.row("Assignees", fieldAssignees, m.inputs[fieldAssignees].View()),
		m.row("Reviewers", fieldReviewers, m.inputs[fieldReviewers].View()),
		m.row("Labels", fieldLabels, m.inputs[fieldLabels].View()),
		m.row("Milestone", fieldMilestone, m.inputs[fieldMilestone].View()),
		m.row("Project", fieldProject, m.inputs[fieldProject].View()),
		m.toggleRow("Draft", m.draft, "D"),
		m.toggleRow("No maintainer edit", m.noMaint, "M"),
		m.templateRow(),
	}

	form := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border).
		Background(t.Bg).
		Padding(1, 2).
		Render(strings.Join(rows, "\n"))

	help := lipgloss.NewStyle().Foreground(t.TextMuted).Render(
		"keys: Tab/j/k navigate · Enter edit · D draft · M no-maintainer-edit · f/F/v fill · t template · b body preview · d diff · p dry-run · s submit · q quit",
	)
	statusColor := t.Info
	if m.phase == phaseErr {
		statusColor = t.Error
	}
	status := lipgloss.NewStyle().Foreground(statusColor).Render(m.status)

	mode := "nav"
	if m.editing {
		mode = "edit"
	}
	modeBadge := lipgloss.NewStyle().
		Foreground(t.TextInverse).
		Background(t.Accent).
		Padding(0, 1).
		Render(mode)

	return lipgloss.JoinVertical(lipgloss.Left,
		header,
		"",
		form,
		"",
		modeBadge+"  "+status,
		help,
	)
}

func (m Model) row(label string, f field, value string) string {
	t := m.theme
	focused := m.focus == f
	labelStyle := lipgloss.NewStyle().Width(18).Foreground(t.TextMuted)
	if focused {
		labelStyle = labelStyle.Foreground(t.Primary).Bold(true)
	}
	marker := " "
	if focused {
		marker = lipgloss.NewStyle().Foreground(t.PrimaryStrong).Render("▸")
	}
	return marker + " " + labelStyle.Render(label) + " " + value
}

func (m Model) toggleRow(label string, on bool, key string) string {
	t := m.theme
	state := "off"
	style := lipgloss.NewStyle().Foreground(t.TextMuted)
	if on {
		state = "on"
		style = lipgloss.NewStyle().Foreground(t.Success).Bold(true)
	}
	return "  " + lipgloss.NewStyle().Width(18).Foreground(t.TextMuted).Render(label) +
		" " + style.Render(state) +
		lipgloss.NewStyle().Foreground(t.TextMuted).Render(fmt.Sprintf("  [%s]", key))
}

func (m Model) templateRow() string {
	t := m.theme
	name := "(none)"
	if m.tmplIdx >= 0 && m.tmplIdx < len(m.templates) {
		name = m.templates[m.tmplIdx].Name
	} else if len(m.templates) > 0 {
		name = fmt.Sprintf("%d available", len(m.templates))
	}
	return "  " + lipgloss.NewStyle().Width(18).Foreground(t.TextMuted).Render("Template") +
		" " + lipgloss.NewStyle().Foreground(t.Accent).Render(name) +
		lipgloss.NewStyle().Foreground(t.TextMuted).Render("  [t]")
}
