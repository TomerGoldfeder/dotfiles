{ user, pkgs, herdr, ... }:

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
    jdk8 # Zulu 8; Spark 3.1.3 (Java 8 or 11). Native aarch64, not Temurin cask.
    cargo # herdr plugin install builds Rust plugins from source
    rustc
  ]) ++ [ herdr.packages.${pkgs.system}.default ];

  fonts.packages = with pkgs; [
    nerd-fonts.jetbrains-mono
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
    ];
    casks = [
      "wezterm"
      "font-jetbrains-mono-nerd-font"
      "claude-code"
      "cursor-cli"
      # Root-owned apps (they self-update). Listed so zap does not try to
      # delete them — Homebrew cannot remove root CodeResources files.
      "google-chrome"
      "docker-desktop"
    ];
  };
}
