package create_test

import (
	"fmt"
	"strings"
	"testing"

	"gpr/internal/create"
)

func TestBuildArgsAssemblesFlags(t *testing.T) {
	args := create.BuildArgs(create.Options{
		Title:            "My PR",
		Body:             "hello",
		Base:             "main",
		Head:             "feature",
		Draft:            true,
		Assignees:        []string{"@me", "alice"},
		Reviewers:        []string{"bob", "org/team"},
		Labels:           []string{"bug", "prio"},
		Milestone:        "v1",
		Project:          "Roadmap",
		NoMaintainerEdit: true,
		DryRun:           true,
	})
	joined := strings.Join(args, " ")
	wants := []string{
		"pr create",
		"--title My PR",
		"--body hello",
		"--base main",
		"--head feature",
		"--draft",
		"--assignee @me",
		"--assignee alice",
		"--reviewer bob",
		"--reviewer org/team",
		"--label bug",
		"--label prio",
		"--milestone v1",
		"--project Roadmap",
		"--no-maintainer-edit",
		"--dry-run",
	}
	for _, w := range wants {
		if !strings.Contains(joined, w) {
			t.Fatalf("missing %q in %q", w, joined)
		}
	}
	if strings.Contains(joined, "--web") || strings.Contains(joined, "--repo") {
		t.Fatalf("forbidden flags present: %q", joined)
	}
}

func TestBuildArgsOmitsEmptyOptional(t *testing.T) {
	args := create.BuildArgs(create.Options{Title: "t", Body: "b"})
	joined := strings.Join(args, " ")
	for _, bad := range []string{"--draft", "--dry-run", "--base", "--assignee", "--template"} {
		if strings.Contains(joined, bad) {
			t.Fatalf("unexpected %s in %q", bad, joined)
		}
	}
}

type captureRunner struct {
	lastName string
	lastArgs []string
	out      string
	err      error
}

func (c *captureRunner) Output(name string, args ...string) (string, error) {
	c.lastName = name
	c.lastArgs = append([]string{}, args...)
	return c.out, c.err
}

func TestRunDryRunVsSubmit(t *testing.T) {
	r := &captureRunner{out: "Would create pull request"}
	out, err := create.Run(r, create.Options{Title: "t", Body: "b", DryRun: true})
	if err != nil {
		t.Fatal(err)
	}
	if out != "Would create pull request" {
		t.Fatalf("out=%q", out)
	}
	if r.lastName != "gh" {
		t.Fatalf("bin=%q", r.lastName)
	}
	joined := strings.Join(r.lastArgs, " ")
	if !strings.Contains(joined, "--dry-run") {
		t.Fatalf("dry-run missing: %q", joined)
	}

	r2 := &captureRunner{out: "https://github.com/o/r/pull/1"}
	out, err = create.Run(r2, create.Options{Title: "t", Body: "b", DryRun: false})
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(strings.Join(r2.lastArgs, " "), "--dry-run") {
		t.Fatal("submit must not pass --dry-run")
	}
	if !strings.Contains(out, "github.com") {
		t.Fatalf("out=%q", out)
	}
}

func TestRunPropagatesErrors(t *testing.T) {
	r := &captureRunner{err: fmt.Errorf("HTTP 401")}
	_, err := create.Run(r, create.Options{Title: "t", Body: "b"})
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestParseList(t *testing.T) {
	got := create.ParseList(" @me, alice , bob ")
	if len(got) != 3 || got[0] != "@me" || got[1] != "alice" || got[2] != "bob" {
		t.Fatalf("%v", got)
	}
}
