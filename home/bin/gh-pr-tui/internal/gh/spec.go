// Package gh is the boundary to git and the gh CLI. Everything the UI needs
// from the outside world goes through the Client interface, so the UI can be
// tested with a fake.
package gh

import (
	"errors"
	"strings"
)

// PRSpec is everything the form collects. It maps 1:1 onto `gh pr create` flags.
type PRSpec struct {
	Base      string // branch the PR merges into ("origin branch")
	Head      string // branch with the changes ("feature branch")
	Title     string
	Body      string
	Assignees []string
	Reviewers []string
	Labels    []string
	Draft     bool
}

// Validate reports the first problem that would make `gh pr create` fail.
func (s PRSpec) Validate() error {
	switch {
	case strings.TrimSpace(s.Title) == "":
		return errors.New("title is required")
	case s.Base == "":
		return errors.New("base branch is required")
	case s.Head == "":
		return errors.New("feature branch is required")
	case s.Base == s.Head:
		return errors.New("base and feature branch are the same")
	}
	return nil
}

// Args builds the `gh pr create` argument list. The body is passed on stdin
// (--body-file -) so it never hits argv length limits or shell quoting.
func (s PRSpec) Args() []string {
	args := []string{
		"pr", "create",
		"--base", s.Base,
		"--head", s.Head,
		"--title", strings.TrimSpace(s.Title),
		"--body-file", "-",
	}
	if len(s.Assignees) > 0 {
		args = append(args, "--assignee", strings.Join(s.Assignees, ","))
	}
	if len(s.Reviewers) > 0 {
		args = append(args, "--reviewer", strings.Join(s.Reviewers, ","))
	}
	if len(s.Labels) > 0 {
		args = append(args, "--label", strings.Join(s.Labels, ","))
	}
	if s.Draft {
		args = append(args, "--draft")
	}
	return args
}
