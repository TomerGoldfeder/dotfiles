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
	tea "github.com/charmbracelet/bubbletea"

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
