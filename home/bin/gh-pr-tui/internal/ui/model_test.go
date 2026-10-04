package ui

import (
	"context"
	"reflect"
	"strings"
	"testing"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"github.com/tomer/gh-pr-tui/internal/gh"
)

type fakeClient struct {
	needsPush bool
	pushed    []string
	created   []gh.PRSpec
	diffCalls [][2]string
}

func (f *fakeClient) Repo(context.Context) (gh.Repo, error) {
	return gh.Repo{Owner: "acme", Name: "api", DefaultBranch: "main"}, nil
}
func (f *fakeClient) CurrentBranch(context.Context) (string, error) { return "feat/x", nil }
func (f *fakeClient) LocalBranches(context.Context) ([]string, error) {
	return []string{"feat/x", "main", "fix/y"}, nil
}
func (f *fakeClient) RemoteBranches(context.Context) ([]string, error) {
	return []string{"main", "release/1.2"}, nil
}
func (f *fakeClient) Viewer(context.Context) (string, error) { return "me", nil }
func (f *fakeClient) Assignable(context.Context, gh.Repo) ([]string, error) {
	return []string{"me", "dana-k", "daniel-r", "lior-m"}, nil
}
func (f *fakeClient) Teams(context.Context, gh.Repo) ([]string, error) {
	return []string{"acme/platform"}, nil
}
func (f *fakeClient) Labels(context.Context) ([]gh.Label, error) {
	return []gh.Label{{Name: "bug", Color: "d73a4a"}, {Name: "good first issue", Color: "7057ff"}}, nil
}
func (f *fakeClient) Diffstat(_ context.Context, b, h string) (gh.Diffstat, error) {
	f.diffCalls = append(f.diffCalls, [2]string{b, h})
	return gh.Diffstat{Commits: 3, Files: 7, Additions: 248, Deletions: 31}, nil
}
func (f *fakeClient) CommitSubjects(context.Context, string, string) ([]string, error) {
	return nil, nil
}
func (f *fakeClient) PRTemplate(context.Context) (string, error)      { return "", nil }
func (f *fakeClient) NeedsPush(context.Context, string) (bool, error) { return f.needsPush, nil }
func (f *fakeClient) Push(_ context.Context, h string) error {
	f.pushed = append(f.pushed, h)
	return nil
}
func (f *fakeClient) CreatePR(_ context.Context, s gh.PRSpec) (string, error) {
	f.created = append(f.created, s)
	return "https://github.com/acme/api/pull/7", nil
}

// harness drives the model like the Bubble Tea runtime, but synchronously and
// only for the app's own messages (no blink/spinner loops).
type harness struct {
	t    *testing.T
	m    Model
	quit bool
	fc   *fakeClient
}

func newHarness(t *testing.T, o Options) *harness {
	fc := &fakeClient{}
	if o.Repo.Name == "" {
		o.Repo = gh.Repo{Owner: "acme", Name: "api", DefaultBranch: "main"}
	}
	h := &harness{t: t, m: New(fc, o), fc: fc}
	h.send(tea.WindowSizeMsg{Width: 120, Height: 36})
	h.run(h.m.loadLists())
	h.run(h.m.loadDiff())
	return h
}

func (h *harness) send(msg tea.Msg) {
	nm, cmd := h.m.Update(msg)
	h.m = nm.(Model)
	h.run(cmd)
}

func (h *harness) run(cmd tea.Cmd) {
	if cmd == nil {
		return
	}
	switch msg := cmd().(type) {
	case tea.BatchMsg:
		for _, c := range msg {
			h.run(c)
		}
	case tea.QuitMsg:
		h.quit = true
	case listsMsg, diffMsg, pushedMsg, createdMsg:
		h.send(msg)
	}
}

func (h *harness) keys(ks ...string) {
	for _, k := range ks {
		var msg tea.KeyMsg
		switch k {
		case "tab":
			msg = tea.KeyMsg{Type: tea.KeyTab}
		case "shift+tab":
			msg = tea.KeyMsg{Type: tea.KeyShiftTab}
		case "enter":
			msg = tea.KeyMsg{Type: tea.KeyEnter}
		case "esc":
			msg = tea.KeyMsg{Type: tea.KeyEsc}
		case "space":
			msg = tea.KeyMsg{Type: tea.KeySpace, Runes: []rune(" ")}
		case "down":
			msg = tea.KeyMsg{Type: tea.KeyDown}
		case "ctrl+s":
			msg = tea.KeyMsg{Type: tea.KeyCtrlS}
		case "ctrl+p":
			msg = tea.KeyMsg{Type: tea.KeyCtrlP}
		case "ctrl+u":
			msg = tea.KeyMsg{Type: tea.KeyCtrlU}
		default:
			msg = tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune(k)}
		}
		h.send(msg)
	}
}

func baseOpts() Options {
	return Options{Base: "main", Head: "feat/x", Title: "Add x", Body: "## Summary"}
}

func TestLettersTypeInTitleButAreShortcutsElsewhere(t *testing.T) {
	h := newHarness(t, baseOpts())
	if h.m.focus != fTitle {
		t.Fatalf("initial focus = %v, want title", h.m.focus)
	}
	h.keys("d")
	if got := h.m.title.Value(); got != "Add xd" || h.m.draft {
		t.Fatalf("typing d in title: title=%q draft=%v", got, h.m.draft)
	}
	h.keys("tab", "tab") // body → assignees
	if h.m.focus != fAssignees {
		t.Fatalf("focus = %v, want assignees", h.m.focus)
	}
	h.keys("d")
	if !h.m.draft || h.m.focus != fDraft {
		t.Fatalf("d on sidebar: draft=%v focus=%v", h.m.draft, h.m.focus)
	}
	h.keys("b")
	if h.m.focus != fBranches {
		t.Fatalf("b → focus %v", h.m.focus)
	}
	h.keys("shift+tab") // wraps to Cancel
	if h.m.focus != fCancel {
		t.Fatalf("shift+tab from first = %v, want cancel", h.m.focus)
	}
}

func TestReviewerPicker(t *testing.T) {
	h := newHarness(t, baseOpts())
	h.keys("tab", "tab", "r", "enter")
	if h.m.picker == nil {
		t.Fatal("picker did not open")
	}
	for _, it := range h.m.picker.items {
		if it.value == "me" {
			t.Fatal("viewer offered as reviewer")
		}
	}
	h.keys("d", "k", "space") // "dk" → dana-k first
	h.keys("esc")
	if h.m.picker != nil || len(h.m.reviewers) != 0 {
		t.Fatalf("esc should cancel: picker=%v reviewers=%v", h.m.picker != nil, h.m.reviewers)
	}
	h.keys("enter", "d", "k", "space", "ctrl+u", "p", "l", "a", "t", "space", "enter")
	want := []string{"dana-k", "acme/platform"}
	if !reflect.DeepEqual(h.m.reviewers, want) {
		t.Fatalf("reviewers = %v, want %v", h.m.reviewers, want)
	}
}

func TestLabelPickerMatchesAcrossSpaces(t *testing.T) {
	h := newHarness(t, baseOpts())
	h.keys("tab", "tab", "l", "enter", "g", "o", "o", "d", "f", "i", "r", "space", "enter")
	if !reflect.DeepEqual(h.m.labels, []string{"good first issue"}) {
		t.Fatalf("labels = %v", h.m.labels)
	}
}

func TestBranchPickerChangesBaseAndReloadsDiff(t *testing.T) {
	h := newHarness(t, baseOpts())
	h.keys("tab", "tab", "b", "enter", "r", "e", "l", "enter")
	if h.m.base != "release/1.2" {
		t.Fatalf("base = %q", h.m.base)
	}
	last := h.fc.diffCalls[len(h.fc.diffCalls)-1]
	if last != [2]string{"release/1.2", "feat/x"} || h.m.diff == nil {
		t.Fatalf("diff not reloaded: %v", h.fc.diffCalls)
	}
}

func TestSubmitRequiresTitle(t *testing.T) {
	o := baseOpts()
	o.Title = ""
	h := newHarness(t, o)
	h.keys("tab", "ctrl+s")
	if h.m.status != "title is required" || h.m.focus != fTitle || len(h.fc.created) != 0 {
		t.Fatalf("status=%q focus=%v created=%d", h.m.status, h.m.focus, len(h.fc.created))
	}
}

func TestSubmitPushesThenCreates(t *testing.T) {
	h := newHarness(t, baseOpts())
	h.fc.needsPush = true
	h.keys("tab", "tab", "a", "enter", "m", "e", "space", "enter", "d", "ctrl+s")
	if !reflect.DeepEqual(h.fc.pushed, []string{"feat/x"}) {
		t.Fatalf("pushed = %v", h.fc.pushed)
	}
	if len(h.fc.created) != 1 {
		t.Fatalf("created %d PRs", len(h.fc.created))
	}
	want := gh.PRSpec{Base: "main", Head: "feat/x", Title: "Add x", Body: "## Summary",
		Assignees: []string{"me"}, Draft: true}
	if !reflect.DeepEqual(h.fc.created[0], want) {
		t.Fatalf("spec\n got %+v\nwant %+v", h.fc.created[0], want)
	}
	if !h.quit || h.m.Result().URL != "https://github.com/acme/api/pull/7" {
		t.Fatalf("quit=%v result=%+v", h.quit, h.m.Result())
	}
}

func TestEscAsksBeforeDiscarding(t *testing.T) {
	h := newHarness(t, baseOpts())
	h.keys("!", "esc")
	if h.quit || !h.m.confirmQuit {
		t.Fatal("dirty form quit without confirmation")
	}
	h.keys("n")
	if h.quit {
		t.Fatal("n should keep editing")
	}
	h.keys("esc", "y")
	if !h.quit || !h.m.Result().Cancelled {
		t.Fatal("y should quit")
	}
}

func TestDryRunReturnsSpecWithoutCreating(t *testing.T) {
	o := baseOpts()
	o.DryRun = true
	h := newHarness(t, o)
	h.keys("ctrl+s")
	if !h.quit || !h.m.Result().DryRun || len(h.fc.created)+len(h.fc.pushed) != 0 {
		t.Fatalf("dry run: quit=%v res=%+v", h.quit, h.m.Result())
	}
}

func TestViewFillsScreenExactly(t *testing.T) {
	for _, sz := range [][2]int{{80, 22}, {120, 36}, {200, 50}} {
		h := newHarness(t, baseOpts())
		h.send(tea.WindowSizeMsg{Width: sz[0], Height: sz[1]})
		h.m.assignees = []string{"me", "dana-k", "a", "b", "c", "d"}
		h.m.labels = []string{"bug", "good first issue"}
		for _, withPicker := range []bool{false, true} {
			if withPicker {
				h.keys("tab", "tab", "l", "enter")
			}
			lines := strings.Split(h.m.View(), "\n")
			if len(lines) != sz[1] {
				t.Errorf("%dx%d picker=%v: %d lines", sz[0], sz[1], withPicker, len(lines))
			}
			for i, l := range lines {
				if w := lipgloss.Width(l); w > sz[0] {
					t.Errorf("%dx%d picker=%v: line %d is %d wide", sz[0], sz[1], withPicker, i, w)
				}
			}
		}
	}
}

func TestFuzzyScore(t *testing.T) {
	if _, ok := fuzzyScore("dk", "dana-k"); !ok {
		t.Error("dk should match dana-k")
	}
	if _, ok := fuzzyScore("zz", "dana-k"); ok {
		t.Error("zz should not match")
	}
	a, _ := fuzzyScore("ma", "main")
	b, _ := fuzzyScore("ma", "feat/schema")
	if a <= b {
		t.Errorf("prefix match should rank higher: main=%d feat/schema=%d", a, b)
	}
}

func TestMarkdownPreview(t *testing.T) {
	out := strings.Join(renderMarkdown("## Summary\n- [x] done\n- item `code`", 40), "\n")
	plain := ansiStrip(out)
	for _, want := range []string{"Summary", "[x] done", "• item code"} {
		if !strings.Contains(plain, want) {
			t.Errorf("preview missing %q in:\n%s", want, plain)
		}
	}
	if strings.Contains(plain, "##") {
		t.Error("heading markers should be stripped")
	}
}

func ansiStrip(s string) string {
	var b strings.Builder
	esc := false
	for _, r := range s {
		switch {
		case r == '\x1b':
			esc = true
		case esc && (r >= 'a' && r <= 'z' || r >= 'A' && r <= 'Z'):
			esc = false
		case !esc:
			b.WriteRune(r)
		}
	}
	return b.String()
}
