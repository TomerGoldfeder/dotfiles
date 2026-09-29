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

  home.sessionPath = [ "${dotfiles}/home/bin" ];

  fonts.fontconfig.enable = true;

  # Edit-in-place: the real file stays in the repo, ~/.config just points at it.
  home.file = agentSkillFiles // agentSkillStoreFiles // agentRuleFiles // {
    ".zshrc" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/zsh/zshrc";
      force = true;
    };
    ".p10k.zsh" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/zsh/p10k.zsh";
      force = true;
    };
    ".config/wezterm" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/wezterm";
      force = true;
    };
    ".config/nvim" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/nvim";
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
    ".config/yazi" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/yazi";
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
}
