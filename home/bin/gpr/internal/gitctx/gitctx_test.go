package gitctx_test

import (
	"fmt"
	"strings"
	"testing"

	"gpr/internal/gitctx"
)

type fakeRunner struct {
	outs map[string]string
	errs map[string]error
}

func key(name string, args ...string) string {
	return name + " " + strings.Join(args, " ")
}

func (f fakeRunner) Output(name string, args ...string) (string, error) {
	k := key(name, args...)
	if err, ok := f.errs[k]; ok {
		return "", err
	}
	if out, ok := f.outs[k]; ok {
		return out, nil
	}
	return "", fmt.Errorf("unexpected command: %s", k)
}

func TestDetectOutsideGitRepo(t *testing.T) {
	r := fakeRunner{
		errs: map[string]error{
			key("git", "-C", "/tmp", "rev-parse", "--show-toplevel"): fmt.Errorf("fatal: not a git repository"),
		},
	}
	_, err := gitctx.Detect("/tmp", r)
	if err == nil {
		t.Fatal("expected error outside git repo")
	}
	if !strings.Contains(err.Error(), "not a git repository") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestDetectUsesGhMergeBase(t *testing.T) {
	root := "/repo"
	branch := "feature"
	r := fakeRunner{
		outs: map[string]string{
			key("git", "-C", "/work", "rev-parse", "--show-toplevel"):                 root,
			key("git", "-C", root, "branch", "--show-current"):                         branch,
			key("git", "-C", root, "symbolic-ref", "refs/remotes/origin/HEAD"):         "refs/remotes/origin/main",
			key("git", "-C", root, "config", "--get", "branch.feature.gh-merge-base"): "develop",
			key("git", "-C", root, "remote"):                                           "origin\nupstream",
		},
	}
	ctx, err := gitctx.Detect("/work", r)
	if err != nil {
		t.Fatal(err)
	}
	if ctx.Root != root || ctx.CurrentBranch != branch {
		t.Fatalf("got root=%q branch=%q", ctx.Root, ctx.CurrentBranch)
	}
	if ctx.DefaultBranch != "main" {
		t.Fatalf("default=%q", ctx.DefaultBranch)
	}
	if ctx.BaseBranch != "develop" {
		t.Fatalf("base=%q want develop", ctx.BaseBranch)
	}
	if ctx.Remote != "origin" {
		t.Fatalf("remote=%q", ctx.Remote)
	}
}

func TestDetectFallsBackToDefaultBranch(t *testing.T) {
	root := "/repo"
	r := fakeRunner{
		outs: map[string]string{
			key("git", "-C", ".", "rev-parse", "--show-toplevel"):             root,
			key("git", "-C", root, "branch", "--show-current"):                 "topic",
			key("git", "-C", root, "symbolic-ref", "refs/remotes/origin/HEAD"): "refs/remotes/origin/main",
			key("git", "-C", root, "remote"):                                   "origin",
		},
		errs: map[string]error{
			key("git", "-C", root, "config", "--get", "branch.topic.gh-merge-base"): fmt.Errorf("missing"),
		},
	}
	ctx, err := gitctx.Detect(".", r)
	if err != nil {
		t.Fatal(err)
	}
	if ctx.BaseBranch != "main" {
		t.Fatalf("base=%q want main", ctx.BaseBranch)
	}
}
