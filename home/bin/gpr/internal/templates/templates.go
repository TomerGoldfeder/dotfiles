// Package templates lists GitHub pull-request template files under a repo.
package templates

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Entry is one PR template the TUI can apply as starting body text.
type Entry struct {
	Name string // display / --template basename
	Path string // absolute path
}

// List finds PR templates under root (GitHub-supported locations).
func List(root string) ([]Entry, error) {
	var found []Entry
	seen := map[string]struct{}{}

	addFile := func(path string) {
		info, err := os.Stat(path)
		if err != nil || info.IsDir() {
			return
		}
		abs, err := filepath.Abs(path)
		if err != nil {
			abs = path
		}
		key := strings.ToLower(abs)
		if _, ok := seen[key]; ok {
			return
		}
		seen[key] = struct{}{}
		found = append(found, Entry{Name: filepath.Base(abs), Path: abs})
	}

	addDir := func(dir string) {
		entries, err := os.ReadDir(dir)
		if err != nil {
			return
		}
		for _, e := range entries {
			if e.IsDir() {
				continue
			}
			lower := strings.ToLower(e.Name())
			if strings.HasSuffix(lower, ".md") || strings.HasSuffix(lower, ".txt") {
				addFile(filepath.Join(dir, e.Name()))
			}
		}
	}

	// Prefer a single canonical casing per location; seen keys are case-folded
	// so macOS APFS (case-insensitive) does not double-count.
	for _, c := range []string{
		filepath.Join(root, ".github", "pull_request_template.md"),
		filepath.Join(root, "docs", "pull_request_template.md"),
		filepath.Join(root, "pull_request_template.md"),
		filepath.Join(root, ".github", "PULL_REQUEST_TEMPLATE.md"),
		filepath.Join(root, "docs", "PULL_REQUEST_TEMPLATE.md"),
		filepath.Join(root, "PULL_REQUEST_TEMPLATE.md"),
	} {
		addFile(c)
	}
	addDir(filepath.Join(root, ".github", "PULL_REQUEST_TEMPLATE"))
	addDir(filepath.Join(root, ".github", "pull_request_template"))

	sort.Slice(found, func(i, j int) bool { return found[i].Name < found[j].Name })
	return found, nil
}

// ReadBody loads template file contents for the form body field.
func ReadBody(path string) (string, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return string(b), nil
}
