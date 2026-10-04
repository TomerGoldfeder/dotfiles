package tui

import (
	"strings"
	"testing"

	tea "github.com/charmbracelet/bubbletea"

	"gpr/internal/gitctx"
)

type stubRunner struct {
	outs map[string]string
}

func (s stubRunner) Output(name string, args ...string) (string, error) {
	k := name + " " + strings.Join(args, " ")
	if out, ok := s.outs[k]; ok {
		return out, nil
	}
	return "", nil
}

func testCtx() gitctx.Context {
	return gitctx.Context{
		Root:          "/repo/acme-api",
		CurrentBranch: "feat/pr-create-tui",
		DefaultBranch: "main",
		BaseBranch:    "main",
		Remote:        "origin",
		Branches:      []string{"feat/pr-create-tui", "feat/other", "main"},
	}
}

func TestViewLabelsOriginAndFeatureBranch(t *testing.T) {
	m := New(testCtx(), stubRunner{}, nil)
	m.width = 100
	m.height = 40
	v := m.View()
	if !strings.Contains(v, "origin") {
		t.Fatalf("view missing origin label:\n%s", v)
	}
	if !strings.Contains(v, "feature-branch") {
		t.Fatalf("view missing feature-branch label:\n%s", v)
	}
	// Visible field labels must not be the old Base/Head rows.
	if strings.Contains(v, " Base") || strings.Contains(v, "▸ Base") || strings.Contains(v, "\nBase") {
		t.Fatalf("view still shows Base label:\n%s", v)
	}
	if strings.Contains(v, " Head") || strings.Contains(v, "▸ Head") || strings.Contains(v, "\nHead") {
		t.Fatalf("view still shows Head label:\n%s", v)
	}
	if !strings.Contains(v, "origin/main") {
		t.Fatalf("view missing origin/main display:\n%s", v)
	}
	if !strings.Contains(v, "Open a pull request") {
		t.Fatalf("view missing header:\n%s", v)
	}
}

func TestCycleFeatureBranchUpdatesHead(t *testing.T) {
	m := New(testCtx(), stubRunner{}, nil)
	m.focusField(fieldHead)
	updated, _ := m.Update(tea.KeyMsg{Type: tea.KeyRight})
	mm := updated.(Model)
	opts := mm.options(false)
	if opts.Head != "feat/other" {
		t.Fatalf("Head=%q want feat/other", opts.Head)
	}
	if opts.Base != "main" {
		t.Fatalf("Base=%q want main", opts.Base)
	}

	updated, _ = mm.Update(tea.KeyMsg{Type: tea.KeyLeft})
	mm = updated.(Model)
	opts = mm.options(false)
	if opts.Head != "feat/pr-create-tui" {
		t.Fatalf("after left Head=%q", opts.Head)
	}
}

func TestOriginMapsToBaseStrippingRemote(t *testing.T) {
	m := New(testCtx(), stubRunner{}, nil)
	m.inputs[fieldBase].SetValue("origin/develop")
	m.normalizeOrigin()
	opts := m.options(false)
	if opts.Base != "develop" {
		t.Fatalf("Base=%q want develop", opts.Base)
	}
	if m.originDisplay() != "origin/develop" {
		t.Fatalf("display=%q", m.originDisplay())
	}
	if opts.Head != "feat/pr-create-tui" {
		t.Fatalf("Head=%q", opts.Head)
	}
}
