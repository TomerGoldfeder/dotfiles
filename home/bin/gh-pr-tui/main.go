// gh-pr-tui: open a GitHub pull request from a full-screen terminal form.
// Install as a gh extension (`gh pr-tui`) or run the binary directly.
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"

	"github.com/tomer/gh-pr-tui/internal/gh"
	"github.com/tomer/gh-pr-tui/internal/ui"
)

func main() {
	var (
		base   = flag.String("base", "", "branch to merge into (default: repo default branch)")
		head   = flag.String("head", "", "feature branch (default: current branch)")
		draft  = flag.Bool("draft", false, "start with Draft checked")
		title  = flag.String("title", "", "prefill the title")
		dryRun = flag.Bool("dry-run", false, "print the gh command instead of pushing and creating the PR")
	)
	flag.StringVar(base, "B", "", "shorthand for --base")
	flag.StringVar(head, "H", "", "shorthand for --head")
	flag.BoolVar(draft, "d", false, "shorthand for --draft")
	flag.Parse()

	if err := run(*base, *head, *title, *draft, *dryRun); err != nil {
		fmt.Fprintln(os.Stderr, "gh-pr-tui:", err)
		os.Exit(1)
	}
}

func run(base, head, title string, draft, dryRun bool) error {
	client := gh.NewExecClient()
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	repo, err := client.Repo(ctx)
	if err != nil {
		return fmt.Errorf("not in a GitHub repository (or gh is not logged in): %w", err)
	}
	if head == "" {
		if head, err = client.CurrentBranch(ctx); err != nil {
			return err
		}
	}
	if base == "" {
		base = repo.DefaultBranch
	}

	// Prefill like `gh pr create --fill`: one commit → its subject; several →
	// the branch name as title and the subjects as a bullet list.
	subjects, _ := client.CommitSubjects(ctx, base, head)
	if title == "" {
		title = defaultTitle(head, subjects)
	}
	body, _ := client.PRTemplate(ctx)
	if body == "" && len(subjects) > 1 {
		body = "- " + strings.Join(subjects, "\n- ")
	}

	m := ui.New(client, ui.Options{
		Repo: repo, Base: base, Head: head,
		Title: title, Body: body, Draft: draft, DryRun: dryRun,
	})
	final, err := tea.NewProgram(m, tea.WithAltScreen()).Run()
	if err != nil {
		return err
	}
	res := final.(ui.Model).Result()
	switch {
	case res.Cancelled:
		fmt.Fprintln(os.Stderr, "Cancelled.")
	case res.DryRun:
		fmt.Println("gh " + shellJoin(res.Spec.Args()) + " <<'EOF'\n" + res.Spec.Body + "\nEOF")
	case res.URL != "":
		fmt.Println(res.URL)
	}
	return nil
}

func defaultTitle(branch string, subjects []string) string {
	if len(subjects) == 1 {
		return subjects[0]
	}
	if i := strings.LastIndex(branch, "/"); i >= 0 {
		branch = branch[i+1:]
	}
	t := strings.NewReplacer("-", " ", "_", " ").Replace(branch)
	if t == "" {
		return ""
	}
	return strings.ToUpper(t[:1]) + t[1:]
}

func shellJoin(args []string) string {
	q := make([]string, len(args))
	for i, a := range args {
		if a != "" && !strings.ContainsAny(a, " \t\n'\"$`\\*?[]{}()<>|&;#~!") {
			q[i] = a
			continue
		}
		q[i] = "'" + strings.ReplaceAll(a, "'", `'\''`) + "'"
	}
	return strings.Join(q, " ")
}
