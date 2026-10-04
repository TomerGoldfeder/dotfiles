package ui

import (
	"fmt"
	"sort"
	"strings"
	"unicode"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
)

type item struct {
	value string
	desc  string // right-aligned, muted
	color string // label hex color; empty for non-labels
	team  bool
}

type pickResult int

const (
	pickOpen pickResult = iota
	pickDone
	pickCancel
)

// picker is a fuzzy finder overlay. Single mode: enter picks the row under
// the cursor. Multi mode: space toggles, enter confirms, esc reverts.
type picker struct {
	title  string
	items  []item
	multi  bool
	sel    map[string]bool
	query  textinput.Model
	cursor int
	shown  []int // indices into items, best match first
	rows   int   // visible rows
	offset int
}

func newPicker(title string, items []item, selected []string, multi bool) picker {
	q := textinput.New()
	q.Prompt = "> "
	q.PromptStyle = sAccent
	q.TextStyle = sText
	q.Placeholder = "type to filter"
	q.PlaceholderStyle = sDim
	q.Focus()
	p := picker{title: title, items: items, multi: multi, sel: map[string]bool{}, query: q, rows: 10}
	for _, s := range selected {
		p.sel[s] = true
	}
	p.filter()
	if !multi && len(selected) == 1 { // start on the current value
		for i, idx := range p.shown {
			if items[idx].value == selected[0] {
				p.cursor = i
			}
		}
	}
	p.clampScroll()
	return p
}

func (p *picker) filter() {
	q := strings.ToLower(strings.ReplaceAll(p.query.Value(), " ", ""))
	type scored struct{ idx, score int }
	var res []scored
	for i, it := range p.items {
		if s, ok := fuzzyScore(q, strings.ToLower(it.value)); ok {
			res = append(res, scored{i, s})
		}
	}
	sort.SliceStable(res, func(a, b int) bool { return res[a].score > res[b].score })
	p.shown = p.shown[:0]
	for _, r := range res {
		p.shown = append(p.shown, r.idx)
	}
	p.cursor, p.offset = 0, 0
}

// fuzzyScore matches q as a subsequence of s. Consecutive runs, word starts
// and prefix matches score higher.
func fuzzyScore(q, s string) (int, bool) {
	if q == "" {
		return 0, true
	}
	score, qi, run := 0, 0, 0
	qr, sr := []rune(q), []rune(s)
	for si := 0; si < len(sr) && qi < len(qr); si++ {
		if sr[si] != qr[qi] {
			run = 0
			continue
		}
		score++
		run++
		score += run * 2
		if si == 0 {
			score += 8
		} else if !unicode.IsLetter(sr[si-1]) && !unicode.IsDigit(sr[si-1]) {
			score += 4
		}
		qi++
	}
	if qi < len(qr) {
		return 0, false
	}
	return score*100 - len(sr), true
}

func (p *picker) clampScroll() {
	if p.cursor < p.offset {
		p.offset = p.cursor
	}
	if p.cursor >= p.offset+p.rows {
		p.offset = p.cursor - p.rows + 1
	}
}

func (p *picker) current() (item, bool) {
	if p.cursor < 0 || p.cursor >= len(p.shown) {
		return item{}, false
	}
	return p.items[p.shown[p.cursor]], true
}

// Selected returns the selection in list order.
func (p *picker) Selected() []string {
	var out []string
	for _, it := range p.items {
		if p.sel[it.value] {
			out = append(out, it.value)
		}
	}
	return out
}

func (p *picker) Update(msg tea.KeyMsg) (pickResult, tea.Cmd) {
	switch msg.String() {
	case "esc":
		return pickCancel, nil
	case "enter":
		if !p.multi {
			it, ok := p.current()
			if !ok {
				return pickOpen, nil
			}
			p.sel = map[string]bool{it.value: true}
		}
		return pickDone, nil
	case "up", "ctrl+p", "ctrl+k":
		if p.cursor > 0 {
			p.cursor--
		}
		p.clampScroll()
		return pickOpen, nil
	case "down", "ctrl+n", "ctrl+j":
		if p.cursor < len(p.shown)-1 {
			p.cursor++
		}
		p.clampScroll()
		return pickOpen, nil
	case " ", "tab":
		if p.multi {
			if it, ok := p.current(); ok {
				p.sel[it.value] = !p.sel[it.value]
				if !p.sel[it.value] {
					delete(p.sel, it.value)
				}
			}
		}
		return pickOpen, nil
	}
	before := p.query.Value()
	var cmd tea.Cmd
	p.query, cmd = p.query.Update(msg)
	if p.query.Value() != before {
		p.filter()
	}
	return pickOpen, cmd
}

func (p *picker) View(w int) string {
	inner := w - 4
	count := fmt.Sprintf("%d/%d", len(p.shown), len(p.items))
	if p.multi && len(p.sel) > 0 {
		count = fmt.Sprintf("%d selected · %s", len(p.sel), count)
	}
	p.query.Width = inner - 3
	lines := []string{p.query.View(), sDim.Render(strings.Repeat("─", inner))}

	if len(p.shown) == 0 {
		lines = append(lines, sDim.Render("  no matches"))
	}
	end := min(p.offset+p.rows, len(p.shown))
	for i := p.offset; i < end; i++ {
		it := p.items[p.shown[i]]
		cur := i == p.cursor
		mark := "  "
		if cur {
			mark = sAccent.Render("▸ ")
		}
		chk := "  "
		if p.multi {
			if p.sel[it.value] {
				chk = sGreen.Bold(true).Render("[x]") + " "
			} else {
				chk = sMuted.Render("[ ]") + " "
			}
		} else if p.sel[it.value] {
			chk = sGreen.Render("✓") + " "
		}
		name := it.value
		if it.color != "" {
			name = labelDot(it.color) + " " + name
		}
		ns := sText
		if cur {
			ns = sBold
		}
		lines = append(lines, spread(mark+chk+ns.Render(name), sMuted.Render(it.desc), inner))
	}
	if end < len(p.shown) {
		lines = append(lines, sDim.Render(fmt.Sprintf("  … %d more", len(p.shown)-end)))
	}
	return box(p.title, count, lines, w, 0, true)
}
