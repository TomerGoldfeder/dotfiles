// Package theme provides the token palette gpr views read from.
//
// Views reference Theme slots only — never raw hex literals.
package theme

import "github.com/charmbracelet/lipgloss"

// Theme is the token palette for the gpr TUI.
type Theme struct {
	Bg            lipgloss.Color
	Surface       lipgloss.Color
	SurfaceStrong lipgloss.Color
	Border        lipgloss.Color
	BorderStrong  lipgloss.Color
	Text          lipgloss.Color
	TextMuted     lipgloss.Color
	TextInverse   lipgloss.Color

	Primary       lipgloss.Color
	PrimaryStrong lipgloss.Color
	Accent        lipgloss.Color

	Success lipgloss.Color
	Warning lipgloss.Color
	Error   lipgloss.Color
	Info    lipgloss.Color
}
