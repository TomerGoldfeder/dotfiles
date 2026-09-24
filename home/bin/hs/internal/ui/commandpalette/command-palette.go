// Package commandpalette renders a fuzzy-filtered command picker as a modal
// surface. Consumers supply a list of commands, render the View, route key
// events through Update, and observe SelectMsg / CancelMsg.
//
// The default matcher is case-insensitive substring on Title (and on Group
// when present). Replace the matcher by setting a function via WithMatcher
// — the function returns a non-zero score to keep a command, zero to drop.
// Higher scores rank earlier.
package commandpalette

import (
	"sort"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"hs/internal/ui/theme"
)

// Command is one row the user can select.
type Command struct {
	ID          string // stable identifier returned in SelectMsg
	Title       string // primary label rendered on the row
	Description string // optional secondary label rendered under Title
	Group       string // optional grouping label rendered as a section header
	Keybinding  string // optional shortcut hint rendered right-aligned
	Live        bool   // table mode: animate status with SpinnerFrame
}

// SelectMsg is emitted when the user presses Enter on a non-empty match list.
type SelectMsg struct {
	Command Command
}

// CancelMsg is emitted when the user presses Esc.
type CancelMsg struct{}

// Matcher returns a score for cmd against query. Zero score drops cmd from
// the result list. Higher scores sort earlier. The default matcher does a
// case-insensitive substring match on Title and Group.
type Matcher func(cmd Command, query string) int

// TableLayout renders rows as fixed-width columns on a single line.
// Title, Keybinding, and Description map to the first three columns.
type TableLayout struct {
	Enabled      bool
	NameHeader   string
	StatusHeader string
	DirHeader    string
	NameWidth    int
	StatusWidth  int
	ColGap       int
	SpinnerFrame string
}

const tableIndicatorWidth = 2

// Palette is a Bubble Tea model for a filterable command picker.
type Palette struct {
	theme       theme.Theme
	commands    []Command
	filter      string
	cursor      int
	width       int
	height      int
	title       string
	placeholder string
	matcher     Matcher
	table       TableLayout
}

// New constructs a Palette with the default substring matcher. No commands
// are loaded; call WithCommands.
func New(t theme.Theme) Palette {
	return Palette{
		theme:       t,
		width:       60,
		height:      10,
		title:       "Commands",
		placeholder: "Type to filter…",
		matcher:     SubstringMatcher,
	}
}

// WithCommands sets the command list. Cursor resets to 0.
func (p Palette) WithCommands(cmds []Command) Palette {
	p.commands = append([]Command(nil), cmds...)
	p.cursor = 0
	return p
}

// WithFilter presets the filter text.
func (p Palette) WithFilter(s string) Palette {
	p.filter = s
	p.cursor = 0
	return p
}

// WithSize sets the rendered width and visible-row height.
func (p Palette) WithSize(w, h int) Palette {
	if w < 20 {
		w = 20
	}
	if h < 3 {
		h = 3
	}
	p.width = w
	p.height = h
	return p
}

// WithTitle sets the title rendered above the filter input.
func (p Palette) WithTitle(s string) Palette { p.title = s; return p }

// WithPlaceholder sets the filter input placeholder.
func (p Palette) WithPlaceholder(s string) Palette { p.placeholder = s; return p }

// WithMatcher replaces the scoring function. Pass nil to restore the default.
func (p Palette) WithMatcher(m Matcher) Palette {
	if m == nil {
		m = SubstringMatcher
	}
	p.matcher = m
	return p
}

// WithTableLayout enables single-line column rendering for session-style lists.
func (p Palette) WithTableLayout(t TableLayout) Palette {
	if t.ColGap <= 0 {
		t.ColGap = 2
	}
	p.table = t
	return p
}

// WithSpinnerFrame sets the animated glyph prefix for live status cells.
func (p Palette) WithSpinnerFrame(frame string) Palette {
	p.table.SpinnerFrame = frame
	return p
}

// Filter returns the current filter text.
func (p Palette) Filter() string { return p.filter }

// Cursor returns the index into the filtered list, not into the source list.
func (p Palette) Cursor() int { return p.cursor }

// Init implements tea.Model.
func (p Palette) Init() tea.Cmd { return nil }

// Update handles key events: filter typing, arrow navigation, Enter, Esc.
func (p Palette) Update(msg tea.Msg) (Palette, tea.Cmd) {
	key, ok := msg.(tea.KeyMsg)
	if !ok {
		return p, nil
	}
	switch key.Type {
	case tea.KeyEsc:
		return p, func() tea.Msg { return CancelMsg{} }
	case tea.KeyEnter:
		matches := p.matches()
		if len(matches) == 0 {
			return p, nil
		}
		picked := matches[p.cursor]
		return p, func() tea.Msg { return SelectMsg{Command: picked} }
	case tea.KeyUp, tea.KeyCtrlP:
		p.cursor--
		if p.cursor < 0 {
			p.cursor = 0
		}
		return p, nil
	case tea.KeyDown, tea.KeyCtrlN:
		matches := p.matches()
		p.cursor++
		if p.cursor >= len(matches) {
			p.cursor = len(matches) - 1
		}
		if p.cursor < 0 {
			p.cursor = 0
		}
		return p, nil
	case tea.KeyBackspace:
		if len(p.filter) > 0 {
			r := []rune(p.filter)
			p.filter = string(r[:len(r)-1])
			p.cursor = 0
		}
		return p, nil
	case tea.KeyCtrlU:
		p.filter = ""
		p.cursor = 0
		return p, nil
	case tea.KeySpace:
		p.filter += " "
		p.cursor = 0
		return p, nil
	case tea.KeyRunes:
		p.filter += string(key.Runes)
		p.cursor = 0
		return p, nil
	}
	return p, nil
}

// View renders the palette as a bordered card.
func (p Palette) View() string {
	titleStyle := lipgloss.NewStyle().
		Foreground(p.theme.TextMuted).
		Bold(true).
		MarginBottom(1)

	inputStyle := lipgloss.NewStyle().
		Border(lipgloss.NormalBorder(), false, false, true, false).
		BorderForeground(p.theme.Border).
		Width(p.width - 4).
		PaddingBottom(0)

	promptStyle := lipgloss.NewStyle().Foreground(p.theme.Primary).Bold(true)
	prompt := promptStyle.Render("› ")

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
		Background(p.theme.Text).
		Foreground(p.theme.Bg).
		Render(" ")

	inputRow := inputStyle.Render(prompt + filterText + cursor)

	var headerRow string
	if p.table.Enabled {
		headerStyle := lipgloss.NewStyle().
			Foreground(p.theme.TextMuted).
			Bold(true)
		headerRow = headerStyle.Render(
			padDisplay("", tableIndicatorWidth) + p.renderTableLine(
				padDisplay(p.table.NameHeader, p.table.NameWidth),
				padDisplay(p.table.StatusHeader, p.table.StatusWidth),
				p.table.DirHeader,
			),
		)
	}

	matches := p.matches()
	bodyHeight := p.height
	if bodyHeight < 1 {
		bodyHeight = 1
	}

	var bodyLines []string
	if len(matches) == 0 {
		empty := lipgloss.NewStyle().
			Foreground(p.theme.TextMuted).
			Italic(true).
			Width(p.width - 4).
			Align(lipgloss.Center).
			Render("No commands match.")
		bodyLines = []string{empty}
	} else {
		start, end := p.windowBounds(len(matches))
		var lastGroup string
		for i := start; i < end; i++ {
			cmd := matches[i]
			if !p.table.Enabled && cmd.Group != "" && cmd.Group != lastGroup {
				groupStyle := lipgloss.NewStyle().
					Foreground(p.theme.TextMuted).
					Bold(true).
					PaddingLeft(1)
				bodyLines = append(bodyLines, groupStyle.Render(strings.ToUpper(cmd.Group)))
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

	hintStyle := lipgloss.NewStyle().
		Foreground(p.theme.TextMuted).
		MarginTop(1)
	hint := hintStyle.Render("↑↓ navigate · enter select · esc cancel")

	parts := []string{}
	if p.title != "" {
		parts = append(parts, titleStyle.Render(p.title))
	}
	parts = append(parts, inputRow)
	if headerRow != "" {
		parts = append(parts, headerRow)
	}
	parts = append(parts, strings.Join(bodyLines, "\n"))
	parts = append(parts, hint)

	card := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(p.theme.BorderStrong).
		Background(p.theme.Surface).
		Padding(1, 2).
		Width(p.width)

	return card.Render(strings.Join(parts, "\n"))
}

// matches scores p.commands against p.filter, drops zero-score rows, and
// returns the survivors in descending-score order. Stable sort.
func (p Palette) matches() []Command {
	if p.matcher == nil {
		p.matcher = SubstringMatcher
	}
	type scored struct {
		cmd   Command
		score int
		idx   int
	}
	out := make([]scored, 0, len(p.commands))
	for i, c := range p.commands {
		s := p.matcher(c, p.filter)
		if s == 0 {
			continue
		}
		out = append(out, scored{cmd: c, score: s, idx: i})
	}
	sort.SliceStable(out, func(i, j int) bool {
		if out[i].score != out[j].score {
			return out[i].score > out[j].score
		}
		return out[i].idx < out[j].idx
	})
	cmds := make([]Command, len(out))
	for i, s := range out {
		cmds[i] = s.cmd
	}
	return cmds
}

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
		indicator = lipgloss.NewStyle().Foreground(p.theme.Primary).Render("▍ ")
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
			lipgloss.NewStyle().Foreground(p.theme.Primary).Render("▍"),
			tableIndicatorWidth,
		)
	}

	textStyle := lipgloss.NewStyle().Foreground(p.theme.Text)
	statusStyle := lipgloss.NewStyle().Foreground(p.theme.TextMuted)
	dirStyle := lipgloss.NewStyle().Foreground(p.theme.TextMuted)
	if active {
		textStyle = textStyle.Bold(true).Foreground(p.theme.PrimaryStrong)
		dirStyle = dirStyle.Foreground(p.theme.Text)
	}
	if cmd.Live {
		statusStyle = statusStyle.Foreground(p.theme.Success)
	}

	statusPlain := padDisplay("  stopped", p.table.StatusWidth)
	if cmd.Live {
		statusPlain = padDisplay(p.table.SpinnerFrame+" running", p.table.StatusWidth)
	}

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

// windowBounds returns the [start, end) slice indices into matches that
// should be visible given the cursor position and available height.
func (p Palette) windowBounds(total int) (int, int) {
	if total <= p.height {
		return 0, total
	}
	half := p.height / 2
	start := p.cursor - half
	if start < 0 {
		start = 0
	}
	end := start + p.height
	if end > total {
		end = total
		start = end - p.height
		if start < 0 {
			start = 0
		}
	}
	return start, end
}

// SubstringMatcher is the default matcher. Case-insensitive substring match on
// Title and Group. Returns 100 when query is empty (every command passes),
// or the inverse position of the match (higher = earlier in the string).
func SubstringMatcher(cmd Command, query string) int {
	if query == "" {
		return 100
	}
	q := strings.ToLower(query)
	t := strings.ToLower(cmd.Title)
	g := strings.ToLower(cmd.Group)
	if i := strings.Index(t, q); i >= 0 {
		return 1000 - i
	}
	if i := strings.Index(g, q); i >= 0 {
		return 500 - i
	}
	return 0
}
