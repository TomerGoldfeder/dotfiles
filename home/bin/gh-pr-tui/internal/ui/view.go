package ui

import (
	"fmt"
	"regexp"
	"strings"
	"unicode/utf8"

	"github.com/charmbracelet/lipgloss"
)

const (
	minWidth  = 80
	minHeight = 22
)

// dims splits the screen: header(1) + gap(1) + branches(3) + main + keybar(1).
func (m Model) dims() (sideW, leftW, mainH int) {
	sideW = max(30, min(44, m.width/3))
	leftW = m.width - sideW - 1
	mainH = m.height - 6
	return
}

func (m *Model) layout() {
	_, leftW, mainH := m.dims()
	inner := leftW - 4
	m.title.Width = max(10, inner-lipgloss.Width(m.title.Prompt)-len("256/256")-2)
	m.body.SetWidth(inner)
	m.body.SetHeight(max(1, mainH-3-2-1)) // minus title box, borders, tab row
}

func (m Model) View() string {
	if m.width < minWidth || m.height < minHeight {
		return sYellow.Render(fmt.Sprintf("Terminal too small: need %d×%d, have %d×%d", minWidth, minHeight, m.width, m.height))
	}
	sideW, leftW, mainH := m.dims()

	left := m.titleView(leftW) + "\n" + m.bodyView(leftW, mainH-3)
	right := m.sidebarView(sideW, mainH)
	out := strings.Join([]string{
		m.headerView(),
		"",
		m.branchesView(),
		lipgloss.JoinHorizontal(lipgloss.Top, left, " ", right),
		m.keybarView(),
	}, "\n")

	if m.picker != nil {
		pw := min(64, m.width-4)
		x := 2
		if m.pickerFor >= pickAssignees {
			x = max(1, leftW-pw+6) // float left of the sidebar so selections stay visible
		}
		out = overlay(out, m.picker.View(pw), x, 5)
	}
	return out
}

func (m Model) headerView() string {
	l := sBold.Render("Open a pull request") + "  " + sMuted.Render(m.opts.Repo.FullName())
	var badge string
	if m.draft {
		badge = sMuted.Render("◌ Draft")
	} else {
		badge = sGreen.Render("● Ready for review")
	}
	return spread(" "+l, badge+" ", m.width)
}

func (m Model) branchChip(name string, side int) string {
	st := lipgloss.NewStyle().Background(cChipBg).Foreground(cText)
	if side == sideHead {
		st = st.Foreground(cBlue)
	}
	if m.focus == fBranches && m.branchSide == side {
		st = lipgloss.NewStyle().Background(cAccent).Foreground(lipgloss.Color("#0d1117")).Bold(true)
	}
	if name == "" {
		name = "select…"
	}
	return st.Render(" " + name + " ▾ ")
}

func (m Model) branchesView() string {
	l := sMuted.Render("base ") + m.branchChip(m.base, sideBase) +
		sMuted.Render("  ←  ") +
		sMuted.Render("feature ") + m.branchChip(m.head, sideHead)

	var r string
	switch {
	case m.base == m.head:
		r = sRed.Render("✗ base and feature are the same branch")
	case m.diff == nil:
		r = sDim.Render("comparing…")
	case m.diff.Commits == 0:
		r = sYellow.Render("nothing to compare")
	default:
		d := m.diff
		r = sMuted.Render(fmt.Sprintf("↑ %d %s · %d %s ", d.Commits, plural(d.Commits, "commit"), d.Files, plural(d.Files, "file"))) +
			sGreen.Render(fmt.Sprintf("+%d", d.Additions)) + " " + sRed.Render(fmt.Sprintf("−%d", d.Deletions))
	}
	if m.needsPush && m.base != m.head {
		r += sYellow.Render(" · will push")
	}
	return box("Branches", "[b]", []string{spread(l, r, m.width-4)}, m.width, 3, m.focus == fBranches)
}

func (m Model) titleView(w int) string {
	n := utf8.RuneCountInString(m.title.Value())
	counter := sDim.Render(fmt.Sprintf("%d/256", n))
	if n == 0 {
		counter = sRed.Render("required")
	}
	return box("Title", "[t]", []string{spread(m.title.View(), counter, w-4)}, w, 3, m.focus == fTitle)
}

func (m Model) bodyView(w, h int) string {
	inner := w - 4
	on := lipgloss.NewStyle().Foreground(cText).Bold(true).Underline(true)
	off := sMuted
	write, prev := on.Render("Write"), off.Render("Preview")
	if m.preview {
		write, prev = off.Render("Write"), on.Render("Preview")
	}
	tabs := spread(write+"  "+prev, sDim.Render("ctrl+p preview · ctrl+o $EDITOR"), inner)

	rows := h - 3
	var content []string
	if m.preview {
		md := renderMarkdown(m.body.Value(), inner)
		top := min(m.previewTop, max(0, len(md)-rows))
		content = md[top:min(len(md), top+rows)]
		if len(md) == 0 {
			content = []string{sDim.Render("Nothing to preview")}
		}
	} else {
		content = strings.Split(m.body.View(), "\n")
	}
	return box("Body", "[e]", append([]string{tabs}, content...), w, h, m.focus == fBody)
}

func (m Model) peopleLines(list []string, inner int, empty string) []string {
	if len(list) == 0 {
		return []string{sDim.Render(empty)}
	}
	const maxShown = 4
	var out []string
	for i, u := range list {
		if i == maxShown {
			out = append(out, sDim.Render(fmt.Sprintf("+%d more", len(list)-maxShown)))
			break
		}
		team := strings.Contains(u, "/")
		suffix := ""
		switch {
		case team:
			suffix = sMuted.Render("team")
		case u == m.viewer:
			suffix = sMuted.Render("you")
		}
		out = append(out, spread(avatar(u, team)+" "+sText.Render("@"+u), suffix, inner))
	}
	return out
}

func (m Model) labelLines(inner int) []string {
	if len(m.labels) == 0 {
		return []string{sDim.Render("None yet")}
	}
	colors := map[string]string{}
	for _, l := range m.labelDefs {
		colors[l.Name] = l.Color
	}
	var lines []string
	cur := ""
	for _, name := range m.labels {
		chip := labelChip(name, colors[name])
		switch {
		case cur == "":
			cur = chip
		case lipgloss.Width(cur)+1+lipgloss.Width(chip) <= inner:
			cur += " " + chip
		default:
			lines = append(lines, cur)
			cur = chip
		}
	}
	return append(lines, cur)
}

func (m Model) sidebarView(w, h int) string {
	inner := w - 4
	check := sMuted.Render("[ ]")
	if m.draft {
		check = sGreen.Bold(true).Render("[x]")
	}
	note := strings.Split(sMuted.Width(inner).Render("Reviewers aren't notified until it's marked ready."), "\n")

	blocks := []string{
		box("Assignees", "[a]", m.peopleLines(m.assignees, inner, "No one — enter to add"), w, 0, m.focus == fAssignees),
		box("Reviewers", "[r]", m.peopleLines(m.reviewers, inner, "None — enter to request"), w, 0, m.focus == fReviewers),
		box("Labels", "[l]", m.labelLines(inner), w, 0, m.focus == fLabels),
		box("Draft", "[d]", append([]string{check + " " + sText.Render("Open as draft")}, note...), w, 0, m.focus == fDraft),
	}
	lines := strings.Split(strings.Join(blocks, "\n"), "\n")

	// Buttons pinned to the bottom of the column.
	label := "Create pull request"
	if m.draft {
		label = "Create draft pull request"
	}
	if m.submitting {
		label = m.spin.View() + " Creating…"
	}
	create := lipgloss.NewStyle().Background(cBtnBg).Foreground(lipgloss.Color("#ffffff")).Bold(true)
	cancel := lipgloss.NewStyle().Background(cChipBg).Foreground(cText)
	cp, xp := "  ", "  "
	if m.focus == fCreate {
		create, cp = create.Background(cBtnHi), "▸ "
	}
	if m.focus == fCancel {
		cancel, xp = cancel.Background(cAccent).Foreground(lipgloss.Color("#0d1117")), "▸ "
	}
	buttons := []string{
		create.Render(spread(cp+label, "ctrl+s ", w)),
		"",
		cancel.Render(spread(xp+"Cancel", "esc ", w)),
	}

	room := h - len(buttons)
	if len(lines) > room {
		lines = lines[:max(0, room)]
	}
	for len(lines) < room {
		lines = append(lines, "")
	}
	for i := range lines {
		lines[i] = fit(lines[i], w)
	}
	return strings.Join(append(lines, buttons...), "\n")
}

func (m Model) keybarView() string {
	type kv struct{ k, v string }
	var keys []kv
	switch {
	case m.picker != nil && m.picker.multi:
		keys = []kv{{"↑↓", "move"}, {"space", "toggle"}, {"enter", "done"}, {"esc", "cancel"}}
	case m.picker != nil:
		keys = []kv{{"↑↓", "move"}, {"enter", "select"}, {"esc", "cancel"}}
	case m.focus == fTitle:
		keys = []kv{{"tab", "next"}, {"enter", "to body"}, {"ctrl+s", "create"}, {"esc", "quit"}}
	case m.focus == fBody:
		keys = []kv{{"tab", "next"}, {"ctrl+p", "preview"}, {"ctrl+o", "$EDITOR"}, {"ctrl+s", "create"}, {"esc", "quit"}}
	case m.focus == fBranches:
		keys = []kv{{"←→", "base/feature"}, {"enter", "pick"}, {"tab", "next"}, {"t e a r l", "jump"}, {"d", "draft"}, {"ctrl+s", "create"}, {"esc", "quit"}}
	default:
		keys = []kv{{"tab ↑↓", "move"}, {"enter", "pick"}, {"x", "clear"}, {"b t e a r l", "jump"}, {"d", "draft"}, {"ctrl+s", "create"}, {"esc", "quit"}}
	}
	var parts []string
	for _, p := range keys {
		ks := sKey
		if p.k == "ctrl+s" {
			ks = ks.Background(cBtnBg).Foreground(lipgloss.Color("#ffffff"))
		}
		parts = append(parts, ks.Render(p.k)+" "+sMuted.Render(p.v))
	}
	bar := " " + strings.Join(parts, "  ")
	if m.status != "" {
		st := sMuted
		if m.statusErr {
			st = sRed
		}
		s := m.status
		if m.submitting {
			s = m.spin.View() + " " + s
		}
		return fit(" "+st.Render(s)+"   "+strings.TrimLeft(bar, " "), m.width)
	}
	return fit(bar, m.width)
}

func plural(n int, s string) string {
	if n == 1 {
		return s
	}
	return s + "s"
}

// ---- minimal markdown preview -------------------------------------------------

var (
	reCode = regexp.MustCompile("`[^`]+`")
	reBold = regexp.MustCompile(`\*\*[^*]+\*\*`)
	reTask = regexp.MustCompile(`^(\s*)[-*] \[([ xX])\] (.*)$`)
	reList = regexp.MustCompile(`^(\s*)[-*+] (.*)$`)
	reHead = regexp.MustCompile(`^(#{1,6})\s+(.*)$`)
)

func inline(s string) string {
	s = reCode.ReplaceAllStringFunc(s, func(c string) string {
		return lipgloss.NewStyle().Foreground(cBlue).Render(strings.Trim(c, "`"))
	})
	return reBold.ReplaceAllStringFunc(s, func(b string) string {
		return lipgloss.NewStyle().Bold(true).Render(strings.Trim(b, "*"))
	})
}

func renderMarkdown(src string, w int) []string {
	if strings.TrimSpace(src) == "" {
		return nil
	}
	var out []string
	wrap := lipgloss.NewStyle().Width(w)
	inFence := false
	for _, ln := range strings.Split(src, "\n") {
		if strings.HasPrefix(strings.TrimSpace(ln), "```") {
			inFence = !inFence
			out = append(out, sDim.Render(strings.Repeat("─", min(w, 24))))
			continue
		}
		var r string
		switch {
		case inFence:
			r = sDim.Render("│ ") + lipgloss.NewStyle().Foreground(cBlue).Render(ln)
		case reHead.MatchString(ln):
			g := reHead.FindStringSubmatch(ln)
			r = lipgloss.NewStyle().Foreground(cPurple).Bold(true).Render(g[2])
		case reTask.MatchString(ln):
			g := reTask.FindStringSubmatch(ln)
			mark := sMuted.Render("[ ]")
			if g[2] != " " {
				mark = sGreen.Render("[x]")
			}
			r = g[1] + mark + " " + inline(g[3])
		case reList.MatchString(ln):
			g := reList.FindStringSubmatch(ln)
			r = g[1] + lipgloss.NewStyle().Foreground(cOrange).Render("•") + " " + inline(g[2])
		case strings.HasPrefix(ln, ">"):
			r = sDim.Render("▎ ") + sMuted.Render(strings.TrimSpace(strings.TrimPrefix(ln, ">")))
		default:
			r = inline(ln)
		}
		out = append(out, strings.Split(wrap.Render(r), "\n")...)
	}
	return out
}
