// Package create assembles and runs `gh pr create` without using the HTTP API.
package create

import (
	"fmt"
	"strings"

	"gpr/internal/gitctx"
)

// Options are the form values mapped to gh flags.
type Options struct {
	Title            string
	Body             string
	Base             string
	Head             string
	Draft            bool
	Assignees        []string
	Reviewers        []string
	Labels           []string
	Milestone        string
	Project          string
	NoMaintainerEdit bool
	DryRun           bool
}

// BuildArgs returns the argv for `gh` (without the binary name).
func BuildArgs(opts Options) []string {
	args := []string{"pr", "create"}
	if opts.Title != "" {
		args = append(args, "--title", opts.Title)
	}
	if opts.Body != "" {
		args = append(args, "--body", opts.Body)
	}
	if opts.Base != "" {
		args = append(args, "--base", opts.Base)
	}
	if opts.Head != "" {
		args = append(args, "--head", opts.Head)
	}
	if opts.Draft {
		args = append(args, "--draft")
	}
	for _, a := range splitCSV(opts.Assignees) {
		args = append(args, "--assignee", a)
	}
	for _, r := range splitCSV(opts.Reviewers) {
		args = append(args, "--reviewer", r)
	}
	for _, l := range splitCSV(opts.Labels) {
		args = append(args, "--label", l)
	}
	if opts.Milestone != "" {
		args = append(args, "--milestone", opts.Milestone)
	}
	if opts.Project != "" {
		args = append(args, "--project", opts.Project)
	}
	if opts.NoMaintainerEdit {
		args = append(args, "--no-maintainer-edit")
	}
	if opts.DryRun {
		args = append(args, "--dry-run")
	}
	return args
}

func splitCSV(items []string) []string {
	var out []string
	for _, item := range items {
		for _, part := range strings.Split(item, ",") {
			part = strings.TrimSpace(part)
			if part != "" {
				out = append(out, part)
			}
		}
	}
	return out
}

// ParseList splits a comma-separated form field into tokens.
func ParseList(s string) []string {
	return splitCSV([]string{s})
}

// Run executes `gh` with BuildArgs. Tests inject a fake Runner.
func Run(r gitctx.Runner, opts Options) (string, error) {
	if r == nil {
		r = gitctx.ExecRunner{}
	}
	args := BuildArgs(opts)
	out, err := r.Output("gh", args...)
	if err != nil {
		return out, fmt.Errorf("gh %s: %w", strings.Join(args, " "), err)
	}
	return out, nil
}
