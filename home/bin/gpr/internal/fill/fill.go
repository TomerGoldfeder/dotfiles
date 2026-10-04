// Package fill populates PR title/body from commit messages (gh --fill family).
package fill

import (
	"fmt"
	"strings"

	"gpr/internal/gitctx"
)

// Mode selects which commit-derived fill strategy to use.
type Mode int

const (
	// Fill uses all commits: first subject as title, subjects as body list.
	Fill Mode = iota
	// FillFirst uses only the first commit subject/body.
	FillFirst
	// FillVerbose uses commit subject+body for the description.
	FillVerbose
)

// Commit is one git commit between base and head.
type Commit struct {
	Subject string
	Body    string
}

// Select returns title and body for the given fill mode.
func Select(commits []Commit, mode Mode) (title, body string, err error) {
	if len(commits) == 0 {
		return "", "", fmt.Errorf("no commits between base and head to fill from")
	}
	switch mode {
	case FillFirst:
		c := commits[0]
		return c.Subject, strings.TrimSpace(c.Body), nil
	case FillVerbose:
		title = commits[0].Subject
		var parts []string
		for _, c := range commits {
			block := c.Subject
			if b := strings.TrimSpace(c.Body); b != "" {
				block += "\n\n" + b
			}
			parts = append(parts, block)
		}
		return title, strings.Join(parts, "\n\n"), nil
	case Fill:
		fallthrough
	default:
		title = commits[0].Subject
		if len(commits) == 1 {
			return title, strings.TrimSpace(commits[0].Body), nil
		}
		var subjects []string
		for _, c := range commits {
			subjects = append(subjects, "- "+c.Subject)
		}
		return title, strings.Join(subjects, "\n"), nil
	}
}

// LoadCommits reads commits reachable from head but not base (git log).
func LoadCommits(root, base, head string, r gitctx.Runner) ([]Commit, error) {
	if r == nil {
		r = gitctx.ExecRunner{Dir: root}
	}
	rangeSpec := base + "..." + head
	out, err := r.Output("git", "-C", root, "log", "--reverse", "--format=%s%x1f%b%x1e", rangeSpec)
	if err != nil {
		return nil, err
	}
	if strings.TrimSpace(out) == "" {
		return nil, nil
	}
	var commits []Commit
	for _, rec := range strings.Split(out, "\x1e") {
		rec = strings.TrimSpace(rec)
		if rec == "" {
			continue
		}
		parts := strings.SplitN(rec, "\x1f", 2)
		c := Commit{Subject: strings.TrimSpace(parts[0])}
		if len(parts) > 1 {
			c.Body = strings.TrimSpace(parts[1])
		}
		if c.Subject != "" {
			commits = append(commits, c)
		}
	}
	return commits, nil
}
