{ config, lib, user, features, ... }:

let
  # rebuild.sh keeps this symlink pointed at the repo.
  dotfiles = "${config.home.homeDirectory}/.dotfiles";
  # Canonical skills live under ai_agents_tools/. Linked into Cursor,
  # Claude Code, and ~/.agents so a new skill is one directory + one attr.
  agentSkillPaths = {
    agentic-harness = "skills/agentic-harness";
    code-standards = "skills/code-standards";
    enhanced-workflow = "skills/enhanced-workflow";
    loop = "skills/loop";
    nix-install = "skills/nix-install";
    performance-journaler = "skills/performance-journaler";
    pr-babysitting = "skills/pr-babysitting";
    pytest-coverage-incremental = "skills/pytest-coverage-incremental";
    repo-navigation = "skills/repo-navigation";
    caveman = "third_party/skills/caveman";
    skill-creator = "third_party/skills/skill-creator";
    tdd-loop = "skills/tdd-loop";
  };
  # Providers that follow symlinks — managed by home.file as symlinks.
  agentSkillHomes = [ ".cursor/skills" ".agents/skills" ".claude/skills" ];
  agentSkillFiles = builtins.listToAttrs (
    builtins.concatMap
      (
        skill:
        map (home: {
          name = "${home}/${skill}";
          value = {
            source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/${agentSkillPaths.${skill}}";
            force = true;
          };
        }) agentSkillHomes
      )
      (builtins.attrNames agentSkillPaths)
  );
in

{
  home.username = user;
  home.homeDirectory = "/Users/${user}";
  home.stateVersion = "24.11";

  fonts.fontconfig.enable = true;

  # Edit-in-place: the real file stays in the repo, ~/.config just points at it.
  home.file = agentSkillFiles // {
    ".config/wezterm" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/wezterm";
      force = true;
    };
    ".config/starship.toml" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/starship.toml";
      force = true;
    };
    ".config/tmux" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/tmux";
      force = true;
    };
    ".config/nvim" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/nvim";
      force = true;
    };
    ".config/aerospace" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/aerospace";
      force = true;
    };
    ".config/sketchybar" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/sketchybar";
      force = true;
    };
    ".config/borders" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/borders";
      force = true;
    };
    ".config/tuicr" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/tuicr";
      force = true;
    };
    # Rules: same SOT file, Cursor wants .mdc, Agents wants AGENTS.md.
    # Claude already reads ~/.claude/CLAUDE.md — leave that alone.
    ".cursor/rules/AGENTS.mdc" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/rules/AGENTS.md";
      force = true;
    };
    ".agents/rules/AGENTS.md" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/rules/AGENTS.md";
      force = true;
    };
    ".claude/CLAUDE.md" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/rules/AGENTS.md";
      force = true;
    };
    # Caveman always-on. Cursor skills are discover-only (no alwaysApply);
    # official always-on path is a rule file (caveman --with-init).
    ".cursor/rules/caveman.mdc" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/rules/caveman.md";
      force = true;
    };
    ".agents/rules/caveman.md" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/rules/caveman.md";
      force = true;
    };
  };

  # SbarLua + C helpers for the Lua SketchyBar config (phucisstupid).
  home.activation.sketchybarLua = lib.mkIf features.sketchybar (lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
    if [ ! -f "$HOME/.local/share/sketchybar_lua/sketchybar.so" ]; then
      tmp=$(mktemp -d)
      git clone --depth 1 https://github.com/FelixKratz/SbarLua.git "$tmp/SbarLua"
      make -C "$tmp/SbarLua" install
      rm -rf "$tmp"
    fi
    if [ -d "$HOME/.config/sketchybar/helpers" ]; then
      make -C "$HOME/.config/sketchybar/helpers"
    fi
  '');

  # Flag off: unload KeepAlive agent then quit, else it respawns.
  home.activation.disableSketchybar = lib.mkIf (!features.sketchybar) (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      uid="$(id -u)"
      /bin/launchctl bootout "gui/$uid/org.nixos.sketchybar" 2>/dev/null || true
      /usr/bin/killall sketchybar 2>/dev/null || true
    ''
  );

  # Flag off: apply start-at-login = false if the GUI is up, then quit it.
  # Also drop leftover login agents from when toml used to set start-at-login.
  home.activation.disableAerospace = lib.mkIf (!features.aerospace) (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      uid="$(id -u)"
      if /usr/bin/pgrep -xq AeroSpace; then
        /opt/homebrew/bin/aerospace reload-config 2>/dev/null || true
      fi
      /usr/bin/killall AeroSpace 2>/dev/null || true
      for label in bobko.aerospace bobko.aero.space; do
        /bin/launchctl bootout "gui/$uid/$label" 2>/dev/null || true
        rm -f "$HOME/Library/LaunchAgents/''${label}.plist"
      done
    ''
  );

  programs.zsh = {
    enable = true;
    autosuggestion.enable = true;      # ghost text from history
    syntaxHighlighting.enable = true;  # commands turn green when valid
    initContent = ''
      bindkey '^f' autosuggest-accept
      # Option+Right: accept one word of the ghost suggestion (not the whole line).
      bindkey "^[[1;3C" forward-word
      bindkey "^[[1;3D" backward-word

      # Dotfiles secrets (GITHUB_TOKEN, etc.) — edit secrets/env.sh locally.
      if [[ -f "${dotfiles}/secrets/env.sh" ]]; then
        source "${dotfiles}/secrets/env.sh"
      fi

      # API tokens and env snippets kept in ~/.oh-my-zsh/custom/ (directory untouched).
      for _token_file in "''${HOME}"/.oh-my-zsh/custom/*.zsh(N); do
        [[ "$(basename "$_token_file")" == example.zsh ]] && continue
        source "$_token_file"
      done
      unset _token_file

   '';
    shellAliases = {
      ".." = "cd ..";
      l = "ls -la";
      ll = "ls -l";
      lsa = "ls -a";
      lt = "eza --tree --level=2 --long --icons --git";
      v = "nvim";
      vim = "nvim";
      vi = "nvim";
      as = "aerospace";
      oc = "opencode";
      add = "git add .";
      commit = "git commit -m ";
      push = "git push";
      pull = "git pull";
      gd = "git diff --name-only";
      gc = "git commit -m";
      gca = "git commit -a -m";
      gp = "git push origin HEAD";
      gpu = "git pull origin";
      gst = "git status";
      gdiff = "git diff";
      gco = "git checkout";
      gb = "git branch";
      gba = "git branch -a";
      gadd = "git add";
      ga = "git add -p";
      gcoall = "git checkout -- .";
      gr = "git remote";
      gre = "git reset";
      k = "kubectl";
      ka = "kubectl apply -f";
      kg = "kubectl get";
      kd = "kubectl describe";
      kdel = "kubectl delete";
      kgpo = "kubectl get pod";
      kgd = "kubectl get deployments";
      kc = "kubectx";
      kns = "kubens";
      kl = "kubectl logs -f";
      ke = "kubectl exec -it";
    };
  };


}
