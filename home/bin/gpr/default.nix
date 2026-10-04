{ lib, buildGoModule }:

buildGoModule {
  pname = "gpr";
  version = "0.1.0";
  src = ./.;

  vendorHash = "sha256-+A/Pmbo230e9P6iEL67W4Pqlpf3kmq7bro9nFAozstA=";

  ldflags = [ "-s" "-w" ];

  meta = with lib; {
    description = "Interactive gh pr create TUI (Tokyo Night midnight)";
    mainProgram = "gpr";
    platforms = platforms.unix;
  };
}
