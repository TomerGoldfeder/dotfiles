package commandpalette

import (
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// renderRow draws a single command row, with selection styling when active.
func (p Palette) renderRow(cmd Command, active bool) string {
	if p.table.Enabled {
		return p.renderTableRow(cmd, active)
	}

	rowWidth := p.width - 4
	titleStyle := lipgloss.NewStyle().Foreground(p.theme.Text)
	kbStyle := lipgloss.NewStyle().Foreground(p.theme.TextMuted).Italic(true)
	indicator := "  "
	if active {
		indicator = lipgloss.NewStyle().Foreground(p.theme.Primary).Bold(true).Render("❯ ")
		titleStyle = titleStyle.Bold(true).Foreground(p.theme.PrimaryStrong)
	}
	title := titleStyle.Render(cmd.Title)
	kbWidth := lipgloss.Width(cmd.Keybinding)
	titleWidth := lipgloss.Width(title)
	gap := rowWidth - lipgloss.Width(indicator) - titleWidth - kbWidth
	if gap < 1 {
		gap = 1
	}
	row := indicator + title + strings.Repeat(" ", gap)
	if cmd.Keybinding != "" {
		row += kbStyle.Render(cmd.Keybinding)
	}
	if cmd.Description != "" && active {
		descStyle := lipgloss.NewStyle().Foreground(p.theme.TextMuted)
		descLine := strings.Repeat(" ", lipgloss.Width(indicator)) + descStyle.Render(cmd.Description)
		return row + "\n" + descLine
	}
	return row
}

func (p Palette) renderTableRow(cmd Command, active bool) string {
	indicator := padDisplay("", tableIndicatorWidth)
	if active {
		indicator = padDisplay(
			lipgloss.NewStyle().Foreground(p.theme.Primary).Bold(true).Render("❯"),
			tableIndicatorWidth,
		)
	}

	textStyle := lipgloss.NewStyle().Foreground(p.theme.Text)
	statusStyle := lipgloss.NewStyle().Foreground(p.theme.TextMuted)
	dirStyle := lipgloss.NewStyle().Foreground(p.theme.TextMuted)
	if active {
		textStyle = textStyle.
			Bold(true).
			Foreground(p.theme.PrimaryStrong).
			Background(p.theme.SurfaceStrong)
		dirStyle = dirStyle.Foreground(p.theme.Text).Background(p.theme.SurfaceStrong)
		statusStyle = statusStyle.Background(p.theme.SurfaceStrong)
	}
	if cmd.Live {
		statusStyle = statusStyle.Foreground(p.theme.Success)
	} else {
		statusStyle = statusStyle.Foreground(p.theme.Warning)
	}

	statusPlain := cmd.Keybinding
	if statusPlain == "" {
		if cmd.Live {
			statusPlain = "● live"
		} else {
			statusPlain = "○ idle"
		}
	}
	if cmd.Live && p.table.SpinnerFrame != "" {
		statusPlain = p.table.SpinnerFrame + " " + statusPlain
	}
	statusPlain = padDisplay(statusPlain, p.table.StatusWidth)

	dir := cmd.Description
	if maxDir := p.maxDirWidth(); lipgloss.Width(dir) > maxDir && maxDir > 3 {
		dir = truncateDisplay(dir, maxDir)
	}

	return indicator + p.renderTableLine(
		textStyle.Render(padDisplay(cmd.Title, p.table.NameWidth)),
		statusStyle.Render(statusPlain),
		dirStyle.Render(dir),
	)
}

func (p Palette) renderTableLine(name, status, dir string) string {
	gap := strings.Repeat(" ", p.table.ColGap)
	return name + gap + status + gap + dir
}

func (p Palette) maxDirWidth() int {
	used := tableIndicatorWidth + p.table.NameWidth + p.table.ColGap +
		p.table.StatusWidth + p.table.ColGap
	avail := p.width - 8 - used
	if avail < 12 {
		return 12
	}
	return avail
}

func padDisplay(s string, width int) string {
	if width <= 0 {
		return s
	}
	w := lipgloss.Width(s)
	if w >= width {
		return s
	}
	return s + strings.Repeat(" ", width-w)
}

func truncateDisplay(s string, maxWidth int) string {
	if lipgloss.Width(s) <= maxWidth {
		return s
	}
	ellipsis := "…"
	for len(s) > 0 && lipgloss.Width(ellipsis+s) > maxWidth {
		s = s[1:]
	}
	return ellipsis + s
}
