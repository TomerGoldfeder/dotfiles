package ui

import (
	"hash/fnv"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/x/ansi"
)

// Palette: GitHub dark, same tokens as the design mockup.
var (
	cAccent = lipgloss.Color("#58a6ff")
	cBorder = lipgloss.Color("#30363d")
	cText   = lipgloss.Color("#e6edf3")
	cMuted  = lipgloss.Color("#8b949e")
	cDim    = lipgloss.Color("#6e7681")
	cGreen  = lipgloss.Color("#3fb950")
	cRed    = lipgloss.Color("#f85149")
	cPurple = lipgloss.Color("#d2a8ff")
	cOrange = lipgloss.Color("#ffa657")
	cBlue   = lipgloss.Color("#79c0ff")
	cYellow = lipgloss.Color("#d29922")
	cChipBg = lipgloss.Color("#21262d")
	cBtnBg  = lipgloss.Color("#238636")
	cBtnHi  = lipgloss.Color("#2ea043")
)

var (
	sText   = lipgloss.NewStyle().Foreground(cText)
	sBold   = lipgloss.NewStyle().Foreground(cText).Bold(true)
	sMuted  = lipgloss.NewStyle().Foreground(cMuted)
	sDim    = lipgloss.NewStyle().Foreground(cDim)
	sAccent = lipgloss.NewStyle().Foreground(cAccent)
	sGreen  = lipgloss.NewStyle().Foreground(cGreen)
	sRed    = lipgloss.NewStyle().Foreground(cRed)
	sYellow = lipgloss.NewStyle().Foreground(cYellow)
	sKey    = lipgloss.NewStyle().Foreground(cText).Background(cBorder).Padding(0, 1)
)

// box draws a rounded panel with its title on the top border and an optional
// key hint on the right, like lazygit:  ╭─ Title ───── [a] ─╮
// h is the total height including borders; h <= 0 sizes to the content.
func box(title, hint string, body []string, w, h int, focused bool) string {
	if w < 8 {
		w = 8
	}
	if h <= 0 {
		h = len(body) + 2
	}
	bc, tc := cBorder, cText
	if focused {
		bc, tc = cAccent, cAccent
	}
	bs := lipgloss.NewStyle().Foreground(bc)
	ts := lipgloss.NewStyle().Foreground(tc).Bold(true)

	left := bs.Render("╭─") + " " + ts.Render(title) + " "
	right := bs.Render("╮")
	if hint != "" {
		right = " " + sDim.Render(hint) + " " + bs.Render("─╮")
	}
	fill := w - lipgloss.Width(left) - lipgloss.Width(right)
	if fill < 0 {
		left = ansi.Truncate(left, w-lipgloss.Width(right)-1, "")
		fill = w - lipgloss.Width(left) - lipgloss.Width(right)
	}
	var b strings.Builder
	b.WriteString(left + bs.Render(strings.Repeat("─", max(fill, 0))) + right)

	inner := w - 4
	side := bs.Render("│")
	for i := 0; i < h-2; i++ {
		line := ""
		if i < len(body) {
			line = body[i]
		}
		b.WriteString("\n" + side + " " + fit(line, inner) + " " + side)
	}
	b.WriteString("\n" + bs.Render("╰"+strings.Repeat("─", w-2)+"╯"))
	return b.String()
}

// fit truncates or pads s (ANSI-aware) to exactly w cells.
func fit(s string, w int) string {
	if w <= 0 {
		return ""
	}
	if lipgloss.Width(s) > w {
		s = ansi.Truncate(s, w, "…")
	}
	if pad := w - lipgloss.Width(s); pad > 0 {
		s += strings.Repeat(" ", pad)
	}
	return s
}

// spread puts l on the left and r on the right of a w-wide line.
func spread(l, r string, w int) string {
	gap := w - lipgloss.Width(l) - lipgloss.Width(r)
	if gap < 1 {
		return fit(l, w)
	}
	return l + strings.Repeat(" ", gap) + r
}

var avatarBgs = []lipgloss.Color{"#1f6feb", "#8957e5", "#bf4b8a", "#9e6a03", "#1a7f37", "#0969da", "#bc4c00"}

// avatar renders two-letter initials on a stable per-login color.
func avatar(login string, team bool) string {
	parts := strings.FieldsFunc(login[strings.LastIndex(login, "/")+1:], func(r rune) bool {
		return r == '-' || r == '_' || r == '.'
	})
	ini := ""
	switch {
	case len(parts) >= 2:
		ini = string([]rune(parts[0])[:1]) + string([]rune(parts[1])[:1])
	case len(parts) == 1 && len([]rune(parts[0])) >= 2:
		ini = string([]rune(parts[0])[:2])
	default:
		ini = login + " "
		ini = ini[:2]
	}
	bg := cBorder
	if !team {
		h := fnv.New32a()
		h.Write([]byte(login))
		bg = avatarBgs[int(h.Sum32())%len(avatarBgs)]
	}
	return lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#ffffff")).Background(bg).
		Render(strings.ToUpper(ini))
}

// labelChip renders a label on its GitHub color, picking a readable text color.
func labelChip(name, hex string) string {
	hex = strings.TrimPrefix(hex, "#")
	if len(hex) != 6 {
		return lipgloss.NewStyle().Foreground(cText).Background(cChipBg).Padding(0, 1).Render(name)
	}
	fg := lipgloss.Color("#ffffff")
	if luminance(hex) > 0.55 {
		fg = lipgloss.Color("#0d1117")
	}
	return lipgloss.NewStyle().Foreground(fg).Background(lipgloss.Color("#"+hex)).Padding(0, 1).Render(name)
}

func labelDot(hex string) string {
	hex = strings.TrimPrefix(hex, "#")
	if len(hex) != 6 {
		return sDim.Render("●")
	}
	return lipgloss.NewStyle().Foreground(lipgloss.Color("#" + hex)).Render("●")
}

func luminance(hex string) float64 {
	var rgb [3]float64
	for i := 0; i < 3; i++ {
		var v int
		for _, c := range hex[i*2 : i*2+2] {
			v *= 16
			switch {
			case c >= '0' && c <= '9':
				v += int(c - '0')
			case c >= 'a' && c <= 'f':
				v += int(c-'a') + 10
			case c >= 'A' && c <= 'F':
				v += int(c-'A') + 10
			}
		}
		rgb[i] = float64(v) / 255
	}
	return 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
}

// overlay draws fg on top of bg with its top-left corner at (x, y).
func overlay(bg, fg string, x, y int) string {
	bgLines := strings.Split(bg, "\n")
	for i, fl := range strings.Split(fg, "\n") {
		row := y + i
		if row < 0 || row >= len(bgLines) {
			continue
		}
		l := bgLines[row]
		left := ansi.Truncate(l, x, "")
		if pad := x - lipgloss.Width(left); pad > 0 {
			left += strings.Repeat(" ", pad)
		}
		right := ansi.TruncateLeft(l, x+lipgloss.Width(fl), "")
		bgLines[row] = left + "\x1b[0m" + fl + "\x1b[0m" + right
	}
	return strings.Join(bgLines, "\n")
}
