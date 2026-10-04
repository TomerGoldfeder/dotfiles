package gh

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

type Repo struct {
	Owner         string
	Name          string
	DefaultBranch string
}

func (r Repo) FullName() string { return r.Owner + "/" + r.Name }

type Label struct {
	Name        string `json:"name"`
	Color       string `json:"color"`
	Description string `json:"description"`
}

type Diffstat struct {
	Commits, Files, Additions, Deletions int
}

// Client is the port the UI depends on.
type Client interface {
	Repo(ctx context.Context) (Repo, error)
	CurrentBranch(ctx context.Context) (string, error)
	LocalBranches(ctx context.Context) ([]string, error)
	RemoteBranches(ctx context.Context) ([]string, error)
	Viewer(ctx context.Context) (string, error)
	Assignable(ctx context.Context, repo Repo) ([]string, error)
	Teams(ctx context.Context, repo Repo) ([]string, error)
	Labels(ctx context.Context) ([]Label, error)
	Diffstat(ctx context.Context, base, head string) (Diffstat, error)
	CommitSubjects(ctx context.Context, base, head string) ([]string, error)
	PRTemplate(ctx context.Context) (string, error)
	// DiffCommand returns an interactive command that pages the PR diff.
	DiffCommand(base, head string) *exec.Cmd
	NeedsPush(ctx context.Context, head string) (bool, error)
	Push(ctx context.Context, head string) error
	CreatePR(ctx context.Context, spec PRSpec) (string, error)
}

// Runner executes a command and returns stdout. stdin may be empty.
type Runner func(ctx context.Context, stdin, name string, args ...string) (string, error)

// ExecRunner runs real processes. stderr is folded into the error.
func ExecRunner(ctx context.Context, stdin, name string, args ...string) (string, error) {
	cmd := exec.CommandContext(ctx, name, args...)
	var out, errb bytes.Buffer
	cmd.Stdout, cmd.Stderr = &out, &errb
	if stdin != "" {
		cmd.Stdin = strings.NewReader(stdin)
	}
	if err := cmd.Run(); err != nil {
		msg := strings.TrimSpace(errb.String())
		if msg == "" {
			msg = err.Error()
		}
		return out.String(), fmt.Errorf("%s %s: %s", name, firstArgs(args), msg)
	}
	return out.String(), nil
}

func firstArgs(a []string) string {
	if len(a) > 2 {
		a = a[:2]
	}
	return strings.Join(a, " ")
}

// ExecClient implements Client with git + gh.
type ExecClient struct {
	Run    Runner
	Remote string // usually "origin"
}

func NewExecClient() *ExecClient { return &ExecClient{Run: ExecRunner, Remote: "origin"} }

func (c *ExecClient) git(ctx context.Context, args ...string) (string, error) {
	out, err := c.Run(ctx, "", "git", args...)
	return strings.TrimSpace(out), err
}

func (c *ExecClient) gh(ctx context.Context, args ...string) (string, error) {
	out, err := c.Run(ctx, "", "gh", args...)
	return strings.TrimSpace(out), err
}

func (c *ExecClient) Repo(ctx context.Context) (Repo, error) {
	out, err := c.gh(ctx, "repo", "view", "--json", "owner,name,defaultBranchRef")
	if err != nil {
		return Repo{}, err
	}
	var v struct {
		Owner            struct{ Login string } `json:"owner"`
		Name             string                 `json:"name"`
		DefaultBranchRef struct{ Name string }  `json:"defaultBranchRef"`
	}
	if err := json.Unmarshal([]byte(out), &v); err != nil {
		return Repo{}, fmt.Errorf("parse gh repo view: %w", err)
	}
	return Repo{Owner: v.Owner.Login, Name: v.Name, DefaultBranch: v.DefaultBranchRef.Name}, nil
}

func (c *ExecClient) CurrentBranch(ctx context.Context) (string, error) {
	return c.git(ctx, "rev-parse", "--abbrev-ref", "HEAD")
}

func (c *ExecClient) LocalBranches(ctx context.Context) ([]string, error) {
	out, err := c.git(ctx, "for-each-ref", "--sort=-committerdate", "--format=%(refname:short)", "refs/heads")
	return lines(out), err
}

func (c *ExecClient) RemoteBranches(ctx context.Context) ([]string, error) {
	prefix := c.Remote + "/"
	out, err := c.git(ctx, "for-each-ref", "--sort=-committerdate", "--format=%(refname:short)", "refs/remotes/"+c.Remote)
	if err != nil {
		return nil, err
	}
	var res []string
	for _, b := range lines(out) {
		b = strings.TrimPrefix(b, prefix)
		if b == "HEAD" || b == c.Remote {
			continue
		}
		res = append(res, b)
	}
	return res, nil
}

func (c *ExecClient) Viewer(ctx context.Context) (string, error) {
	return c.gh(ctx, "api", "user", "--jq", ".login")
}

func (c *ExecClient) Assignable(ctx context.Context, r Repo) ([]string, error) {
	out, err := c.gh(ctx, "api", "--paginate", fmt.Sprintf("repos/%s/assignees", r.FullName()), "--jq", ".[].login")
	return lines(out), err
}

// Teams returns "org/slug" for every team that can be requested as reviewer.
// Personal repos have no teams; the caller should treat errors as "none".
func (c *ExecClient) Teams(ctx context.Context, r Repo) ([]string, error) {
	out, err := c.gh(ctx, "api", "--paginate", fmt.Sprintf("repos/%s/teams", r.FullName()), "--jq", ".[].slug")
	if err != nil {
		return nil, err
	}
	var res []string
	for _, s := range lines(out) {
		res = append(res, r.Owner+"/"+s)
	}
	return res, nil
}

func (c *ExecClient) Labels(ctx context.Context) ([]Label, error) {
	out, err := c.gh(ctx, "label", "list", "--limit", "500", "--json", "name,color,description")
	if err != nil {
		return nil, err
	}
	var ls []Label
	if err := json.Unmarshal([]byte(out), &ls); err != nil {
		return nil, fmt.Errorf("parse gh label list: %w", err)
	}
	sort.SliceStable(ls, func(i, j int) bool { return strings.ToLower(ls[i].Name) < strings.ToLower(ls[j].Name) })
	return ls, nil
}

func (c *ExecClient) baseRef(base string) string { return c.Remote + "/" + base }

func (c *ExecClient) Diffstat(ctx context.Context, base, head string) (Diffstat, error) {
	var d Diffstat
	rng := c.baseRef(base) + "..." + head
	n, err := c.git(ctx, "rev-list", "--count", c.baseRef(base)+".."+head)
	if err != nil {
		return d, err
	}
	d.Commits, _ = strconv.Atoi(n)
	out, err := c.git(ctx, "diff", "--shortstat", rng)
	if err != nil {
		return d, err
	}
	d.Files, d.Additions, d.Deletions = parseShortstat(out)
	return d, nil
}

var shortstatRe = regexp.MustCompile(`(\d+) (file|insertion|deletion)`)

func parseShortstat(s string) (files, adds, dels int) {
	for _, m := range shortstatRe.FindAllStringSubmatch(s, -1) {
		n, _ := strconv.Atoi(m[1])
		switch m[2] {
		case "file":
			files = n
		case "insertion":
			adds = n
		case "deletion":
			dels = n
		}
	}
	return
}

func (c *ExecClient) CommitSubjects(ctx context.Context, base, head string) ([]string, error) {
	out, err := c.git(ctx, "log", "--reverse", "--format=%s", c.baseRef(base)+".."+head)
	return lines(out), err
}

// DiffCommand shows exactly what the PR will contain: the three-dot diff
// (changes on head since it forked from base). With delta on PATH the diff is
// piped through it (delta reads its own [delta] gitconfig section, so
// side-by-side, line numbers and theme follow your settings); otherwise git
// pages it with your configured core.pager. GH_PR_TUI_DIFF overrides both and
// receives the range as $1, e.g. GH_PR_TUI_DIFF='git difftool -d "$1"'.
func (c *ExecClient) DiffCommand(base, head string) *exec.Cmd {
	rng := c.baseRef(base) + "..." + head
	if custom := os.Getenv("GH_PR_TUI_DIFF"); custom != "" {
		return exec.Command("sh", "-c", custom, "sh", rng)
	}
	if _, err := exec.LookPath("delta"); err == nil {
		return exec.Command("sh", "-c", `git diff "$1" | delta --paging=always`, "sh", rng)
	}
	return exec.Command("git", "--paginate", "diff", rng)
}

// PRTemplate returns the repo's default pull request template, if any.
func (c *ExecClient) PRTemplate(ctx context.Context) (string, error) {
	root, err := c.git(ctx, "rev-parse", "--show-toplevel")
	if err != nil {
		return "", err
	}
	for _, p := range []string{
		".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md",
		"pull_request_template.md", "PULL_REQUEST_TEMPLATE.md",
		"docs/pull_request_template.md", "docs/PULL_REQUEST_TEMPLATE.md",
	} {
		if b, err := os.ReadFile(filepath.Join(root, p)); err == nil {
			return string(b), nil
		}
	}
	return "", nil
}

// NeedsPush is true when head has no upstream on the remote, or has commits
// the remote copy doesn't.
func (c *ExecClient) NeedsPush(ctx context.Context, head string) (bool, error) {
	remoteRef := "refs/remotes/" + c.Remote + "/" + head
	if _, err := c.git(ctx, "rev-parse", "--verify", "--quiet", remoteRef); err != nil {
		return true, nil
	}
	n, err := c.git(ctx, "rev-list", "--count", c.Remote+"/"+head+".."+head)
	if err != nil {
		return false, err
	}
	return n != "0", nil
}

func (c *ExecClient) Push(ctx context.Context, head string) error {
	_, err := c.git(ctx, "push", "--set-upstream", c.Remote, head)
	return err
}

func (c *ExecClient) CreatePR(ctx context.Context, spec PRSpec) (string, error) {
	out, err := c.Run(ctx, spec.Body+"\n", "gh", spec.Args()...)
	if err != nil {
		return "", err
	}
	// gh prints the PR URL as the last line of stdout.
	ls := lines(out)
	if len(ls) == 0 {
		return "", nil
	}
	return ls[len(ls)-1], nil
}

func lines(s string) []string {
	s = strings.TrimSpace(s)
	if s == "" {
		return nil
	}
	return strings.Split(s, "\n")
}
