package fill_test

import (
	"strings"
	"testing"

	"gpr/internal/fill"
)

func sample() []fill.Commit {
	return []fill.Commit{
		{Subject: "feat: add widget", Body: "details about widget"},
		{Subject: "fix: typo", Body: ""},
		{Subject: "docs: readme", Body: "more docs"},
	}
}

func TestSelectFill(t *testing.T) {
	title, body, err := fill.Select(sample(), fill.Fill)
	if err != nil {
		t.Fatal(err)
	}
	if title != "feat: add widget" {
		t.Fatalf("title=%q", title)
	}
	if !strings.Contains(body, "- feat: add widget") || !strings.Contains(body, "- fix: typo") {
		t.Fatalf("body=%q", body)
	}
}

func TestSelectFillFirst(t *testing.T) {
	title, body, err := fill.Select(sample(), fill.FillFirst)
	if err != nil {
		t.Fatal(err)
	}
	if title != "feat: add widget" {
		t.Fatalf("title=%q", title)
	}
	if body != "details about widget" {
		t.Fatalf("body=%q", body)
	}
}

func TestSelectFillVerbose(t *testing.T) {
	title, body, err := fill.Select(sample(), fill.FillVerbose)
	if err != nil {
		t.Fatal(err)
	}
	if title != "feat: add widget" {
		t.Fatalf("title=%q", title)
	}
	if !strings.Contains(body, "details about widget") || !strings.Contains(body, "docs: readme") {
		t.Fatalf("body=%q", body)
	}
}

func TestSelectEmptyFails(t *testing.T) {
	_, _, err := fill.Select(nil, fill.Fill)
	if err == nil {
		t.Fatal("expected error")
	}
}
