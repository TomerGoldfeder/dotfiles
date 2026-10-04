// gpr — interactive gh pr create TUI (Tokyo Night midnight).
package main

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"

	"gpr/internal/gitctx"
	"gpr/internal/templates"
	"gpr/internal/tui"
)

func main() {
	cwd, err := os.Getwd()
	if err != nil {
		fail(err)
	}
	runner := gitctx.ExecRunner{Dir: cwd}
	ctx, err := gitctx.Detect(cwd, runner)
	if err != nil {
		fail(err)
	}
	// Prefer repo root for subsequent git/gh calls.
	runner.Dir = ctx.Root

	tmpls, err := templates.List(ctx.Root)
	if err != nil {
		fail(err)
	}

	m := tui.New(ctx, runner, tmpls)
	p := tea.NewProgram(m, tea.WithAltScreen())
	final, err := p.Run()
	if err != nil {
		fail(err)
	}
	if done, ok := final.(tui.Model); ok {
		if done.Result() != "" {
			fmt.Println(done.Result())
		}
	}
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err.Error())
	os.Exit(1)
}
