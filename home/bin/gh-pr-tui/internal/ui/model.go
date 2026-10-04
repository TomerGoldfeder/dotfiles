// Package ui is the Bubble Tea front end: one screen laid out like GitHub's
// "Open a pull request" page, plus a fuzzy picker overlay.
package ui

import (
	"context"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textarea"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"

	"github.com/tomer/gh-pr-tui/internal/gh"
)

type focus int

// Tab order follows the screen: branches, title, body, then the sidebar.
const (
	fBranches focus = iota
	fTitle
	fBody
	fAssignees
	fReviewers
	fLabels
	fDraft
	fCreate
	fCancel
	numFocus
)

const (
	sideBase = 0
	sideHead = 1
)

// Options seed the form.
type Options struct {
	Repo   gh.Repo
	Base   string
	Head   string
	Title  string
	Body   string
	Draft  bool
	DryRun bool // collect the spec and quit without pushing or creating
}

// Result is what the program hands back to main.
type Result struct {
	URL       string
	Spec      gh.PRSpec
	DryRun    bool
	Cancelled bool
}

type Model struct {
	client gh.Client
	opts   Options

	base, head string
	title      textinput.Model
	body       textarea.Model
	preview    bool
	previewTop int
	assignees  []string
	reviewers  []string
	labels     []string
	draft      bool

	focus      focus
	branchSide int

	picker    *picker
	pickerFor pickTarget

	// data loaded in the background
	listsLoaded    bool
	localBranches  []string
	remoteBranches []string
	users, teams   []string
	labelDefs      []gh.Label
	viewer         string
	diff           *gh.Diffstat
	needsPush      bool

	status      string
	statusErr   bool
	submitting  bool
	spin        spinner.Model
	confirmQuit bool

	initTitle, initBody string
	width, height       int
	result              Result
}

type pickTarget int

const (
	pickBase pickTarget = iota
	pickHead
	pickAssignees
	pickReviewers
	pickLabels
)

func New(client gh.Client, o Options) Model {
	ti := textinput.New()
	ti.Prompt = "› "
	ti.PromptStyle = sAccent
	ti.TextStyle = sBold
	ti.Placeholder = "Title"
	ti.PlaceholderStyle = sDim
	ti.CharLimit = 256
	ti.SetValue(o.Title)

	ta := textarea.New()
	ta.Prompt = ""
	ta.ShowLineNumbers = true
	ta.MaxHeight = 0
	ta.CharLimit = 0
	ta.Placeholder = "Describe your changes (markdown)"
	fs, bs := textarea.DefaultStyles()
	for _, s := range []*textarea.Style{&fs, &bs} {
		s.CursorLine = sText
		s.Text = sText
		s.LineNumber = sDim
		s.CursorLineNumber = sMuted
		s.Placeholder = sDim
		s.EndOfBuffer = sDim
	}
	ta.FocusedStyle, ta.BlurredStyle = fs, bs
	ta.SetValue(o.Body)
	ta.KeyMap.LinePrevious.SetKeys("up") // ctrl+p is ours (preview)
	ta.KeyMap.InputBegin.SetKeys("ctrl+home")
	ta.KeyMap.InputEnd.SetKeys("ctrl+end")

	sp := spinner.New()
	sp.Spinner = spinner.MiniDot
	sp.Style = sAccent

	m := Model{
		client: client, opts: o,
		base: o.Base, head: o.Head,
		title: ti, body: ta, draft: o.Draft,
		spin:      sp,
		initTitle: o.Title, initBody: o.Body,
		width: 120, height: 36,
	}
	m.setFocus(fTitle)
	m.layout()
	return m
}

// Result is valid after the program exits.
func (m Model) Result() Result { return m.result }

// ---- messages -------------------------------------------------------------

type listsMsg struct {
	local, remote, users, teams []string
	labels                      []gh.Label
	viewer                      string
	err                         error
}

type diffMsg struct {
	base, head string
	d          gh.Diffstat
	needsPush  bool
	err        error
}

type pushedMsg struct{ err error }
type createdMsg struct {
	url string
	err error
}
type editorMsg struct {
	path string
	err  error
}

func (m Model) Init() tea.Cmd {
	return tea.Batch(textinput.Blink, m.loadLists(), m.loadDiff())
}

func (m Model) loadLists() tea.Cmd {
	c, repo := m.client, m.opts.Repo
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		var msg listsMsg
		type res struct {
			v   []string
			err error
		}
		run := func(f func() ([]string, error)) chan res {
			ch := make(chan res, 1)
			go func() { v, err := f(); ch <- res{v, err} }()
			return ch
		}
		local := run(func() ([]string, error) { return c.LocalBranches(ctx) })
		remote := run(func() ([]string, error) { return c.RemoteBranches(ctx) })
		users := run(func() ([]string, error) { return c.Assignable(ctx, repo) })
		teams := run(func() ([]string, error) { return c.Teams(ctx, repo) })
		viewer := run(func() ([]string, error) { v, err := c.Viewer(ctx); return []string{v}, err })
		labelsCh := make(chan struct {
			v   []gh.Label
			err error
		}, 1)
		go func() {
			v, err := c.Labels(ctx)
			labelsCh <- struct {
				v   []gh.Label
				err error
			}{v, err}
		}()

		keep := func(r res) []string {
			if r.err != nil && msg.err == nil {
				msg.err = r.err
			}
			return r.v
		}
		msg.local = keep(<-local)
		msg.remote = keep(<-remote)
		msg.users = keep(<-users)
		msg.teams = (<-teams).v // personal repos have no teams: not an error
		if v := keep(<-viewer); len(v) > 0 {
			msg.viewer = v[0]
		}
		l := <-labelsCh
		msg.labels = l.v
		if l.err != nil && msg.err == nil {
			msg.err = l.err
		}
		return msg
	}
}

func (m Model) loadDiff() tea.Cmd {
	c, base, head := m.client, m.base, m.head
	if base == "" || head == "" {
		return nil
	}
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()
		d, err := c.Diffstat(ctx, base, head)
		np, _ := c.NeedsPush(ctx, head)
		return diffMsg{base: base, head: head, d: d, needsPush: np, err: err}
	}
}

// ---- update ---------------------------------------------------------------

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.layout()
		return m, nil

	case listsMsg:
		m.listsLoaded = true
		m.local(msg)
		if msg.err != nil {
			m.setStatus("some lists failed to load: "+firstLine(msg.err.Error()), true)
		}
		return m, nil

	case diffMsg:
		if msg.base == m.base && msg.head == m.head {
			if msg.err != nil {
				m.diff = nil
			} else {
				d := msg.d
				m.diff = &d
			}
			m.needsPush = msg.needsPush
		}
		return m, nil

	case spinner.TickMsg:
		if !m.submitting {
			return m, nil
		}
		var cmd tea.Cmd
		m.spin, cmd = m.spin.Update(msg)
		return m, cmd

	case pushedMsg:
		if msg.err != nil {
			m.submitting = false
			m.setStatus("push failed: "+firstLine(msg.err.Error()), true)
			return m, nil
		}
		m.needsPush = false
		m.setStatus("creating pull request…", false)
		return m, m.create()

	case createdMsg:
		m.submitting = false
		if msg.err != nil {
			m.setStatus(firstLine(msg.err.Error()), true)
			return m, nil
		}
		m.result = Result{URL: msg.url, Spec: m.Spec()}
		return m, tea.Quit

	case editorMsg:
		if msg.err != nil {
			m.setStatus("editor: "+msg.err.Error(), true)
		} else if b, err := os.ReadFile(msg.path); err == nil {
			m.body.SetValue(strings.TrimRight(string(b), "\n"))
		}
		os.Remove(msg.path)
		return m, nil

	case tea.KeyMsg:
		return m.handleKey(msg)
	}

	// Blink and other internal messages go to whichever input is focused.
	var cmd tea.Cmd
	switch m.focus {
	case fTitle:
		m.title, cmd = m.title.Update(msg)
	case fBody:
		m.body, cmd = m.body.Update(msg)
	}
	return m, cmd
}

func (m *Model) local(msg listsMsg) {
	m.localBranches, m.remoteBranches = msg.local, msg.remote
	m.users, m.teams, m.labelDefs, m.viewer = msg.users, msg.teams, msg.labels, msg.viewer
}

func (m Model) handleKey(k tea.KeyMsg) (tea.Model, tea.Cmd) {
	key := k.String()
	if key == "ctrl+c" {
		m.result = Result{Cancelled: true}
		return m, tea.Quit
	}
	if m.submitting {
		return m, nil
	}
	if m.confirmQuit {
		m.confirmQuit = false
		if key == "y" || key == "Y" {
			m.result = Result{Cancelled: true}
			return m, tea.Quit
		}
		m.setStatus("", false)
		return m, nil
	}
	if m.picker != nil {
		res, cmd := m.picker.Update(k)
		switch res {
		case pickDone:
			return m, m.applyPick()
		case pickCancel:
			m.picker = nil
		}
		return m, cmd
	}

	switch key {
	case "ctrl+s":
		return m.submit()
	case "tab":
		m.setFocus((m.focus + 1) % numFocus)
		return m, nil
	case "shift+tab":
		m.setFocus((m.focus + numFocus - 1) % numFocus)
		return m, nil
	case "esc":
		return m.quit()
	}

	switch m.focus {
	case fTitle:
		if key == "enter" || key == "down" {
			m.setFocus(fBody)
			return m, nil
		}
		var cmd tea.Cmd
		m.title, cmd = m.title.Update(k)
		return m, cmd
	case fBody:
		switch key {
		case "ctrl+p":
			m.preview = !m.preview
			m.previewTop = 0
			return m, nil
		case "ctrl+o":
			return m, m.openEditor()
		}
		if m.preview {
			switch key {
			case "up", "k":
				m.previewTop = max(0, m.previewTop-1)
			case "down", "j":
				m.previewTop++
			}
			return m, nil
		}
		var cmd tea.Cmd
		m.body, cmd = m.body.Update(k)
		return m, cmd
	}
	return m.navKey(key)
}

// navKey handles keys on the non-text panels, where letters are shortcuts.
func (m Model) navKey(key string) (tea.Model, tea.Cmd) {
	switch key {
	case "b":
		m.setFocus(fBranches)
	case "t":
		m.setFocus(fTitle)
	case "e":
		m.setFocus(fBody)
	case "a":
		m.setFocus(fAssignees)
	case "r":
		m.setFocus(fReviewers)
	case "l":
		m.setFocus(fLabels)
	case "d":
		m.draft = !m.draft
		m.setFocus(fDraft)
	case "q":
		return m.quit()
	case "up", "k":
		m.setFocus(m.focus - 1)
	case "down", "j":
		if m.focus < numFocus-1 {
			m.setFocus(m.focus + 1)
		}
	case "left":
		if m.focus == fBranches {
			m.branchSide = sideBase
		} else if m.focus == fCancel {
			m.setFocus(fCreate)
		}
	case "right":
		if m.focus == fBranches {
			m.branchSide = sideHead
		} else if m.focus == fCreate {
			m.setFocus(fCancel)
		}
	case "enter", " ":
		switch m.focus {
		case fBranches:
			if m.branchSide == sideBase {
				m.openPicker(pickBase)
			} else {
				m.openPicker(pickHead)
			}
		case fAssignees:
			m.openPicker(pickAssignees)
		case fReviewers:
			m.openPicker(pickReviewers)
		case fLabels:
			m.openPicker(pickLabels)
		case fDraft:
			m.draft = !m.draft
		case fCreate:
			return m.submit()
		case fCancel:
			return m.quit()
		}
	case "backspace", "x":
		switch m.focus { // clear a list quickly
		case fAssignees:
			m.assignees = nil
		case fReviewers:
			m.reviewers = nil
		case fLabels:
			m.labels = nil
		}
	}
	return m, nil
}

func (m *Model) setFocus(f focus) {
	if f < 0 {
		f = 0
	}
	m.focus = f
	m.title.Blur()
	m.body.Blur()
	switch f {
	case fTitle:
		m.title.Focus()
		m.title.CursorEnd()
	case fBody:
		m.body.Focus()
	}
}

func (m *Model) setStatus(s string, isErr bool) { m.status, m.statusErr = s, isErr }

func (m Model) dirty() bool {
	return m.title.Value() != m.initTitle || m.body.Value() != m.initBody ||
		len(m.assignees)+len(m.reviewers)+len(m.labels) > 0
}

func (m Model) quit() (tea.Model, tea.Cmd) {
	if m.dirty() {
		m.confirmQuit = true
		m.setStatus("Discard this pull request? y/N", true)
		return m, nil
	}
	m.result = Result{Cancelled: true}
	return m, tea.Quit
}

// ---- pickers ----------------------------------------------------------------

func (m *Model) openPicker(t pickTarget) {
	if !m.listsLoaded {
		m.setStatus("still loading from GitHub…", false)
		return
	}
	var (
		items []item
		sel   []string
		title string
		multi = true
	)
	switch t {
	case pickBase:
		title, multi, sel = "Base branch", false, []string{m.base}
		items = branchItems(m.remoteBranches, m.opts.Repo.DefaultBranch, "default")
	case pickHead:
		title, multi, sel = "Feature branch", false, []string{m.head}
		items = branchItems(m.localBranches, "", "")
	case pickAssignees:
		title, sel = "Assignees", m.assignees
		if m.viewer != "" {
			items = append(items, item{value: m.viewer, desc: "you"})
		}
		for _, u := range m.users {
			if u != m.viewer {
				items = append(items, item{value: u})
			}
		}
	case pickReviewers:
		title, sel = "Request reviewers", m.reviewers
		for _, u := range m.users {
			if u != m.viewer { // GitHub rejects self-review requests
				items = append(items, item{value: u})
			}
		}
		for _, tm := range m.teams {
			items = append(items, item{value: tm, desc: "team", team: true})
		}
	case pickLabels:
		title, sel = "Labels", m.labels
		for _, l := range m.labelDefs {
			items = append(items, item{value: l.Name, desc: l.Description, color: l.Color})
		}
	}
	p := newPicker(title, items, sel, multi)
	p.rows = max(3, min(12, m.height-12))
	p.clampScroll()
	m.picker, m.pickerFor = &p, t
}

func branchItems(branches []string, first, firstDesc string) []item {
	var items []item
	if first != "" {
		items = append(items, item{value: first, desc: firstDesc})
	}
	for _, b := range branches {
		if b != first {
			items = append(items, item{value: b})
		}
	}
	return items
}

func (m *Model) applyPick() tea.Cmd {
	sel := m.picker.Selected()
	t := m.pickerFor
	m.picker = nil
	switch t {
	case pickBase, pickHead:
		if len(sel) == 0 {
			return nil
		}
		if t == pickBase {
			m.base = sel[0]
		} else {
			m.head = sel[0]
		}
		m.diff = nil
		return m.loadDiff()
	case pickAssignees:
		m.assignees = sel
	case pickReviewers:
		m.reviewers = sel
	case pickLabels:
		m.labels = sel
	}
	return nil
}

// ---- submit -----------------------------------------------------------------

// Spec is the PR the form currently describes.
func (m Model) Spec() gh.PRSpec {
	return gh.PRSpec{
		Base: m.base, Head: m.head,
		Title: m.title.Value(), Body: m.body.Value(),
		Assignees: m.assignees, Reviewers: m.reviewers, Labels: m.labels,
		Draft: m.draft,
	}
}

func (m Model) submit() (tea.Model, tea.Cmd) {
	spec := m.Spec()
	if err := spec.Validate(); err != nil {
		m.setStatus(err.Error(), true)
		if strings.HasPrefix(err.Error(), "title") {
			m.setFocus(fTitle)
		}
		return m, nil
	}
	if m.opts.DryRun {
		m.result = Result{Spec: spec, DryRun: true}
		return m, tea.Quit
	}
	m.submitting = true
	c, head := m.client, m.head
	m.setStatus("checking "+head+" on remote…", false)
	push := func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
		defer cancel()
		need, err := c.NeedsPush(ctx, head)
		if err != nil {
			return pushedMsg{err}
		}
		if need {
			return pushedMsg{c.Push(ctx, head)}
		}
		return pushedMsg{}
	}
	return m, tea.Batch(m.spin.Tick, push)
}

func (m Model) create() tea.Cmd {
	c, spec := m.client, m.Spec()
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
		defer cancel()
		url, err := c.CreatePR(ctx, spec)
		return createdMsg{url, err}
	}
}

// ---- $EDITOR ------------------------------------------------------------------

func (m Model) openEditor() tea.Cmd {
	editor := os.Getenv("VISUAL")
	if editor == "" {
		editor = os.Getenv("EDITOR")
	}
	if editor == "" {
		editor = "vi"
	}
	f, err := os.CreateTemp("", "pr-body-*.md")
	if err != nil {
		return func() tea.Msg { return editorMsg{err: err} }
	}
	f.WriteString(m.body.Value())
	f.Close()
	parts := strings.Fields(editor)
	cmd := exec.Command(parts[0], append(parts[1:], f.Name())...)
	path := f.Name()
	return tea.ExecProcess(cmd, func(err error) tea.Msg { return editorMsg{path: path, err: err} })
}

func firstLine(s string) string {
	if i := strings.IndexByte(s, '\n'); i >= 0 {
		return s[:i]
	}
	return s
}
