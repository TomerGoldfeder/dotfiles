package gh

import (
	"context"
	"reflect"
	"strings"
	"testing"
)

func TestArgs(t *testing.T) {
	s := PRSpec{
		Base: "main", Head: "feat/x", Title: "  Add x  ", Body: "b",
		Assignees: []string{"me"}, Reviewers: []string{"dana", "acme/platform"},
		Labels: []string{"cli", "enhancement"}, Draft: true,
	}
	want := []string{"pr", "create", "--base", "main", "--head", "feat/x", "--title", "Add x",
		"--body-file", "-", "--assignee", "me", "--reviewer", "dana,acme/platform",
		"--label", "cli,enhancement", "--draft"}
	if got := s.Args(); !reflect.DeepEqual(got, want) {
		t.Fatalf("args\n got %q\nwant %q", got, want)
	}

	min := PRSpec{Base: "main", Head: "f", Title: "t"}.Args()
	for _, f := range []string{"--assignee", "--reviewer", "--label", "--draft"} {
		for _, a := range min {
			if a == f {
				t.Errorf("unexpected %s in %q", f, min)
			}
		}
	}
}

func TestValidate(t *testing.T) {
	cases := map[string]PRSpec{
		"title is required":                    {Base: "main", Head: "f", Title: "  "},
		"base and feature branch are the same": {Base: "main", Head: "main", Title: "t"},
		"feature branch is required":           {Base: "main", Title: "t"},
	}
	for want, s := range cases {
		if err := s.Validate(); err == nil || err.Error() != want {
			t.Errorf("Validate(%+v) = %v, want %q", s, err, want)
		}
	}
	if err := (PRSpec{Base: "main", Head: "f", Title: "t"}).Validate(); err != nil {
		t.Errorf("valid spec: %v", err)
	}
}

type call struct {
	stdin string
	argv  string
}

func fakeRunner(responses map[string]string, calls *[]call) Runner {
	return func(_ context.Context, stdin, name string, args ...string) (string, error) {
		argv := name + " " + strings.Join(args, " ")
		*calls = append(*calls, call{stdin, argv})
		for prefix, out := range responses {
			if strings.HasPrefix(argv, prefix) {
				return out, nil
			}
		}
		return "", nil
	}
}

func TestExecClientParsing(t *testing.T) {
	var calls []call
	c := &ExecClient{Remote: "origin", Run: fakeRunner(map[string]string{
		"gh repo view": `{"owner":{"login":"acme"},"name":"api","defaultBranchRef":{"name":"main"}}`,
		"git for-each-ref --sort=-committerdate --format=%(refname:short) refs/remotes": "origin/HEAD\norigin\norigin/main\norigin/release/1.2\n",
		"gh label list":        `[{"name":"enhancement","color":"a2eeef"},{"name":"bug","color":"d73a4a"}]`,
		"git diff --shortstat": " 7 files changed, 248 insertions(+), 31 deletions(-)\n",
		"git rev-list --count": "3\n",
		"gh pr create":         "Warning: 1 uncommitted change\nhttps://github.com/acme/api/pull/42\n",
	}, &calls)}
	ctx := context.Background()

	r, err := c.Repo(ctx)
	if err != nil || r != (Repo{"acme", "api", "main"}) {
		t.Fatalf("Repo = %+v, %v", r, err)
	}
	rb, _ := c.RemoteBranches(ctx)
	if !reflect.DeepEqual(rb, []string{"main", "release/1.2"}) {
		t.Errorf("RemoteBranches = %q", rb)
	}
	ls, _ := c.Labels(ctx)
	if len(ls) != 2 || ls[0].Name != "bug" {
		t.Errorf("Labels not sorted: %+v", ls)
	}
	d, _ := c.Diffstat(ctx, "main", "feat")
	if d != (Diffstat{3, 7, 248, 31}) {
		t.Errorf("Diffstat = %+v", d)
	}
	url, err := c.CreatePR(ctx, PRSpec{Base: "main", Head: "feat", Title: "t", Body: "hello"})
	if err != nil || url != "https://github.com/acme/api/pull/42" {
		t.Errorf("CreatePR = %q, %v", url, err)
	}
	last := calls[len(calls)-1]
	if last.stdin != "hello\n" {
		t.Errorf("body not sent on stdin: %q", last.stdin)
	}
}

func TestParseShortstat(t *testing.T) {
	f, a, d := parseShortstat(" 1 file changed, 1 deletion(-)")
	if f != 1 || a != 0 || d != 1 {
		t.Errorf("got %d %d %d", f, a, d)
	}
}

func TestDiffCommand(t *testing.T) {
	c := NewExecClient()
	t.Setenv("PATH", t.TempDir()) // no delta
	t.Setenv("GH_PR_TUI_DIFF", "")
	if got := strings.Join(c.DiffCommand("main", "feat").Args, " "); got != "git --paginate diff origin/main...feat" {
		t.Errorf("fallback = %q", got)
	}
	t.Setenv("GH_PR_TUI_DIFF", `git difftool -d "$1"`)
	if got := c.DiffCommand("main", "feat").Args; got[len(got)-1] != "origin/main...feat" || got[2] != `git difftool -d "$1"` {
		t.Errorf("override = %q", got)
	}
}
