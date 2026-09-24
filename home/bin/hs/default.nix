{ lib, buildGoModule }:

buildGoModule {
  pname = "hs";
  version = "0.1.0";
  src = ./.;

  vendorHash = "sha256-uwBJAqN4sIepiiJf9lCDumLqfKJEowQO2tOiSWD3Fig=";

  ldflags = [ "-s" "-w" ];

  meta = with lib; {
    description = "Herdr session picker (glyph command-palette + spinner)";
    mainProgram = "hs";
    platforms = platforms.unix;
  };
}
