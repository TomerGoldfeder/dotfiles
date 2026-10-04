// Package tui is the Bubble Tea PR-open form.
package tui

import (
	"fmt"
	"os/exec"
	"strings"

	"github.com/charmbracelet/bubbles/textarea"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/glamour"

	"gpr/internal/create"
	"gpr/internal/fill"
	"gpr/internal/gitctx"
	"gpr/internal/templates"
	"gpr/internal/theme"
)

type field int

const (
	fieldTitle field = iota
	fieldBody
	fieldBase
	fieldHead
	fieldAssignees
	fieldReviewers
	fieldLabels
	fieldMilestone
	fieldProject
	fieldCount
)

type phase int

const (
	phaseForm phase = iota
	phasePreview
	phaseDiff
	phaseDone
	phaseErr
)

// Model is the PR form program state.
type Model struct {
	theme     theme.Theme
	ctx       gitctx.Context
	runner    gitctx.Runner
	templates []templates.Entry
	tmplIdx   int

	focus    field
	editing  bool
	draft    bool
	noMaint  bool
	inputs   []textinput.Model
	body     textarea.Model
	phase    phase
	status   string
	preview  string
	width    int
	height   int
	quitting bool
	result   string
}

// New builds a form seeded from repo context.
func New(ctx gitctx.Context, r gitctx.Runner, tmpls []templates.Entry) Model {
	if r == nil {
		r = gitctx.ExecRunner{Dir: ctx.Root}
	}
	t := theme.Default
	inputs := make([]textinput.Model, fieldCount)
	for i := range inputs {
		ti := textinput.New()
		ti.Prompt = ""
		ti.TextStyle = ti.TextStyle.Foreground(t.Text)
		ti.Cursor.Style = ti.Cursor.Style.Foreground(t.PrimaryStrong)
		inputs[i] = ti
	}
	inputs[fieldTitle].Placeholder = "PR title"
	inputs[fieldBase].SetValue(ctx.BaseBranch)
	inputs[fieldHead].SetValue(ctx.CurrentBranch)
	inputs[fieldAssignees].Placeholder = "@me, user"
	inputs[fieldReviewers].Placeholder = "user, org/team"
	inputs[fieldLabels].Placeholder = "bug, enhancement"
	inputs[fieldMilestone].Placeholder = "milestone name"
	inputs[fieldProject].Placeholder = "project title"

	ta := textarea.New()
	ta.Placeholder = "PR body (markdown)"
	ta.SetHeight(8)
	ta.ShowLineNumbers = false
	ta.FocusedStyle.CursorLine = ta.FocusedStyle.CursorLine.Background(t.Surface)
	ta.BlurredStyle.CursorLine = ta.BlurredStyle.CursorLine.Background(t.Surface)

	m := Model{
		theme:     t,
		ctx:       ctx,
		runner:    r,
		templates: tmpls,
		tmplIdx:   -1,
		inputs:    inputs,
		body:      ta,
		phase:     phaseForm,
		status:    "Tab focus · Enter edit · f/F/v fill · t template · d diff · p dry-run · s submit · q quit",
	}
	m.inputs[fieldTitle].Focus()
	return m
}

// Result is the PR URL (or create output) after a successful submit.
func (m Model) Result() string { return m.result }

// Init implements tea.Model.
func (m Model) Init() tea.Cmd { return textinput.Blink }

type runResultMsg struct {
	out    string
	err    error
	dryRun bool
}

type diffMsg struct {
	out string
	err error
}

type fillMsg struct {
	title string
	body  string
	err   error
	mode  fill.Mode
}

func (m Model) options(dry bool) create.Options {
	return create.Options{
		Title:            strings.TrimSpace(m.inputs[fieldTitle].Value()),
		Body:             m.body.Value(),
		Base:             strings.TrimSpace(m.inputs[fieldBase].Value()),
		Head:             strings.TrimSpace(m.inputs[fieldHead].Value()),
		Draft:            m.draft,
		Assignees:        create.ParseList(m.inputs[fieldAssignees].Value()),
		Reviewers:        create.ParseList(m.inputs[fieldReviewers].Value()),
		Labels:           create.ParseList(m.inputs[fieldLabels].Value()),
		Milestone:        strings.TrimSpace(m.inputs[fieldMilestone].Value()),
		Project:          strings.TrimSpace(m.inputs[fieldProject].Value()),
		NoMaintainerEdit: m.noMaint,
		DryRun:           dry,
	}
}

func (m Model) cmdCreate(dry bool) tea.Cmd {
	opts := m.options(dry)
	r := m.runner
	return func() tea.Msg {
		out, err := create.Run(r, opts)
		return runResultMsg{out: out, err: err, dryRun: dry}
	}
}

func (m Model) cmdFill(mode fill.Mode) tea.Cmd {
	root, base, head := m.ctx.Root, m.inputs[fieldBase].Value(), m.inputs[fieldHead].Value()
	r := m.runner
	return func() tea.Msg {
		commits, err := fill.LoadCommits(root, base, head, r)
		if err != nil {
			return fillMsg{err: err, mode: mode}
		}
		title, body, err := fill.Select(commits, mode)
		return fillMsg{title: title, body: body, err: err, mode: mode}
	}
}

func (m Model) cmdDiff() tea.Cmd {
	root := m.ctx.Root
	base := m.inputs[fieldBase].Value()
	head := m.inputs[fieldHead].Value()
	return func() tea.Msg {
		args := []string{"-C", root, "diff", "--stat", base + "..." + head}
		out, err := exec.Command("git", args...).CombinedOutput()
		text := string(out)
		if _, lookErr := exec.LookPath("delta"); lookErr == nil {
			dargs := []string{"-C", root, "diff", base + "..." + head}
			cmd := exec.Command("git", dargs...)
			delta := exec.Command("delta", "--paging", "never")
			pipe, pipeErr := cmd.StdoutPipe()
			if pipeErr == nil {
				delta.Stdin = pipe
				var combined strings.Builder
				delta.Stdout = &combined
				delta.Stderr = &combined
				if startErr := cmd.Start(); startErr == nil {
					if runErr := delta.Run(); runErr == nil {
						_ = cmd.Wait()
						return diffMsg{out: combined.String()}
					}
				}
			}
		}
		return diffMsg{out: text, err: err}
	}
}

func renderMarkdown(src string, width int) string {
	if width < 40 {
		width = 80
	}
	r, err := glamour.NewTermRenderer(
		glamour.WithStylePath("dark"),
		glamour.WithWordWrap(width-4),
	)
	if err != nil {
		return src
	}
	out, err := r.Render(src)
	if err != nil {
		return src
	}
	return out
}

func (m *Model) blurAll() {
	for i := range m.inputs {
		m.inputs[i].Blur()
	}
	m.body.Blur()
}

func (m *Model) focusField(f field) {
	m.blurAll()
	m.focus = f
	if f == fieldBody {
		m.body.Focus()
		return
	}
	m.inputs[f].Focus()
}

func (m *Model) applyTemplate() {
	if len(m.templates) == 0 {
		m.status = "no PR templates under .github"
		return
	}
	m.tmplIdx = (m.tmplIdx + 1) % len(m.templates)
	e := m.templates[m.tmplIdx]
	body, err := templates.ReadBody(e.Path)
	if err != nil {
		m.status = fmt.Sprintf("template: %v", err)
		return
	}
	m.body.SetValue(body)
	m.status = fmt.Sprintf("template: %s", e.Name)
}
