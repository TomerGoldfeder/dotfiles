package templates_test

import (
	"os"
	"path/filepath"
	"testing"

	"gpr/internal/templates"
)

func TestListSingleAndDirectoryTemplates(t *testing.T) {
	root := t.TempDir()
	gh := filepath.Join(root, ".github")
	if err := os.MkdirAll(filepath.Join(gh, "PULL_REQUEST_TEMPLATE"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(gh, "pull_request_template.md"), []byte("# Default\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(gh, "PULL_REQUEST_TEMPLATE", "bug.md"), []byte("bug"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(gh, "PULL_REQUEST_TEMPLATE", "feature.md"), []byte("feat"), 0o644); err != nil {
		t.Fatal(err)
	}

	list, err := templates.List(root)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 3 {
		t.Fatalf("got %d templates: %+v", len(list), list)
	}
	names := map[string]bool{}
	for _, e := range list {
		names[e.Name] = true
		body, err := templates.ReadBody(e.Path)
		if err != nil || body == "" {
			t.Fatalf("read %s: %v %q", e.Path, err, body)
		}
	}
	for _, want := range []string{"pull_request_template.md", "bug.md", "feature.md"} {
		if !names[want] {
			t.Fatalf("missing %s in %+v", want, names)
		}
	}
}

func TestListEmptyWhenNone(t *testing.T) {
	list, err := templates.List(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 0 {
		t.Fatalf("want empty, got %+v", list)
	}
}
