{ config, lib, user, ... }:

let
  # rebuild.sh keeps this symlink pointed at the repo.
  dotfiles = "${config.home.homeDirectory}/.dotfiles";
in

{
  home.username = user;
  home.homeDirectory = "/Users/${user}";
  home.stateVersion = "24.11";

  fonts.fontconfig.enable = true;

  # Edit-in-place: the real file stays in the repo, ~/.config just points at it.
  home.file = {
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
    # macOS nu reads ~/Library/Application Support/nushell (not ~/.config)
    # unless XDG_CONFIG_HOME is set. History stays in Application Support.
    ".config/nushell/config.nu" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/nushell/config.nu";
      force = true;
    };
    ".config/nushell/env.nu" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/nushell/env.nu";
      force = true;
    };
    "Library/Application Support/nushell/config.nu" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/nushell/config.nu";
      force = true;
    };
    "Library/Application Support/nushell/env.nu" = {
      source = config.lib.file.mkOutOfStoreSymlink "${dotfiles}/home/.config/nushell/env.nu";
      force = true;
    };
  };

  # SbarLua + C helpers for the Lua SketchyBar config (phucisstupid).
  home.activation.sketchybarLua = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
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
  '';

  programs.zsh = {
    enable = true;
    autosuggestion.enable = true;      # ghost text from history
    syntaxHighlighting.enable = true;  # commands turn green when valid
    initContent = ''
      bindkey '^f' autosuggest-accept
      bindkey "^[[1;3C" forward-word   # Option + Right
      bindkey "^[[1;3D" backward-word  # Option + Left

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
      add = "git add .";
      commit = "git commit -m ";
      push = "git push";
      pull = "git pull";
      gd = "git diff --name-only";
      oc = "opencode";
      vim = "nvim";
      vi = "nvim";
      lsa = "ls -a";
    };
  };


}
