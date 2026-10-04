package commandpalette

import (
	"sort"
	"strings"
)

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
