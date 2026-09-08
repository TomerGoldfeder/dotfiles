{ user, pkgs, lib, features, ... }:

{
  # Determinate already manages the Nix daemon, so nix-darwin shouldn't.
  nix.enable = false;

  nixpkgs.hostPlatform = "aarch64-darwin";

  system.primaryUser = user;
  users.users.${user} = {
    home = "/Users/${user}";
  };
  system.stateVersion = 6;

  system.defaults = {
    NSGlobalDomain._HIHideMenuBar = true; # SketchyBar replaces the menu bar
    finder.CreateDesktop = false;
    trackpad.Clicking = true;
  };

  # nix-darwin's set-environment overwrites PATH and omits Homebrew, so
  # GUI terminals (WezTerm) never see brew formulae like tmux.
  environment.extraInit = ''
    export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
  '';
  environment.variables.LANG = "en_US.UTF-8";

  environment.systemPackages = with pkgs; [
    neovim
    starship
    eza
    # LazyVim lang.markdown lints via nvim-lint; mason cannot install these
    # without npm. Put the binaries on PATH instead of :MasonInstall.
    markdownlint-cli2
    markdown-toc
    nodejs
    jq # SketchyBar weather + Spotify plugins
    kubectl
    # Bundled CLI inside bb.app — not in nixpkgs. Wrapper so `bb` is on PATH
    # for scripts and non-interactive shells, not only a zsh alias.
    (writeShellScriptBin "bb" ''
      bb_bin="/Applications/bb.app/Contents/Resources/app.asar.unpacked/node_modules/bb-app/host-daemon/dist/bb"
      if [ ! -x "$bb_bin" ]; then
        echo "bb CLI not found at $bb_bin (is bb.app installed?)" >&2
        echo "Headless alternative: npx --yes --allow-scripts=better-sqlite3,node-pty,@parcel/watcher bb-app@latest" >&2
        exit 127
      fi
      exec "$bb_bin" "$@"
    '')
    (writeShellScriptBin "bb-sync" ''
      exec bash "$HOME/.config/bb/sync.sh" "$@"
    '')
  ];

  fonts.packages = with pkgs; [
    nerd-fonts.jetbrains-mono
  ];

  programs.zsh.enable = true;
  programs.zsh.promptInit = ''
    eval "$(starship init zsh)"
  '';

  # Start SketchyBar / JankyBorders in the Aqua session. Homebrew
  # `brew services` cannot do this during darwin-rebuild (root → user
  # launchctl bootstrap → error 5).
  launchd.user.agents.sketchybar = {
    serviceConfig = {
      ProgramArguments = [ "/opt/homebrew/bin/sketchybar" ];
      KeepAlive = true;
      RunAtLoad = true;
      EnvironmentVariables = {
        PATH = "/opt/homebrew/bin:/opt/homebrew/sbin:/run/current-system/sw/bin:/usr/sbin:/usr/bin:/bin:/sbin";
        LANG = "en_US.UTF-8";
        DOTFILES_WINDOW_MANAGER = if features.aerospace then "aerospace" else "macos_native";
      };
    };
  };
  # `open` exits after launching the GUI; KeepAlive would spam. Flag off: no agent.
  launchd.user.agents.aerospace = lib.mkIf features.aerospace {
    serviceConfig = {
      ProgramArguments = [ "/usr/bin/open" "-a" "AeroSpace" ];
      RunAtLoad = true;
      KeepAlive = false;
    };
  };
  launchd.user.agents.borders = {
    serviceConfig = {
      # No args → borders executes ~/.config/borders/bordersrc
      ProgramArguments = [ "/opt/homebrew/bin/borders" ];
      KeepAlive = true;
      RunAtLoad = true;
      EnvironmentVariables = {
        PATH = "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/bin:/bin:/usr/sbin:/sbin";
        LANG = "en_US.UTF-8";
      };
    };
  };

  homebrew = {
    enable = true;
    onActivation.cleanup = "zap";
    onActivation.autoUpdate = true;
    onActivation.extraFlags = [ "--force" ];
    brews = [
      "tmux"
      "lua"
      "switchaudio-osx"
      "media-control"
      "glab"
      "tuicr" # code-review TUI (homebrew-core)
      {
        # Do not start_service/restart_service here: darwin-rebuild runs as
        # root and `launchctl bootstrap user/…` then fails with I/O error 5.
        name = "FelixKratz/formulae/sketchybar";
        trusted = true;
      }
      {
        name = "FelixKratz/formulae/borders";
        trusted = true;
      }
    ];
    taps = [
      "nikitabobko/tap"
      "FelixKratz/formulae"
    ];
    casks = [
      "bb" # getbb.app desktop (arm64). CLI on PATH is the wrapper above.
      "wezterm"
      "nikitabobko/tap/aerospace"
      "font-jetbrains-mono-nerd-font"
      "font-maple-mono-nf" # SketchyBar (phucisstupid)
      "font-sketchybar-app-font"
      # Root-owned apps (they self-update). Listed so zap does not try to
      # delete them — Homebrew cannot remove root CodeResources files.
      "google-chrome"
      "docker-desktop"
    ];
  };
}
