package commandpalette

import (
	"strconv"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// View renders the palette as a bordered card with a real statusline.
func (p Palette) View() string {
	innerWidth := p.width - 4
	if innerWidth < 20 {
		innerWidth = 20
	}

	parts := []string{}
	if p.title != "" {
		parts = append(parts, p.renderTitle(innerWidth))
	}
	parts = append(parts, p.renderFilter(innerWidth))

	matches := p.matches()
	if p.table.Enabled {
		parts = append(parts, p.renderTableHeader())
	}
	parts = append(parts, p.renderBody(matches, innerWidth))
	parts = append(parts, p.renderStatusline(matches, innerWidth))

	card := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(p.theme.BorderStrong).
		Background(p.theme.Surface).
		Padding(1, 2).
		Width(p.width)

	return card.Render(strings.Join(parts, "\n"))
}

func (p Palette) renderTitle(innerWidth int) string {
	icon := lipgloss.NewStyle().Foreground(p.theme.Accent).Bold(true).Render("󰣇")
	label := lipgloss.NewStyle().
		Foreground(p.theme.PrimaryStrong).
		Bold(true).
		Render("  " + p.title)
	badge := lipgloss.NewStyle().
		Foreground(p.theme.TextInverse).
		Background(p.theme.Primary).
		Padding(0, 1).
		Bold(true).
		Render("SESSION")
	left := icon + label
	gap := innerWidth - lipgloss.Width(left) - lipgloss.Width(badge)
	if gap < 1 {
		gap = 1
	}
	return left + strings.Repeat(" ", gap) + badge
}

func (p Palette) renderFilter(innerWidth int) string {
	inputStyle := lipgloss.NewStyle().
		Border(lipgloss.NormalBorder(), false, false, true, false).
		BorderForeground(p.theme.Border).
		Width(innerWidth).
		PaddingBottom(0)

	prompt := lipgloss.NewStyle().
		Foreground(p.theme.Primary).
		Bold(true).
		Render("󰍉 ")

	filterText := p.filter
	if filterText == "" {
		filterText = lipgloss.NewStyle().
			Foreground(p.theme.TextMuted).
			Italic(true).
			Render(p.placeholder)
	} else {
		filterText = lipgloss.NewStyle().Foreground(p.theme.Text).Render(filterText)
	}
	cursor := lipgloss.NewStyle().
		Background(p.theme.Primary).
		Foreground(p.theme.TextInverse).
		Render(" ")

	return inputStyle.Render(prompt + filterText + cursor)
}

func (p Palette) renderTableHeader() string {
	headerStyle := lipgloss.NewStyle().
		Foreground(p.theme.TextMuted).
		Bold(true)
	return headerStyle.Render(
		padDisplay("", tableIndicatorWidth) + p.renderTableLine(
			padDisplay(p.table.NameHeader, p.table.NameWidth),
			padDisplay(p.table.StatusHeader, p.table.StatusWidth),
			p.table.DirHeader,
		),
	)
}

func (p Palette) renderBody(matches []Command, innerWidth int) string {
	bodyHeight := p.height
	if bodyHeight < 1 {
		bodyHeight = 1
	}

	var bodyLines []string
	if len(matches) == 0 {
		empty := lipgloss.NewStyle().
			Foreground(p.theme.Warning).
			Italic(true).
			Width(innerWidth).
			Align(lipgloss.Center).
			Render("󰛨  No sessions match this filter")
		bodyLines = []string{empty}
	} else {
		start, end := p.windowBounds(len(matches))
		var lastGroup string
		for i := start; i < end; i++ {
			cmd := matches[i]
			if !p.table.Enabled && cmd.Group != "" && cmd.Group != lastGroup {
				groupStyle := lipgloss.NewStyle().
					Foreground(p.theme.Accent).
					Bold(true).
					PaddingLeft(1)
				bodyLines = append(bodyLines, groupStyle.Render("󰉋  "+strings.ToUpper(cmd.Group)))
				lastGroup = cmd.Group
			}
			bodyLines = append(bodyLines, p.renderRow(cmd, i == p.cursor))
		}
		for len(bodyLines) < bodyHeight {
			bodyLines = append(bodyLines, "")
		}
		if len(bodyLines) > bodyHeight {
			bodyLines = bodyLines[:bodyHeight]
		}
	}
	return strings.Join(bodyLines, "\n")
}

func (p Palette) renderStatusline(matches []Command, innerWidth int) string {
	modeLabel := "BROWSE"
	modeColor := p.theme.Info
	if p.filter != "" {
		modeLabel = "FILTER"
		modeColor = p.theme.Accent
	}

	mode := lipgloss.NewStyle().
		Foreground(p.theme.TextInverse).
		Background(modeColor).
		Bold(true).
		Padding(0, 1).
		Render(modeLabel)

	countText := lipgloss.NewStyle().
		Foreground(p.theme.PrimaryStrong).
		Bold(true).
		Render(formatCount(len(matches), len(p.commands)))

	keys := lipgloss.NewStyle().
		Foreground(p.theme.TextMuted).
		Render("↑↓ enter·esc  ⌃u clear")

	contentWidth := innerWidth - 2
	if contentWidth < 10 {
		contentWidth = 10
	}
	left := mode + "  " + countText
	gap := contentWidth - lipgloss.Width(left) - lipgloss.Width(keys)
	if gap < 1 {
		gap = 1
	}
	row := " " + left + strings.Repeat(" ", gap) + keys + " "

	return lipgloss.NewStyle().
		Background(p.theme.SurfaceStrong).
		Width(innerWidth).
		MarginTop(1).
		Render(row)
}

func formatCount(matched, total int) string {
	if matched == total {
		return "󰲠 " + strconv.Itoa(matched) + " sessions"
	}
	return "󰲠 " + strconv.Itoa(matched) + "/" + strconv.Itoa(total) + " matches"
}
