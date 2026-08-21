{ user, pkgs, ... }:

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
    nushell
    # LazyVim lang.markdown lints via nvim-lint; mason cannot install these
    # without npm. Put the binaries on PATH instead of :MasonInstall.
    markdownlint-cli2
    markdown-toc
    nodejs
    jq # SketchyBar weather + Spotify plugins
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
      };
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
