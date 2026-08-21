# Adapted from https://github.com/omerxx/dotfiles/blob/master/nushell/config.nu
# Bash equivalents: https://www.nushell.sh/book/coming_from_bash.html#command-equivalents
#
# `ls` / `ls --all` are Nushell builtins and print the rounded table (name, type,
# size, modified). Do not alias them to eza or ^ls.

$env.config.show_banner = false
$env.config.edit_mode = "vi"
$env.config.ls.use_ls_colors = true
$env.config.table.mode = "rounded"
$env.config.table.index_mode = "always"

# Keep humanized dates ("3 months ago") like the default / omerxx screenshot.
$env.config.datetime_format.table = null

def --env cx [arg] {
  cd $arg
  ls -l
}

alias l = ls --all
alias c = clear
alias ll = ls -l
alias lt = eza --tree --level=2 --long --icons --git
alias v = nvim
alias vim = nvim
alias vi = nvim
alias as = aerospace
alias oc = opencode

# Git
alias add = git add .
alias commit = git commit -m
alias push = git push
alias pull = git pull
alias gd = git diff --name-only
alias gc = git commit -m
alias gca = git commit -a -m
alias gp = git push origin HEAD
alias gpu = git pull origin
alias gst = git status
alias glog = git log --graph --topo-order --pretty='%w(100,0,6)%C(yellow)%h%C(bold)%C(black)%d %C(cyan)%ar %C(green)%an%n%C(bold)%C(white)%s %N' --abbrev-commit
alias gdiff = git diff
alias gco = git checkout
alias gb = git branch
alias gba = git branch -a
alias gadd = git add
alias ga = git add -p
alias gcoall = git checkout -- .
alias gr = git remote
alias gre = git reset

# K8s
alias k = kubectl
alias ka = kubectl apply -f
alias kg = kubectl get
alias kd = kubectl describe
alias kdel = kubectl delete
alias kgpo = kubectl get pod
alias kgd = kubectl get deployments
alias kc = kubectx
alias kns = kubens
alias kl = kubectl logs -f
alias ke = kubectl exec -it

use ~/.cache/starship/init.nu
