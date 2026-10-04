package theme

import "github.com/charmbracelet/lipgloss"

// Default is the live gpr theme (Tokyo Night midnight).
var Default = TokyoNightMidnight

// TokyoNightMidnight is the near-black Tokyo Night palette.
// Hexes match folke/tokyonight.nvim darkest surfaces — not classic night #1a1b26.
var TokyoNightMidnight = Theme{
	Bg:            lipgloss.Color("#0C0E14"),
	Surface:       lipgloss.Color("#16161e"),
	SurfaceStrong: lipgloss.Color("#1f2335"),
	Border:        lipgloss.Color("#3b4261"),
	BorderStrong:  lipgloss.Color("#7aa2f7"),
	Text:          lipgloss.Color("#c0caf5"),
	TextMuted:     lipgloss.Color("#565f89"),
	TextInverse:   lipgloss.Color("#0C0E14"),

	Primary:       lipgloss.Color("#7aa2f7"),
	PrimaryStrong: lipgloss.Color("#89ddff"),
	Accent:        lipgloss.Color("#bb9af7"),

	Success: lipgloss.Color("#9ece6a"),
	Warning: lipgloss.Color("#e0af68"),
	Error:   lipgloss.Color("#f7768e"),
	Info:    lipgloss.Color("#7dcfff"),
}
