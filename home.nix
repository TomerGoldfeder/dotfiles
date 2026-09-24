{ config, lib, pkgs, user, herdr, ... }:

let
  # rebuild.sh keeps this symlink pointed at the repo.
  dotfiles = "${config.home.homeDirectory}/.dotfiles";
  # Canonical skills live under ai_agents_tools/skills/. Linked into every
  # agent home that follows Agent Skills — drop a directory, rebuild.
  agentSkillsDir = ./ai_agents_tools/skills;
  agentSkillEntries = builtins.readDir agentSkillsDir;
  agentSkillNames = builtins.filter
    (name: agentSkillEntries.${name} == "directory")
    (builtins.attrNames agentSkillEntries);
  # Cursor / Claude Code / Agents / OpenCode / Pi
  agentSkillHomes = [
    ".cursor/skills"
    ".agents/skills"
    ".claude/skills"
    ".config/opencode/skills"
    ".pi/agent/skills"
  ];
  agentSkillFiles = builtins.listToAttrs (
    builtins.concatMap
      (
        skill:
        map (home: {
          name = "${home}/${skill}";
          value = {
            source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/skills/${skill}";
            force = true;
          };
        }) agentSkillHomes
      )
      agentSkillNames
  );
  # Flake-input skill trees (store paths). Basename = skill name. Plain
  # source + force — not mkOutOfStoreSymlink. Example: herdr.
  agentSkillStorePaths = [ "${herdr}/skills/herdr" ];
  agentSkillStoreFiles = builtins.listToAttrs (
    builtins.concatMap
      (
        storePath:
        let
          # Attribute names must not carry store context from the path.
          skill = builtins.unsafeDiscardStringContext (baseNameOf storePath);
        in
        map (home: {
          name = "${home}/${skill}";
          value = {
            source = storePath;
            force = true;
          };
        }) agentSkillHomes
      )
      agentSkillStorePaths
  );
  # Same AGENTS.md SOT; each harness wants its own path/name.
  agentRuleFiles = {
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
    ".config/opencode/AGENTS.md" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/rules/AGENTS.md";
      force = true;
    };
    ".pi/agent/AGENTS.md" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/ai_agents_tools/rules/AGENTS.md";
      force = true;
    };
  };
in

{
  home.username = user;
  home.homeDirectory = "/Users/${user}";
  home.stateVersion = "24.11";

  fonts.fontconfig.enable = true;

  # Edit-in-place: the real file stays in the repo, ~/.config just points at it.
  home.file = agentSkillFiles // agentSkillStoreFiles // agentRuleFiles // {
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
    ".config/tuicr" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/tuicr";
      force = true;
    };
    ".config/herdr/config.toml" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/herdr/config.toml";
      force = true;
    };
    ".config/herdr/plugins.list" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/herdr/plugins.list";
      force = true;
    };
    ".config/herdr/int_plugins.list" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/herdr/int_plugins.list";
      force = true;
    };
    ".config/aerospace/aerospace.toml" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/aerospace/aerospace.toml";
      force = true;
    };
    ".config/borders" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/borders";
      force = true;
    };
    ".config/sketchybar" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/sketchybar";
      force = true;
    };
    # compinit only autoloads a file named _git. The bash script must sit
    # beside it; git-completion.zsh looks there first.
    ".zsh/completions/_git" = {
      source = "${pkgs.git}/share/git/contrib/completion/git-completion.zsh";
    };
    ".zsh/completions/git-completion.bash" = {
      source = "${pkgs.git}/share/git/contrib/completion/git-completion.bash";
    };
  };

  # Create-once seed for ~/.second_brain_vault. If the directory already
  # exists, leave it alone (never clobber wiki/schema/index/log).
  home.activation.secondBrainVault = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    if [ ! -d "$HOME/.second_brain_vault" ]; then
      cp -R "${dotfiles}/ai_agents_tools/skills/second-brain/vault-seed" \
        "$HOME/.second_brain_vault"
      find "$HOME/.second_brain_vault" -name .gitkeep -delete
    fi
  '';

  # Load SketchyBar after ~/.config/sketchybar symlink exists (launchd may
  # have started the daemon earlier with no config).
  home.activation.sketchybarConfig = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
    if command -v sketchybar >/dev/null && [ -x "$HOME/.config/sketchybar/sketchybarrc" ]; then
      sketchybar --reload
    fi
  '';

  # Ensure listed Herdr plugins are installed (idempotent reinstall).
  home.activation.herdrPlugins = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    export PATH="/run/current-system/sw/bin:/opt/homebrew/bin:$PATH"
    list="${dotfiles}/home/.config/herdr/plugins.list"
    if [ ! -f "$list" ]; then
      echo "herdr plugins list missing: $list" >&2
      exit 1
    fi
    if ! command -v herdr >/dev/null; then
      echo "herdr not on PATH during activation; skip plugin install" >&2
      exit 1
    fi
    while IFS= read -r plugin || [ -n "$plugin" ]; do
      case "$plugin" in
        ""|\#*) continue ;;
      esac
      echo "herdr plugin install $plugin"
      # Herdr server may be down during darwin-rebuild; do not block HM symlinks.
      herdr plugin install "$plugin" --yes || {
        echo "herdr plugin install failed: $plugin (continuing)" >&2
      }
    done < "$list"
    int_list="${dotfiles}/home/.config/herdr/int_plugins.list"
    herdr_config="${dotfiles}/home/.config/herdr"
    if [ ! -f "$int_list" ]; then
      echo "herdr internal plugins list missing: $int_list" >&2
      exit 1
    fi
    while IFS= read -r plugin || [ -n "$plugin" ]; do
      case "$plugin" in
        ""|\#*) continue ;;
      esac
      echo "herdr plugin link $herdr_config/$plugin"
      herdr plugin link "$herdr_config/$plugin" || {
        echo "herdr plugin link failed: $plugin (continuing)" >&2
      }
    done < "$int_list"
  '';

  # Ctrl-R history widget. Integration also binds Tab; fzf-tab is sourced
  # later (order 950) so Tab stays the completion menu.
  programs.fzf = {
    enable = true;
    enableZshIntegration = true;
  };

  programs.zsh = {
    enable = true;
    autosuggestion.enable = true;      # ghost text from history
    syntaxHighlighting.enable = true;  # commands turn green when valid
    initContent = lib.mkMerge [
      (lib.mkOrder 400 ''
        # Before compinit, so `git <Tab>` can complete subcommands.
        fpath=("''${HOME}/.zsh/completions" $fpath)
      '')
      (lib.mkOrder 950 ''
        zstyle ':completion:*:descriptions' format '[%d]'
        zstyle ':completion:*' menu no
        source ${pkgs.zsh-fzf-tab}/share/fzf-tab/fzf-tab.plugin.zsh
      '')
      ''
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

      # java.zsh exports a missing Temurin 8 path. Prefer the nix-darwin JDK.
      export JAVA_HOME="${pkgs.jdk8.home}"
      export PATH="$JAVA_HOME/bin:$PATH"
      ''
    ];
    shellAliases = {
      ".." = "cd ..";
      # listing dirs
      ls = "ls --color";
      lsa = "ls -la";
      # neovim 
      v = "nvim";
      vim = "nvim";
      vi = "nvim";
      # agents init
      oc = "opencode";
      ca = "cursor-agent";
      cc = "claude";
      # pr review
      tt = "tuicr tui";
      add = "git add .";
      commit = "git commit -m ";
      push = "git push";
      pull = "git pull";
      gd = "git diff --name-only";
      gst = "git status";
      gco = "git checkout";
      gb = "git branch";
      gba = "git branch -a";
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
