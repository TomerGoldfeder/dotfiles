# Adapted from https://github.com/omerxx/dotfiles/blob/master/nushell/env.nu
# (nushell 0.95 → 0.114: $nu.home-dir, std/util path add; no mise/zoxide/carapace/turso)

use std/util "path add"

# Last path add is first on PATH. Nix before Homebrew so nvim/eza/starship win.
path add "/opt/homebrew/bin"
path add "/opt/homebrew/sbin"
path add "/nix/var/nix/profiles/default/bin"
path add "/run/current-system/sw/bin"

$env.EDITOR = "nvim"
$env.STARSHIP_CONFIG = ($nu.home-dir | path join ".config" "starship.toml")

# KEY=VALUE from the zsh secrets file (export prefix and comments ignored).
let secrets = ($nu.home-dir | path join ".dotfiles" "secrets" "env.sh")
if ($secrets | path exists) {
  open $secrets
  | lines
  | str trim
  | where {|l| $l != "" and not ($l | str starts-with "#")}
  | each {|l|
      let line = ($l | str replace -r '^export\s+' '')
      let eq = ($line | str index-of "=")
      if $eq != null {
        let key = ($line | str substring 0..<$eq | str trim)
        let val = (
          $line
          | str substring ($eq + 1)..
          | str trim
          | str trim -c '"'
          | str trim -c "'"
        )
        {key: $key, val: $val}
      }
    }
  | where {|r| $r != null and $r.key != ""}
  | reduce --fold {} {|it, acc| $acc | upsert $it.key $it.val}
  | load-env
}

let starship_dir = ($nu.home-dir | path join ".cache" "starship")
mkdir $starship_dir
starship init nu | save -f ($starship_dir | path join "init.nu")
