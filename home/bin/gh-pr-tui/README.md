# gh-pr-tui

A full-screen terminal form for opening a GitHub pull request, laid out like GitHub's
"Open a pull request" page: branches on top, title and body on the left, and
assignees / reviewers / labels / draft in a sidebar on the right.

It shells out to `git` and `gh`, so it reuses your existing `gh auth login`.

## Requirements

- Go ≥ 1.24 (build only)
- `gh` logged in (`gh auth status`)
- Run it inside a git repo with a GitHub `origin` remote

## Build & run

```sh
go build -o gh-pr-tui .
./gh-pr-tui            # from inside any GitHub repo
```

Install it as a gh extension so it runs as `gh pr-tui`:

```sh
go build -o gh-pr-tui . && gh extension install .
cd ~/src/some-repo && gh pr-tui
```

## Flags

| flag | meaning |
|---|---|
| `-B, --base` | branch to merge into (default: repo default branch) |
| `-H, --head` | feature branch (default: current branch) |
| `-d, --draft` | start with Draft checked |
| `--title` | prefill the title |
| `--dry-run` | print the `gh pr create` command instead of pushing and creating |

## Keys

| where | key | action |
|---|---|---|
| anywhere | `tab` / `shift+tab` | next / previous field |
| anywhere | `ctrl+s` | push (if needed) and create the PR |
| anywhere | `esc` | quit (asks first if you typed something) |
| title | `enter` | jump to body |
| body | `ctrl+p` | toggle Write / Preview |
| body | `ctrl+o` | edit body in `$VISUAL` / `$EDITOR` |
| panels | `b t e a r l` | jump to Branches, Title, Body, Assignees, Reviewers, Labels |
| panels | `d` | toggle Draft |
| panels | `enter` | open the picker for that panel |
| panels | `x` | clear that list |
| panels | `v` | view the PR diff (delta if installed), `q` to return |
| branches | `←` `→` | choose base or feature, then `enter` |
| picker | type | fuzzy filter (spaces ignored) |
| picker | `space` | toggle (multi-select) |
| picker | `enter` / `esc` | confirm / cancel |

## Behaviour

- Title prefill: one commit → its subject; several → the branch name. Body prefill: the repo's
  PR template, else a bullet list of commit subjects.
- If the feature branch isn't on `origin` (or is ahead of it), `ctrl+s` runs
  `git push --set-upstream origin <branch>` before `gh pr create`.
- `v` shows exactly what the PR will contain: `git diff origin/<base>...<feature>` (committed
  changes only). If `delta` is on `PATH` it's piped through `delta --paging=always`, which reads
  your `[delta]` gitconfig (side-by-side, line numbers, theme). Without delta, git pages it with
  your `core.pager`. Override with `GH_PR_TUI_DIFF`, which gets the range as `$1`, e.g.
  `export GH_PR_TUI_DIFF='git difftool --dir-diff "$1"'`.
- The body goes to `gh` on stdin (`--body-file -`); the PR URL is printed on exit.

## Layout

```
main.go              flags, prefill, run program, print URL
internal/gh          PRSpec → gh args; Client interface + git/gh exec implementation
internal/ui          Bubble Tea model, view, fuzzy picker, markdown preview
```

`go.mod` replaces `golang.org/x/{sys,text}` with their GitHub mirrors (the build sandbox
couldn't reach golang.org). It's harmless; delete the `replace` block and run
`go mod tidy` if you prefer the canonical paths.

## Tests

```sh
go test ./...
```
