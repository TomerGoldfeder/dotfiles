{ user, pkgs, herdr, ... }:

let
  aerospace-cheatsheet = pkgs.callPackage ./home/bin/aerospace-cheatsheet { };
  hp = pkgs.callPackage ./home/bin/hs { };
in

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
    finder.CreateDesktop = false;
    trackpad.Clicking = true;
  };

  # nix-darwin's set-environment overwrites PATH and omits Homebrew, so
  # GUI terminals (WezTerm) never see brew formulae like tmux.
  environment.extraInit = ''
    export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
  '';
  environment.variables.LANG = "en_US.UTF-8";
  # Spark 3.1 / PySpark: local JVM. ~/.oh-my-zsh/custom/java.zsh still
  # points at missing Temurin 8; home.nix re-exports this after that file.
  environment.variables.JAVA_HOME = "${pkgs.jdk8.home}";

  environment.systemPackages = (with pkgs; [
    neovim
    starship
    fzf # herdr pane-navigator (and other TUIs)
    # LazyVim lang.markdown lints via nvim-lint; mason cannot install these
    # without npm. Put the binaries on PATH instead of :MasonInstall.
    markdownlint-cli2
    markdown-toc
    nodejs
    kubectl
    jq
    jdk8 # Zulu 8; Spark 3.1.3 (Java 8 or 11). Native aarch64, not Temurin cask.
    cargo # herdr plugin install builds Rust plugins from source
    rustc
  ]) ++ [
    herdr.packages.${pkgs.system}.default
    aerospace-cheatsheet
    hs
  ];

  fonts.packages = with pkgs; [
    nerd-fonts.jetbrains-mono
    nerd-fonts.symbols-only # SketchyBar + future nerd glyphs (Symbols Nerd Font)
  ];

  programs.zsh.enable = true;
  programs.zsh.promptInit = ''
    eval "$(starship init zsh)"
  '';

  homebrew = {
    enable = true;
    onActivation.cleanup = "zap";
    onActivation.autoUpdate = true;
    onActivation.extraFlags = [ "--force" ];
    brews = [
      "tmux"
      "glab"
      "tuicr" # code-review TUI (homebrew-core)
      "opencode"
      "pi-coding-agent"
      "fzf" # pane-navigator; also in systemPackages — brew covers herdr PATH until rebuild
      {
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
      "font-sketchybar-app-font"
      "claude-code"
      "cursor-cli"
      # Root-owned apps (they self-update). Listed so zap does not try to
      # delete them — Homebrew cannot remove root CodeResources files.
      "google-chrome"
      "docker-desktop"
    ];
  };

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

  launchd.user.agents.aerospace-cheatsheet = {
    serviceConfig = {
      ProgramArguments = [
        "/run/current-system/sw/bin/aerospace-cheatsheet"
        "--gui"
      ];
      KeepAlive = true;
      RunAtLoad = true;
      EnvironmentVariables = {
        PATH = "/run/current-system/sw/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/sbin:/usr/bin:/bin:/sbin";
        LANG = "en_US.UTF-8";
      };
    };
  };
}
