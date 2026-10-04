// Package gitctx loads the git repository context gpr needs from cwd.
package gitctx

import (
	"bytes"
	"fmt"
	"os/exec"
	"strings"
)

// Runner executes external commands. Tests inject a fake.
type Runner interface {
	Output(name string, args ...string) (string, error)
}

// ExecRunner shells out via os/exec.
type ExecRunner struct {
	Dir string
}

// Output runs a command and returns trimmed stdout.
func (r ExecRunner) Output(name string, args ...string) (string, error) {
	cmd := exec.Command(name, args...)
	if r.Dir != "" {
		cmd.Dir = r.Dir
	}
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		msg := strings.TrimSpace(stderr.String())
		if msg == "" {
			msg = err.Error()
		}
		return "", fmt.Errorf("%s %v: %s", name, args, msg)
	}
	return strings.TrimSpace(stdout.String()), nil
}

// Context is the repo state used to seed the PR form.
type Context struct {
	Root          string
	CurrentBranch string
	DefaultBranch string
	BaseBranch    string
	Remote        string
}

// Detect refuses non-git directories and fills branch/base/remote defaults.
func Detect(cwd string, r Runner) (Context, error) {
	if r == nil {
		r = ExecRunner{Dir: cwd}
	}
	root, err := r.Output("git", "-C", cwd, "rev-parse", "--show-toplevel")
	if err != nil {
		return Context{}, fmt.Errorf("not a git repository (or any of the parent directories): %w", err)
	}

	branch, err := r.Output("git", "-C", root, "branch", "--show-current")
	if err != nil {
		return Context{}, err
	}
	if branch == "" {
		return Context{}, fmt.Errorf("detached HEAD: check out a branch before opening a PR")
	}

	defaultBranch := detectDefaultBranch(root, r)
	base := defaultBranch
	if mergeBase, err := r.Output("git", "-C", root, "config", "--get", "branch."+branch+".gh-merge-base"); err == nil && mergeBase != "" {
		base = mergeBase
	}

	remote := "origin"
	if rem, err := r.Output("git", "-C", root, "remote"); err == nil {
		lines := strings.Fields(rem)
		if len(lines) > 0 {
			remote = lines[0]
		}
	}

	return Context{
		Root:          root,
		CurrentBranch: branch,
		DefaultBranch: defaultBranch,
		BaseBranch:    base,
		Remote:        remote,
	}, nil
}

func detectDefaultBranch(root string, r Runner) string {
	if sym, err := r.Output("git", "-C", root, "symbolic-ref", "refs/remotes/origin/HEAD"); err == nil {
		const prefix = "refs/remotes/origin/"
		if strings.HasPrefix(sym, prefix) {
			return strings.TrimPrefix(sym, prefix)
		}
	}
	for _, name := range []string{"main", "master"} {
		if _, err := r.Output("git", "-C", root, "rev-parse", "--verify", name); err == nil {
			return name
		}
	}
	return "main"
}
