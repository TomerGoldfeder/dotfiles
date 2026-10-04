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
	}
}

func TestViewShowsCoreFormRows(t *testing.T) {
	m := New(testCtx(), stubRunner{}, nil)
	m.width = 100
	m.height = 40
	v := m.View()
	if !strings.Contains(v, "gpr") {
		t.Fatalf("view missing title:\n%s", v)
	}
	if !strings.Contains(v, "feat/pr-create-tui") || !strings.Contains(v, "main") {
		t.Fatalf("view missing branch context:\n%s", v)
	}
	if !strings.Contains(v, "Base") || !strings.Contains(v, "Head") {
		t.Fatalf("view missing base/head rows:\n%s", v)
	}
	if !strings.Contains(v, "No maintainer edit") {
		t.Fatalf("view missing toggle rows:\n%s", v)
	}
}

func TestTabMovesFocusAndEnterStartsEditing(t *testing.T) {
	m := New(testCtx(), stubRunner{}, nil)
	if m.focus != fieldTitle {
		t.Fatalf("initial focus=%v want %v", m.focus, fieldTitle)
	}
	updated, _ := m.Update(tea.KeyMsg{Type: tea.KeyTab})
	mm := updated.(Model)
	if mm.focus != fieldBody {
		t.Fatalf("after tab focus=%v want %v", mm.focus, fieldBody)
	}
	updated, _ = mm.Update(tea.KeyMsg{Type: tea.KeyEnter})
	mm = updated.(Model)
	if !mm.editing {
		t.Fatalf("expected editing mode after enter")
	}
	updated, _ = mm.Update(tea.KeyMsg{Type: tea.KeyEsc})
	mm = updated.(Model)
	if mm.editing {
		t.Fatalf("expected editing mode to end on esc")
	}
}

func TestOptionsReflectEditedBaseAndHead(t *testing.T) {
	m := New(testCtx(), stubRunner{}, nil)
	m.inputs[fieldBase].SetValue("develop")
	m.inputs[fieldHead].SetValue("feat/other")
	opts := m.options(false)
	if opts.Base != "develop" {
		t.Fatalf("Base=%q want develop", opts.Base)
	}
	if opts.Head != "feat/other" {
		t.Fatalf("Head=%q want feat/other", opts.Head)
	}
}
