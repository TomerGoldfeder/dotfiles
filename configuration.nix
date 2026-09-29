{ user, pkgs, herdr, ... }:

let
  h = pkgs.callPackage ./home/bin/hs { };
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

  # nix-darwin's set-environment overwrites PATH and omits Homebrew.
  environment.extraInit = ''
    export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
  '';
  environment.variables.LANG = "en_US.UTF-8";
  environment.variables.JAVA_HOME = "${pkgs.jdk8.home}";

  environment.systemPackages = (with pkgs; [
    neovim
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
    h
  ];

  fonts.packages = with pkgs; [
    nerd-fonts.jetbrains-mono
  ];

  programs.zsh.enable = true;

  homebrew = {
    enable = true;
    onActivation.cleanup = "zap";
    onActivation.autoUpdate = true;
    onActivation.extraFlags = [ "--force" ];
    brews = [
      "git"
      "glab"
      "opencode"
      "pi-coding-agent"
      "fzf" # pane-navigator; also in systemPackages — brew covers herdr PATH until rebuild
      "eza"
      "powerlevel10k"
      # yazi + runtime deps (https://yazi-rs.github.io/docs/installation)
      "yazi"
      "sevenzip"
      "jq"
      "poppler"
      "fd"
      "ripgrep"
      "zoxide"
      "resvg"
      {
        name = "ffmpeg-full";
        link = "overwrite";
      }
      {
        name = "imagemagick-full";
        link = "overwrite";
      }
    ];
    casks = [
      "wezterm"
      "font-jetbrains-mono-nerd-font"
      "font-symbols-only-nerd-font" # yazi icons
      "claude-code"
      "cursor-cli"
      # Root-owned apps (they self-update). Listed so zap does not try to
      # delete them — Homebrew cannot remove root CodeResources files.
      "google-chrome"
      "docker-desktop"
    ];
  };
}
